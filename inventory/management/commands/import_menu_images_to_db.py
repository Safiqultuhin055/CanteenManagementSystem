"""
Import existing media/menu_items/* files into menu_items.image_data BLOB.

Run once after enabling BLOB columns (database/22_menu_item_image_blob.sql).

  py manage.py import_menu_images_to_db
  py manage.py import_menu_images_to_db --force
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from inventory.models import MenuItem
from inventory.services.menu_image import content_type_for_ext, save_menu_item_image_bytes


class Command(BaseCommand):
    help = 'Load media/menu_items files into SQL Server image_data BLOB column.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Replace existing BLOB data')

    def handle(self, *args, **options):
        force = options['force']
        media_dir = Path(settings.MEDIA_ROOT) / 'menu_items'
        if not media_dir.is_dir():
            self.stderr.write(f'No folder: {media_dir}')
            return

        imported = skipped = missing = 0
        for item in MenuItem.objects.filter(is_deleted=False).order_by('item_code'):
            if item.has_image and not force:
                skipped += 1
                continue

            candidates = [
                media_dir / f'{item.item_code}.png',
                media_dir / f'{item.item_code}.jpg',
                media_dir / f'{item.item_code}.jpeg',
                media_dir / f'{item.item_code}.webp',
            ]
            if item.image_path:
                candidates.insert(0, Path(settings.MEDIA_ROOT) / item.image_path)

            source = next((p for p in candidates if p.is_file()), None)
            if not source:
                missing += 1
                self.stdout.write(self.style.WARNING(f'  skip {item.item_code}: no file on disk'))
                continue

            ext = source.suffix.lstrip('.') or 'png'
            data = source.read_bytes()
            save_menu_item_image_bytes(item, data, content_type_for_ext(ext))
            imported += 1
            self.stdout.write(f'  {item.item_code}: {source.name} -> BLOB ({len(data)} bytes)')

        self.stdout.write(
            self.style.SUCCESS(
                f'Done — {imported} imported, {skipped} skipped, {missing} missing file.'
            )
        )
