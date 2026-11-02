"""Crawler test against an in-memory fake server (httpx.MockTransport): no network needed."""
from pathlib import Path

import httpx

from price_tracker.fetcher import crawl

FIXTURES = Path(__file__).parent / "fixtures"

PAGES = {
    "/index.html": "page1.html",
    "/catalogue/page-2.html": "page2.html",
}


def handler(request: httpx.Request) -> httpx.Response:
    name = PAGES.get(request.url.path)
    if name is None:
        return httpx.Response(404)
    return httpx.Response(200, text=(FIXTURES / name).read_text(encoding="utf-8"))


async def test_crawl_follows_next_links():
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        items = await crawl("https://books.toscrape.com/index.html", max_pages=5, delay=0, client=client)
    assert [i.title for i in items] == [
        "A Light in the Attic",
        "Tipping the Velvet",
        "It's Only the Himalayas",
    ]


async def test_crawl_respects_max_pages():
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        items = await crawl("https://books.toscrape.com/index.html", max_pages=1, delay=0, client=client)
    assert len(items) == 2
