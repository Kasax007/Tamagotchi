"""Spawn eggs (16x16, 26.3 style: one egg-shaped sprite per mob, dark tinted outline, a pattern that hints at the pet).

Base egg = shaded egg mask (top-left light); every pet adds a hand-authored pattern patch made of the palette
colours from the design brief.  Patches may reach outside the egg mask (ears, hat brim, antennae).
"""
from __future__ import annotations

import pal  # noqa: F401
from pxl import auto_ramp, hex2rgb, outline, paint, L, M, tint, blank, img, arr
import numpy as np
from PIL import Image

EGG_W = [4, 6, 8, 10, 10, 12, 12, 12, 12, 12, 12, 10, 8, 6]  # rows y = 1..14, centred on x = 7.5
EGG = {}
for i, w in enumerate(EGG_W):
    y = 1 + i
    x0 = 8 - w // 2
    for x in range(x0, x0 + w):
        EGG[(x, y)] = True
EDGE = {c for c in EGG if any(n not in EGG for n in ((c[0] + 1, c[1]), (c[0] - 1, c[1]), (c[0], c[1] + 1), (c[0], c[1] - 1)))}

EGGS: dict[str, Image.Image] = {}


def base_egg(color):
    r = auto_ramp(color)
    cv = {}
    for (x, y) in EGG:
        lit = (x - 6.5) * 0.55 + (y - 6.5) * 0.85
        if lit < -5.2:
            i = 1
        elif lit < 2.6:
            i = 2
        elif lit < 6.2:
            i = 3
        else:
            i = 4
        if (x, y) in EDGE:
            if lit < -2.0:
                i = max(1, i - 1) if i > 1 else 0
            elif lit > 3.0:
                i = min(4, i + 1)
        cv[(x, y)] = r[i]
    # glossy highlight, top-left
    for c in ((4, 4), (3, 5), (5, 3)):
        if c in cv:
            cv[c] = r[0]
    return cv, r


def patch(cv, x0, y0, rows, legend):
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch == ".":
                continue
            cv[(x0 + dx, y0 + dy)] = legend[ch]


def pts(cv, d, legend):
    for (x, y), ch in d.items():
        cv[(x, y)] = legend[ch]


def finish(name, cv):
    a = np.zeros((16, 16, 4), dtype=np.uint8)
    for (x, y), c in cv.items():
        if 0 <= x < 16 and 0 <= y < 16:
            a[y, x] = c if len(c) == 4 else (c[0], c[1], c[2], 255)
    EGGS[name] = outline(img(a), strength=0.30)


def hx(h):
    return hex2rgb(h)


# ---------------------------------------------------------------- desert dragon
cv, r = base_egg("#E8C88C")
lg = dict(t=hx("#C8643A"), u=hx("#9E4A30"), c=hx("#F6E7C5"), s=hx("#D8B676"), B=hx("#2F8FC9"), b=hx("#8FD4F4"), d=hx("#1D5A94"))
patch(cv, 3, 4, ["t.t.t.t.t.", "tttttttttt", ".u.u.u.u.u"], lg)           # back plates
patch(cv, 4, 10, ["..cccccc..".strip()[:0] or "cccccccc", "cccccccc", ".cccccc."], lg)  # cream belly
patch(cv, 6, 7, ["bB", "Bd"], lg)                                          # scarab gem
pts(cv, {(5, 10): "s", (10, 10): "s"}, lg)
finish("desert_dragon", cv)

# ---------------------------------------------------------------- jungle dragon
cv, r = base_egg("#5FA83A")
lg = dict(l=hx("#B9DA6A"), d=hx("#2F6B2A"), p=hx("#F06A8C"), q=hx("#FFA3BC"), y=hx("#FFD84A"), m=hx("#4A8A32"))
pts(cv, {(7, 6): "l", (8, 6): "l", (7, 7): "l", (8, 8): "l", (7, 9): "l", (8, 10): "l", (7, 11): "l",
         (6, 8): "l", (5, 7): "l", (9, 9): "l", (10, 8): "l", (6, 10): "l", (5, 9): "l", (9, 11): "l", (10, 10): "l"}, lg)
pts(cv, {(4, 12): "d", (5, 12): "d", (6, 13): "d", (7, 13): "d", (8, 13): "d", (9, 13): "d", (10, 12): "d", (11, 12): "d",
         (3, 11): "d", (12, 11): "d"}, lg)
patch(cv, 9, 2, [".pp.", "ppyp", "pppp", ".pp."], lg)                      # hibiscus
pts(cv, {(10, 3): "q"}, lg)
finish("jungle_dragon", cv)

# ---------------------------------------------------------------- tide dragon
cv, r = base_egg("#3AA7B3")
lg = dict(D=hx("#23649B"), E=hx("#1B4E82"), a=hx("#A8E4E0"), g=hx("#5FF2FF"), w=hx("#E6FFFE"))
for x in range(2, 14):
    for y in (11, 12, 13, 14):
        if (x, y) in cv:
            cv[(x, y)] = lg["D"] if y > 11 or x % 2 == 0 else cv[(x, y)]
