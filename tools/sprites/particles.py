"""Particle sprites: 8x8 effects and 16x16 emote bubbles (white speech bubble, dark soft outline, tail at the bottom)."""
from __future__ import annotations

import math

import pal  # noqa: F401
from pxl import L, M, paint, outline, hex2rgb, RAMPS, img, arr, blank
import numpy as np
from PIL import Image

PARTICLES: dict[str, Image.Image] = {}   # sprite name -> image
PARTICLE_JSON: dict[str, list[str]] = {}  # particle name -> sprite names


def reg(name, im):
    PARTICLES[name] = im


def ascii8(rows, legend, protect=None, ol=True, **kw):
    im = paint(M("\n".join(rows), 8, 8), legend)
    return outline(im, **kw) if ol else im


# ---------------------------------------------------------------- zzz  (big Z + small z)
reg("zzz", paint(M("""
.....www
......b.
.....BBB
wwwwww..
...bb...
..bb....
.bb.....
BBBBBB..
""", 8, 8), L("w=#A9C0FF", "b=#5F82E0", "B=#3F5FBF")))
PARTICLE_JSON["zzz"] = ["zzz"]

# ---------------------------------------------------------------- sparkle (4 frames, twinkle)
SP = L("w=#FFFDF0", "y=#FFE98A", "o=#FFC94A")


def sparkle_frame(level):
    cv = [["."] * 8 for _ in range(8)]
    cx = cy = 4
    cv[cy][cx] = "w"
    arms = {0: 1, 1: 2, 2: 3, 3: 2}[level]
    for k in range(1, arms + 1):
        ch = "y" if k < arms or arms == 1 else "o"
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            cv[cy + dy][cx + dx] = ch if k == 1 else ("o" if k == arms else "y")
    if level in (1, 2):
        for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            cv[cy + dy][cx + dx] = "y"
    if level == 3:
        cv[cy][cx] = "y"
    return paint(["".join(r) for r in cv], SP)


for i, lv in enumerate((0, 1, 2, 3)):
    reg(f"sparkle_{i}", sparkle_frame(lv))
PARTICLE_JSON["sparkle"] = [f"sparkle_{i}" for i in range(4)]

# ---------------------------------------------------------------- sweat drop
reg("sweat", paint(M("""
........
...o....
..olo...
..ollo..
.ollwlo.
.olllbo.
..obbo..
...oo...
""", 8, 8), L("o=#2F63A6", "l=#8FD3FF", "w=#EAFAFF", "b=#4FA3E8")))
PARTICLE_JSON["sweat"] = ["sweat"]

# ---------------------------------------------------------------- stink (green wavy lines)
reg("stink", paint(M("""
.ab..ab.
..ab..ab
..ab..ab
.ab..ab.
ab..ab..
ab..ab..
.ab..ab.
..ab..ab
""", 8, 8), L("a=#B4EE72", "b=#46A646")))
PARTICLE_JSON["stink"] = ["stink"]

# ---------------------------------------------------------------- laser dot (bright red core + soft glow)
a = np.zeros((8, 8, 4), dtype=np.uint8)
for y in range(8):
    for x in range(8):
        d = math.hypot(x + 0.5 - 4, y + 0.5 - 4)
        if d <= 1.05:
            c = (255, 244, 238, 255)
        elif d <= 1.9:
            c = (255, 58, 58, 255)
        elif d <= 2.7:
            c = (255, 48, 48, 150)
        elif d <= 3.4:
            c = (255, 48, 48, 70)
        elif d <= 4.0:
            c = (255, 48, 48, 28)
        else:
            c = (0, 0, 0, 0)
        a[y, x] = c
reg("laser_dot", img(a))
PARTICLE_JSON["laser_dot"] = ["laser_dot"]

# ---------------------------------------------------------------- leaf (2 variants)
def leaf_img(S, d, length, w, flip=False):
    n = math.hypot(*d)
    d = (d[0] / n, d[1] / n)
    nx, ny = -d[1], d[0]
    lit = 1 if (-nx - ny) > 0 else -1
    pr = RAMPS["pitaya_leaf"]
    a = np.zeros((8, 8, 4), dtype=np.uint8)
    for y in range(8):
        for x in range(8):
            px, py = x + 0.5 - S[0], y + 0.5 - S[1]
            t = px * d[0] + py * d[1]
            if t < 0 or t > length:
                continue
            s = px * nx + py * ny
            u = t / length
            hw = w * math.sin(math.pi * min(1.0, u ** 0.75))
            if abs(s) <= hw + 0.1:
                if abs(s) < 0.4:
                    col = pr[3]
                elif s * lit > 0:
                    col = pr[1] if u < 0.7 else pr[0]
                else:
                    col = pr[2]
                a[y, x] = col
    return img(a)


def outline8(im):
    return outline(im, strength=0.30)


# leaf shapes are drawn into the inner 6x6 so the outline fits
def leaf_inner(S, d, length, w):
    im = leaf_img(S, d, length, w)
    return outline8(im)


reg("leaf_0", leaf_inner((1.4, 6.0), (0.72, -0.69), 5.4, 1.6))
reg("leaf_1", leaf_inner((6.2, 6.1), (-0.45, -0.89), 5.4, 1.5))
PARTICLE_JSON["leaf"] = ["leaf_0", "leaf_1"]

