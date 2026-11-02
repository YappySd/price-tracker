"""HTML parsing for books.toscrape.com, a public sandbox site made for scraping practice."""
from __future__ import annotations

import logging
import re
from decimal import Decimal
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .models import Item

logger = logging.getLogger(__name__)


def parse_price(text: str) -> Decimal:
    """'£51.77' -> Decimal('51.77'). Any currency symbol or stray characters are ignored."""
    cleaned = re.sub(r"[^\d.]", "", text)
    if not cleaned:
        raise ValueError(f"no price found in {text!r}")
    return Decimal(cleaned)


def parse_catalog(html: str, page_url: str) -> tuple[list[Item], str | None]:
    """Return (items on the page, absolute URL of the next page or None)."""
    soup = BeautifulSoup(html, "html.parser")
    items: list[Item] = []

    for block in soup.select("article.product_pod"):
        link = block.select_one("h3 a")
        price_tag = block.select_one("p.price_color")
        if link is None or price_tag is None or not link.get("href"):
            logger.warning("Skipping a product block with unexpected markup")
            continue
        try:
            price = parse_price(price_tag.get_text())
        except ValueError:
            logger.warning("Skipping %r: unreadable price", link.get("title"))
            continue

        availability = block.select_one("p.availability")
        in_stock = bool(availability and "in stock" in availability.get_text().lower())
        title = str(link.get("title") or link.get_text(strip=True))
        items.append(Item(urljoin(page_url, str(link["href"])), title, price, in_stock))

    next_link = soup.select_one("li.next a")
    next_url = urljoin(page_url, str(next_link["href"])) if next_link and next_link.get("href") else None
    return items, next_url
