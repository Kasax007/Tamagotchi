"""Block textures (16x16).  Structures are authored as ASCII / cell sets; shading follows the top-left light.

``TEX[name]`` is a PIL image (animated textures are vertical strips, see ``ANIM``).
Shared footprints (``GEO``) are used by the model builder too, so textures and boxes always agree.
"""
from __future__ import annotations

import math

import pal  # noqa: F401
from modelkit import round_rect, rect_cells
from pxl import (RAMPS, L, M, paint, blank, img, arr, hash2, hex2rgb, noise_shift, vstack, with_alpha, rgb2oklch,
                 oklch2rgb)
import numpy as np
from PIL import Image

TEX: dict[str, Image.Image] = {}
ANIM: dict[str, dict] = {}   # texture name -> mcmeta animation dict


def R(name, i):
    return RAMPS[name][i]


def px_canvas():
    return {}


def to_img(cells, w=16, h=16, fill=None):
    a = np.zeros((h, w, 4), dtype=np.uint8)
    if fill is not None:
        a[:, :] = fill
    for (x, y), c in cells.items():
        if 0 <= x < w and 0 <= y < h:
            a[y, x] = c if len(c) == 4 else (c[0], c[1], c[2], 255)
    return img(a)


def pick(ramp, i, tint=0):
    return RAMPS[ramp][max(0, min(4, i + tint))]


def tint_of(x, y, seed, p=0.22):
    v = hash2(x, y, seed)
    return -1 if v < p else (1 if v > 1 - p else 0)


# ======================================================================================
# shared footprints
# ======================================================================================
GEO = {}
# pet bed (x, z cells)
GEO["bed_outerA"] = round_rect(1, 1, 15, 15, [3, 2, 1])
GEO["bed_outerB"] = round_rect(2, 2, 14, 14, [2, 1])
GEO["bed_hollow"] = round_rect(4, 4, 12, 12, [2, 1])
BED_PAW = [
    ".x..x.",
    "x.xx.x",
    "..xx..",
    ".xxxx.",
    ".xxxx.",
    "..xx..",
]
GEO["bed_paw"] = {(5 + dx, 5 + dz) for dz, row in enumerate(BED_PAW) for dx, ch in enumerate(row) if ch == "x"}   # stitched paw on the cushion
# dragon nest
GEO["nest_outer"] = round_rect(0, 0, 16, 16, [4, 2, 1])
GEO["nest_hollow"] = round_rect(3, 3, 13, 13, [2, 1])
# bowl
GEO["bowl_outer"] = round_rect(3, 3, 13, 13, 1)
GEO["bowl_hollow"] = round_rect(4, 4, 12, 12, 1)
# bath
GEO["bath_outer"] = round_rect(1, 1, 15, 15, [3, 2, 1])
GEO["bath_hollow"] = round_rect(3, 3, 13, 13, [2, 1])
# mushroom caps (normal / squished)
GEO["cap_n1"] = round_rect(0, 0, 16, 16, [4, 2, 1])
GEO["cap_n2"] = round_rect(2, 2, 14, 14, [3, 1])
GEO["cap_n3"] = round_rect(4, 4, 12, 12, [2, 1])
GEO["cap_s1"] = round_rect(0, 0, 16, 16, [3, 1])
GEO["cap_s2"] = round_rect(1, 1, 15, 15, [3, 1])
GEO["cap_s3"] = round_rect(3, 3, 13, 13, [2, 1])


def lit_of(x, y, cx=8.0, cy=8.0):
    return (x + 0.5 - cx) + (y + 0.5 - cy)


# ======================================================================================
# 1. pet bed
# ======================================================================================
def build_bed():
    # side band: rows 10..15 are y = 6..0 (default uv), tier B above tier A
    rows = {
        10: "lllhllllhlllllhl",
        11: "lblllbllblllbllb",
        12: "blblblblblblblbl",   # stitched seam between the two tiers
        13: "bbbsbbbbbsbbbbbs",
        14: "bsbbsbsbbsbbsbsb",
        15: "sssdsssdsssdsssd",
    }
    leg = L("hlbsd=fabric")           # grayscale: the block's dye colour multiplies it (tintindex 0)
    full = []
    for y in range(16):
        full.append(rows.get(y, rows[10 + (y % 2)]))
    TEX["pet_bed_side"] = noise_shift(paint(full, leg), amount=0.018, seed=3, period=16)

    # top view painting: the rim (gray, tinted) in pet_bed_top together with the stitched paw print, the cream cushion
    # (untinted) in pet_bed_cushion
    A, B, H = GEO["bed_outerA"], GEO["bed_outerB"], GEO["bed_hollow"]
    cells = {}
    for (x, z) in A:
        t = lit_of(x, z)
        if (x, z) in H:
            continue
        if (x, z) in B:   # upper roll, 2px wide
            i = 0 if t < -6 else (1 if t < 2 else 2)
            if t < -6 and hash2(x, z, 5) < 0.5:
                i = 1
            cells[(x, z)] = R("fabric", i)
        else:             # outer step of the lower tier
            i = 1 if t < -2 else (2 if t < 6 else 3)
            cells[(x, z)] = R("fabric", i)
    pawc = GEO["bed_paw"]
    for (x, z) in H:     # filler under the cushion: never sampled by the model, but keeps the sheet opaque
        cells[(x, z)] = R("fabric", 2)
    for (x, z) in pawc:   # embroidery: base thread, lit upper left, shaded lower right (gray: the dye colours it)
        lower_right = (x + 1, z) not in pawc or (x, z + 1) not in pawc
        upper_left = (x - 1, z) not in pawc or (x, z - 1) not in pawc
        cells[(x, z)] = R("fabric", 3 if lower_right and not upper_left else (1 if upper_left and not lower_right else 2))
    TEX["pet_bed_top"] = to_img(cells, fill=R("fabric", 2))
    # cushion: cream, shaded next to the rim
    cells = {}
    for (x, z) in H:
        edge = any(n not in H for n in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)))
        i = 2 if edge else 1
        if not edge and hash2(x, z, 9) < 0.18:
            i = 0
        cells[(x, z)] = R("cream", i)
    TEX["pet_bed_cushion"] = to_img(cells, fill=R("cream", 1))


# ======================================================================================
# 2. pet basket
# ======================================================================================
def weave_tile(ramp, seed, tint_p=0.28):
    HS = ["1112", "2233"]
    cells = {}
    for cy in range(4):
        for cx in range(4):
            horiz = (cx + cy) % 2 == 0
            for sub in range(2):
                t = tint_of(cx, cy * 2 + sub, seed, tint_p)
                for i in range(2):
                    for j in range(4):
                        idx = int(HS[i][j])
                        if horiz:
                            x, y = cx * 4 + j, cy * 4 + sub * 2 + i
                        else:
                            x, y = cx * 4 + sub * 2 + i, cy * 4 + j
                        cells[(x, y)] = pick(ramp, idx, t)
    return to_img(cells)


