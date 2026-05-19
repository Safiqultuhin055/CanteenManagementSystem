"""
Product-style menu images: transparent PNG, centered item, soft shadow (POS cutout look).
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

SIZE = 512
_ASSETS = Path(__file__).resolve().parent.parent / 'assets' / 'menu_samples'


def _canvas() -> 'Image.Image':
    from PIL import Image
    return Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))


def _shadow(draw, cx: int, cy: int, rx: int, ry: int, alpha: int = 55):
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(15, 23, 42, alpha))


def _paste_centered(base: 'Image.Image', overlay: 'Image.Image', scale: float = 0.72):
    from PIL import Image
    max_side = int(SIZE * scale)
    ow, oh = overlay.size
    ratio = min(max_side / ow, max_side / oh)
    nw, nh = max(1, int(ow * ratio)), max(1, int(oh * ratio))
    resized = overlay.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (SIZE - nw) // 2
    y = (SIZE - nh) // 2 - int(SIZE * 0.04)
    if resized.mode != 'RGBA':
        resized = resized.convert('RGBA')
    base.alpha_composite(resized, (x, y))


def _finish(img: 'Image.Image') -> bytes:
    buf = BytesIO()
    img.save(buf, format='PNG', optimize=True)
    return buf.getvalue()


def _draw_plate(draw, cx: int, cy: int, r: int):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(248, 250, 252, 255))
    draw.ellipse([cx - r + 8, cy - r + 10, cx + r - 8, cy + r - 6], fill=(241, 245, 249, 255))


def _from_asset(name: str, scale: float = 0.78) -> bytes | None:
    path = _ASSETS / name
    if not path.is_file():
        return None
    from PIL import Image, ImageDraw
    base = _canvas()
    draw = ImageDraw.Draw(base)
    _shadow(draw, SIZE // 2, int(SIZE * 0.82), 118, 28)
    photo = Image.open(path).convert('RGBA')
    _paste_centered(base, photo, scale=scale)
    return _finish(base)


def _draw_breakfast_paratha(draw, cx: int, cy: int):
    for i, dy in enumerate((0, 14, 28)):
        w, h = 140 - i * 8, 22
        draw.rounded_rectangle(
            [cx - w // 2, cy - 40 + dy, cx + w // 2, cy - 40 + dy + h],
            radius=10,
            fill=(234, 179, 8, 255) if i == 0 else (202, 138, 4, 255),
        )
    draw.ellipse([cx - 22, cy - 58, cx + 22, cy - 18], fill=(250, 204, 21, 255))


def _draw_toast(draw, cx: int, cy: int):
    draw.rounded_rectangle([cx - 70, cy - 50, cx + 70, cy + 40], radius=14, fill=(180, 83, 9, 255))
    draw.rounded_rectangle([cx - 58, cy - 40, cx + 58, cy + 28], radius=10, fill=(245, 158, 11, 255))


def _draw_rice_plate(draw, cx: int, cy: int, accent: tuple[int, int, int, int]):
    _draw_plate(draw, cx, cy, 118)
    draw.ellipse([cx - 78, cy - 48, cx + 78, cy + 42], fill=(254, 243, 199, 255))
    draw.polygon(
        [cx - 30, cy + 10, cx, cy - 28, cx + 34, cy + 14],
        fill=accent,
    )


def _draw_biryani(draw, cx: int, cy: int):
    draw.ellipse([cx - 95, cy - 20, cx + 95, cy + 88], fill=(120, 53, 15, 255))
    draw.ellipse([cx - 82, cy - 42, cx + 82, cy + 58], fill=(217, 119, 6, 255))
    draw.ellipse([cx - 68, cy - 28, cx + 68, cy + 38], fill=(251, 191, 36, 255))
    for ox in (-24, 0, 24):
        draw.ellipse([cx + ox - 8, cy - 18, cx + ox + 8, cy - 2], fill=(220, 38, 38, 220))


def _draw_samosa(draw, cx: int, cy: int):
    draw.polygon(
        [cx, cy - 70, cx + 62, cy + 48, cx - 62, cy + 48],
        fill=(202, 138, 4, 255),
    )
    draw.polygon(
        [cx, cy - 52, cx + 42, cy + 32, cx - 42, cy + 32],
        fill=(250, 204, 21, 255),
    )


def _draw_roll(draw, cx: int, cy: int):
    draw.rounded_rectangle([cx - 88, cy - 28, cx + 88, cy + 28], radius=28, fill=(254, 243, 199, 255))
    draw.rounded_rectangle([cx - 72, cy - 18, cx + 72, cy + 18], radius=20, fill=(248, 113, 113, 255))


def _draw_tea_cup(draw, cx: int, cy: int):
    draw.ellipse([cx - 88, cy + 34, cx + 88, cy + 58], fill=(248, 250, 252, 255))
    draw.rounded_rectangle([cx - 58, cy - 42, cx + 58, cy + 42], radius=12, fill=(125, 211, 252, 255))
    draw.ellipse([cx - 50, cy - 50, cx + 50, cy - 8], fill=(120, 53, 15, 255))
    draw.arc([cx + 52, cy - 20, cx + 92, cy + 30], 270, 90, fill=(125, 211, 252, 255), width=10)


def _draw_juice_glass(draw, cx: int, cy: int):
    draw.polygon(
        [cx - 48, cy - 62, cx + 48, cy - 62, cx + 36, cy + 52, cx - 36, cy + 52],
        fill=(251, 146, 60, 180),
    )
    draw.rectangle([cx - 40, cy - 10, cx + 40, cy + 44], fill=(249, 115, 22, 255))
    draw.ellipse([cx - 48, cy - 72, cx + 48, cy - 48], fill=(253, 186, 116, 255))


def _draw_payesh(draw, cx: int, cy: int):
    draw.ellipse([cx - 90, cy + 18, cx + 90, cy + 52], fill=(248, 250, 252, 255))
    draw.ellipse([cx - 78, cy - 28, cx + 78, cy + 32], fill=(254, 249, 195, 255))
    draw.ellipse([cx - 62, cy - 12, cx + 62, cy + 18], fill=(253, 224, 71, 255))


def _draw_thali(draw, cx: int, cy: int):
    _draw_plate(draw, cx, cy, 128)
    colors = [(248, 113, 113, 255), (251, 191, 36, 255), (74, 222, 128, 255), (96, 165, 250, 255)]
    positions = [(-42, -18), (42, -18), (-42, 28), (42, 28)]
    for (ox, oy), col in zip(positions, colors):
        draw.ellipse([cx + ox - 28, cy + oy - 22, cx + ox + 28, cy + oy + 22], fill=col)


def _render_drawn(kind: str) -> bytes:
    from PIL import ImageDraw
    img = _canvas()
    draw = ImageDraw.Draw(img)
    cx, cy = SIZE // 2, int(SIZE * 0.52)
    _shadow(draw, cx, int(SIZE * 0.84), 120, 30)

    if kind == 'paratha':
        _draw_breakfast_paratha(draw, cx, cy)
    elif kind == 'toast':
        _draw_toast(draw, cx, cy)
    elif kind == 'rice_chicken':
        _draw_rice_plate(draw, cx, cy, (185, 28, 28, 255))
    elif kind == 'rice_fish':
        _draw_rice_plate(draw, cx, cy, (14, 116, 144, 255))
    elif kind == 'rice_veg':
        _draw_rice_plate(draw, cx, cy, (22, 163, 74, 255))
    elif kind == 'biryani':
        _draw_biryani(draw, cx, cy)
    elif kind == 'curry_rice':
        _draw_rice_plate(draw, cx, cy, (124, 45, 18, 255))
    elif kind == 'samosa':
        _draw_samosa(draw, cx, cy)
    elif kind == 'roll':
        _draw_roll(draw, cx, cy)
    elif kind == 'tea':
        _draw_tea_cup(draw, cx, cy)
    elif kind == 'juice':
        _draw_juice_glass(draw, cx, cy)
    elif kind == 'payesh':
        _draw_payesh(draw, cx, cy)
    elif kind == 'thali':
        _draw_thali(draw, cx, cy)
    elif kind == 'combo':
        _draw_thali(draw, cx, cy)
    else:
        _draw_plate(draw, cx, cy, 100)
        draw.ellipse([cx - 40, cy - 40, cx + 40, cy + 40], fill=(148, 163, 184, 200))

    return _finish(img)


ITEM_ART = {
    'BRK001': 'paratha',
    'BRK002': 'toast',
    'LUN001': 'rice_chicken',
    'LUN002': 'rice_fish',
    'LUN003': 'rice_veg',
    'LUN004': 'biryani',
    'DIN001': 'curry_rice',
    'SNK001': 'samosa',
    'SNK002': 'roll',
    'BEV001': 'tea',
    'BEV002': 'coffee_asset',
    'BEV003': 'juice',
    'DES001': 'payesh',
    'SPL001': 'thali',
    'CMB001': 'combo',
}


def render_menu_product_image(item_code: str, item_name: str = '', is_vegetarian: bool = False) -> bytes:
    """Transparent PNG product cutout for a menu item code."""
    code = (item_code or '').upper()
    kind = ITEM_ART.get(code)

    if kind == 'coffee_asset':
        data = _from_asset('coffee.png', scale=0.8)
        if data:
            return data

    if kind:
        return _render_drawn(kind)

    return _render_drawn('rice_veg' if is_vegetarian else 'combo')
