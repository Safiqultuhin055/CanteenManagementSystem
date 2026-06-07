"""Menu item images stored in SQL Server (menu_items.image_data BLOB)."""
from django.db import connection

from inventory.models import MenuItem
from inventory.services.menu_image_cache import invalidate_menu_item_image, item_has_image

CONTENT_TYPES = {
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'webp': 'image/webp',
    'gif': 'image/gif',
}


def content_type_for_ext(ext: str) -> str:
    return CONTENT_TYPES.get((ext or 'png').lower().lstrip('.'), 'application/octet-stream')


def save_menu_item_image_bytes(item: MenuItem, data: bytes, content_type: str = 'image/png') -> None:
    """Write image bytes to menu_items.image_data (+ content type)."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE menu_items
            SET image_data = %s,
                image_content_type = %s,
                image_path = NULL,
                updated_at = SYSDATETIME()
            WHERE id = %s
            """,
            [data, content_type, item.pk],
        )
    invalidate_menu_item_image(item.pk)


def assign_image_from_bytes(item: MenuItem, data: bytes, ext: str = 'png') -> str:
    content_type = content_type_for_ext(ext)
    save_menu_item_image_bytes(item, data, content_type)
    return content_type


__all__ = [
    'CONTENT_TYPES',
    'assign_image_from_bytes',
    'content_type_for_ext',
    'item_has_image',
    'save_menu_item_image_bytes',
]
