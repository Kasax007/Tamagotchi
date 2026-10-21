"""Painting helpers: hue-shifted ramps, face canvases, surface patterns and expressive eyes."""
import colorsys
import random

import numpy as np

EXPRESSIONS = ('normal', 'blink', 'happy', 'sleep', 'sad', 'angry', 'love')


# ---------------------------------------------------------------- colour

def hx(s):
    s = s.lstrip('#')
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def _shift(rgb, dh=0.0, ds=0.0, dv=0.0):
    r, g, b = (c / 255 for c in rgb)
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    h = (h + dh / 360.0) % 1.0
    s = min(1.0, max(0.0, s + ds))
    v = min(1.0, max(0.0, v + dv))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (round(r * 255), round(g * 255), round(b * 255))


def ramp(base, warm=1.0):
    """5-step ramp [deep, shadow, base, light, highlight] with hue shifting (shadows cooler)."""
    b = hx(base) if isinstance(base, str) else base
    h = colorsys.rgb_to_hsv(*(c / 255 for c in b))[0] * 360
    # shift shadows toward blue/purple (240-270deg), highlights toward yellow (60deg)
    def toward(target, amount):
        diff = ((target - h + 540) % 360) - 180
        return max(-abs(amount), min(abs(amount), diff))
    return [
        _shift(b, toward(250, 16 * warm), 0.10, -0.34),
        _shift(b, toward(250, 8 * warm), 0.06, -0.17),
        b,
        _shift(b, toward(60, 6 * warm), -0.06, 0.10),
        _shift(b, toward(60, 12 * warm), -0.14, 0.20),
    ]


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---------------------------------------------------------------- texture + canvases

class Texture:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.rgba = np.zeros((h, w, 4), np.uint8)
        self.glow = np.zeros((h, w, 4), np.uint8)

    def save(self, path, glow_path=None):
        from PIL import Image
        Image.fromarray(self.rgba, 'RGBA').save(path)
        if glow_path is not None and self.glow[..., 3].any():
            Image.fromarray(self.glow, 'RGBA').save(glow_path)
            return True
        return False


