"""Reset the POS menu to the current canteen list and stock today.

Idempotent:
  * Soft-deletes any active menu item whose code is not in NEW_ITEMS.
  * Upserts each NEW_ITEMS row by item_code (name, price, category, image).
  * Generates a gradient tile image (Bengali name + emoji) as a PNG BLOB.
  * Ensures a daily_food_stock row for today with prepared_quantity.

Run:  python scripts/seed_canteen_menu.py
"""
import io
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'canteen_system.settings')
django.setup()

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from core.business_date import get_business_date  # noqa: E402
from inventory.models import DailyFoodStock, MenuItem  # noqa: E402
from inventory.services.menu_image_cache import invalidate_menu_item_image  # noqa: E402

PREPARED_QTY = 100

FONT_BN = 'C:/Windows/Fonts/Nirmala.ttf'
FONT_BN_BOLD = 'C:/Windows/Fonts/NirmalaB.ttf'
FONT_LATIN = 'C:/Windows/Fonts/arialbd.ttf'
FONT_EMOJI = 'C:/Windows/Fonts/seguiemj.ttf'

# code, English name, Bangla name, price, category_id, emoji, veg, (grad start, grad end)
NEW_ITEMS = [
    ('CANT-01', 'Paratha',       'পরোটা',        10, 1, '🫓', True,  ('#f59e0b', '#b45309')),
    ('CANT-02', 'Khichuri',      'খিচুড়ি',       50, 2, '🍲', True,  ('#f97316', '#c2410c')),
    ('CANT-03', 'Egg',           'ডিম',          20, 1, '🥚', False, ('#fbbf24', '#d97706')),
    ('CANT-04', 'Vegetable Fry', 'সবজি ভাজি',    10, 2, '🥗', True,  ('#22c55e', '#15803d')),
    ('CANT-05', 'Dal',           'ডাল',          10, 2, '🍛', True,  ('#eab308', '#a16207')),
    ('CANT-06', 'Singara',       'সিঙ্গারা',      10, 4, '🥟', True,  ('#f97316', '#9a3412')),
    ('CANT-07', 'Samosa',        'সমুচা',        10, 4, '🥟', True,  ('#fb923c', '#c2410c')),
    ('CANT-08', 'Bhut-Muri',     'বুট-মুড়ি',      20, 4, '🥣', True,  ('#84cc16', '#4d7c0f')),
    ('CANT-09', 'Khaja',         'খাজা',         10, 6, '🍥', True,  ('#f472b6', '#be185d')),
    ('CANT-10', 'Tea',           'চা',           10, 5, '🍵', True,  ('#10b981', '#047857')),
    ('CANT-11', 'Biscuit',       'বিস্কুট',       10, 4, '🍪', True,  ('#d97706', '#92400e')),
    ('CANT-12', 'Bun Bread',     'বন-রুটি',       10, 4, '🍞', True,  ('#f59e0b', '#b45309')),
    ('CANT-13', 'Dry Cake',      'ড্রাই কেক',     10, 6, '🍰', True,  ('#fb7185', '#be123c')),
    ('CANT-14', 'Water Bottle',  'পানির বোতল',    20, 5, '💧', True,  ('#38bdf8', '#0369a1')),
    ('CANT-15', 'Mojo',          'মোজো',         20, 5, '🥤', True,  ('#a78bfa', '#6d28d9')),
]


