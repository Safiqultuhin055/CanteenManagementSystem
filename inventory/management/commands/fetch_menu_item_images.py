"""
Fetch product photos from the web per menu item (Wikimedia Commons + TheMealDB).

Coffee (BEV002) uses your bundled sample image.

  py -m pip install requests Pillow duckduckgo-search
  py manage.py fetch_menu_item_images --force
  py manage.py fetch_menu_item_images --code LUN004
"""
from django.core.management.base import BaseCommand

from inventory.models import MenuItem
from inventory.services.menu_image_web import fetch_and_save_menu_item


class Command(BaseCommand):
    help = 'Download web product images and save to menu_items.image_data (BLOB).'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Replace existing images')
        parser.add_argument('--code', type=str, help='Only this item_code (e.g. LUN004)')
    def handle(self, *args, **options):
        try:
            import requests  # noqa: F401
        except ImportError:
            self.stderr.write(self.style.ERROR('Run: py -m pip install requests Pillow'))
            return

        qs = MenuItem.objects.filter(is_deleted=False).order_by('id')
        if options.get('code'):
            qs = qs.filter(item_code__iexact=options['code'].strip())

        force = options['force']

        ok = fail = skip = 0
        for item in qs:
            if item.has_image and not force:
                skip += 1
                self.stdout.write(f'  skip {item.item_code} (already has image)')
                continue

            self.stdout.write(f'  fetch {item.item_code} — {item.item_name}...')
            result = fetch_and_save_menu_item(item)
            if result:
                ok += 1
                self.stdout.write(self.style.SUCCESS(f'    -> saved to database ({result})'))
            else:
                fail += 1
                self.stdout.write(self.style.WARNING(f'    -> failed (try again or upload in admin)'))

        self.stdout.write(
            self.style.SUCCESS(f'Done: {ok} updated, {skip} skipped, {fail} failed.')
        )