class Canvas:
    """A face region. (0,0) is the top-left of the face picture as seen from outside."""

    def __init__(self, tex, rect, face, rng, mats):
        self.tex = tex
        self.u, self.v, self.w, self.h = rect
        self.face = face
        self.rng = rng
        self.mats = mats

    def inside(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def px(self, x, y, col, a=255):
        x, y = int(x), int(y)
        if self.inside(x, y) and col is not None:
            self.tex.rgba[self.v + y, self.u + x] = (*col, a)

    def get(self, x, y):
        return tuple(int(c) for c in self.tex.rgba[self.v + y, self.u + x, :3])

    def clear(self, x, y):
        if self.inside(x, y):
            self.tex.rgba[self.v + y, self.u + x] = (0, 0, 0, 0)

    def glow(self, x, y, col, a=255):
        x, y = int(x), int(y)
        if self.inside(x, y):
            self.tex.glow[self.v + y, self.u + x] = (*col, a)

    def rect(self, x0, y0, x1, y1, col):
        """Inclusive rectangle."""
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.px(x, y, col)

    def fill(self, col):
        self.rect(0, 0, self.w - 1, self.h - 1, col)

    def hline(self, x0, x1, y, col):
        self.rect(x0, y, x1, y, col)

    def vline(self, x, y0, y1, col):
        self.rect(x, y0, x, y1, col)

    def mirror_px(self, x, y, col):
        """Pixel and its horizontal mirror."""
        self.px(x, y, col)
        self.px(self.w - 1 - x, y, col)

    def pattern(self, pts, x0, y0, cols):
        """Draw ASCII rows; each char maps through cols (dict). '.'/' ' = skip."""
        for j, row in enumerate(pts):
            for i, ch in enumerate(row):
                if ch in cols:
                    self.px(x0 + i, y0 + j, cols[ch])

    def m(self, name):
        return self.mats[name]


# ---------------------------------------------------------------- materials + base shading

class Mat:
    """A material: ramp + surface pattern."""

    def __init__(self, base, pattern='smooth', density=0.10, warm=1.0, ramp_override=None, flat=False):
        self.r = ramp_override or ramp(base, warm)
        self.pattern = pattern
        self.density = density
        self.flat = flat

    def __getitem__(self, i):
        return self.r[i]


def shade_face(c, mat):
    """Base fill: top lighter, bottom darker, sides with a soft vertical gradient and rim light."""
    r = mat.r
    f = c.face
    if mat.flat:
        c.fill(r[2])
        return
    if f == 'top':
        c.fill(r[3])
        for x in range(c.w):  # front edge catches the light
            if c.rng.random() < 0.6:
                c.px(x, c.h - 1, r[4])
    elif f == 'bottom':
        c.fill(r[1])
    else:
        c.fill(r[2])
        if c.h >= 3:
            for x in range(c.w):
                c.px(x, 0, r[3])
        if c.h >= 4:
            for x in range(c.w):
                c.px(x, c.h - 1, r[1])


def apply_pattern(c, mat):
    p, dens, r, rng = mat.pattern, mat.density, mat.r, c.rng
    base_row = 0
    if p == 'smooth':
        for y in range(c.h):
            for x in range(c.w):
                if rng.random() < dens:
                    cur = c.get(x, y)
                    lvl = _level_of(cur, r)
                    c.px(x, y, r[max(0, min(4, lvl + rng.choice((-1, 1))))])
    elif p == 'scales':
        # staggered little arcs: a darker pixel under a lighter one every 3 px
        for y in range(1, c.h, 2):
            off = 0 if (y // 2) % 2 == 0 else 1
            for x in range(off, c.w, 3):
                cur = _level_of(c.get(x, y), r)
                c.px(x, y, r[max(0, cur - 1)])
                if y - 1 >= 0 and rng.random() < 0.5:
                    c.px(x, y - 1, r[min(4, _level_of(c.get(x, y - 1), r) + 1)])
    elif p == 'fur':
        for y in range(c.h):
            for x in range(c.w):
                if rng.random() < dens:
                    cur = _level_of(c.get(x, y), r)
                    d = rng.choice((-1, -1, 1))
                    c.px(x, y, r[max(0, min(4, cur + d))])
                    if y + 1 < c.h and rng.random() < 0.5:
                        c.px(x, y + 1, r[max(0, min(4, cur + d))])
    elif p == 'stone':
        n = _value_noise(c.w, c.h, rng, 3)
        for y in range(c.h):
            for x in range(c.w):
                cur = _level_of(c.get(x, y), r)
                t = n[y][x]
                if t > 0.72:
                    c.px(x, y, r[min(4, cur + 1)])
                elif t < 0.28:
                    c.px(x, y, r[max(0, cur - 1)])
        for _ in range(max(1, c.w * c.h // 40)):
            x, y = rng.randrange(c.w), rng.randrange(c.h)
            c.px(x, y, r[0])
    elif p == 'wood':
        for y in range(c.h):
            if y % 4 == 3:
                for x in range(c.w):
                    c.px(x, y, r[1])
            else:
                for x in range(c.w):
                    if rng.random() < dens:
                        c.px(x, y, r[max(0, _level_of(c.get(x, y), r) - 1)])
    elif p == 'none':
        pass


def _level_of(col, r):
    best, bi = None, 2
    for i, rc in enumerate(r):
        dd = sum((col[k] - rc[k]) ** 2 for k in range(3))
        if best is None or dd < best:
            best, bi = dd, i
    return bi


def _value_noise(w, h, rng, cell):
    gw, gh = w // cell + 2, h // cell + 2
    g = [[rng.random() for _ in range(gw)] for _ in range(gh)]
    out = []
    for y in range(h):
        row = []
        for x in range(w):
            fx, fy = x / cell, y / cell
            ix, iy = int(fx), int(fy)
            tx, ty = fx - ix, fy - iy
            a = g[iy][ix] * (1 - tx) + g[iy][ix + 1] * tx
            b = g[iy + 1][ix] * (1 - tx) + g[iy + 1][ix + 1] * tx
            row.append(a * (1 - ty) + b * ty)
        out.append(row)
    return out


# ---------------------------------------------------------------- eyes

PUPIL = (34, 26, 48)


def eye(c, x, y, expr, iris=(70, 60, 110), skin=None, lid=None, size=(2, 3), glow=None, white=(255, 255, 255),
        side='l', pupil=None, highlight=True):
    """Draw one eye with its top-left at (x, y). size = (w, h) of the open eye (2x2, 2x3 or 3x3).
    skin = colour used to 'erase' around closed eyes (defaults to the pixel already there).
    side = 'l' / 'r' (which side of the face; used for asymmetric brows)."""
    w, h = size
    dark = (pupil or PUPIL) if glow is None else glow
    lidc = lid or (60, 40, 50)
    if expr in ('normal', 'angry', 'sad'):
        for j in range(h):
            for i in range(w):
                c.px(x + i, y + j, dark)
        # iris tint on the lower row(s), catch-light top-left
        for i in range(w):
            c.px(x + i, y + h - 1, iris)
        if glow is not None:
            for j in range(h):
                for i in range(w):
                    c.glow(x + i, y + j, glow)
        if highlight:
            c.px(x, y, white)
        # 'r' = the pet's right eye = left in the face picture, so its inner corner is its right column
        inner = x + w - 1 if side == 'r' else x
        outer = x if side == 'r' else x + w - 1
        if expr == 'angry':
            c.px(inner, y, lidc)            # brows slant down toward the nose
            c.px(inner, y - 1, lidc)
            if highlight:
                c.px(outer, y, white)
        if expr == 'sad':
            c.px(outer, y, lidc)            # droopy outer lid
            c.px(inner, y + h, (120, 200, 255))  # tear
    elif expr == 'blink':
        c.hline(x, x + w - 1, y + h - 1, dark)
        if glow is not None:
            c.glow(x, y + h - 1, glow)
            c.glow(x + w - 1, y + h - 1, glow)
    elif expr == 'sleep':
        # relaxed closed eye: little downward curve
        yy = y + h - 1
        c.px(x - 1 if w < 3 else x, yy - 1, dark)
        c.hline(x, x + w - 1, yy, dark)
        c.px(x + w if w < 3 else x + w - 1, yy - 1, dark)
    elif expr == 'happy':
        # ^ ^
        yy = y + h - 1
        cx = x + (w - 1) / 2.0
        if w == 2:
            ox = x - 1 if side == 'r' else x      # caret grows outward, never toward the other eye
            c.px(ox, yy, dark)
            c.px(ox + 1, yy - 1, dark)
            c.px(ox + 2, yy, dark)
        else:
            c.px(x, yy, dark)
            c.px(x + 1, yy - 1, dark)
            c.px(x + 2, yy, dark)
        if glow is not None:
            c.glow(x, yy - 1, glow)
            c.glow(x + w - 1, yy - 1, glow)
    elif expr == 'love':
        red, pink = (230, 50, 90), (255, 140, 170)
        # 3x3 heart centred on the eye
        hx0 = x - (1 if w == 2 else 0)
        hy0 = y + max(0, h - 3)
        for (i, j) in ((0, 0), (2, 0), (0, 1), (1, 1), (2, 1), (1, 2)):
            c.px(hx0 + i, hy0 + j, red)
        c.px(hx0, hy0, pink)
        c.glow(hx0 + 1, hy0 + 1, (255, 90, 130), 160)


def eyes(c, y, expr, gap=2, size=(2, 3), x=None, **kw):
    """Symmetric pair centred on the face."""
    w, h = size
    if x is None:
        total = 2 * w + gap
        x = (c.w - total) // 2
    eye(c, x, y, expr, size=size, side='r', **kw)
    eye(c, x + w + gap, y, expr, size=size, side='l', **kw)
    return x


def blush(c, y, x_left, x_right, col=(255, 140, 160)):
    c.px(x_left, y, col)
    c.px(x_right, y, col)


def make_rng(seed):
    return random.Random(seed)