pts(cv, {(x, 11): "D" for x in range(2, 14, 2)}, lg)
pts(cv, {(x, 13): "E" for x in range(4, 12)}, lg)
patch(cv, 4, 5, ["aa", "a."], lg)
patch(cv, 10, 4, ["aa", "a."], lg)
patch(cv, 9, 8, ["a"], lg)
pts(cv, {(6, 8): "g", (7, 8): "w", (8, 6): "g", (5, 9): "g", (10, 7): "g", (11, 9): "g"}, lg)
finish("tide_dragon", cv)

# ---------------------------------------------------------------- frost penguin
cv, r = base_egg("#2D3A57")
lg = dict(w=hx("#F4F6FA"), s=hx("#C9D2E4"), o=hx("#F2A23A"), O=hx("#C77A24"), r=hx("#D9433F"), R=hx("#A62F38"), k=hx("#E7B8B2"))
patch(cv, 5, 8, [".wwww.", "wwwwww", "wwwwww", "wwwwss", ".wsss."], lg)       # belly
patch(cv, 7, 7, ["oo"], lg)                                                   # beak
pts(cv, {(7, 8): "O", (8, 8): "o"}, lg)
patch(cv, 3, 5, ["rrrrrrrrrr"], lg)                                           # scarf
patch(cv, 3, 6, ["RRRRRRRRRR"], lg)
patch(cv, 10, 7, ["rr", "rr", "Rr"], lg)                                      # scarf tail
pts(cv, {(5, 4): "w", (10, 4): "w"}, lg)                                      # eyes
finish("frost_penguin", cv)

# ---------------------------------------------------------------- ember pup
cv, r = base_egg("#2A2222")
lg = dict(a=hx("#4A3B38"), A=hx("#3A2E2C"), L=hx("#FF8A2A"), Y=hx("#FFD44A"), d=hx("#1E1818"))
for c in ((4, 6), (5, 6), (10, 5), (11, 5), (9, 12), (10, 12), (4, 11), (3, 10), (6, 3), (7, 3)):
    cv[c] = lg["a"]
pts(cv, {(5, 3): "L", (6, 4): "L", (6, 5): "L", (7, 6): "L", (8, 6): "L", (8, 7): "L", (9, 8): "L", (9, 9): "L", (10, 10): "L",
         (10, 11): "L", (4, 8): "L", (5, 9): "L", (5, 10): "L", (4, 11): "L"}, lg)
pts(cv, {(6, 5): "Y", (8, 6): "Y", (8, 7): "Y", (9, 9): "Y", (5, 9): "Y"}, lg)
patch(cv, 1, 3, ["aa", "aA", "A."], lg)                                      # floppy ears
patch(cv, 13, 3, ["aa", "Aa", ".A"], lg)
finish("ember_pup", cv)

# ---------------------------------------------------------------- sculk wisp
cv, r = base_egg("#0F2B35")
lg = dict(d=hx("#071A21"), c=hx("#2EE6F0"), p=hx("#9CF7FA"), m=hx("#13414D"))
for c in ((3, 8), (4, 9), (11, 7), (10, 10), (8, 12), (5, 12), (6, 5), (9, 4)):
    cv[c] = lg["m"]
patch(cv, 4, 5, ["cc", "pc"], lg)
patch(cv, 9, 8, ["cc", "pc"], lg)
pts(cv, {(6, 10): "c", (11, 11): "c", (5, 8): "c", (10, 4): "c", (8, 6): "p", (7, 11): "c", (12, 8): "c"}, lg)
pts(cv, {(4, 2): "m", (4, 1): "c", (11, 2): "m", (11, 1): "c"}, lg)           # antennae
finish("sculk_wisp", cv)

# ---------------------------------------------------------------- void kitten
cv, r = base_egg("#2A1940")
lg = dict(p=hx("#4B2E6E"), P=hx("#3A2358"), m=hx("#E05BFF"), M=hx("#F5A8FF"), w=hx("#F4E9FF"), i=hx("#9A5AA8"), k=hx("#14081F"))
for c in ((5, 11), (6, 11), (9, 5), (10, 5), (4, 9), (11, 10), (7, 13), (8, 13)):
    cv[c] = lg["p"]
patch(cv, 4, 7, ["mM", ".k"], lg)                                           # eyes (left)
patch(cv, 10, 7, ["Mm", "k."], lg)
pts(cv, {(7, 10): "i", (8, 10): "i"}, lg)                                    # nose
pts(cv, {(4, 4): "w", (11, 5): "w", (5, 13): "w", (10, 12): "w", (8, 4): "w", (3, 8): "w", (12, 9): "w"}, lg)
pts(cv, {(4, 1): "p", (3, 2): "p", (4, 2): "i", (3, 3): "p", (11, 1): "p", (12, 2): "p", (11, 2): "i", (12, 3): "p"}, lg)
finish("void_kitten", cv)

