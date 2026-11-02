from decimal import Decimal
from pathlib import Path

import pytest

from price_tracker.parser import parse_catalog, parse_price

FIXTURES = Path(__file__).parent / "fixtures"
BASE = "https://books.toscrape.com/index.html"


@pytest.mark.parametrize(
    ("text", "expected"),
    [("£51.77", "51.77"), ("Â£53.74", "53.74"), (" 10 ", "10"), ("USD 1.5", "1.5")],
)
def test_parse_price(text, expected):
    assert parse_price(text) == Decimal(expected)


def test_parse_price_without_digits_raises():
    with pytest.raises(ValueError):
        parse_price("free")


def test_parse_first_page():
    html = (FIXTURES / "page1.html").read_text(encoding="utf-8")
    items, next_url = parse_catalog(html, BASE)

    # the third block has no href and must be skipped, not crash the parser
    assert [i.title for i in items] == ["A Light in the Attic", "Tipping the Velvet"]
    assert items[0].price == Decimal("51.77")
    assert items[0].in_stock is True
    assert items[0].url == "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    assert items[1].in_stock is False
    assert next_url == "https://books.toscrape.com/catalogue/page-2.html"


def test_parse_last_page_has_no_next_and_resolves_relative_links():
    html = (FIXTURES / "page2.html").read_text(encoding="utf-8")
    items, next_url = parse_catalog(html, "https://books.toscrape.com/catalogue/page-2.html")

    assert next_url is None
    assert len(items) == 1
    assert items[0].url == "https://books.toscrape.com/catalogue/its-only-the-himalayas_981/index.html"
