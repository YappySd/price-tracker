"""SQLite storage: current price per item plus a history of every price change."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from decimal import Decimal

from .models import Item, PriceChange

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    url TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    price TEXT NOT NULL,
    in_stock INTEGER NOT NULL,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS price_history (
    url TEXT NOT NULL REFERENCES items(url),
    price TEXT NOT NULL,
    seen_at TEXT NOT NULL
);
"""


class Storage:
    def __init__(self, path: str) -> None:
        self._conn = sqlite3.connect(path)
        self._conn.executescript(SCHEMA)

    def close(self) -> None:
        self._conn.close()

    def save(self, items: list[Item]) -> list[PriceChange]:
        """Store the items and return those whose price differs from the last run."""
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        changes: list[PriceChange] = []
        with self._conn:
            for item in items:
                row = self._conn.execute(
                    "SELECT price FROM items WHERE url = ?", (item.url,)
                ).fetchone()
                if row is None:
                    self._conn.execute(
                        "INSERT INTO items (url, title, price, in_stock, first_seen, last_seen) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (item.url, item.title, str(item.price), int(item.in_stock), now, now),
                    )
                    self._conn.execute(
                        "INSERT INTO price_history (url, price, seen_at) VALUES (?, ?, ?)",
                        (item.url, str(item.price), now),
                    )
                    continue

                old_price = Decimal(row[0])
                if old_price != item.price:
                    changes.append(PriceChange(item, old_price))
                    self._conn.execute(
                        "INSERT INTO price_history (url, price, seen_at) VALUES (?, ?, ?)",
                        (item.url, str(item.price), now),
                    )
                self._conn.execute(
                    "UPDATE items SET title = ?, price = ?, in_stock = ?, last_seen = ? "
                    "WHERE url = ?",
                    (item.title, str(item.price), int(item.in_stock), now, item.url),
                )
        return changes

    def history(self, url: str) -> list[tuple[str, Decimal]]:
        rows = self._conn.execute(
            "SELECT seen_at, price FROM price_history WHERE url = ? ORDER BY rowid", (url,)
        ).fetchall()
        return [(seen_at, Decimal(price)) for seen_at, price in rows]