def _hex(c):
    c = c.lstrip('#')
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _wrap(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ''
    for w in words:
        trial = (cur + ' ' + w).strip()
        b = draw.textbbox((0, 0), trial, font=font)
        if b[2] - b[0] <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def make_tile(name_bn, name_en, price, emoji, grad):
    """640x480 gradient tile: monogram badge + English name + price.

    Bengali is intentionally NOT drawn here (Pillow has no complex-script
    shaping without libraqm, which breaks Bengali matras). The POS card shows
    the Bangla name as HTML text under this image, where the browser shapes it.
    """
    W, H = 640, 480
    top, bot = _hex(grad[0]), _hex(grad[1])
    base = Image.new('RGB', (W, H), top)
    px = base.load()
    for y in range(H):
        t = y / (H - 1)
        px_row = (
            int(top[0] + (bot[0] - top[0]) * t),
            int(top[1] + (bot[1] - top[1]) * t),
            int(top[2] + (bot[2] - top[2]) * t),
        )
        for x in range(W):
            px[x, y] = px_row
    img = base.convert('RGBA')

    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    # Monogram badge (first letter) — decorative.
    od.ellipse([W / 2 - 82, 56, W / 2 + 82, 220], fill=(255, 255, 255, 38))
    initial = (name_en[:1] or '?').upper()
    mf = _font(FONT_LATIN, 120)
    mb = od.textbbox((0, 0), initial, font=mf)
    od.text(((W - (mb[2] - mb[0])) / 2 - mb[0], 138 - (mb[3] - mb[1]) / 2 - mb[1]),
            initial, font=mf, fill=(255, 255, 255, 235))
    # Bottom scrim for text legibility.
    od.rounded_rectangle([32, 250, W - 32, H - 30], radius=30, fill=(2, 6, 23, 165))
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    def centered(text, font, y, fill):
        b = draw.textbbox((0, 0), text, font=font)
        draw.text(((W - (b[2] - b[0])) / 2 - b[0], y), text, font=font, fill=fill)

    name_font = _font(FONT_LATIN, 52)
    lines = _wrap(draw, name_en, name_font, W - 110)
    y = 300 if len(lines) > 1 else 316
    for ln in lines:
        centered(ln, name_font, y, (255, 255, 255, 255))
        y += 58
    centered(f'Tk {price}', _font(FONT_LATIN, 44), 392, (110, 231, 183, 255))

    buf = io.BytesIO()
    img.convert('RGB').save(buf, format='PNG', optimize=True)
    return buf.getvalue()


def run():
    today = get_business_date()
    keep_codes = {row[0] for row in NEW_ITEMS}

    # 1) Soft-delete every currently active item not in the new list.
    removed = 0
    for m in MenuItem.objects.filter(is_deleted=False):
        if m.item_code not in keep_codes:
            m.is_deleted = True
            m.is_active = False
            m.is_available = False
            m.save(update_fields=['is_deleted', 'is_active', 'is_available', 'updated_at'])
            removed += 1
    print(f'Soft-deleted {removed} old menu item(s).')

    # 2) Upsert the new items + image + today's stock.
    for code, name_en, name_bn, price, cat_id, emoji, veg, grad in NEW_ITEMS:
        item = MenuItem.objects.filter(item_code=code).first()
        if not item:
            item = MenuItem(item_code=code)
        item.item_name = name_en
        item.item_name_bn = name_bn
        item.category_id = cat_id
        item.unit_price = price
        item.tax_rate = 0
        item.is_vegetarian = veg
        item.is_active = True
        item.is_available = True
        item.is_deleted = False
        item.image_data = make_tile(name_bn, name_en, price, emoji, grad)
        item.image_content_type = 'image/png'
        item.image_path = None
        item.save()
        invalidate_menu_item_image(item.pk)

        stock = DailyFoodStock.objects.filter(
            menu_item_id=item.pk, stock_date=today, is_deleted=False,
        ).first()
        if not stock:
            stock = DailyFoodStock(menu_item_id=item.pk, stock_date=today)
            stock.sold_quantity = 0
            stock.waste_quantity = 0
        stock.prepared_quantity = PREPARED_QTY
        stock.unit_price = price
        stock.is_available = True
        stock.is_active = True
        stock.is_deleted = False
        stock.expired_date = None
        stock.save()
        print(f'  {code:8} {name_en:14} {name_bn:12} Tk{price:<4} stock={PREPARED_QTY}')

    print(f'\nDone. {len(NEW_ITEMS)} items live with images + today ({today}) stock.')


if __name__ == '__main__':
    run()