# ---------------------------------------------------------------- pebble golem
cv, r = base_egg("#8C8C8C")
lg = dict(d=hx("#5E5E62"), D=hx("#47474D"), M=hx("#6E9A3A"), m=hx("#8CBD50"), n=hx("#4F7A2E"), c=hx("#5FE3E0"), C=hx("#B8FAF6"),
          g=hx("#F2C94C"), G=hx("#FFF0A0"), l=hx("#A8A8AC"))
for c in ((9, 4), (10, 4), (3, 9), (4, 9), (10, 12), (11, 12), (7, 12)):
    cv[c] = lg["l"]
pts(cv, {(8, 3): "d", (8, 4): "d", (7, 5): "d", (7, 6): "d", (8, 7): "d", (8, 8): "d", (9, 9): "d", (6, 9): "d", (5, 10): "d", (12, 8): "d", (11, 7): "d"}, lg)
patch(cv, 4, 3, [".mMM", "mMMn", "MMn.", ".n.."], lg)                        # moss
pts(cv, {(6, 1): "n", (7, 1): "M", (8, 2): "m"}, lg)
patch(cv, 9, 6, ["Cc", "cc"], lg)                                            # diamond fleck
patch(cv, 4, 11, ["Gg", "gg"], lg)                                           # gold fleck
pts(cv, {(11, 10): "c", (10, 3): "g"}, lg)
finish("pebble_golem", cv)

# ---------------------------------------------------------------- hex toad
cv, r = base_egg("#6E8F3E")
lg = dict(o=hx("#4D6A2C"), b=hx("#E3D58A"), B=hx("#C2B26A"), p=hx("#5B3A82"), q=hx("#7A56A6"), d=hx("#3F2761"), g=hx("#E8C04A"),
          e=hx("#F1EBB0"), k=hx("#2A2330"), m=hx("#3B4E1E"))
patch(cv, 4, 9, [".bbbbbbbb.", "bbbbbbbbbb", "bbbbbbbbBB", ".bBBBBBB."[:0] or "..BBBBBB.."], lg)  # belly
for c in ((4, 7), (5, 7), (10, 8), (11, 8), (3, 10), (12, 11), (9, 6), (6, 12)):
    cv[c] = lg["o"]
pts(cv, {(x, 7): "m" for x in range(5, 11)}, lg)                              # mouth
# witch hat: cone over the top, brim a bit wider than the egg
patch(cv, 6, 1, ["qqpp", ".qppp"[:0] or "qqppp"], lg)
patch(cv, 4, 3, ["qqqpppp"[:0] or "qqpppppp"], lg)
patch(cv, 2, 4, ["qqpppppppppp"[:0] or "qqqpppppppdd"], lg)
pts(cv, {(7, 3): "g", (8, 3): "g", (7, 2): "d", (8, 2): "d"}, lg)            # buckle band
patch(cv, 4, 5, ["ee", "ek"], lg)                                            # eyes
patch(cv, 10, 5, ["ee", "ke"], lg)
finish("hex_toad", cv)

# ---------------------------------------------------------------- mimic
cv, r = base_egg("#A0703C")
lg = dict(d=hx("#6B4423"), D=hx("#3B1F12"), g=hx("#E8B84A"), G=hx("#FFE08A"), h=hx("#B8872A"), t=hx("#F4F1E6"), T=hx("#C9C4B4"),
          p=hx("#E8708A"), P=hx("#B84C68"), l=hx("#BC8A52"))
for y in (2, 3, 4, 5, 9, 10, 11, 12, 13):                                   # plank seams
    for x in (5, 10):
        if (x, y) in cv:
            cv[(x, y)] = lg["d"]
for y in (7, 8):
    for x in range(2, 14):
        if (x, y) in cv:
            cv[(x, y)] = lg["D"]
pts(cv, {(x, 3): "g" for x in range(3, 13) if (x, 3) in cv}, lg)             # gold strap on the lid
pts(cv, {(x, 3): "G" for x in range(3, 6)}, lg)
pts(cv, {(x, 6): "d" for x in range(2, 14)}, lg)                              # lid seam
pts(cv, {(4, 6): "t", (6, 6): "t", (9, 6): "t", (11, 6): "t", (4, 7): "T", (6, 7): "T", (9, 7): "T", (11, 7): "T",
         (5, 8): "t", (8, 8): "t", (10, 8): "t", (3, 8): "t", (12, 8): "t"}, lg)  # teeth
patch(cv, 6, 7, ["pp", "pP"], lg)                                             # tongue
patch(cv, 7, 10, ["gh", "hh"], lg)                                            # lock
pts(cv, {(3, 12): "g", (12, 12): "g", (4, 13): "h", (11, 13): "h"}, lg)
finish("mimic", cv)

SPAWN_EGGS = ["desert_dragon", "jungle_dragon", "tide_dragon", "frost_penguin", "ember_pup",
              "sculk_wisp", "void_kitten", "pebble_golem", "hex_toad", "mimic"]

if __name__ == "__main__":
    from sheets import sprite_sheet
    from pxl import OUT
    sprite_sheet([(n + "_spawn_egg", [EGGS[n]]) for n in SPAWN_EGGS], OUT / "dbg_eggs.png", k=10, cols=5)
