"""
Generate product-style cutout images (transparent PNG) per menu item.

Coffee (BEV002) uses the bundled sample photo; other items get illustrated cutouts.

Requires: pip install Pillow

Usage:
  py manage.py seed_menu_item_images
  py manage.py seed_menu_item_images --force
"""
from django.core.management.base import BaseCommand

from inventory.models import MenuItem
from inventory.services.menu_image import assign_image_from_bytes
from inventory.services.menu_product_art import render_menu_product_image


class Command(BaseCommand):
    help = 'Generate product cutout PNGs and save to menu_items.image_data (BLOB).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Replace existing images',
        )

    def handle(self, *args, **options):
        try:
            from PIL import Image  # noqa: F401
        except ImportError:
            self.stderr.write('Install Pillow first: py -m pip install Pillow')
            return

        force = options['force']
        items = MenuItem.objects.filter(is_deleted=False).order_by('id')
        created = 0
        skipped = 0

        for item in items:
            if item.has_image and not force:
                skipped += 1
                continue

            data = render_menu_product_image(
                item.item_code,
                item.item_name,
                item.is_vegetarian,
            )
            assign_image_from_bytes(item, data, ext='png')
            created += 1
            self.stdout.write(f'  {item.item_code}: saved to database BLOB')

        self.stdout.write(
            self.style.SUCCESS(
                f'Done — {created} image(s) written, {skipped} skipped (use --force to replace).'
            )
        )
