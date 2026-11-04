import csv
from decimal import Decimal

from price_tracker.cli import excel_safe, write_csv
from price_tracker.models import Item


def test_formula_like_titles_stay_text(tmp_path):
    # A title on a scraped page is controlled by that site; Excel must not run it as a formula.
    items = [
        Item("https://shop.example/1", '=HYPERLINK("http://x","click")', Decimal("9.99")),
        Item("https://shop.example/2", "Normal book", Decimal("5.00"), in_stock=False),
    ]
    path = tmp_path / "out.csv"
    write_csv(items, path)
    with path.open(encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert rows[0] == ["title", "price", "in_stock", "url"]
    assert rows[1][0].startswith("'=HYPERLINK")
    assert rows[2] == ["Normal book", "5.00", "0", "https://shop.example/2"]


def test_excel_safe():
    assert excel_safe("+1") == "'+1" and excel_safe("@x") == "'@x" and excel_safe("Book") == "Book"
