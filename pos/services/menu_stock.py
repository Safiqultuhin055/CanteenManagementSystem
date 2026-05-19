"""Today's daily food stock for POS menu display."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from core.business_date import get_business_date
from inventory.models import DailyFoodStock, MenuItem


@dataclass
class PosMenuStock:
    item: MenuItem
    stock: DailyFoodStock | None
    unit_price: Decimal
    prepared: int | None
    sold: int
    waste: int
    remaining: int | None
    tracked: bool
    sold_out: bool
    low_stock: bool

    @property
    def stock_label(self) -> str:
        if not self.tracked:
            return 'Open'
        if self.sold_out:
            return 'Sold out'
        return f'{self.remaining} left'

    @property
    def stock_level(self) -> str:
        """CSS hook: ok | low | out | open."""
        if not self.tracked:
            return 'open'
        if self.sold_out:
            return 'out'
        if self.remaining is not None and self.remaining <= 5:
            return 'low'
        return 'ok'


def build_pos_menu_stock(menu_items, stock_date=None) -> list[PosMenuStock]:
    """Attach today's daily_food_stock to each menu item for POS."""
    stock_date = stock_date or get_business_date()
    stock_rows = DailyFoodStock.objects.filter(
        stock_date=stock_date,
        is_deleted=False,
        is_active=True,
    )
    stock_by_item = {row.menu_item_id: row for row in stock_rows}

    result: list[PosMenuStock] = []
    for item in menu_items:
        stock = stock_by_item.get(item.id)
        if stock:
            remaining = max(
                0,
                int(stock.prepared_quantity or 0)
                - int(stock.sold_quantity or 0)
                - int(stock.waste_quantity or 0),
            )
            sold_out = not stock.is_available or remaining <= 0
            result.append(
                PosMenuStock(
                    item=item,
                    stock=stock,
                    unit_price=stock.unit_price,
                    prepared=int(stock.prepared_quantity or 0),
                    sold=int(stock.sold_quantity or 0),
                    waste=int(stock.waste_quantity or 0),
                    remaining=remaining,
                    tracked=True,
                    sold_out=sold_out,
                    low_stock=not sold_out and remaining <= 5,
                )
            )
        else:
            result.append(
                PosMenuStock(
                    item=item,
                    stock=None,
                    unit_price=item.unit_price,
                    prepared=None,
                    sold=0,
                    waste=0,
                    remaining=None,
                    tracked=False,
                    sold_out=False,
                    low_stock=False,
                )
            )
    return result
