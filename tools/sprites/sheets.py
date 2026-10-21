"""Review sheets: contact_items.png, contact_particles.png, contact_blocks.png (+ small-size check)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from pxl import OUT, ASSETS

GREY = (122, 122, 126)
DARK = (34, 34, 40)
SLOT = (139, 139, 139)
FONT = None


def font(size=12):
    global FONT
    try:
        return ImageFont.load_default(size=size)
    except Exception:  # pragma: no cover
        return ImageFont.load_default()


def scaled(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def on_bg(im, k, bg, pad=0):
    s = scaled(im, k)
    out = Image.new("RGBA", (s.width + pad * 2, s.height + pad * 2), bg + (255,))
    out.alpha_composite(s, (pad, pad))
    return out


def sprite_sheet(entries, path, k=8, cols=5, title=None):
    """entries: list of (name, [frames]).  Each sprite: x`k` on grey and dark; animated ones get a frame strip."""
    f = font(12)
    cell_w = 0
    tiles = []
    for name, frames in entries:
        w = frames[0].width * k
        h = frames[0].height * k
        a = on_bg(frames[0], k, GREY)
        b = on_bg(frames[0], k, DARK)
        tile_w = w * 2 + 6
        extra_h = 0
        strip = None
        if len(frames) > 1:
            ks = max(2, k // 2)
            sw = frames[0].width * ks
            strip = Image.new("RGBA", (max(tile_w, len(frames) * (sw + 4)), frames[0].height * ks + 4), GREY + (255,))
            for i, fr in enumerate(frames):
                strip.alpha_composite(scaled(fr, ks), (i * (sw + 4) + 2, 2))
            extra_h = strip.height + 2
            tile_w = max(tile_w, strip.width)
        tiles.append((name, a, b, strip, tile_w, h + 16 + extra_h))
    cell_w = max(t[4] for t in tiles) + 12
    cell_h = max(t[5] for t in tiles) + 10
    rows = (len(tiles) + cols - 1) // cols
    top = 24 if title else 6
    sheet = Image.new("RGBA", (cols * cell_w + 6, rows * cell_h + top), (60, 60, 66, 255))
    d = ImageDraw.Draw(sheet)
    if title:
        d.text((8, 4), title, fill=(235, 235, 240), font=font(14))
    for i, (name, a, b, strip, tw, th) in enumerate(tiles):
        x = (i % cols) * cell_w + 6
        y = (i // cols) * cell_h + top
        sheet.alpha_composite(a, (x, y + 14))
        sheet.alpha_composite(b, (x + a.width + 6, y + 14))
        d.text((x, y), name, fill=(235, 235, 240), font=f)
        if strip is not None:
            sheet.alpha_composite(strip, (x, y + 14 + a.height + 2))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(path)
    return sheet


def small_sheet(entries, path, cols=10):
    """1x / 2x / 3x on a slot-grey background (readability at real size)."""
    f = font(10)
    cell = 16 * 3 + 16 * 2 + 16 + 20
    rows = (len(entries) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * cell, rows * 70), SLOT + (255,))
    d = ImageDraw.Draw(sheet)
    for i, (name, frames) in enumerate(entries):
        x = (i % cols) * cell + 4
        y = (i // cols) * 70 + 4
        im = frames[0]
        sheet.alpha_composite(im, (x, y))
        sheet.alpha_composite(scaled(im, 2), (x + 20, y))
        sheet.alpha_composite(scaled(im, 3), (x + 56, y))
        d.text((x, y + 52), name[:18], fill=(30, 30, 30), font=f)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(path)
