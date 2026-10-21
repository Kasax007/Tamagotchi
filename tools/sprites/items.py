"""Item sprites (16x16, dark hue-tinted outline like vanilla).

Each sprite is authored as an ASCII fill map; the 1px outline is added by ``pxl.outline`` (selective,
tinted from the neighbouring fill colour).  ``~`` marks a transparent pixel that must NOT receive an outline
(holes in loops).  Animated sprites return several frames that are stacked into a vertical strip.
"""
from __future__ import annotations

import pal  # noqa: F401  (registers ramps)
from pxl import L, M, paint, outline, overlay, blank, with_alpha, hex2rgb, RAMPS

ITEMS: dict[str, dict] = {}


def reg(name, frames, handheld=False, anim=None, outline_kw=None):
    """Register an item.  ``frames`` = list of (rows, legend) or finished images; outline is applied here."""
    imgs = []
    for fr in frames:
        if isinstance(fr, tuple):
            rows, leg = fr
            rows = M("\n".join(rows)) if not isinstance(rows, list) else M("\n".join(rows))
            im = paint([r.replace("~", ".") for r in rows], leg)
            # protected pixels: transparent holes that must stay clear
            prot = {(x, y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch == "~"}
            im = outline_protected(im, prot, **(outline_kw or {}))
        else:
            im = fr
        imgs.append(im)
    ITEMS[name] = dict(frames=imgs, handheld=handheld, anim=anim)


def outline_protected(im, prot, **kw):
    return outline(im, protect=prot, **kw)


# ======================================================================================
# tamagotchi_heart  (animated: heartbeat + shine + twinkle)
# ======================================================================================
HEART_LEG = L("yYgdD=gold", "rpPsS=heartpink", "w=#FFF7F3", "k=#FFFDF0", "j=#FFE98A")

HEART_SMALL = [
    "................",
    "................",
    "................",
    "................",
    "....yYg..Ygg....",
    "...yppPgYpPPg...",
    "...YpwpPPPPsd...",
    "...YpPPPPPssd...",
    "....gPPPPssd....",
    ".....gPPssd.....",
    "......gsSd......",
    ".......dD.......",
    "................",
    "................",
    "................",
    "................",
]

HEART_BIG = [
    "................",
    "................",
    "................",
    "...yYYg..YYgg...",
    "..yppPPgYpPPPg..",
    "..YpwpPPPPPPsd..",
    "..YpwPPPPPPssd..",
    "..YPPPPPPPsssd..",
    "...gPPPPPsssd...",
    "....gPPPsssd....",
    ".....gPsssd.....",
    "......gsSd......",
    ".......dD.......",
    "................",
    "................",
    "................",
]

LIGHTER = {"P": "p", "p": "r", "s": "P", "S": "s", "g": "Y", "d": "g", "D": "d", "Y": "y", "r": "w"}


def shine(rows, c):
    out = []
    for y, row in enumerate(rows):
        r = list(row)
        for x, ch in enumerate(r):
            if ch in LIGHTER and c - 1 <= x + y <= c:
                r[x] = LIGHTER[ch]
        out.append("".join(r))
    return out


def sparkle(img, level):
    """twinkle star (drawn after the outline) in the top-left corner."""
    core, arm = hex2rgb("#FFFDF0"), hex2rgb("#FFE98A")
    im = img.copy()
    px = im.load()
    cx, cy = 2, 2
    if level >= 1:
        px[cx, cy] = core
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            px[cx + dx, cy + dy] = arm
    if level >= 2:
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            if 0 <= cx + dx < 16 and 0 <= cy + dy < 16:
                px[cx + dx, cy + dy] = arm
        for dx, dy in ((1, 1), (-1, -1)):
            px[cx + dx, cy + dy] = hex2rgb("#FFF6C8")
    return im


def build_heart():
    ol = dict(strength=0.30)
    f_small = paint(HEART_SMALL, HEART_LEG)
    f_big = paint(HEART_BIG, HEART_LEG)
    small = outline(f_small, **ol)
    big = outline(f_big, **ol)
    frames = [
        small,
        sparkle(big, 1),
        sparkle(big, 2),
        outline(paint(shine(HEART_SMALL, 10), HEART_LEG), **ol),
        outline(paint(shine(HEART_SMALL, 14), HEART_LEG), **ol),
        sparkle(outline(paint(shine(HEART_SMALL, 18), HEART_LEG), **ol), 1),
    ]
    seq = [(0, 18), (1, 2), (2, 3), (3, 2), (4, 2), (5, 2)]
    reg("tamagotchi_heart", frames, anim=dict(frames=[{"index": i, "time": t} for i, t in seq]))


build_heart()


# ======================================================================================
# tama_pager  (egg-shaped virtual pet, animated LCD)
# ======================================================================================
PAGER_LEG = L(
    "hlbsS=shellpink",
    "z=#9B83A8", "Z=#5F4B73",
    "12345=lcd",
    "a=#FFF6B8", "A=#FFC83E", "B=#E29E2E",
    "c=#B8F6EA", "C=#4CD2C0", "D=#1F928F",
    "e=#BCD8FF", "E=#6B9CF0", "F=#3253A8",
)
PAGER_LEG["k"] = RAMPS["steel"][1]  # keyring silver
PAGER_LEG["K"] = RAMPS["steel"][3]

PAGER_BASE = [
    "................",
    ".......kk.......",
    "......k~~K......",
    ".....hllbbs.....",
    "....hllbbbbs....",
    "...hllbbbbbbs...",
    "...lzzzzzzzzs...",
    "..lbz@@@@@@Zbs..",
    "..lbz@@@@@@Zbs..",
    "..lbz@@@@@@Zbs..",
    "..lbz@@@@@@Zbs..",
    "..lbZZZZZZZZbs..",
    "..lbaAbcCbeEbs..",
    "...bABbCDbEFs...",
    "....bsssssss....",
    "................",
]

# LCD: bright pet on a dark-green screen (digits are the lcd ramp: 1 lightest ... 5 darkest)
LCD_FRAMES = {
    "neutral": ["414414", "111111", "151151", "411114"],
    "blink": ["414414", "111111", "111111", "411114"],
    "hop": ["111111", "151151", "411114", "445544"],
}


def pager_frame(name):
    rows = [list(r) for r in PAGER_BASE]
    lcd = LCD_FRAMES[name]
    for i in range(4):
        for j in range(6):
            rows[7 + i][5 + j] = lcd[i][j]
    return ["".join(r) for r in rows]


def build_pager():
    frames = []
    for nm in ("neutral", "blink", "hop"):
        rows = pager_frame(nm)
        rr = M("\n".join(r.replace("~", ".") for r in rows))
        im = paint(rr, PAGER_LEG)
        prot = {(x, y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch == "~"}
        frames.append(outline_protected(im, prot, strength=0.30))
    seq = [(0, 12), (2, 3), (0, 5), (1, 3)]
    reg("tama_pager", frames, anim=dict(frames=[{"index": i, "time": t} for i, t in seq]))


build_pager()


# ======================================================================================
# helper: single static sprite from ASCII
# ======================================================================================
def static(name, rows, legend, handheld=False, **kw):
    rr = M("\n".join(r.replace("~", ".") for r in rows))
    im = paint(rr, legend)
    prot = {(x, y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch == "~"}
    reg(name, [outline(im, protect=prot, **kw)], handheld=handheld)


# ======================================================================================
# pet_brush  (handheld: bristles up-right, wooden handle down-left)
# ======================================================================================
static("pet_brush", [
    "................",
    "................",
    "..........ea....",
    ".........ewwca..",
    "........eqwqwcd.",
    ".......eqwqwqwcd",
    ".......aqwqwqscd",
    "........aqwqsdd.",
    ".......bcpsdd...",
    "......ab.dd.....",
    ".....ab.........",
    "....ab..........",
    "...ab...........",
    "..ab............",
    ".ab.............",
    "................",
], L("eabcd=woodbrush", "w=#FFF8E4", "q=#F7A8C4", "s=#D883A8", "p=#FFCADB"), handheld=True)




# ======================================================================================
# helpers for composed sprites (code assisted ASCII: pile of small shapes with dark separation lines)
# ======================================================================================
import math


def canvas(w=16, h=16):
    return [["."] * w for _ in range(h)]


def stamp(cv, tpl, x0, y0, sep=None, flip=False):
    """Draw template ``tpl`` onto the char canvas; existing pixels touching the new shape become ``sep``."""
    rows = [r[::-1] for r in tpl] if flip else list(tpl)
    cells = {(x0 + x, y0 + y): ch for y, r in enumerate(rows) for x, ch in enumerate(r) if ch != "."}
    return stamp_cells(cv, cells, sep)


def stamp_cells(cv, cells, sep=None):
    if sep:
        for (x, y) in cells:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if (nx, ny) not in cells and 0 <= nx < len(cv[0]) and 0 <= ny < len(cv) and cv[ny][nx] != ".":
                    cv[ny][nx] = sep
    for (x, y), ch in cells.items():
        if 0 <= x < len(cv[0]) and 0 <= y < len(cv):
            cv[y][x] = ch
    return cv


def rows_of(cv):
    return ["".join(r) for r in cv]


def nb4(c):
    return [(c[0] + 1, c[1]), (c[0] - 1, c[1]), (c[0], c[1] + 1), (c[0], c[1] - 1)]


# ======================================================================================
# laser_pointer  (handheld: slim silver/blue pen, red tip, button)
# ======================================================================================
PEN = {  # y: shades for the three diagonals x+y = 14, 15, 16  (upper-left edge, middle, lower-right edge)
    13: "cdd",
    12: "abc", 11: "abc", 10: "abc",
    9: "HBC", 8: "BqC", 7: "BCD",
    6: "ddE",
    5: "abc",
    4: "rRf", 3: "rRf", 2: "TrR",
}
cv = canvas()
for y, s in PEN.items():
    for k, ch in enumerate(s):
        cv[y][14 + k - y] = ch
static("laser_pointer", rows_of(cv), L(
    "abcde=steel", "H=#9CC4FF", "B=#6B9CF0", "C=#4772D2", "D=#3253A8", "q=#FF4A4A",
    "T=#FFE2D8", "r=#FF7468", "R=#F03A3E", "f=#BC2438", "E=#252E48"), handheld=True)


# ======================================================================================
# tamacon  (the pet encyclopedia: a pink pocket book with a tiny LCD and an egg-with-heart emblem)
# ======================================================================================
static("tamacon", [
    "................",
    ".qRhhhhhhhhhhh..",
    ".qRllzzzzzzzlbk.",
    ".gYllz15151Zlbm.",
    ".gYllz11111Zlbk.",
    ".qRllz41514Zlbm.",
    ".qRllZZZZZZZlbk.",
    ".qRllllllllllbm.",
    ".qRllllkkklllbk.",
    ".qRlllkRkRmllbm.",
    ".gYlllkRRRmllbk.",
    ".gYlllkkRknllbm.",
    ".qRllllnnnlllbk.",
    ".qRsssssssssssk.",
    ".qqkmkmkmkmkmkm.",
    "................",
], L("hlbsS=shellpink", "z=#9B83A8", "Z=#5F4B73", "12345=lcd", "r=heartpink.1", "R=heartpink.2", "q=heartpink.3",
     "Y=gold.2", "g=gold.3", "k=cream.1", "m=cream.2", "n=cream.3"), strength=0.30)


# ======================================================================================
# squeaky_ball  (red & yellow ball with a white star)
# ======================================================================================
static("squeaky_ball", [
    "................",
    "................",
    ".....rRRqqq.....",
    "...rkRRqqqqqQ...",
    "..rkRRqwqqqqQQ..",
    "..RRwwwwWqqQQQ..",
    "..RqqwwWqqqQQP..",
    "..qqqwqWqqQQPP..",
    "..qqwqqqWQQQgd..",
    "..qqqQQQQQYgdd..",
    "..qQQQQYYggddD..",
    "..QQYYggggddDD..",
    "...YggggdddDD...",
    ".....ggddDD.....",
    "................",
    "................",
], L("rRqQP=ballred", "yYgdD=ballyellow", "w=#FFFCF4", "W=#DCDBE8", "k=#FFD2C8"))


# ======================================================================================
# feather_wand  (handheld: stick + string + three feathers)
# ======================================================================================
def feather(S, d, length, w, chars):
    """Rasterise a leaf shaped feather.  chars = (tip, light, dark, spine)."""
    n = math.hypot(*d)
    d = (d[0] / n, d[1] / n)
    nx, ny = -d[1], d[0]
    lit = 1 if (nx * -1 + ny * -1) > 0 else -1  # which side faces the top-left light
    cells = {}
    for y in range(16):
        for x in range(16):
            px, py = x + 0.5 - S[0], y + 0.5 - S[1]
            t = px * d[0] + py * d[1]
            if t < 0 or t > length:
                continue
            s = px * nx + py * ny
            u = t / length
            hw = w * math.sin(math.pi * min(1.0, u ** 0.7))
            if abs(s) <= hw + 0.15:
                if u > 0.93:
                    ch = chars[0]
                elif abs(s) < 0.45:
                    ch = chars[3]
                elif s * lit > 0:
                    ch = chars[1]
                else:
                    ch = chars[2]
                cells[(x, y)] = ch
    return cells


cv = canvas()
for (n, c) in (("c", "bcd"), ("d", "bcd")):
    pass
WAND_STICK = {14: (2, 3), 13: (3, 4), 12: (4, 5), 11: (5, 6), 10: (6, 7)}
for y, (xa, xb) in WAND_STICK.items():
    cv[y][xa] = "a"
    cv[y][xb] = "c"
stamp_cells(cv, feather((10.0, 6.6), (0.88, -0.48), 5.6, 2.0, "jtuT"), sep="o")
stamp_cells(cv, feather((8.8, 6.6), (-0.72, -0.69), 7.0, 2.1, "hpqP"), sep="o")
stamp_cells(cv, feather((9.6, 6.4), (0.1, -1.0), 5.3, 1.9, "iyzY"), sep="o")
for (x, y), ch in {(8, 9): "s", (8, 8): "n", (9, 8): "n", (9, 7): "n", (10, 7): "s"}.items():
    cv[y][x] = ch
static("feather_wand", rows_of(cv), L(
    "abcd=woodbrush", "n=#F4EEE2", "s=#C9BFB2", "o=#7A3A55",
    "hpqP=featherpink", "iyzY=featheryellow", "jtuT=featherteal"), handheld=True)


# ======================================================================================
# pet_kibble  (sack with paw print, kibble bits spilling)
# ======================================================================================
SACK = [
    "................",
    "................",
    "...a....b.......",
    "...abbbbc.......",
    "....abbc........",
    "...gGGGGd.......",
    "..abbbbbbc......",
    ".abbbbbbbbc.....",
    ".abbbbbbbbbc....",
    ".abbbbbbbbbc....",
    ".abbbbbbbbbc....",
    ".abbbbbbbbbc....",
    ".abbbbbbbbbc....",
    "..abbbbbbbcc....",
    "...cccccccd.....",
    "................",
]
PAW = [  # 7 x 6, toes in an arc over a rounded pad
    "..w.w..",
    "w.....w",
    ".......",
    "..www..",
    ".wwwww.",
    "..www..",
]
cv = [list(r) for r in SACK]
for y, r in enumerate(PAW):
    for x, ch in enumerate(r):
        if ch == "w":
            cv[7 + y][3 + x] = "w"
for (px, py, tone) in ((11, 9, 0), (13, 11, 1), (11, 13, 0)):
    stamp(cv, ["nk", "km"] if tone == 0 else ["kK", "Km"], px, py)
cv[14][14] = "m"
cv[8][14] = "k"
static("pet_kibble", rows_of(cv), L(
    "sabcd=sack", "w=#FFFCF4", "gG=gold", "n=#C68E58", "k=#A56E3F", "K=#855030", "m=#623822"))


# ======================================================================================
# fish_crackers  (pile of orange fish-shaped crackers)
# ======================================================================================
FISH = [
    "..hll..b",
    ".hllbbbb",
    "hbebbbs.",
    ".bbbbsss",
    "..bss..s",
]
cv = canvas()
for (fx, fy, fl) in ((7, 1, True), (1, 5, False), (5, 9, True)):
    stamp(cv, FISH, fx, fy, sep="o", flip=fl)
static("fish_crackers", rows_of(cv), L("hlbsd=fishcracker", "e=#5A2E1E", "o=#9A5224"))


# ======================================================================================
# dragon_fruit  (cut pitaya: magenta skin, green scale tips, white flesh, black seeds)
# ======================================================================================
PIT_ROWS = [(6, 9), (4, 11), (3, 12), (2, 13), (2, 13), (2, 13), (2, 13), (3, 12), (4, 11), (6, 9)]  # y = 3..12
shape = {(x, 3 + i) for i, (x0, x1) in enumerate(PIT_ROWS) for x in range(x0, x1 + 1)}
skin = {c for c in shape if any(n not in shape for n in nb4(c))}
rest = shape - skin
rind = {c for c in rest if any(n in skin for n in nb4(c))}
flesh = rest - rind
cv = canvas()
for (x, y) in shape:
    lit = (x - 7.5) + (y - 7.5)
    if (x, y) in skin:
        ch = "b" if lit < -2 else ("c" if lit < 3 else "d")
    elif (x, y) in rind:
        ch = "a" if lit < 0 else "b"
    else:
        ch = "g" if lit < -2 else ("f" if lit < 3 else "h")
    cv[y][x] = ch
for (x, y) in ((5, 6), (9, 6), (7, 7), (4, 8), (10, 8), (6, 9), (8, 10), (11, 9), (6, 5)):
    if (x, y) in flesh:
        cv[y][x] = "k"
LEAVES = {(5, 3): "m", (4, 2): "l", (3, 1): "L", (10, 3): "m", (11, 2): "l", (12, 1): "L",
          (3, 11): "m", (2, 12): "l", (1, 13): "L", (12, 11): "m", (13, 12): "l", (14, 13): "L",
          (1, 8): "l", (0, 8): "L", (14, 7): "l"}
for (x, y), ch in LEAVES.items():
    if 0 <= x < 16 and 0 <= y < 16:
        cv[y][x] = ch
static("dragon_fruit", rows_of(cv), L("abcde=pitaya", "Llm=pitaya_leaf", "fghij=pitaya_flesh", "k=#3A2A44"))


# ======================================================================================
# ember_jerky  (dark red strip, glowing ember specks)
# ======================================================================================
JERKY_ROWS = {  # y: (x0, x1)  inclusive; a diagonal slab with rounded ends
    2: (11, 12), 3: (9, 13), 4: (8, 13), 5: (7, 13), 6: (6, 12), 7: (5, 11), 8: (4, 10),
    9: (3, 9), 10: (2, 8), 11: (2, 6), 12: (3, 4),
}
EMBERS = {(9, 4): "e", (10, 4): "o", (6, 7): "y", (7, 7): "e", (5, 9): "e", (11, 5): "o", (8, 8): "o",
          (4, 11): "y", (12, 3): "e", (7, 6): "o", (6, 8): "o"}
cv = canvas()
for y, (x0, x1) in JERKY_ROWS.items():
    for x in range(x0, x1 + 1):
        ch = "b"
        if x == x0:
            ch = "h"
        elif x == x0 + 1 and (x + y) % 3 == 0:
            ch = "l"
        elif x == x1:
            ch = "s"
        elif (x + y) % 5 == 0:
            ch = "l"
        elif (x + y) % 7 == 3:
            ch = "s"
        cv[y][x] = ch
for y in (2, 12):  # tips
    for x in range(JERKY_ROWS[y][0], JERKY_ROWS[y][1] + 1):
        cv[y][x] = "h" if y == 2 else "s"
for (x, y), ch in EMBERS.items():
    cv[y][x] = ch
static("ember_jerky", rows_of(cv), L("hlbsd=jerky", "w=#FFF2A0", "y=#FFD24A", "e=#FF9A2E", "o=#E8541E"))


# ======================================================================================
# rock_candy  (stick with purple / pink / aqua crystal chunks)
# ======================================================================================
GEM6 = [
    "..hl..",
    ".hllb.",
    "hllbbs",
    "llbbss",
    ".lbbs.",
    "..bs..",
]
GEM5 = [
    "..hl.",
    ".hllb",
    "hllbs",
    ".lbbs",
    "..bs.",
]


def recolor(tpl, tag):
    # per-gem letters so one legend can hold three ramps: h,l,b,s -> tag-specific chars
    table = {"purple": "ABCD", "pink": "EFGH", "aqua": "IJKL"}[tag]
    m = dict(zip("hlbs", table))
    return ["".join(m.get(c, c) for c in r) for r in tpl]


cv = canvas()
# wooden stick (diagonal, 2px)
for k, y in enumerate(range(14, 7, -1)):
    x = 1 + k
    cv[y][x] = "w"
    cv[y][x + 1] = "W"
stamp(cv, recolor(GEM6, "purple"), 8, 1, sep="o")
stamp(cv, recolor(GEM5, "aqua"), 10, 6, sep="o")
stamp(cv, recolor(GEM5, "pink"), 4, 5, sep="o")
static("rock_candy", rows_of(cv), L(
    "ABCD=crystal_purple", "EFGH=crystal_pink", "IJKL=crystal_aqua",
    "w=#D9B77A", "W=#A57A45", "o=#4A2F6E",
), handheld=False)


# ======================================================================================
# glow_gummy  (translucent glowing yellow-green gummy bear)
# ======================================================================================
static("glow_gummy", [
    "................",
    "....GG....GG....",
    "....GhggggwG....",
    "...GhwggggggG...",
    "...GgggggggDG...",
    "...GggeggegDD...",
    "....GggkkgGD....",
    "....GgggggGD....",
    "..GGGhgggggGDD..",
    "..GGggggggggDD..",
    "...GGgggggggD...",
    "....DgggggGD....",
    "....DgGDDgGD....",
    "...GgGGD.GgGD...",
    "...DDDD..DDDD...",
    "................",
], L("hgGDd=gummy", "w=#FFFFE6", "e=#2F6A24", "k=#5BA82E"))


# ======================================================================================
# golden_biscuit  (round golden cookie with a crown stamp)
# ======================================================================================
BIS_ROWS = {1: (5, 9), 2: (3, 11), 3: (2, 12), 4: (1, 13), 5: (1, 13), 6: (1, 13), 7: (1, 13), 8: (1, 13), 9: (1, 13),
            10: (1, 13), 11: (2, 12), 12: (3, 11), 13: (5, 9)}
shape = {(x, y) for y, (x0, x1) in BIS_ROWS.items() for x in range(x0, x1 + 1)}
ring = {c for c in shape if any(n not in shape for n in nb4(c))}
cv = canvas()
for (x, y) in shape:
    t = (x - 7) + (y - 7)
    if (x, y) in ring:
        ch = "y" if t < -3 else ("g" if t < 3 else "d")
        if (x + y) % 2 == 0 and ch == "g":
            ch = "d"
        if (x + y) % 2 == 0 and ch == "y":
            ch = "Y"
    else:
        ch = "h" if t < -6 else ("Y" if t < 2 else ("g" if t < 6 else "d"))
    cv[y][x] = ch
CROWN = [
    "X..X..X",
    "XX.X.XX",
    "XXXXXXX",
    "XXXXXXX",
]
pts = {(4 + x, 5 + y) for y, r in enumerate(CROWN) for x, c in enumerate(r) if c == "X"}
for (x, y) in pts:
    cv[y][x] = "D"
for (x, y) in pts:  # embossed: light rim on the lower right
    for dx, dy in ((1, 0), (0, 1), (1, 1)):
        if (x + dx, y + dy) not in pts and (x + dx, y + dy) in shape:
            cv[y + dy][x + dx] = "w"
static("golden_biscuit", rows_of(cv), L("yYgdb=biscuit", "h=#FFF7C8", "D=#B06E1E", "w=#FFF0A6", "j=#FF7A8A"))