def build_basket():
    TEX["pet_basket_weave"] = weave_tile("wicker", 11)
    cells = {}
    for y in range(16):
        for x in range(16):
            i = [1, 1, 2, 3][(x + y) % 4]
            t = tint_of(x // 2, y // 2, 4, 0.2)
            cells[(x, y)] = pick("wicker", i, t)
    TEX["pet_basket_rim"] = to_img(cells)
    # blanket: 4x4 checks, blue / off-white, with a knit grid
    cells = {}
    for y in range(16):
        for x in range(16):
            blue = ((x // 4) + (y // 4)) % 2 == 0          # "blue" checks are gray here: the model tints them (tintindex 0)
            ramp = "fabric" if blue else "blanket_white"
            i = 1
            if x % 4 == 3 or y % 4 == 3:
                i = 3 if blue else 2
            if x % 4 == 0 and y % 4 == 0:
                i = 0
            cells[(x, y)] = pick(ramp, i, tint_of(x, y, 17, 0.12))
    TEX["pet_basket_blanket"] = to_img(cells)


# ======================================================================================
# 3. dragon nest
# ======================================================================================
def build_nest():
    # side: woven strands of straw and twigs (rows of 2px), irregular segments with dark gaps
    cells = {}
    for band in range(8):
        y0 = band * 2
        twig = band % 3 == 1
        x = -int(hash2(band, 1, 21) * 4)
        while x < 16:
            seg = 4 + int(hash2(band, x + 40, 22) * 5)
            ramp = "twig" if (twig or hash2(band, x, 23) < 0.15) else "straw"
            for sx in range(x, x + seg - 1):
                for i in range(2):
                    idx = 1 + i + (1 if ramp == "twig" else 0)
                    if sx == x:
                        idx -= 1
                    cells[(sx % 16, y0 + i)] = pick(ramp, max(0, idx), tint_of(sx, band, 24, 0.2))
            gx = (x + seg - 1) % 16
            for i in range(2):
                cells[(gx, y0 + i)] = RAMPS["twig"][4] if i == 1 else RAMPS["straw"][4]
            x += seg
    TEX["dragon_nest_straw"] = to_img(cells)

    # top view: crossing straw/twig strokes on the ring, soft down inside
    O, H = GEO["nest_outer"], GEO["nest_hollow"]
    cells = {}
    for (x, z) in O:
        if (x, z) in H:
            continue
        stroke = (x + 2 * z) % 7
        twig = (x * 3 + z) % 11 < 3
        if twig:
            c = pick("twig", [1, 2, 2, 3][(x + z) % 4])
        else:
            c = pick("straw", [0, 1, 1, 2, 3][(stroke + z) % 5])
        cells[(x, z)] = c
    for (x, z) in H:
        edge = any(n not in H for n in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)))
        v = hash2(x, z, 31)
        i = 1
        if edge:
            i = 2
        elif v < 0.12:
            i = 2
        elif v > 0.82:
            i = 0
        cells[(x, z)] = pick("down", i)
    # a few feathery curls in the down
    for (x, z) in ((6, 6), (7, 6), (9, 9), (10, 9), (5, 9), (8, 5), (11, 7), (7, 10)):
        if (x, z) in H:
            cells[(x, z)] = R("down", 3)
    for (x, z) in ((6, 5), (8, 6), (9, 8), (10, 8), (6, 9)):
        if (x, z) in H:
            cells[(x, z)] = R("down", 0)
    TEX["dragon_nest_top"] = to_img(cells)

    # eggshell (speckled, cracked rim is made by the boxes)
    cells = {}
    for y in range(16):
        for x in range(16):
            v = hash2(x, y, 41)
            i = 1
            if v < 0.10:
                i = 3
            elif v < 0.22:
                i = 2
            elif v > 0.90:
                i = 0
            if y % 8 == 0:
                i = min(4, i + 1)
            cells[(x, y)] = pick("shell", i)
    TEX["dragon_nest_shell"] = to_img(cells)

    # gold coin (top + edge)
    cells = {}
    for y in range(16):
        for x in range(16):
            i = 2
            if (x + y) % 5 == 0:
                i = 1
            if x < 2 or y < 2:
                i = 1
            if x > 12 or y > 12:
                i = 3
            cells[(x, y)] = pick("gold", i)
    cells[(10, 8)] = R("gold", 0)
    cells[(10, 9)] = R("gold", 0)
    cells[(11, 9)] = R("gold", 1)
    TEX["dragon_nest_coin"] = to_img(cells)


# ======================================================================================
# 4. food bowl
# ======================================================================================
def build_bowl():
    # side band: rows 11..15 = y 5..0 (default uv).  Paw print (6x4) on rows 11..14, foot shadow on row 15.
    paw = {11: (6, 9), 12: (5, 10), 13: (7, 8), 14: (6, 7, 8, 9)}
    pawset = {(x, y) for y, xs in paw.items() for x in xs}
    cells = {}
    for y in range(16):
        for x in range(16):
            if y < 11:
                c = R("ceramic", 2)
            elif y == 15:
                c = R("ceramic", 3)
            else:
                c = R("ceramic", 2)
                if x < 3:
                    c = R("ceramic", 1)
                elif x > 12:
                    c = R("ceramic", 3)
                if 11 <= y <= 14 and (x - 1, y - 1) in pawset and (x, y) not in pawset:
                    c = R("ceramic", 3)           # soft drop shadow of the print
                if (x, y) in pawset:
                    c = hex2rgb("#FBFEFF")
            cells[(x, y)] = c
    TEX["food_bowl_side"] = noise_shift(to_img(cells), amount=0.010, seed=6, period=16)

    O, H = GEO["bowl_outer"], GEO["bowl_hollow"]
    cells = {}
    for (x, z) in O:
        if (x, z) in H:
            edge = any(n not in H for n in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)))
            c = R("ceramic", 3) if edge else R("ceramic", 2)
            if not edge and (x, z) in ((5, 5), (6, 5), (5, 6)):
                c = R("ceramic", 1)
            cells[(x, z)] = c
        else:
            t_ = lit_of(x, z)
            cells[(x, z)] = R("ceramic", 0 if t_ < -2 else (1 if t_ < 4 else 2))
    TEX["food_bowl_top"] = to_img(cells)

    cells = {}
    for y in range(16):
        for x in range(16):
            i = 1 if y <= 11 else (2 if y <= 13 else 3)
            cells[(x, y)] = pick("ceramic", i, tint_of(x, y, 8, 0.1))
    TEX["food_bowl_inner"] = to_img(cells)

    # kibble: brick-like pellets, light enough to read against their gaps
    cells = {(x, y): R("kibble", 3) for y in range(16) for x in range(16)}
    for row in range(6):
        off = (row % 2) * 1
        for col in range(-1, 6):
            x0 = col * 3 + off
            y0 = row * 3
            tone = hash2(row, col, 51)
            base = 2 if tone < 0.45 else (1 if tone < 0.8 else 2)
            pats = [(0, 0, base - 1), (1, 0, base), (0, 1, base), (1, 1, base + 1)]
            for (dx, dy, i) in pats:
                cells[(x0 + dx, y0 + dy)] = pick("kibble", max(0, min(4, i)))
            if hash2(row, col, 52) < 0.35:
                cells[(x0 + 2, y0)] = pick("kibble", 4)
    TEX["food_bowl_kibble"] = to_img(cells)


