"""
Fetch product photos from the web per menu item (Wikimedia Commons + TheMealDB).

Coffee (BEV002) uses your bundled sample image.

  py -m pip install requests Pillow duckduckgo-search
  py manage.py fetch_menu_item_images --force
  py manage.py fetch_menu_item_images --code LUN004
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from inventory.models import MenuItem
from inventory.services.menu_image_web import fetch_and_save_menu_item


class Command(BaseCommand):
    help = 'Download web product images per menu item and update image_path.'

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
        settings.MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
        (settings.MEDIA_ROOT / 'menu_items').mkdir(parents=True, exist_ok=True)

        ok = fail = skip = 0
        for item in qs:
            if item.item_image and not force:
                skip += 1
                self.stdout.write(f'  skip {item.item_code} (already has image)')
                continue

            self.stdout.write(f'  fetch {item.item_code} — {item.item_name}...')
            rel = fetch_and_save_menu_item(item)
            if rel:
                ok += 1
                self.stdout.write(self.style.SUCCESS(f'    -> {rel}'))
            else:
                fail += 1
                self.stdout.write(self.style.WARNING(f'    -> failed (try again or upload in admin)'))

        self.stdout.write(
            self.style.SUCCESS(f'Done: {ok} updated, {skip} skipped, {fail} failed.')
        )
