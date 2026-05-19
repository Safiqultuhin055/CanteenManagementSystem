"""
Download product-style food images from the web and prepare POS cutouts.

Sources (in order): bundled coffee sample → Wikimedia Commons → TheMealDB → DuckDuckGo.
"""
from __future__ import annotations

import logging
import time
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit

import requests
from PIL import Image

from inventory.services.menu_image import assign_image_from_bytes
from inventory.services.menu_product_art import (
    SIZE,
    _from_asset,
    _paste_centered,
    _shadow,
    render_menu_product_image,
)

logger = logging.getLogger(__name__)

UA = 'CanteenManagementSystem/1.0 (Django; menu image seed)'
HEADERS = {
    'User-Agent': UA,
    'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
}

_ASSETS_COFFEE = Path(__file__).resolve().parent.parent / 'assets' / 'menu_samples' / 'coffee.png'

# Wikimedia Commons file search terms per item
COMMONS_SEARCH: dict[str, str] = {
    'BRK001': 'paratha',
    'BRK002': 'toast bread butter',
    'LUN001': 'chicken rice plate',
    'LUN002': 'fish curry rice',
    'LUN003': 'vegetable fried rice',
    'LUN004': 'biryani',
    'DIN001': 'beef curry',
    'SNK001': 'samosa',
    'SNK002': 'chicken wrap sandwich',
    'BEV001': 'tea cup',
    'BEV003': 'mango juice glass',
    'DES001': 'kheer rice pudding',
    'SPL001': 'indian thali',
    'CMB001': 'indian lunch plate rice',
}

# TheMealDB search.php fallback
MEALDB_SEARCH: dict[str, str] = {
    'BRK001': 'paratha',
    'BRK002': 'toast',
    'LUN001': 'chicken rice',
    'LUN002': 'fish',
    'LUN003': 'rice',
    'LUN004': 'biryani',
    'DIN001': 'beef',
    'SNK002': 'chicken',
    'BEV001': 'tea',
    'BEV003': 'mango',
    'DES001': 'pudding',
    'SPL001': 'thali',
    'CMB001': 'rice',
}


def _clean_url(url: str) -> str:
    return urlsplit(url).geturl()


def _remove_light_background(img: Image.Image, threshold: int = 235) -> Image.Image:
    img = img.convert('RGBA')
    pixels = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if r >= threshold and g >= threshold and b >= threshold:
                pixels[x, y] = (r, g, b, 0)
            elif min(r, g, b) >= threshold - 28:
                fade = max(r, g, b) - (threshold - 32)
                alpha = max(0, min(255, int(255 - fade * 8)))
                pixels[x, y] = (r, g, b, min(a, alpha))
    return img


def _trim_transparent(img: Image.Image) -> Image.Image:
    img = img.convert('RGBA')
    bbox = img.getbbox()
    return img.crop(bbox) if bbox else img


def _has_transparency(img: Image.Image) -> bool:
    if img.mode != 'RGBA':
        return False
    extrema = img.getextrema()
    return len(extrema) == 4 and extrema[3][0] < 250


