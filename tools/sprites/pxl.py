"""Core helpers for the Tamagotchi pixel-art generators.

Everything (blocks, items, spawn eggs, particles) is drawn from hand-authored ASCII maps
(one character = one pixel) plus named palette ramps, so any asset can be regenerated and tweaked.

Conventions
-----------
* Ramps have 5 shades: [highlight, light, base, shadow, deep]. Light comes from the top-left.
* A *legend* maps map-characters to colours.  Build one with ``L('abcde=RAMPNAME', 'o=#304050')``:
  ``abcde=NAME`` assigns the 5 ramp shades to the 5 characters in order, ``c=#rrggbb`` (or
  ``c=#rrggbbaa``) a single colour, ``c=NAME.2`` one shade of a ramp.  ``.`` is always transparent.
* Never pure black, never pure white (see docs/ART.md).
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "src/main/resources/assets/tamagotchi"
DATA = ROOT / "src/main/resources/data/tamagotchi"
OUT = Path(__file__).resolve().parent / "out"

# --------------------------------------------------------------------------------------
# colour maths (OKLab based ramps, so shades stay perceptually even)
# --------------------------------------------------------------------------------------


def hex2rgb(h: str):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    if len(h) == 8:
        return (r, g, b, int(h[6:8], 16))
    return (r, g, b, 255)


def rgb2hex(c) -> str:
    return "#%02X%02X%02X" % tuple(int(round(v)) for v in c[:3])


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _unlin(c):
    c = max(0.0, c)
    return 255.0 * (12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055)


def rgb2oklab(c):
    r, g, b = _lin(c[0]), _lin(c[1]), _lin(c[2])
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = l ** (1 / 3), m ** (1 / 3), s ** (1 / 3)
    return (
        0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
        1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
        0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s,
    )


def oklab2rgb_raw(L, a, b):
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    return r, g, bb


def oklch2rgb(L, C, h):
    """OKLCH -> sRGB (0..255), reducing chroma until the colour is in gamut."""
    L = min(max(L, 0.0), 1.0)
    for _ in range(40):
        a, b = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
        r, g, bb = oklab2rgb_raw(L, a, b)
        if -0.0005 <= min(r, g, bb) and max(r, g, bb) <= 1.0005:
            break
        C *= 0.93
    return (_unlin(min(1, max(0, r))), _unlin(min(1, max(0, g))), _unlin(min(1, max(0, bb))))


def rgb2oklch(c):
    L, a, b = rgb2oklab(c)
    return L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def _pull_hue(h, target, amount):
    d = ((target - h + 180) % 360) - 180
    return (h + d * amount) % 360


WARM = 70.0  # hue highlights are pulled toward
COOL = 285.0  # hue shadows are pulled toward


def auto_ramp(base, dl=(0.17, 0.085, 0.0, -0.10, -0.20), warm=0.14, cool=0.20, sat=(0.80, 0.95, 1.0, 1.05, 0.95)):
    """5-shade hue-shifted ramp from a base colour (hex string or rgb): highlights drift warm and
    desaturate a little, shadows drift cool and saturate a little."""
    if isinstance(base, str):
        base = hex2rgb(base)
    L0, C0, h0 = rgb2oklch(base)
    out = []
    for i, d in enumerate(dl):
        if d > 0:
            h = _pull_hue(h0, WARM, warm * (d / dl[0]))
        elif d < 0:
            h = _pull_hue(h0, COOL, cool * (d / dl[-1]))
        else:
            h = h0
        r, g, b = oklch2rgb(L0 + d, C0 * sat[i], h)
        out.append((int(round(r)), int(round(g)), int(round(b)), 255))
    return out


def ramp(*hexes):
    return [hex2rgb(h) for h in hexes]


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(4 if len(a) > 3 and len(b) > 3 else 3))


def tint(c, dL=0.0, dC=0.0, h=None, alpha=None):
    """Tweak a colour in OKLCH: lightness delta, chroma factor delta, hue override."""
    L, C, hh = rgb2oklch(c)
    r, g, b = oklch2rgb(L + dL, max(0.0, C * (1 + dC)), hh if h is None else h)
    a = c[3] if len(c) > 3 else 255
    return (int(round(r)), int(round(g)), int(round(b)), a if alpha is None else alpha)


def with_alpha(c, a):
    return (c[0], c[1], c[2], a)


# --------------------------------------------------------------------------------------
# named ramps registry
# --------------------------------------------------------------------------------------

RAMPS: dict[str, list] = {}


def define(name, ramp_or_base, **kw):
    """Register a ramp.  ``ramp_or_base`` is either a list of 5 hex strings or one base hex."""
    if isinstance(ramp_or_base, (list, tuple)):
        RAMPS[name] = [hex2rgb(h) if isinstance(h, str) else h for h in ramp_or_base]
    else:
        RAMPS[name] = auto_ramp(ramp_or_base, **kw)
    return RAMPS[name]


# --------------------------------------------------------------------------------------
# ASCII maps
# --------------------------------------------------------------------------------------


def L(*specs):
    """Build a legend.  See module docstring."""
    leg = {".": (0, 0, 0, 0)}
    for spec in specs:
        chars, rhs = spec.split("=", 1)
        if rhs.startswith("#"):
            assert len(chars) == 1, spec
            leg[chars] = hex2rgb(rhs)
        elif "." in rhs and rhs.rsplit(".", 1)[1].isdigit():
            name, idx = rhs.rsplit(".", 1)
            assert len(chars) == 1, spec
            leg[chars] = RAMPS[name][int(idx)]
        else:
            r = RAMPS[rhs]
            assert len(chars) <= len(r), spec
            for ch, col in zip(chars, r):
                leg[ch] = col
    return leg


def M(text: str, w=16, h=16):
    """Parse an ASCII map; checks the size so broken maps fail loudly."""
    rows = [ln.rstrip("\n") for ln in text.strip("\n").split("\n")]
    rows = [r.strip() if len(r.strip()) == w else r for r in rows]
    assert len(rows) == h, f"map has {len(rows)} rows, expected {h}:\n{text}"
    for i, r in enumerate(rows):
        assert len(r) == w, f"row {i} has {len(r)} chars, expected {w}: {r!r}"
    return rows


def paint(rows, legend, w=None, h=None) -> Image.Image:
    h = h or len(rows)
    w = w or len(rows[0])
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch not in legend:
                raise KeyError(f"char {ch!r} at ({x},{y}) not in legend; row={row!r}")
            arr[y, x] = legend[ch]
    return Image.fromarray(arr, "RGBA")


def sprite(text, legend, w=16, h=16):
    return paint(M(text, w, h), legend)


def arr(img):
    return np.array(img.convert("RGBA"))


def img(a):
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def blank(w=16, h=16, color=(0, 0, 0, 0)):
    return Image.new("RGBA", (w, h), color)


def overlay(base: Image.Image, top: Image.Image, dx=0, dy=0):
    out = base.copy()
    out.alpha_composite(top, (dx, dy))
    return out


def vstack(frames):
    w = frames[0].width
    h = sum(f.height for f in frames)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    y = 0
    for f in frames:
        out.paste(f, (0, y))
        y += f.height
    return out


def hstack(frames, gap=0):
    h = frames[0].height
    w = sum(f.width for f in frames) + gap * (len(frames) - 1)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x = 0
    for f in frames:
        out.paste(f, (x, 0))
        x += f.width + gap
    return out


def shift_img(im: Image.Image, dx, dy):
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.paste(im, (dx, dy))
    return out


# --------------------------------------------------------------------------------------
# outlines
# --------------------------------------------------------------------------------------


def outline(im: Image.Image, strength=0.30, blue=0.0, diag=False, color=None, only_alpha_ge=128, protect=None) -> Image.Image:
    """Add a 1px dark, hue-tinted outline around the opaque silhouette.

    Every outline pixel takes the colour of its (brightest-lit) opaque neighbour, darkened in OKLCH
    and hue-shifted a little toward cool, so the outline stays tinted like vanilla item outlines.
    ``color`` forces one outline colour instead.  Pixels that are only partly transparent (glow) do
    not count as silhouette."""
    a = arr(im)
    h, w = a.shape[:2]
    out = a.copy()
    solid = a[:, :, 3] >= only_alpha_ge
    for y in range(h):
        for x in range(w):
            if a[y, x, 3] != 0:
                continue
            if protect and (x, y) in protect:
                continue
            cands = []
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) + (((1, 1), (-1, 1), (1, -1), (-1, -1)) if diag else ()):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and solid[ny, nx]:
                    cands.append(a[ny, nx])
            if not cands:
                continue
            if color is not None:
                out[y, x] = color
                continue
            # use the darkest neighbour (keeps outlines consistent along a bright rim)
            c = min(cands, key=lambda p: rgb2oklab(p)[0])
            L0, C0, h0 = rgb2oklch(c)
            hh = _pull_hue(h0, COOL, 0.18 + blue)
            r, g, b = oklch2rgb(max(0.14, L0 * strength + 0.04), C0 * 0.9 + 0.01, hh)
            out[y, x] = (int(round(r)), int(round(g)), int(round(b)), 255)
    return img(out)


# --------------------------------------------------------------------------------------
# deterministic low-contrast noise (for large flat areas; 1 shade apart)
# --------------------------------------------------------------------------------------


def hash2(x, y, seed=0):
    n = (x * 374761393 + y * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def noise_shift(im: Image.Image, chars_mask=None, amount=0.025, seed=1, period=None, chroma_amount=0.0):
    """Nudge lightness of opaque pixels by +-amount (OKLab L) with a deterministic hash so flat areas get a
    gentle, low-contrast grain.  ``period`` makes the noise tile every n px (keeps block textures seamless)."""
    a = arr(im)
    h, w = a.shape[:2]
    out = a.copy()
    for y in range(h):
        for x in range(w):
            if a[y, x, 3] == 0:
                continue
            if chars_mask is not None and not chars_mask[y][x]:
                continue
            px, py = (x % period, y % period) if period else (x, y)
            v = hash2(px, py, seed)
            if v < 0.34:
                d = -amount
            elif v > 0.66:
                d = amount
            else:
                continue
            L0, C0, h0 = rgb2oklch(a[y, x])
            r, g, b = oklch2rgb(L0 + d, C0 * (1 + (chroma_amount if d > 0 else -chroma_amount)), h0)
            out[y, x, :3] = (int(round(r)), int(round(g)), int(round(b)))
    return img(out)


# --------------------------------------------------------------------------------------
# file output
# --------------------------------------------------------------------------------------


def save_png(im: Image.Image, path: Path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.convert("RGBA").save(path, optimize=True)


def write_json(path: Path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")


def write_mcmeta(png_path: Path, frametime=2, frames=None, interpolate=False, width=None, height=None):
    anim = {"frametime": frametime}
    if interpolate:
        anim["interpolate"] = True
    if width:
        anim["width"] = width
    if height:
        anim["height"] = height
    if frames is not None:
        anim["frames"] = frames
    write_json(Path(str(png_path) + ".mcmeta"), {"animation": anim})


def tex_path(kind: str, name: str) -> Path:
    return ASSETS / "textures" / kind / f"{name}.png"
