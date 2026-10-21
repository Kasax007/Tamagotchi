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
    leg = L("hlbsd=coral")
    full = []
    for y in range(16):
        full.append(rows.get(y, rows[10 + (y % 2)]))
    TEX["pet_bed_side"] = noise_shift(paint(full, leg), amount=0.018, seed=3, period=16)

    # top view painting (rim steps + cushion + paw print)
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
            cells[(x, z)] = R("coral", i)
        else:             # outer step of the lower tier
            i = 1 if t < -2 else (2 if t < 6 else 3)
            cells[(x, z)] = R("coral", i)
    # cushion: cream, shaded next to the rim
    for (x, z) in H:
        edge = any(n not in H for n in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)))
        i = 2 if edge else 1
        if not edge and hash2(x, z, 9) < 0.18:
            i = 0
        cells[(x, z)] = R("cream", i)
    paw = [
        ".x..x.",
        "x.xx.x",
        "..xx..",
        ".xxxx.",
        ".xxxx.",
        "..xx..",
    ]
    pawc = {(5 + dx, 5 + dz) for dz, row in enumerate(paw) for dx, ch in enumerate(row) if ch == "x"}
    for (x, z) in pawc:   # embroidery: base thread, lit upper left, shaded lower right
        lower_right = (x + 1, z) not in pawc or (x, z + 1) not in pawc
        upper_left = (x - 1, z) not in pawc or (x, z - 1) not in pawc
        cells[(x, z)] = R("coral", 3 if lower_right and not upper_left else (1 if upper_left and not lower_right else 2))
    TEX["pet_bed_top"] = to_img(cells)


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
            blue = ((x // 4) + (y // 4)) % 2 == 0
            ramp = "blue_check" if blue else "blanket_white"
            i = 1 if blue else 1
            if x % 4 == 3 or y % 4 == 3:
                i = 2 if not blue else 2
            if x % 4 == 0 and y % 4 == 0:
                i = 0 if not blue else 0
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


def build_all():
    for fn in (build_bed, build_basket, build_nest, build_bowl, build_bath, build_mushroom, build_wheel, build_post, build_house):
        fn()
    return TEX


if __name__ == "__main__":
    from sheets import sprite_sheet
    from pxl import OUT
    build_all()
    names = sorted(TEX)
    sprite_sheet([(n, [TEX[n].crop((0, 0, 16, 16))]) for n in names], OUT / "dbg_block_tex.png", k=6, cols=8)