# ======================================================================================
# 5. pet bath
# ======================================================================================
def build_bath():
    cells = {}
    hoops = {9: 0, 10: 2, 13: 0, 14: 2}   # texture rows (v = 16 - y) that carry the iron hoops
    for y in range(16):
        for x in range(16):
            stave = x // 4
            if x % 4 == 0 and y not in hoops:
                c = R("tubwood", 4)
            else:
                i = 1 + (stave % 2)
                if x % 4 == 1:
                    i -= 1
                if x % 4 == 3:
                    i += 1
                t = tint_of(x, y, 61, 0.18)
                c = pick("tubwood", i, t)
                if y == 8:
                    c = pick("tubwood", 0 if x % 4 == 1 else 1)
                if y == 15:
                    c = pick("tubwood", 3)
            if y in hoops:
                base = hoops[y]
                c = pick("iron", base + (1 if x % 4 else 0))
                if y in (9, 13) and x % 8 == 2:
                    c = R("iron", 0)   # rivet
                if y in (10, 14) and x % 8 == 3:
                    c = R("iron", 4)
            cells[(x, y)] = c
    TEX["pet_bath_wood"] = to_img(cells)

    O, H = GEO["bath_outer"], GEO["bath_hollow"]
    cells = {}
    for (x, z) in O:
        if (x, z) in H:
            i = 3 + (1 if (z % 3 == 0) else 0)
            c = pick("tubwood", i)
            if (x, z) in ((4, 4), (5, 4), (4, 5)):
                c = R("tubwood", 3)
            cells[(x, z)] = c
        else:
            t = lit_of(x, z)
            i = 0 if t < -7 else (1 if t < 3 else 2)
            if hash2(x, z, 71) < 0.18:
                i = min(4, i + 1)
            cells[(x, z)] = R("tubwood", i)
    TEX["pet_bath_top"] = to_img(cells)

    cells = {}
    for y in range(16):
        for x in range(16):
            i = 3 if x % 4 else 4
            if y in (9, 10):
                i = 4
            cells[(x, y)] = pick("tubwood", i, tint_of(x, y, 73, 0.15))
    TEX["pet_bath_inner"] = to_img(cells)

    # rubber duck atlas: rows 0-1 top, 2-3 side, 4-5 head side (eye), 6-7 beak
    cells = {}
    for y in range(16):
        for x in range(16):
            if y < 2:
                c = R("duck", 1 if y == 0 else 2)
            elif y < 4:
                c = R("duck", 2 if y == 2 else 3)
            elif y < 6:
                c = R("duck", 2 if y == 4 else 3)
            elif y < 8:
                c = R("beak", 1 if y == 6 else 2)
            else:
                c = R("duck", 2)
            cells[(x, y)] = c
    cells[(1, 4)] = hex2rgb("#2A2330")
    cells[(0, 4)] = R("duck", 0)
    cells[(3, 2)] = R("duck", 1)
    TEX["pet_bath_duck"] = to_img(cells)

    # animated water, 8 frames: drifting waves, bobbing bubbles, foam rim
    frames = []
    H = GEO["bath_hollow"]
    bubbles = [(5, 9, 0.9), (9, 6, 1.7), (7, 4, 2.6), (10, 10, 3.3)]
    for f in range(8):
        cells = {}
        for (x, z) in H:
            phase = (x * 2 + z * 3) / 16.0 * 2 * math.pi
            w = math.sin(phase - f * math.pi / 4) + 0.5 * math.sin((x - z) / 16.0 * 2 * math.pi * 2 + f * math.pi / 4)
            i = 2
            if w > 1.0:
                i = 0
            elif w > 0.35:
                i = 1
            elif w < -1.0:
                i = 4
            elif w < -0.35:
                i = 3
            c = with_alpha(R("water", i), 205)
            edge = any(n not in H for n in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)))
            if edge:
                fo = 1 if (x * 7 + z * 5 + f) % 3 else 2
                c = with_alpha(R("foam", fo), 235)
            cells[(x, z)] = c
        # bubbles drift 1px per frame in a loop and wobble sideways
        for (bx, bz, ph) in bubbles:
            cx = bx + int(round(math.sin(f * math.pi / 4 + ph)))
            cz = (bz + f) % 6 + 4
            for (dx, dz, k) in ((0, 0, 1), (1, 0, 2), (0, 1, 2), (1, 1, 3)):
                p = (cx + dx, cz + dz)
                if p in H:
                    cells[p] = with_alpha(R("foam", k if k != 1 else 0), 255)
            if (cx, cz) in H:
                cells[(cx, cz)] = hex2rgb("#FFFFFF")
        frames.append(to_img(cells))
    TEX["pet_bath_water"] = vstack(frames)
    ANIM["pet_bath_water"] = {"frametime": 4, "interpolate": True}


# ======================================================================================
# 6. bouncy mushroom
# ======================================================================================
def build_mushroom():
    # top view: red cap with soft spots
    cells = {}
    spots = [(5.5, 5.5, 2.5), (11.0, 4.5, 1.7), (9.5, 10.0, 2.8), (3.8, 10.5, 1.6), (12.5, 11.5, 1.2), (7.0, 1.8, 1.2)]
    for y in range(16):
        for x in range(16):
            t = lit_of(x, y)
            i = 1 if t < -6 else (2 if t < 4 else 3)
            if hash2(x, y, 81) < 0.12:
                i += 1 if i < 3 else -1
            cells[(x, y)] = pick("cap", i)
    for (cx, cy, r) in spots:
        for y in range(16):
            for x in range(16):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if d <= r:
                    k = 1
                    if (x + 0.5 - cx) + (y + 0.5 - cy) < -r * 0.6:
                        k = 0
                    elif (x + 0.5 - cx) + (y + 0.5 - cy) > r * 0.5:
                        k = 2
                    cells[(x, y)] = pick("spot", k)
    TEX["bouncy_mushroom_cap_top"] = to_img(cells)

    # cap side band (rows 0..5 top -> bottom), partial spots
    cells = {}
    band = [1, 1, 2, 2, 3, 4]
    for y in range(16):
        for x in range(16):
            i = band[min(y, 5)] if y < 6 else 3
            if hash2(x, y, 83) < 0.10 and y < 6:
                i = min(4, i + 1)
            cells[(x, y)] = pick("cap", i)
    for (x0, y0, w, h) in ((3, 2, 3, 2), (11, 0, 2, 2)):
        for dy in range(h):
            for dx in range(w):
                if (dx, dy) in ((0, 0), (w - 1, 0)) and w > 2 and h > 1:
                    continue
                k = 0 if dy == 0 and dx == 0 else (1 if dy == 0 else 2)
                cells[((x0 + dx) % 16, y0 + dy)] = pick("spot", k if h > 1 else 1)
    TEX["bouncy_mushroom_cap_side"] = to_img(cells)

    # stem: cream, darkest right under the cap (row 0)
    cells = {}
    for y in range(16):
        for x in range(16):
            i = 3 if y == 0 else (2 if y == 1 else 1)
            if x % 4 == 3:
                i += 1 if y > 1 else 0
            if hash2(x, y, 85) < 0.1:
                i = min(4, i + 1)
            cells[(x, y)] = pick("cream", i)
    TEX["bouncy_mushroom_stem"] = to_img(cells)

    # gills (underside): radial lines
    cells = {}
    for y in range(16):
        for x in range(16):
            ang = math.atan2(y + 0.5 - 8, x + 0.5 - 8)
            line = (round(ang / (math.pi / 8)) % 2 == 0) and math.hypot(x + 0.5 - 8, y + 0.5 - 8) > 2.5
            cells[(x, y)] = pick("cream", 2 if line else 1, 1 if line and (x + y) % 3 == 0 else 0)
    TEX["bouncy_mushroom_gills"] = to_img(cells)


# ======================================================================================
# 7. running wheel stand
# ======================================================================================
def build_wheel():
    cells = {}
    for y in range(16):
        for x in range(16):
            plank = x // 4
            i = 1 + (plank % 2)
            if x % 4 == 0:
                i = 3
            if x % 4 == 1:
                i -= 1
            t = tint_of(x, y, 91, 0.16)
            c = pick("lightwood", i, t)
            if y % 8 == 7 and x % 4 == 2:
                c = R("lightwood", 4)   # nail
            cells[(x, y)] = c
    TEX["running_wheel_wood"] = to_img(cells)
    cells = {}
    for y in range(16):
        for x in range(16):
            i = 2
            if x < 2 or y < 2:
                i = 1
            if x > 13 or y > 13:
                i = 3
            if (x + y) % 6 == 0 and 2 <= x <= 13 and 2 <= y <= 13:
                i = 1
            cells[(x, y)] = pick("copper", i)
    for (x, y) in ((4, 4), (11, 4), (4, 11), (11, 11)):
        cells[(x, y)] = R("copper", 0)
        cells[(x + 1, y + 1)] = R("copper", 4)
    TEX["running_wheel_copper"] = to_img(cells)