# ---------------------------------------------------------------- sonar ring (16x16)
a = np.zeros((16, 16, 4), dtype=np.uint8)
for y in range(16):
    for x in range(16):
        d = math.hypot(x + 0.5 - 8, y + 0.5 - 8)
        ang = (x + y) - 15
        if 5.8 <= d < 6.9:
            c = (190, 252, 255, 255) if ang < -3 else ((70, 232, 246, 255) if ang < 4 else (40, 196, 226, 255))
        elif 6.9 <= d < 7.9:
            c = (70, 232, 246, 90)
        elif 4.9 <= d < 5.8:
            c = (70, 232, 246, 70)
        else:
            c = (0, 0, 0, 0)
        a[y, x] = c
reg("sonar", img(a))
PARTICLE_JSON["sonar"] = ["sonar"]

# ---------------------------------------------------------------- emote bubbles (16x16)
BUBBLE_FILL = hex2rgb("#FDFDFF")
BUBBLE_SHADE = hex2rgb("#D8DDF0")
BUBBLE_OUTLINE = hex2rgb("#3C4066")


def bubble_base():
    a = np.zeros((16, 16, 4), dtype=np.uint8)
    body = {}
    for y in range(1, 11):
        x0, x1 = 2, 13
        if y in (1, 10):
            x0, x1 = 4, 11
        elif y in (2, 9):
            x0, x1 = 3, 12
        for x in range(x0, x1 + 1):
            body[(x, y)] = BUBBLE_FILL
    for x in range(6, 10):
        body[(x, 11)] = BUBBLE_FILL
    for x in (7, 8):
        body[(x, 12)] = BUBBLE_FILL
    body[(7, 13)] = BUBBLE_FILL
    for (x, y), c in body.items():
        # soft shade on the lowest row of the bubble body and down the tail
        if y >= 10 or (x, y) in ((7, 12), (8, 12), (7, 13)) or (y == 9 and (x <= 3 or x >= 12) and False):
            c = BUBBLE_SHADE
        a[y, x] = c
    return a


def put(a, x0, y0, rows, legend):
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch == ".":
                continue
            a[y0 + dy, x0 + dx] = legend[ch]


def emote(name, rows, legend, x0, y0):
    a = bubble_base()
    put(a, x0, y0, rows, legend)
    im = outline(img(a), color=BUBBLE_OUTLINE)
    reg(name, im)
    PARTICLE_JSON[name] = [name]


# hungry: drumstick (meat upper left, bone lower right)
emote("emote_hungry", [
    "..ooo.....",
    ".oMMmo....",
    "oMMMMmo...",
    "oMMMmdo...",
    "oMMmddo...",
    ".odddoowo.",
    "..ooo.owwo",
    "......owo.",
], L("o=#6A3A1A", "M=#EAA24E", "m=#D07A2E", "d=#A35420", "w=#FBF7EC"), 3, 2)
# the bone's two knobs sit at the lower right

# sleepy: Z z
emote("emote_sleepy", [
    "......wwww",
    ".......bb.",
    "......BBBB",
    "wwwwww....",
    "...bb.....",
    "..bb......",
    ".bb.......",
    "BBBBBB....",
], L("w=#9DB6F5", "b=#5F82E0", "B=#3F5FBF"), 3, 2)

# dirty: green stink lines + fly
emote("emote_dirty", [
    ".ab.ab....",
    "..ab.ab...",
    "..ab.ab.k.",
    ".ab.ab.wkw",
    "ab.ab...k.",
    "ab.ab.....",
    ".ab.ab....",
    "..........",
], L("a=#9EE05C", "b=#3F9E44", "k=#2B2B3A", "w=#BFE3FF"), 3, 2)

# bored: ?
emote("emote_bored", [
    "..bbbb..",
    ".bb..bb.",
    "......bb",
    "....bbb.",
    "...bb...",
    "...bb...",
    "........",
    "...bb...",
], L("b=#5B6A93"), 4, 2)

# sad: rain cloud + drop
emote("emote_sad", [
    "...cccc...",
    "..cLLLCc..",
    ".cLLLLCCc.",
    "cLCCCCCCDc",
    ".dddddddd.",
    "..b..b....",
    "..B..B.b..",
    ".....B.B..",
][:0] or [
    "...lll....",
    "..lLLLl...",
    ".lLLLLCl..",
    "lLLCCCCCl.",
    ".llllllll.",
    "..b..b....",
    "..B..B..b.",
    ".....B..B.",
], L("l=#6E7BA0", "L=#C9D3E8", "C=#9AA7C4", "b=#8FD3FF", "B=#3F8FE0"), 3, 2)

# love: heart
emote("emote_love", [
    "..hh..hh..",
    ".hppPPpPp.",
    "hppPPPPPPs",
    "hpPPPPPPss",
    ".PPPPPPss.",
    "..PPPPss..",
    "...PPss...",
    "....ss....",
], L("h=#FFC4D2", "p=#FF8FA8", "P=#F0506F", "s=#C22E5C"), 3, 2)

if __name__ == "__main__":
    from sheets import sprite_sheet
    from pxl import OUT
    names = list(PARTICLES)
    sprite_sheet([(n, [PARTICLES[n]]) for n in names], OUT / "dbg_particles.png", k=10, cols=7)
