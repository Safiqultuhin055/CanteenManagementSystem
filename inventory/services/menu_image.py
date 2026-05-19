"""Helpers for menu item images on disk and in SQL Server."""
from pathlib import Path

from django.conf import settings
from django.db import connection

from inventory.models import MenuItem


def relative_image_path(item_code: str, ext: str = 'jpg') -> str:
    safe = ''.join(c if c.isalnum() or c in '-_' else '_' for c in (item_code or 'item'))
    return f'menu_items/{safe}.{ext}'


def save_menu_item_image_file(item: MenuItem, source_path: Path) -> str:
    """Write file under MEDIA_ROOT and update menu_items.image_path."""
    rel = relative_image_path(item.item_code, source_path.suffix.lstrip('.') or 'jpg')
    dest_dir = settings.MEDIA_ROOT / 'menu_items'
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = settings.MEDIA_ROOT / rel

    with open(source_path, 'rb') as src:
        dest.write_bytes(src.read())

    with connection.cursor() as cursor:
        cursor.execute(
            'UPDATE menu_items SET image_path = %s WHERE id = %s',
            [rel.replace('\\', '/'), item.id],
        )

    return rel


def assign_image_from_bytes(item: MenuItem, data: bytes, ext: str = 'jpg') -> str:
    rel = relative_image_path(item.item_code, ext)
    dest = settings.MEDIA_ROOT / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)

    with connection.cursor() as cursor:
        cursor.execute(
            'UPDATE menu_items SET image_path = %s WHERE id = %s',
            [rel, item.id],
        )
    return rel