def prepare_product_cutout(raw: bytes, scale: float = 0.78) -> bytes | None:
    try:
        photo = Image.open(BytesIO(raw))
    except Exception:
        return None

    if photo.width < 160 or photo.height < 160:
        return None

    photo = photo.convert('RGBA')
    if _has_transparency(photo):
        photo = _trim_transparent(photo)
    else:
        photo = _remove_light_background(photo)
        photo = _trim_transparent(photo)

    if photo.width < 72 or photo.height < 72:
        return None

    from PIL import ImageDraw

    base = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)
    _shadow(draw, SIZE // 2, int(SIZE * 0.82), 118, 28)
    _paste_centered(base, photo, scale=scale)

    buf = BytesIO()
    base.save(buf, format='PNG', optimize=True)
    return buf.getvalue()


def download_image(url: str, timeout: int = 25) -> bytes | None:
    try:
        url = _clean_url(url)
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        data = resp.content
        if len(data) < 4000 or len(data) > 12_000_000:
            return None
        Image.open(BytesIO(data)).verify()
        return data
    except Exception as exc:
        logger.debug('Download failed %s: %s', url[:70], exc)
        return None


def _try_urls(urls: list[str]) -> bytes | None:
    seen = set()
    for url in urls:
        url = _clean_url(url)
        if not url or url in seen:
            continue
        seen.add(url)
        raw = download_image(url)
        if not raw:
            continue
        cutout = prepare_product_cutout(raw)
        if cutout:
            return cutout
        time.sleep(0.2)
    return None


def commons_image_urls(term: str, limit: int = 5) -> list[str]:
    """Free images from Wikimedia Commons (same index as Google Images often uses)."""
    urls: list[str] = []
    try:
        r = requests.get(
            'https://commons.wikimedia.org/w/api.php',
            params={
                'action': 'query',
                'list': 'search',
                'srsearch': term,
                'srnamespace': 6,
                'srlimit': limit,
                'format': 'json',
            },
            headers={'User-Agent': UA},
            timeout=20,
        )
        r.raise_for_status()
        titles = [x['title'] for x in r.json().get('query', {}).get('search', [])]
        if not titles:
            return urls

        r2 = requests.get(
            'https://commons.wikimedia.org/w/api.php',
            params={
                'action': 'query',
                'titles': '|'.join(titles),
                'prop': 'imageinfo',
                'iiprop': 'url',
                'iiurlwidth': 960,
                'format': 'json',
            },
            headers={'User-Agent': UA},
            timeout=20,
        )
        r2.raise_for_status()
        for pdata in r2.json().get('query', {}).get('pages', {}).values():
            ii = pdata.get('imageinfo', [{}])[0]
            u = ii.get('thumburl') or ii.get('url')
            if u and 'upload.wikimedia.org' in u:
                urls.append(_clean_url(u))
    except Exception as exc:
        logger.warning('Commons search failed for %r: %s', term, exc)
    return urls


def mealdb_image_url(term: str) -> str | None:
    try:
        r = requests.get(
            f'https://www.themealdb.com/api/json/v1/1/search.php?s={term}',
            headers=HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        meals = r.json().get('meals') or []
        for meal in meals:
            thumb = meal.get('strMealThumb')
            if thumb:
                return thumb
    except Exception:
        pass
    return None


def duckduckgo_image_urls(query: str, max_results: int = 8) -> list[str]:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return []

    urls: list[str] = []
    try:
        with DDGS() as ddgs:
            for row in ddgs.images(query, max_results=max_results, size='Medium', type_image='photo'):
                u = row.get('image') or row.get('thumbnail')
                if u and u.startswith('http'):
                    urls.append(u)
    except Exception as exc:
        logger.debug('DuckDuckGo images: %s', exc)
    return urls


def collect_image_urls(item_code: str, item_name: str) -> list[str]:
    code = (item_code or '').upper()
    urls: list[str] = []

    term = COMMONS_SEARCH.get(code) or item_name
    urls.extend(commons_image_urls(term, limit=6))

    alt = MEALDB_SEARCH.get(code)
    if alt:
        thumb = mealdb_image_url(alt)
        if thumb:
            urls.append(thumb)

    return urls


def collect_image_urls_with_ddg(item_code: str, item_name: str) -> list[str]:
    """Same as collect_image_urls but appends DuckDuckGo results (may rate-limit)."""
    urls = collect_image_urls(item_code, item_name)
    code = (item_code or '').upper()
    term = COMMONS_SEARCH.get(code) or item_name
    ddg_q = f'{item_name or term} food product photo isolated white background'
    urls.extend(duckduckgo_image_urls(ddg_q, max_results=4))
    return urls


def fetch_item_image_bytes(item_code: str, item_name: str = '', is_vegetarian: bool = False) -> bytes | None:
    code = (item_code or '').upper()

    if code == 'BEV002':
        return _from_asset('coffee.png', scale=0.8)

    urls = collect_image_urls(code, item_name)
    data = _try_urls(urls)
    if data:
        return data

    return render_menu_product_image(item_code, item_name, is_vegetarian)


def fetch_and_save_menu_item(item, delay: float = 0.5) -> str | None:
    data = fetch_item_image_bytes(item.item_code, item.item_name, item.is_vegetarian)
    time.sleep(delay)
    if not data:
        return None
    return assign_image_from_bytes(item, data, ext='png')