# ======================================================================================
# 8. scratching post
# ======================================================================================
def build_post():
    cells = {}
    for y in range(16):
        for x in range(16):
            i = [1, 1, 2, 3][(x + y) % 4]
            if y % 4 == 3:
                i = 3 if x % 2 else 4
            cells[(x, y)] = pick("sisal", i, tint_of(x, y, 101, 0.1))
    TEX["scratching_post_sisal"] = to_img(cells)

    def carpet(kind):
        cells = {}
        for y in range(16):
            for x in range(16):
                v = hash2(x, y, 111 if kind == "top" else 112)
                i = 2
                if v < 0.18:
                    i = 1
                elif v > 0.82:
                    i = 3
                cells[(x, y)] = pick("carpet", i)
        return cells

    c = carpet("top")
    for y in range(16):
        for x in range(16):
            inplat = 3 <= x < 13 and 3 <= y < 13
            onbase = 2 <= x < 14 and 2 <= y < 14
            if inplat:
                border = x in (3, 12) or y in (3, 12)
                c[(x, y)] = pick("carpet", 0 if border and x + y < 16 else (1 if (x + y) % 3 else 2), 0)
                if border and x + y >= 16:
                    c[(x, y)] = R("carpet", 2)
            elif onbase:
                c[(x, y)] = R("carpet", 3 if (x + y) % 2 else 2)
    TEX["scratching_post_carpet_top"] = to_img(c)

    c = carpet("side")
    for y in range(16):
        for x in range(16):
            if y in (0, 14):
                c[(x, y)] = R("carpet", 1 if x % 2 else 0)        # piping, light
            elif y in (1, 15):
                c[(x, y)] = R("carpet", 3 if x % 2 else 4)       # lower edge, shadow
            elif y in (2, 13):
                c[(x, y)] = R("carpet", 2)
    TEX["scratching_post_carpet_side"] = to_img(c)

    cells = {}
    for y in range(16):
        for x in range(16):
            v = hash2(x, y, 121)
            i = 2
            if (x + y) % 3 == 0:
                i = 1
            if v < 0.25:
                i = 0 if x + y < 14 else 1
            elif v > 0.7:
                i = 3
            if x + y > 22:
                i = 3
            cells[(x, y)] = pick("pompom", i)
    TEX["scratching_post_pompom"] = to_img(cells)
    TEX["scratching_post_string"] = to_img({(x, y): R("cream", 1 if x % 2 else 2) for x in range(16) for y in range(16)})


# ======================================================================================
# 9. pet house
# ======================================================================================
def build_house():
    cells = {}
    for y in range(16):
        for x in range(16):
            plank = x // 4
            i = 2 + (1 if plank % 2 else 0) - (1 if plank == 2 else 0)
            if x % 4 == 0:
                i = 4
            elif x % 4 == 1:
                i = max(0, i - 1)
            elif x % 4 == 3:
                i = min(4, i + 0)
            c = pick("housewood", i if x % 4 else 4, tint_of(x, y, 131, 0.14))
            if x % 4 == 0:
                c = R("housewood", 4)
            if y % 16 in (1, 14) and x % 4 == 2:
                c = R("housewood", 4)   # nail heads
            cells[(x, y)] = c
    TEX["pet_house_planks"] = to_img(cells)

    cells = {}
    for y in range(16):
        for x in range(16):
            row = y // 4
            i = 2 + (row % 2)
            if y % 4 == 0:
                i = 4
            elif y % 4 == 1:
                i -= 1
            c = pick("housewood", i, tint_of(x, y, 133, 0.16))
            if y % 4 == 0:
                c = R("housewood", 4)
            cells[(x, y)] = c
    TEX["pet_house_floor"] = to_img(cells)

    cells = {}
    for y in range(16):
        for x in range(16):
            i = 3 if x % 4 else 4
            if x % 4 == 1:
                i = 3
            cells[(x, y)] = pick("housewood", i, tint_of(x, y, 135, 0.12))
    TEX["pet_house_inner"] = to_img(cells)

    # roof shingles: 4x4 tabs in rows of 4px, offset by 2px every other row; lit lower edge, rounded corners
    cells = {}
    for y in range(16):
        for x in range(16):
            row = y // 4
            xs = (x + (2 if row % 2 else 0)) % 16
            tab = xs // 4
            xx, yy = xs % 4, y % 4
            base = 1 + (1 if (tab + row) % 3 == 0 else 0) + (1 if (tab * 2 + row) % 5 == 1 else 0)
            i = {0: base + 1, 1: base, 2: base, 3: base - 1}[yy]
            c = pick("shingle", max(0, min(4, i)))
            if yy == 3 and xx in (0, 3):
                c = R("shingle", 4)                 # rounded tab corners
            if xx == 0 and yy < 3:
                c = R("shingle", 4 if yy == 2 else 3)  # seam between tabs
            cells[(x, y)] = c
    TEX["pet_house_roof"] = to_img(cells)

    # name plate (front face uses region 0..4 x 0..2): cream plaque, brown border, tiny paw
    cells = {}
    for y in range(16):
        for x in range(16):
            cells[(x, y)] = R("cream", 1)
    for x in range(4):
        cells[(x, 0)] = R("housewood", 3)
        cells[(x, 1)] = R("housewood", 3) if x in (0, 3) else R("cream", 1)
    cells[(1, 1)] = R("coral", 2)
    cells[(2, 1)] = R("coral", 3)
    for x in range(4):
        cells[(x, 2)] = R("housewood", 4)
    for y in range(16):
        for x in range(16):
            if y >= 3:
                cells[(x, y)] = R("housewood", 3)
    TEX["pet_house_plate"] = to_img(cells)


# ======================================================================================
# second furniture batch: painting helpers
# ======================================================================================
def cv(w=16, h=16, fill=(0, 0, 0, 0)):
    a = np.zeros((h, w, 4), dtype=np.uint8)
    a[:, :] = fill
    return a


def px(a, x, y, c):
    if 0 <= x < a.shape[1] and 0 <= y < a.shape[0]:
        a[y, x] = c if len(c) == 4 else (c[0], c[1], c[2], 255)


def rect(a, x0, y0, x1, y1, c):
    for y in range(y0, y1):
        for x in range(x0, x1):
            px(a, x, y, c)


def stamp(a, x, y, rows, leg):
    """Paint ASCII rows at (x, y); characters missing from ``leg`` (e.g. '.') are left alone."""
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in leg:
                px(a, x + i, y + j, leg[ch])


def gray(v, a=255):
    return (int(v), int(v), int(v), a)


def shade_cells(cells, fn):
    """Paint ``fn(u, v)`` (a colour) for every (u, v) of ``cells`` on a fresh 16x16 canvas."""
    a = cv()
    for (u, v) in cells:
        px(a, u, v, fn(u, v))
    return a


# ======================================================================================
# 10. egg lamp: tintable (grayscale) shell, untinted base, screen module and buttons
# ======================================================================================
GEO["egg_w"] = [6, 8, 8, 8, 8, 8, 8, 8, 6, 6, 4]     # shell diameter in px per row, bottom (y = 2) to top (y = 12)
GEO["egg_y0"] = 2
GEO["egg_mod"] = (5, 4, 11, 10)                      # screen module (bezel + LCD) x0, y0, x1, y1 (excl.), world cells
GEO["egg_btn"] = [(10, 3, 11, 4, 0, 5), (7, 3, 9, 4, 1, 4), (5, 3, 6, 4, 2, 5)]   # x0, y0, x1, y1, colour no., z0 of the cell


def egg_plan(w):
    """Footprint (x, z cells) of a shell row of diameter w: a pixel circle."""
    h = w // 2
    return round_rect(8 - h, 8 - h, 8 + h, 8 + h, [2, 1] if w == 8 else 1)


# LCD icon (viewer's left to right, rows top to bottom; '#' = dark pixel): a smiley
EGG_LCD_ART = [
    "#..#",
    "....",
    "#..#",
    ".##.",
]
EGG_BTN_COL = [("FFF6B8", "FFC83E", "E29E2E"), ("B8F6EA", "4CD2C0", "1F928F"), ("BCD8FF", "6B9CF0", "3253A8")]   # the pager's yellow / teal / blue


