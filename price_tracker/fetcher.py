"""Polite crawler: one request at a time, a pause between pages, a few retries."""
from __future__ import annotations

import asyncio
import logging

import httpx

from .models import Item
from .parser import parse_catalog

logger = logging.getLogger(__name__)

USER_AGENT = "price-tracker/1.0 (portfolio project; contact: see README)"
RETRIES = 3


async def fetch_html(client: httpx.AsyncClient, url: str) -> str:
    last_error: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
        except (httpx.TransportError, httpx.HTTPStatusError) as exc:
            last_error = exc
            logger.warning("Attempt %d/%d for %s failed: %s", attempt, RETRIES, url, exc)
            if attempt < RETRIES:
                await asyncio.sleep(2 ** attempt * 0.5)
    raise RuntimeError(f"Could not fetch {url}") from last_error


async def crawl(
    start_url: str,
    max_pages: int = 3,
    delay: float = 1.0,
    client: httpx.AsyncClient | None = None,
) -> list[Item]:
    """Follow 'next' links from start_url and collect items from up to max_pages pages."""
    own_client = client is None
    if client is None:
        client = httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT}, timeout=15.0, follow_redirects=True
        )
    items: list[Item] = []
    try:
        url: str | None = start_url
        for page_number in range(1, max_pages + 1):
            if url is None:
                break
            html = await fetch_html(client, url)
            page_items, url = parse_catalog(html, str(url))
            logger.info("Page %d: %d items", page_number, len(page_items))
            items.extend(page_items)
            if url is not None and page_number < max_pages and delay > 0:
                await asyncio.sleep(delay)
    finally:
        if own_client:
            await client.aclose()
    return items
