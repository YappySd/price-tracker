from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Item:
    url: str
    title: str
    price: Decimal
    in_stock: bool = True


@dataclass(frozen=True)
class PriceChange:
    item: Item
    old_price: Decimal

    @property
    def is_drop(self) -> bool:
        return self.item.price < self.old_price
