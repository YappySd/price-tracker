"""Optional Telegram notifications about price drops."""
from __future__ import annotations

from html import escape

from .models import PriceChange


def format_drops(changes: list[PriceChange], currency: str = "£") -> str | None:
    """Build a message about price DROPS only. Returns None when there is nothing to report."""
    drops = [c for c in changes if c.is_drop]
    if not drops:
        return None
    lines = [f"<b>Цены снизились: {len(drops)}</b>"]
    for change in drops:
        item = change.item
        lines.append(
            f'<a href="{escape(item.url, quote=True)}">{escape(item.title)}</a>: '
            f"{currency}{change.old_price} → <b>{currency}{item.price}</b>"
        )
    return "\n".join(lines)


def send_telegram(token: str, chat_id: str, text: str) -> None:
    import httpx  # imported here so formatting stays usable (and testable) without network deps

    response = httpx.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=15.0,
    )
    response.raise_for_status()
