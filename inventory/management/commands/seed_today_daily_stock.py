"""
Create or update daily_food_stock for all active menu items (today's business date).

Usage:
  py manage.py seed_today_daily_stock
  py manage.py seed_today_daily_stock --qty 50
  py manage.py seed_today_daily_stock --force
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.business_date import get_business_date
from inventory.models import DailyFoodStock, MenuItem

# Default prepared qty by food category code prefix
DEFAULT_PREPARED_BY_CATEGORY = {
    'BRK': 40,
    'LUN': 60,
    'DIN': 50,
    'SNK': 80,
    'BEV': 100,
    'DES': 40,
    'SPL': 25,
    'CMB': 35,
}
FALLBACK_PREPARED = 50


def prepared_qty_for_item(menu_item, default_qty: int) -> int:
    code = (getattr(menu_item.category, 'category_code', None) or '')[:3].upper()
    return DEFAULT_PREPARED_BY_CATEGORY.get(code, default_qty)


class Command(BaseCommand):
    help = "Seed today's daily_food_stock rows for every active menu item."

    def add_arguments(self, parser):
        parser.add_argument(
            '--qty',
            type=int,
            default=FALLBACK_PREPARED,
            help=f'Default prepared quantity when category has no preset (default {FALLBACK_PREPARED})',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Update existing rows (prepared qty, unit price, is_available); keeps sold/waste',
        )
        parser.add_argument(
            '--date',
            type=str,
            help='Stock date YYYY-MM-DD (default: server business date)',
        )

    def handle(self, *args, **options):
        if options.get('date'):
            from datetime import datetime
            stock_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
        else:
            stock_date = get_business_date()

        default_qty = options['qty']
        force = options['force']
        now = timezone.now()

        items = MenuItem.objects.filter(
            is_active=True,
            is_deleted=False,
        ).select_related('category').order_by('id')

        created = updated = skipped = 0

        for item in items:
            prepared = prepared_qty_for_item(item, default_qty)
            existing = DailyFoodStock.objects.filter(
                menu_item_id=item.id,
                stock_date=stock_date,
                is_deleted=False,
            ).first()

            if existing:
                if not force:
                    skipped += 1
                    continue
                existing.prepared_quantity = prepared
                existing.unit_price = item.unit_price
                existing.is_available = True
                existing.is_active = True
                existing.ready_time = existing.ready_time or now
                existing.updated_at = now
                existing.save(update_fields=[
                    'prepared_quantity', 'unit_price', 'is_available', 'is_active',
                    'ready_time', 'updated_at',
                ])
                updated += 1
                self.stdout.write(
                    f'  update {item.item_code}: {prepared} prep (sold {existing.sold_quantity})'
                )
            else:
                DailyFoodStock.objects.create(
                    menu_item_id=item.id,
                    stock_date=stock_date,
                    prepared_quantity=prepared,
                    sold_quantity=0,
                    waste_quantity=0,
                    unit_price=item.unit_price,
                    ready_time=now,
                    is_available=True,
                    is_active=True,
                    is_deleted=False,
                )
                created += 1
                self.stdout.write(f'  create {item.item_code}: {prepared} prep @ Tk {item.unit_price}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Done for {stock_date}: {created} created, {updated} updated, {skipped} skipped '
                f'(use --force to refresh existing).'
            )
        )
