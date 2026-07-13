"""Fast serve/cache for menu item BLOB images."""
from __future__ import annotations

import hashlib
from typing import NamedTuple

from django.core.cache import cache
from django.db import connection

CACHE_PREFIX = 'menu_item_image:v1:'
CACHE_TTL = 60 * 60 * 24 * 7  # 7 days — invalidate on upload


class MenuImagePayload(NamedTuple):
    data: bytes
    content_type: str
    etag: str


def cache_key(item_id: int) -> str:
    return f'{CACHE_PREFIX}{item_id}'


def invalidate_menu_item_image(item_id: int) -> None:
    cache.delete(cache_key(item_id))


def fetch_menu_item_image(item_id: int) -> MenuImagePayload | None:
    """Load image bytes from cache or SQL Server (single row, BLOB only)."""
    # Version the cache key by the row's updated_at so a re-uploaded image is
    # served fresh WITHOUT a server restart (LocMemCache is per-process, so an
    # invalidate() from a script/other worker can't reach a running server).
    version = image_version(item_id)
    key = f'{cache_key(item_id)}:{version}'
    cached = cache.get(key)
    if cached:
        return MenuImagePayload(*cached)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT image_data, image_content_type
            FROM menu_items
            WHERE id = %s AND is_deleted = 0 AND image_data IS NOT NULL
            """,
            [item_id],
        )
        row = cursor.fetchone()

    if not row or not row[0]:
        return None

    data = bytes(row[0])
    content_type = row[1] or 'image/png'
    etag = hashlib.md5(data, usedforsecurity=False).hexdigest()
    payload = MenuImagePayload(data, content_type, etag)
    cache.set(key, (payload.data, payload.content_type, payload.etag), CACHE_TTL)
    return payload


def image_version(item_id: int) -> str:
    """Cheap change-token for an item's image (updated_at ticks, no BLOB load)."""
    with connection.cursor() as cursor:
        cursor.execute(
            'SELECT updated_at FROM menu_items WHERE id = %s AND is_deleted = 0',
            [item_id],
        )
        row = cursor.fetchone()
    if not row or not row[0]:
        return '0'
    return hashlib.md5(str(row[0]).encode(), usedforsecurity=False).hexdigest()[:12]


def item_has_image(item_id: int) -> bool:
    """Check image exists without loading VARBINARY payload."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT CASE WHEN image_data IS NULL THEN 0 ELSE 1 END
            FROM menu_items WHERE id = %s AND is_deleted = 0
            """,
            [item_id],
        )
        row = cursor.fetchone()
    return bool(row and row[0])
