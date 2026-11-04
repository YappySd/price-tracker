from __future__ import annotations

import argparse
import asyncio
import csv
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from .fetcher import crawl
from .models import Item
from .notify import format_drops, send_telegram
from .storage import Storage

DEFAULT_URL = "https://books.toscrape.com/index.html"


# Titles come from someone else's website. Excel would run a cell starting with one of these
# as a formula, so such text is written with a leading apostrophe.
FORMULA_START = ("=", "+", "-", "@", chr(9), chr(13))  # chr(9) = tab, chr(13) = carriage return


def excel_safe(value: object) -> str:
    text = str(value)
    return "'" + text if text.startswith(FORMULA_START) else text


def write_csv(items: list[Item], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["title", "price", "in_stock", "url"])
        for item in items:
            writer.writerow([excel_safe(item.title), item.price, int(item.in_stock), excel_safe(item.url)])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="price-tracker", description="Collect prices from a catalog and report changes."
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="start page of the catalog")
    parser.add_argument("--pages", type=int, default=3, help="max pages to crawl (default 3)")
    parser.add_argument("--delay", type=float, default=1.0, help="seconds between requests")
    parser.add_argument("--db", default="prices.db", help="SQLite file (default prices.db)")
    parser.add_argument("--csv", type=Path, help="also write the result to this CSV file")
    parser.add_argument(
        "--notify", action="store_true", help="send price drops to Telegram (see .env.example)"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    items = asyncio.run(crawl(args.url, max_pages=args.pages, delay=args.delay))
    if not items:
        logging.error("No items found. Check the URL or the page structure.")
        return 1

    storage = Storage(args.db)
    try:
        changes = storage.save(items)
    finally:
        storage.close()

    print(f"Items collected: {len(items)}; price changes since last run: {len(changes)}")
    for change in changes:
        arrow = "↓" if change.is_drop else "↑"
        print(f"  {arrow} {change.item.title}: {change.old_price} -> {change.item.price}")

    if args.csv:
        write_csv(items, args.csv)
        print(f"CSV saved to {args.csv}")

    if args.notify:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not token or not chat_id:
            logging.error("--notify needs TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
            return 2
        message = format_drops(changes)
        if message:
            send_telegram(token, chat_id, message)
            print("Telegram notification sent")
        else:
            print("No price drops, nothing to send")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
