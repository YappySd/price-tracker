from decimal import Decimal

from price_tracker.models import Item
from price_tracker.notify import format_drops
from price_tracker.storage import Storage


def make_item(price: str, url: str = "https://example.com/a") -> Item:
    return Item(url=url, title="Book A", price=Decimal(price))


def test_first_run_stores_items_without_changes(tmp_path):
    storage = Storage(str(tmp_path / "prices.db"))
    assert storage.save([make_item("10.00")]) == []
    assert storage.history("https://example.com/a")[0][1] == Decimal("10.00")


def test_same_price_is_not_a_change(tmp_path):
    storage = Storage(str(tmp_path / "prices.db"))
    storage.save([make_item("10.00")])
    assert storage.save([make_item("10.00")]) == []
    assert len(storage.history("https://example.com/a")) == 1


def test_price_drop_and_rise_are_detected_and_recorded(tmp_path):
    storage = Storage(str(tmp_path / "prices.db"))
    storage.save([make_item("10.00")])

    drop = storage.save([make_item("8.50")])
    assert len(drop) == 1 and drop[0].is_drop
    assert drop[0].old_price == Decimal("10.00")

    rise = storage.save([make_item("9.00")])
    assert len(rise) == 1 and not rise[0].is_drop

    assert [p for _, p in storage.history("https://example.com/a")] == [
        Decimal("10.00"),
        Decimal("8.50"),
        Decimal("9.00"),
    ]


def test_format_drops_reports_only_drops(tmp_path):
    storage = Storage(str(tmp_path / "prices.db"))
    storage.save([make_item("10.00", "https://example.com/a"), make_item("5.00", "https://example.com/b")])
    changes = storage.save([make_item("8.00", "https://example.com/a"), make_item("6.00", "https://example.com/b")])

    message = format_drops(changes)
    assert message is not None
    assert "8.00" in message and "6.00" not in message


def test_format_drops_returns_none_without_drops():
    assert format_drops([]) is None