def egg_texture_silhouette():
    """Texture-space (u, v) cells of the egg's front view: u = 15 - x, v = 15 - y of the world cells."""
    cells = set()
    for r, w in enumerate(GEO["egg_w"]):
        v = 15 - (GEO["egg_y0"] + r)
        for u in range(8 - w // 2, 8 + w // 2):
            cells.add((u, v))
    return cells


def build_egg_lamp():
    sil = egg_texture_silhouette()
    umin = min(u for u, _ in sil)
    umax = max(u for u, _ in sil)
    vmin = min(v for _, v in sil)
    vmax = max(v for _, v in sil)

    def shell(kind, lit):
        ramp = [244, 238, 230, 220, 208] if lit else [240, 233, 223, 211, 197]
        k = {"front": 1.0, "side": 0.88 if lit else 1.0}[kind]
        ramp = [r * k for r in ramp]

        def fn(u, v):
            fu = (u - umin) / (umax - umin)
            fv = (v - vmin) / (vmax - vmin)
            t = 0.62 * fu + 0.38 * fv
            i = 1 if t < 0.28 else (2 if t < 0.56 else 3)
            if t > 0.84:
                i = 4 if not lit else 3
            right = (u + 1, v) not in sil
            below = (u, v + 1) not in sil
            if (right or below) and kind != "side":
                i = min(4, i + 1)
            if kind == "front" and (u, v) in ((6, 5), (6, 6), (7, 5)):
                i = 0
            if kind == "side" and (u, v) in ((5, 5), (5, 6)):
                i = 0
            return gray(ramp[i])
        return shade_cells(sil, fn)

    for lit in (False, True):
        suf = "_lit" if lit else ""
        TEX[f"egg_lamp_shell{suf}"] = img(shell("front", lit))
        TEX[f"egg_lamp_side{suf}"] = img(shell("side", lit))

    # ledges (top / bottom of the stepped shell) in top view coordinates: u = x, v = z
    for lit in (False, True):
        suf = "_lit" if lit else ""
        ramp = [244, 241, 236, 228, 218] if lit else [240, 236, 228, 216, 202]
        cells = {(x, z) for x in range(4, 12) for z in range(4, 12)}
        TEX[f"egg_lamp_top{suf}"] = img(shade_cells(cells, lambda x, z: gray(ramp[1 if (x + z) < 14 else (2 if (x + z) < 18 else 3)])))

    # face: screen module (bezel ring + LCD), buttons; painted in front view coordinates (u = 15 - x, v = 15 - y)
    mx0, my0, mx1, my1 = GEO["egg_mod"]
    for lit in (False, True):
        a = cv()
        lcd = RAMPS["lcd_warm"] if lit else RAMPS["lcd_off"]
        for y in range(my0, my1):
            for x in range(mx0, mx1):
                u, v = 15 - x, 15 - y
                inner = mx0 < x < mx1 - 1 and my0 < y < my1 - 1
                if inner:
                    i, j = (mx1 - 2) - x, (my1 - 2) - y        # column (viewer's left to right), row (top to bottom) in the art
                    ch = EGG_LCD_ART[j][i]
                    c = lcd[1]
                    if ch == "#":
                        c = lcd[3]
                else:
                    top_left = (y == my1 - 1) or (x == mx1 - 1)          # light from the top left (viewer's left = higher x)
                    c = R("bezel", 1 if top_left else 3)
                    if (x, y) in ((mx1 - 1, my1 - 1),):
                        c = R("bezel", 0)
                    if (x, y) in ((mx0, my0),):
                        c = R("bezel", 4)
                px(a, u, v, c)
        for (bx0, by0, bx1, by1, k, _z) in GEO["egg_btn"]:
            base = hex2rgb("#" + EGG_BTN_COL[k][1])
            for x in range(bx0, bx1):
                for y in range(by0, by1):
                    px(a, 15 - x, 15 - y, base)
        TEX["egg_lamp_face" + ("_lit" if lit else "")] = img(a)

    # base: cream plate + collar.  rows 15 / 14 hold the side bands, rows 4..11 the ledge seen from above
    a = cv()
    for x in range(16):
        px(a, x, 15, R("eggbase", 1 if x < 7 else (2 if x < 11 else 3)))
        px(a, x, 14, R("eggbase", 2 if x < 8 else 3))
    px(a, 4, 15, R("eggbase", 0))
    px(a, 5, 15, R("eggbase", 0))
    for z in range(4, 12):
        for x in range(16):
            px(a, x, z, R("eggbase", 1 if (x + z) < 13 else (2 if (x + z) < 18 else 3)))
    TEX["egg_lamp_base"] = img(a)


# ======================================================================================
# 11. pet portrait: wooden frame, tintable (grayscale) backdrop with polka dots, cream / gold plaque
# ======================================================================================
GEO["portrait_ring"] = ({(x, y) for x in range(16) for y in range(16) if x < 2 or x >= 14 or y >= 14 or y < 1}
                        - {(0, 0), (15, 0), (0, 15), (15, 15)})          # 2 px frame, 1 px at the bottom (sits under the plaque)
GEO["portrait_back"] = (2, 1, 14, 14)              # backdrop x0, y0, x1, y1 (world cells), front face at z = 14.5
GEO["portrait_plaque"] = (3, 1, 13, 4)             # plaque x0, y0, x1, y1, front face at z = 14


def build_portrait():
    # frame, painted in front view coordinates (u = 15 - x, v = 15 - y); the whole sheet starts as wood so nothing
    # a face could sample is ever transparent
    a = cv(fill=R("lightwood", 2))
    for (x, y) in GEO["portrait_ring"]:
        d = min(x, 15 - x, y, 15 - y)            # 0 = outer pixel, 1 = inner pixel of the 2 px ring
        lit_edge = (y == 15 - d) or (x == 15 - d)          # top / viewer's left side of its ring layer (light from the top left)
        dark_edge = (y == d) or (x == d)
        if d == 0:
            i = 0 if lit_edge and not dark_edge else (2 if dark_edge and not lit_edge else 1)
        else:                                    # inner lip: lit on its far (bottom / right) side, shaded where it faces the light
            i = 3 if lit_edge and not dark_edge else (1 if dark_edge and not lit_edge else 2)
        if hash2(x, y, 141) < 0.14:
            i = min(4, max(0, i + (1 if hash2(x, y, 142) < 0.5 else -1)))
        px(a, 15 - x, 15 - y, R("lightwood", i))
    for (x, y) in ((1, 14), (14, 14)):                                 # little gold studs in the top corners
        px(a, 15 - x, 15 - y, R("gold", 1))
    TEX["pet_portrait_frame"] = img(a)

    # side / back wood: grain running across
    a = cv()
    for y in range(16):
        for x in range(16):
            i = [2, 2, 1, 2, 3, 2, 2, 1][(y + (x // 5)) % 8]
            if hash2(x, y, 143) < 0.12:
                i = min(4, i + 1)
            px(a, x, y, R("lightwood", i))
    TEX["pet_portrait_wood"] = img(a)

    # backdrop: light gray (dye tint multiplies it) with staggered 2x2 polka dots, soft light from the top left
    a = cv()
    for v in range(16):
        for u in range(16):
            px(a, u, v, gray(224 - 10 * (u + v) / 30.0))
    dots = [(3, 3), (7, 3), (11, 3), (5, 7), (9, 7), (3, 11), (7, 11), (11, 11)]     # (u, v) of the dots' top left corner
    for (du, dv) in dots:
        rect(a, du, dv, du + 2, dv + 2, gray(240))
        px(a, du + 1, dv + 1, gray(232))
    for u in range(2, 14):                       # the frame's lip shades the top edge of the canvas
        px(a, u, 2, gray(212))
    TEX["pet_portrait_back"] = img(a)

    # plaque (front view coordinates: x 3..13, y 1..4 -> u 3..13, v 12..15): cream with gold end caps.  The name is drawn
    # on the middle row (y 2..3 = v 13).
    pl = RAMPS["cream"]
    a = cv(fill=R("gold", 1))
    for u in range(3, 13):
        px(a, u, 12, pl[0])
        px(a, u, 13, pl[1])
        px(a, u, 14, pl[2])
    for v in range(12, 15):
        px(a, 3, v, R("gold", 1 if v == 12 else 2))
        px(a, 12, v, R("gold", 1 if v == 12 else 2))
    px(a, 3, 13, R("gold", 3))
    px(a, 12, 13, R("gold", 3))
    px(a, 0, 0, R("gold", 1))                                        # edge swatch for the plaque's sides
    TEX["pet_portrait_plaque"] = img(a)


# ======================================================================================
# 12. pet flap: plank panel, frame around the opening, hinged flap (clear-blue plastic with a paw)
# ======================================================================================
GEO["flap_hole"] = (4, 1, 12, 9)                   # opening x0, y0, x1, y1
GEO["flap_frame"] = (3, 0, 13, 10)                 # outer rect of the frame ring around it
GEO["flap_flap"] = (5, 2, 11, 9)                   # closed flap x0, y0, x1, y1 (hangs from y1, z 7..8)


def build_flap():
    # planks: four 4 px boards, seams, nails; painted over the whole 16x16 (front view coordinates)
    a = cv()
    for y in range(16):
        for x in range(16):
            board = x // 4
            i = 1 + (1 if board % 2 else 0)
            if x % 4 == 0:
                i = 3
            elif x % 4 == 1:
                i = max(0, i - 1)
            c = pick("lightwood", i, tint_of(x, y, 151, 0.10))
            if x % 4 == 0:
                c = R("lightwood", 3 if y % 5 else 4)
            if y in (1, 14) and x % 4 == 2:
                c = R("lightwood", 4)      # nail heads
            px(a, x, y, c)
    TEX["pet_flap_planks"] = img(a)

    # frame ring: dark brown (the sheet is brown everywhere so side faces never sample air), lit top / viewer's left edge
    a = cv(fill=R("housewood", 3))
    fx0, fy0, fx1, fy1 = GEO["flap_frame"]
    hx0, hy0, hx1, hy1 = GEO["flap_hole"]
    for y in range(fy0, fy1):
        for x in range(fx0, fx1):
            if hx0 <= x < hx1 and hy0 <= y < hy1:
                continue
            i = 3
            if y == fy1 - 1 or x == fx1 - 1:
                i = 2                                           # lit outer edges (top, viewer's left)
            elif y == fy0 or x == fx0:
                i = 4
            if y == hy1:
                i = 1                                           # lintel lit where it overhangs the opening
            px(a, 15 - x, 15 - y, R("housewood", i))
    for (x, y) in ((fx0 + 1, fy1 - 1), (fx1 - 2, fy1 - 1), (fx0 + 1, fy0), (fx1 - 2, fy0)):
        px(a, 15 - x, 15 - y, R("gold", 2))                     # little brass screws
    TEX["pet_flap_frame"] = img(a)

    # flap: plastic with a paw, hinge strip on top (front view coordinates), edge swatches in the sheet's corner
    a = cv(fill=R("flapblue", 2))
    fx0, fy0, fx1, fy1 = GEO["flap_flap"]
    for y in range(fy0, fy1):
        for x in range(fx0, fx1):
            u, v = 15 - x, 15 - y
            i = 2
            if x == fx0 or y == fy0:                 # shaded rim (viewer's right, bottom)
                i = 3
            px(a, u, v, R("flapblue", i))
    px(a, 15 - (fx1 - 1), 15 - (fy1 - 2), R("flapblue", 0))        # glint, top left
    px(a, 15 - (fx1 - 2), 15 - (fy1 - 2), R("flapblue", 1))
    px(a, 15 - (fx1 - 1), 15 - (fy1 - 3), R("flapblue", 1))
    paw = [".#..#.", "#....#", "..##..", ".####."]          # same paw as the food bowl
    stamp(a, 5, 9, paw, {"#": hex2rgb("#FBFEFF")})
    for u in range(5, 11):                           # hinge strip along the top edge
        px(a, u, 15 - (fy1 - 1), R("steel", 2 if u % 2 else 3))
    px(a, 0, 0, R("flapblue", 3))
    px(a, 1, 0, R("steel", 3))
    px(a, 2, 0, R("flapblue", 1))
    TEX["pet_flap_flap"] = img(a)


# ======================================================================================
# 13. treat dispenser: raspberry base with chute / coin slot / button, cutout glass jar, colourful treats
# ======================================================================================
GEO["disp_body"] = round_rect(3, 3, 13, 13, 1)           # 10 x 10 body, y 0..6
GEO["disp_collar"] = round_rect(4, 4, 12, 12, 1)         # y 6..7
GEO["disp_jar"] = round_rect(4, 4, 12, 12, 1)            # glass, y 7..13
GEO["disp_heap"] = round_rect(5, 5, 11, 11, 1)           # treats, y 7..12
GEO["disp_heap_top"] = round_rect(6, 6, 10, 10, 1)       # y 12..13
GEO["disp_hole"] = (6, 1, 10, 3, 3, 5)                   # chute: x0, y0, x1, y1, z0, z1 (cut out of the body's front)


def build_dispenser():
    hp = RAMPS["heartpink"]
    # body front (front view coordinates u = 15 - x, v = 15 - y), the whole sheet in raspberry so no face samples air
    a = cv()
    for v in range(16):
        for u in range(16):
            i = 2
            if v == 10:
                i = 1                                # lit top row
            elif v == 15:
                i = 3
            if u <= 5 and 10 < v < 15:
                i = min(i, 2) - 0                    # left (viewer) side stays base
            if u >= 10 and 10 < v < 15:
                i = 3 if hash2(u, v, 161) > 0.45 else 2    # right side a bit darker
            if hash2(u, v, 162) < 0.08:
                i = max(0, min(4, i + 1))
            px(a, u, v, hp[i])
    px(a, 0, 0, R("ink", 3))                         # swatches for the chute's dark walls / bright floor
    px(a, 1, 0, R("eggbase", 2))
    cr = RAMPS["eggbase"]
    # chute: dark hole is carved by the model; a cream rim around it and a tray lip underneath
    for u in range(5, 11):
        px(a, u, 12, cr[1])                          # rim above (y = 3)
    for v in (13, 14):
        px(a, 5, v, cr[2])
        px(a, 10, v, cr[3])
    for u in range(4, 12):
        px(a, u, 15, cr[1] if u < 8 else cr[2])      # tray lip (y = 0)
    # coin slot: steel plate with a dark slit, left of the middle (viewer's left)
    for v in (10, 11):
        px(a, 4, v, R("steel", 1))
        px(a, 5, v, R("ink", 2))
        px(a, 6, v, R("steel", 2))
    px(a, 4, 10, R("steel", 0))
    # button: round, golden, lit top left
    px(a, 9, 10, R("gold", 0)); px(a, 10, 10, R("gold", 1))
    px(a, 9, 11, R("gold", 2)); px(a, 10, 11, R("gold", 3))
    TEX["treat_dispenser_front"] = img(a)

    # body sides / back / top ledge / lid: raspberry, lit from the left, cream foot band
    a = cv()
    for v in range(16):
        for u in range(16):
            i = 2
            if v == 10:
                i = 1
            elif v == 15:
                i = 3
            if u >= 10:
                i = min(4, i + 1) if v not in (15,) else 3
            elif u <= 5 and i == 2:
                i = 1 if hash2(u, v, 163) < 0.4 else 2
            if hash2(u, v, 164) < 0.08:
                i = max(0, min(4, i + 1))
            px(a, u, v, hp[i])
    for u in range(16):
        px(a, u, 15, cr[1 if u < 8 else 2])
    px(a, 0, 0, R("ink", 3))
    TEX["treat_dispenser_body"] = img(a)

    # cream trim (collar, knob): lit from the left
    a = cv()
    for v in range(16):
        for u in range(16):
            px(a, u, v, cr[1 if u < 7 else (2 if u < 11 else 3)])
    TEX["treat_dispenser_trim"] = img(a)

    # glass: transparent; thin light edge lines on the chamfers and a glossy streak on the viewer's left of each facet
    a = cv(fill=(0, 0, 0, 0))
    for v in range(3, 9):
        px(a, 4, v, R("glass", 2))
        px(a, 11, v, R("glass", 3))
    for v in (4, 5, 6):
        px(a, 5, v, R("glass", 0))
    for v in (7, 8):
        px(a, 10, v, R("glass", 2))
    px(a, 5, 7, R("glass", 1))
    px(a, 8, 4, R("glass", 0))
    px(a, 9, 5, R("glass", 1))
    TEX["treat_dispenser_glass"] = img(a)

    # treats: a dense pile, no gaps: 2 x 2 candies / kibble and 4 x 2 fish crackers laid in rows, lit top left.  The colours
    # cycle through the palette so every part of the jar shows several of them.
    a = cv(fill=R("kibble", 2))
    cycle = [("pompom", 1), ("kibble", 1), ("candy_mint", 1), ("biscuit", 1), ("heartpink", 1), ("kibble", 2), ("candy_mint", 2), ("pompom", 2)]
    n = 0
    for row in range(8):
        y0 = row * 2
        x = -(row % 3)
        while x < 16:
            if (row * 5 + n) % 6 == 4:                         # fish cracker
                ramp, i = "fishcracker", 1
                for dx in range(4):
                    px(a, x + dx, y0, R(ramp, i - (1 if dx == 0 else 0)))
                    px(a, x + dx, y0 + 1, R(ramp, min(4, i + 1 + (1 if dx == 3 else 0))))
                px(a, x + 1, y0, R("fishcracker", 4))          # eye
                x += 4
            else:
                ramp, i = cycle[(row * 3 + n) % len(cycle)]
                for dy in range(2):
                    for dx in range(2):
                        j = i + (0 if dy == 0 else 1) + (0 if dx == 0 else 1)
                        px(a, x + dx, y0 + dy, R(ramp, max(0, min(4, j - 1))))
                x += 2
            n += 1
    TEX["treat_dispenser_treats"] = img(a)


# ======================================================================================
# 14. pet incubator: cream base with a pink stripe, dial and LED, a nest pad at y = 3 (the egg stands there), a heating
#     ring around it and a cutout glass dome
# ======================================================================================
GEO["inc_base"] = round_rect(2, 2, 14, 14, [2, 1])       # y 0..3
GEO["inc_d10"] = round_rect(3, 3, 13, 13, [2, 1])
GEO["inc_d8"] = round_rect(4, 4, 12, 12, [2, 1])
GEO["inc_d6"] = round_rect(5, 5, 11, 11, 1)
GEO["inc_led"] = (11, 1)                                 # LED cell (x, y) on the front row


def build_incubator():
    cr = RAMPS["eggbase"]
    pk = RAMPS["pompom"]
    # base: ledge + nest pad in top view coordinates (u = x, v = z), side bands in the bottom rows
    a = cv()
    for v in range(16):
        for u in range(16):
            px(a, u, v, cr[1 if (u + v) < 14 else (2 if (u + v) < 20 else 3)])
    for z in range(5, 11):                               # the nest pad: soft white-pink down, inside the heating ring
        for x in range(5, 11):
            i = 1
            if hash2(x, z, 171) < 0.25:
                i = 0
            elif hash2(x, z, 172) < 0.25:
                i = 2
            c = R("down", i)
            if hash2(x, z, 173) < 0.18:
                c = R("shellpink", 1)
            px(a, x, z, c)
    for u in range(16):                                  # side bands: y = 2 (v 13) cream, y = 1 (v 14) pink stripe, y = 0 (v 15) shade
        px(a, u, 13, cr[1])
        px(a, u, 14, pk[2])
        px(a, u, 15, cr[2])
    px(a, 0, 0, R("ink", 3))
    TEX["pet_incubator_base"] = img(a)

    for lit in (False, True):
        suf = "_on" if lit else ""
        # front (front view coordinates): same bands + dial + LED
        a = cv()
        for u in range(16):
            for v in range(16):
                px(a, u, v, cr[1])
            px(a, u, 13, cr[1])
            px(a, u, 14, pk[2])
            px(a, u, 15, cr[2])
        knob = [".##.", "####", ".##."]                   # lavender dial like the pager's bezel, cream pointer
        for j, row in enumerate(knob):
            for i, ch in enumerate(row):
                if ch == "#":
                    c = R("bezel", 0) if (i + j) <= 1 else (R("bezel", 2) if j == 2 or i == 3 else R("bezel", 1))
                    px(a, 6 + i, 13 + j, c)
        px(a, 7, 13, cr[0])                              # the dial's pointer
        for (u, v) in ((10, 14), (12, 14)):              # tick dots to the right of the dial
            px(a, u, v, R("bezel", 3))
        px(a, 0, 0, R("coil_off", 4) if not lit else R("ember", 1))   # the LED texel (swatch)
        TEX["pet_incubator_front" + suf] = img(a)

        # heating coil: ring on top (top view u = x, v = z), side segments in row 12
        a = cv()
        ramp = "ember" if lit else "coil_off"
        ring = GEO["inc_d8"] - GEO["inc_d6"]
        ordered = sorted(ring, key=lambda c: (math.atan2(c[1] - 7.5, c[0] - 7.5)))
        for k, (x, z) in enumerate(ordered):
            seg = (k // 2) % 2
            i = (1 if seg else 2) if lit else (2 if seg else 3)
            px(a, x, z, R(ramp, i))
        for u in range(16):
            px(a, u, 12, R(ramp, (1 if u % 4 < 2 else 2) if lit else (2 if u % 4 < 2 else 3)))
        for v in range(16):
            for u in range(16):
                if a[v, u, 3] == 0:
                    px(a, u, v, R(ramp, 3))
        TEX["pet_incubator_coil" + suf] = img(a)

        # glass dome (front view coordinates): section d10 = rows v 7..11 (y 8..4), d8 = rows v 5..6 (y 10, 9);
        # transparent with light chamfer lines and a glossy streak; texel (0, 0) is an opaque ledge colour
        gl = RAMPS["glass_warm"] if lit else RAMPS["glass"]
        a = cv(fill=(0, 0, 0, 0))
        for v in range(5, 12):
            px(a, 4, v, gl[1] if v > 6 else gl[0])
            px(a, 11, v, gl[2] if v > 6 else gl[1])
        for v in (7, 8, 9):
            px(a, 5, v, gl[0])
        for v in (5, 6):
            px(a, 6, v, gl[0])
        px(a, 5, 10, gl[1])
        px(a, 9, 8, gl[0])
        px(a, 10, 7, gl[1])
        px(a, 0, 0, gl[1])
        TEX["pet_incubator_glass" + suf] = img(a)

    # cap: solid cream with a pink tint, lit from the left
    a = cv()
    for v in range(16):
        for u in range(16):
            px(a, u, v, R("shellpink", 0 if u < 6 else (1 if u < 10 else 2)))
    TEX["pet_incubator_cap"] = img(a)


# ======================================================================================
# 15. toy box: azure body with wooden corner posts, pink lid with stars, hinges at the back; toys inside
# ======================================================================================
PAW6 = [".#..#.", "#....#", "..##..", ".####."]


def build_toy_box():
    bl, pk, gd = RAMPS["toyblue"], RAMPS["pompom"], RAMPS["gold"]
    wd, cr, st = RAMPS["lightwood"], RAMPS["cream"], RAMPS["steel"]
    white = hex2rgb("#FBFEFF")

    def body_rows(a, u0, u1):
        """azure body rows v 9..15 between columns u0..u1 (exclusive)"""
        for u in range(u0, u1):
            px(a, u, 9, gd[1] if (u % 4) else gd[0])        # yellow band under the lid
            for v in range(10, 15):
                i = 2 if v < 14 else 3
                if v == 10:
                    i = 1
                px(a, u, v, bl[i])
            px(a, u, 15, bl[3] if u % 2 else bl[4])
            if hash2(u, 11, 181) < 0.12:
                px(a, u, 12, bl[1])

    def posts(a, lu, ru):
        """light wood posts (2 px) at the left / right end of the body rows (columns lu, lu+1 and ru, ru+1)"""
        for v in range(9, 16):
            for k, u in enumerate((lu, lu + 1)):
                px(a, u, v, wd[0 if k == 0 else 1] if v < 15 else wd[3])
            for k, u in enumerate((ru, ru + 1)):
                px(a, u, v, wd[2 if k == 0 else 3] if v < 15 else wd[4])

    def lid_rows(a, u0, u1, u_up0, u_up1):
        """lid lower slab rows v 7 (y 8) / 8 (y 7), upper slab rows v 5 / 6"""
        for u in range(u0, u1):
            px(a, u, 7, pk[2])
            px(a, u, 8, pk[3])
        for u in range(u_up0, u_up1):
            px(a, u, 5, pk[0])
            px(a, u, 6, pk[1])

    # ---- front (front view coordinates u = 15 - x, v = 15 - y) ------------------------------------------------------
    a = cv(fill=bl[2])
    lid_rows(a, 1, 15, 2, 14)
    body_rows(a, 1, 15)
    posts(a, 1, 13)
    stamp(a, 5, 10, PAW6, {"#": white})                       # painted paw print
    for (u, v) in ((3, 11), (4, 13), (11, 11), (12, 13)):     # confetti
        px(a, u, v, gd[0])
    px(a, 3, 12, gd[1]); px(a, 12, 12, gd[1])
    for (u, v) in ((4, 5), (9, 6), (12, 5), (6, 7), (11, 8)):  # sparkles on the lid
        px(a, u, v, gd[0])
    for v in range(7, 11):                                    # golden clasp across the lid / body seam
        for u in (7, 8):
            px(a, u, v, gd[1] if u == 7 else gd[2])
    px(a, 7, 7, gd[0])
    px(a, 7, 9, R("ink", 3)); px(a, 8, 9, R("ink", 3))
    TEX["toy_box_front"] = img(a)

    # ---- sides (west / east): u = z / 15 - z ---------------------------------------------------------------------------
    a = cv(fill=bl[2])
    lid_rows(a, 2, 14, 4, 12)
    body_rows(a, 2, 14)
    posts(a, 2, 12)
    ball = [".##.", "####", "####", ".##."]
    stamp(a, 6, 10, ball, {"#": R("ballred", 2)})
    px(a, 6, 11, R("ballred", 0)); px(a, 7, 10, R("ballred", 1))
    for u in (7, 8):
        px(a, u, 12, white)                                      # white stripe across the ball
    px(a, 11, 11, gd[0]); px(a, 4, 13, gd[0])
    TEX["toy_box_side"] = img(a)

    # ---- back (south): u = x, hinges ----------------------------------------------------------------------------------
    a = cv(fill=bl[2])
    lid_rows(a, 1, 15, 2, 14)
    body_rows(a, 1, 15)
    posts(a, 1, 13)
    for (u0, u1) in ((3, 5), (11, 13)):
        for v in range(7, 11):
            for u in range(u0, u1):
                px(a, u, v, st[1] if u == u0 else st[2])
        px(a, u0, 8, R("ink", 3)); px(a, u1 - 1, 10, R("ink", 3))
        px(a, u0, 7, st[0])
    TEX["toy_box_back"] = img(a)

    # ---- lid top (up faces): u = x, v = z --------------------------------------------------------------------------------
    a = cv(fill=pk[3])
    for v in range(16):
        for u in range(16):
            if 2 <= u < 14 and 4 <= v < 12:
                px(a, u, v, pk[1 if (u + v) % 7 else 0])
            elif 1 <= u < 15 and 2 <= v < 14:
                px(a, u, v, pk[2])

    def star(cx, cy):
        px(a, cx, cy, gd[0])
        for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            px(a, cx + dx, cy + dy, gd[1])
    star(5, 6); star(10, 5); star(8, 9); star(12, 10); star(4, 10)
    for (u, v) in ((7, 5), (6, 8), (11, 7), (9, 11)):
        px(a, u, v, white)
    TEX["toy_box_top"] = img(a)

    # ---- inner wood (inside walls, floor, rim, lid underside): light planks -------------------------------------------------
    a = cv()
    for y in range(16):
        for x in range(16):
            i = [1, 1, 2, 1, 1, 3][(y // 2) % 6] if y % 2 == 0 else [2, 2, 3, 2, 2, 4][(y // 2) % 6]
            if hash2(x, y, 182) < 0.12:
                i = min(4, i + 1)
            px(a, x, y, R("lightwood", i))
    TEX["toy_box_inner"] = img(a)

    # ---- toys: swatches in row 0, plush face patch, a mosaic of toys seen from above (u = x, v = z) ------------------------
    a = cv()
    pile = [("ballred", 2), ("gold", 1), ("toyblue", 2), ("gummy", 2), ("pompom", 1), ("cream", 1), ("featherteal", 2), ("plush", 2),
            ("ballred", 1), ("toyblue", 1), ("gold", 2), ("pompom", 2)]
    for row in range(8):
        y0 = row * 2
        x = -int(hash2(row, 0, 183) * 3)
        k = 0
        while x < 16:
            ramp, i = pile[int(hash2(row, k, 184) * len(pile)) % len(pile)]
            w = 2 + (1 if hash2(row, k, 185) < 0.35 else 0)
            k += 1
            for dy in range(2):
                for dx in range(w):
                    j = i + (0 if dy == 0 else 1) + (1 if dx == w - 1 else 0)
                    px(a, x + dx, y0 + dy, R(ramp, max(0, min(4, j - 1))))
            x += w
    sw = [R("ballred", 2), R("ballred", 1), cr[0], R("plush", 2), R("plush", 1), R("plush", 3), cr[1], R("ink", 3),
          R("featherpink", 2), R("featherpink", 1), R("featherteal", 2), gd[1], R("toyblue", 2), R("toyblue", 3), R("featherteal", 3), R("featheryellow", 1)]
    for u, c in enumerate(sw):
        px(a, u, 0, c)
    # plush face patch (3 x 2 texels at u 0..2, v 1..2): eyes on the top row, muzzle + nose below
    for u, c in enumerate((R("ink", 3), R("plush", 2), R("ink", 3))):
        px(a, u, 1, c)
    for u, c in enumerate((cr[1], R("ink", 2), cr[1])):
        px(a, u, 2, c)
    px(a, 3, 1, R("plush", 2)); px(a, 3, 2, R("plush", 2))
    TEX["toy_box_toys"] = img(a)


def build_all():
    for fn in (build_bed, build_basket, build_nest, build_bowl, build_bath, build_mushroom, build_wheel, build_post, build_house,
               build_egg_lamp, build_portrait, build_flap, build_dispenser, build_incubator, build_toy_box):
        fn()
    return TEX


if __name__ == "__main__":
    from sheets import sprite_sheet
    from pxl import OUT
    build_all()
    names = sorted(TEX)
    sprite_sheet([(n, [TEX[n].crop((0, 0, 16, 16))]) for n in names], OUT / "dbg_block_tex.png", k=6, cols=8)
