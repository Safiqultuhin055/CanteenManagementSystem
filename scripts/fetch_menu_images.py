"""Replace generated menu tiles with real photos from the web.

Source: Openverse API (openverse.org) — free, no key, CC-licensed images
(licensing-clean for internal use). Each image is downloaded, center-cropped
to 640x480 (the POS card's 4:3 box) and stored as a JPEG BLOB in menu_items.

If every candidate for an item fails, its existing image is left untouched.

Run:  python scripts/fetch_menu_images.py
"""
import io
import os
import sys

import django
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'canteen_system.settings')
django.setup()

from PIL import Image  # noqa: E402

from inventory.models import MenuItem  # noqa: E402
from inventory.services.menu_image_cache import invalidate_menu_item_image  # noqa: E402

OV_URL = 'https://api.openverse.org/v1/images/'
UA = 'CanteenPOS/1.0 (internal menu image seeding)'
TARGET = (640, 480)
MAX_BYTES = 12 * 1024 * 1024

# item_code -> ordered list of search queries (first that yields a usable image wins)
QUERIES = {
    'CANT-01': ['paratha', 'paratha flatbread'],
    'CANT-02': ['khichuri', 'khichdi rice lentil'],
    'CANT-03': ['boiled egg', 'fried egg'],
    'CANT-04': ['mixed vegetable curry', 'fried vegetables dish'],
    'CANT-05': ['dal lentil soup', 'lentil curry'],
    'CANT-06': ['singara snack', 'samosa fried snack'],
    'CANT-07': ['samosa', 'samosa snack'],
    'CANT-08': ['jhalmuri puffed rice', 'puffed rice muri'],
    'CANT-09': ['khaja sweet', 'indian sweet dessert'],
    'CANT-10': ['milk tea cup', 'cup of tea'],
    'CANT-11': ['biscuit cookie', 'biscuits'],
    'CANT-12': ['bun bread', 'bread bun'],
    'CANT-13': ['pound cake slice', 'plain cake'],
    'CANT-14': ['water bottle', 'plastic water bottle'],
    'CANT-15': ['cola soft drink bottle', 'soft drink bottle'],
}


def search_openverse(query, limit=6):
    try:
        r = requests.get(
            OV_URL,
            params={'q': query, 'page_size': limit, 'license_type': 'all',
                    'mature': 'false'},
            headers={'User-Agent': UA}, timeout=25,
        )
        if r.status_code != 200:
            return []
        return [x.get('url') for x in (r.json().get('results') or []) if x.get('url')]
    except Exception:
        return []


def cover_crop(img, size=TARGET):
    """Scale to cover the target box, then center-crop (no distortion)."""
    tw, th = size
    img = img.convert('RGB')
    w, h = img.size
    scale = max(tw / w, th / h)
    nw, nh = max(tw, int(round(w * scale))), max(th, int(round(h * scale)))
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    return img.crop((left, top, left + tw, top + th))


def download_image(url):
    try:
        r = requests.get(url, headers={'User-Agent': UA}, timeout=25, stream=True)
        if r.status_code != 200:
            return None
        ct = r.headers.get('Content-Type', '')
        if 'image' not in ct:
            return None
        raw = r.content
        if not raw or len(raw) > MAX_BYTES:
            return None
        img = Image.open(io.BytesIO(raw))
        img.load()
        if min(img.size) < 120:      # skip tiny thumbnails
            return None
        out = io.BytesIO()
        cover_crop(img).save(out, format='JPEG', quality=86, optimize=True)
        return out.getvalue()
    except Exception:
        return None


def run():
    ok = 0
    for code, queries in QUERIES.items():
        item = MenuItem.objects.filter(item_code=code, is_deleted=False).first()
        if not item:
            print(f'  {code}: item not found, skipped')
            continue
        blob = None
        used = ''
        for q in queries:
            for url in search_openverse(q):
                blob = download_image(url)
                if blob:
                    used = f'{q}  <-  {url[:60]}'
                    break
            if blob:
                break
        if not blob:
            print(f'  {code} {item.item_name:14} FAILED — kept existing image')
            continue
        item.image_data = blob
        item.image_content_type = 'image/jpeg'
        item.image_path = None
        item.save(update_fields=['image_data', 'image_content_type', 'image_path', 'updated_at'])
        invalidate_menu_item_image(item.pk)
        ok += 1
        print(f'  {code} {item.item_name:14} OK  {len(blob)//1024}KB  {used}')
    print(f'\nUpdated {ok}/{len(QUERIES)} items with web photos.')


if __name__ == '__main__':
    run()
