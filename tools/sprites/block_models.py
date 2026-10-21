"""Block models, blockstates, block items and loot tables for the nine Tamagotchi blocks.

Boxes are built on a 1px grid (see modelkit); footprints come from block_tex.GEO so textures, boxes and
bounds agree.  Models stay inside the bounds given by the Java collision shapes (BOUNDS below, asserted).
"""
from __future__ import annotations

import pal  # noqa: F401
from block_tex import GEO
from modelkit import Model, default_uv, merge_rects, rect_cells, round_rect

NS = "tamagotchi"

BOUNDS = {
    "pet_bed": ((1, 0, 1), (15, 6, 15)),
    "pet_basket": ((1, 0, 1), (15, 8, 15)),
    "dragon_nest": ((0, 0, 0), (16, 6, 16)),
    "food_bowl": ((3, 0, 3), (13, 5, 13)),
    "pet_bath": ((1, 0, 1), (15, 10, 15)),
    "bouncy_mushroom": ((0, 0, 0), (16, 10, 16)),
    "running_wheel": ((0, 0, 0), (16, 16, 16)),
    "scratching_post": ((2, 0, 2), (14, 16, 14)),
    "pet_house": ((0, 0, 0), (16, 16, 16)),
}

MODELS: dict[str, Model] = {}


def T(name):
    return f"{NS}:block/{name}"


def new(name, tex, particle, parent="minecraft:block/block"):
    m = Model(name, {k: T(v) for k, v in tex.items()}, parent=parent)
    m.textures["particle"] = T(tex[particle])
    MODELS[name] = m
    return m


def side_uv(d, frm, to, v0, v1):
    u = default_uv(d, frm, to)
    return [u[0], v0, u[2], v1]


def face_kind(rect, d, hollow):
    """'inner' if any cell across the face lies in the hollow, else 'outer'."""
    x0, z0, x1, z1 = rect
    if d == "north":
        nb = [(x, z0 - 1) for x in range(x0, x1)]
    elif d == "south":
        nb = [(x, z1) for x in range(x0, x1)]
    elif d == "west":
        nb = [(x0 - 1, z) for z in range(z0, z1)]
    else:
        nb = [(x1, z) for z in range(z0, z1)]
    return "inner" if any(c in hollow for c in nb) else "outer"


def ring(m, cells, hollow, y0, y1, outer, inner, up, down=None, sides_override=None):
    """Merged boxes for a footprint; each side face takes the 'inner' texture when it faces the hollow."""
    for (x0, z0, x1, z1) in merge_rects(cells):
        kw = {}
        for d in ("north", "south", "west", "east"):
            kw[d] = inner if face_kind((x0, z0, x1, z1), d, hollow) == "inner" else outer
        kw["up"] = up
        kw["down"] = down if down else outer
        m.box((x0, y0, z0), (x1, y1, z1), **kw)


def layer(m, cells, y0, y1, **faces):
    for (x0, z0, x1, z1) in merge_rects(cells):
        m.box((x0, y0, z0), (x1, y1, z1), **faces)


# ======================================================================================
# 1. pet_bed
# ======================================================================================
def pet_bed():
    m = new("pet_bed", dict(side="pet_bed_side", top="pet_bed_top"), "side")
    A, B, H = GEO["bed_outerA"], GEO["bed_outerB"], GEO["bed_hollow"]
    ring(m, A - H, H, 0, 4, "side", "side", "top", "side")
    ring(m, B - H, H, 4, 6, "side", "side", "top", "side")
    layer(m, H, 0, 3, up="top")           # cream cushion: only its top is visible (y = 3)


# ======================================================================================
# 2. pet_basket  (facing = north)
# ======================================================================================
def pet_basket():
    m = new("pet_basket", dict(weave="pet_basket_weave", rim="pet_basket_rim", blanket="pet_basket_blanket"), "weave")
    m.box((1, 0, 1), (15, 1, 15), all="weave")
    m.box((1, 1, 1), (15, 4, 3), all="weave", up="rim")            # low front wall (the way in)
    m.box((1, 1, 13), (15, 8, 15), all="weave", up="rim")          # tall back wall
    for (z0, z1, h) in ((3, 6, 5), (6, 9, 6), (9, 13, 7)):         # stepped side walls
        m.box((1, 1, z0), (3, h, z1), all="weave", up="rim")
        m.box((13, 1, z0), (15, h, z1), all="weave", up="rim")
    m.box((3, 1, 3), (13, 4, 13), up="blanket")                    # blanket, flush with the front rim
    m.box((3, 4, 8), (13, 6, 13), up="blanket", north=("blanket", (3, 10, 13, 12)))   # folded back edge
    m.box((3, 4, 3), (8, 5, 8), up="blanket", north=("blanket", (8, 10, 13, 11)), east=("blanket", (3, 10, 8, 11)))  # corner fold


# ======================================================================================
# 3. dragon_nest
# ======================================================================================
NEST_HEIGHTS = """
....45565455....
..556545565545..
.45565545655654.
.6554......5565.
4556........5654
545..........655
655..........545
554..........565
456..........655
565..........554
555..........456
5455........6554
.6545......5565.
.45655455654556.
..554565565455..
....45565545....
"""


def dragon_nest():
    m = new("dragon_nest", dict(straw="dragon_nest_straw", top="dragon_nest_top", shell="dragon_nest_shell",
                               coin="dragon_nest_coin"), "straw")
    O, H = GEO["nest_outer"], GEO["nest_hollow"]
    rows = NEST_HEIGHTS.strip().split("\n")
    assert len(rows) == 16 and all(len(r) == 16 for r in rows)
    hts = {(x, z): int(ch) for z, r in enumerate(rows) for x, ch in enumerate(r) if ch.isdigit()}
    assert set(hts) == (O - H), "nest height map must match the ring footprint"
    for lvl, (ya, yb) in enumerate(((0, 4), (4, 5), (5, 6))):
        cells = {c for c, h in hts.items() if h >= yb}
        if lvl == 0:
            ring(m, cells, H, ya, yb, "straw", "straw", "top", "straw")
        else:
            ring(m, cells, H, ya, yb, "straw", "straw", "top", "straw")
    layer(m, H, 0, 3, up="top")                                    # soft down
    # two cracked shell shards and a tiny gold coin
    m.box((5, 3, 8), (8, 4, 11), all="shell")
    m.box((5, 4, 8), (6, 5, 11), all="shell")
    m.box((5, 4, 10), (8, 5, 11), all="shell")
    m.box((9, 3, 5), (11, 4, 7), all="shell")
    m.box((10, 4, 5), (11, 5, 6), all="shell")
    m.box((9, 3, 9), (12, 4, 10), all="coin")                      # coin: a plus shaped 3x3 disc
    m.box((10, 3, 8), (11, 4, 11), all="coin")


# ======================================================================================
# 4. food_bowl  (fill 0..3)
# ======================================================================================
def food_bowl(fill):
    name = "food_bowl" if fill == 0 else f"food_bowl_fill{fill}"
    m = new(name, dict(side="food_bowl_side", top="food_bowl_top", inner="food_bowl_inner", kibble="food_bowl_kibble"), "side")
    O, H = GEO["bowl_outer"], GEO["bowl_hollow"]
    layer(m, O, 0, 2, up="top", north="side", south="side", east="side", west="side", down="side")
    ring(m, O - H, H, 2, 5, "side", "inner", "top", "side")
    k = dict(all="kibble")
    if fill == 1:
        layer(m, round_rect(5, 5, 11, 11, 1), 2, 3, **k)
    elif fill == 2:
        layer(m, H, 2, 3, **k)
        layer(m, round_rect(4, 4, 12, 12, 2), 3, 4, **k)
    elif fill == 3:
        layer(m, H, 2, 3, **k)
        layer(m, round_rect(4, 4, 12, 12, 2), 3, 4, **k)
        layer(m, round_rect(5, 5, 11, 11, 1), 4, 5, **k)


# ======================================================================================
# 5. pet_bath  (filled = false / true)
# ======================================================================================
def pet_bath(filled):
    name = "pet_bath_filled" if filled else "pet_bath"
    m = new(name, dict(wood="pet_bath_wood", top="pet_bath_top", inner="pet_bath_inner", duck="pet_bath_duck",
                       water="pet_bath_water"), "wood")
    O, H = GEO["bath_outer"], GEO["bath_hollow"]
    layer(m, O, 0, 1, up="top", north="wood", south="wood", east="wood", west="wood", down="wood")
    ring(m, O - H, H, 1, 8, "wood", "inner", "top", "wood")
    # rubber duck on the back rim: low body, raised head and tail, orange bill
    m.box((5, 8, 13), (10, 9, 15), up=("duck", (0, 0, 5, 2)), down=("duck", (0, 2, 5, 4)),
          north=("duck", (0, 2, 5, 3)), south=("duck", (0, 2, 5, 3)), east=("duck", (0, 3, 2, 4)), west=("duck", (0, 3, 2, 4)))
    m.box((8, 9, 13), (10, 10, 15), up=("duck", (0, 0, 2, 2)), north=("duck", (0, 4, 2, 5)), south=("duck", (0, 5, 2, 6)),
          east=("duck", (0, 2, 2, 3)), west=("duck", (0, 2, 2, 3)), down=("duck", (0, 2, 2, 4)))
    m.box((5, 9, 13), (6, 10, 15), up=("duck", (0, 0, 1, 2)), north=("duck", (0, 2, 1, 3)), south=("duck", (0, 2, 1, 3)),
          east=("duck", (0, 3, 2, 4)), west=("duck", (0, 3, 2, 4)), down=("duck", (0, 2, 1, 4)))
    m.box((10, 9, 13), (11, 10, 15), up=("duck", (0, 6, 1, 8)), down=("duck", (0, 6, 1, 8)), north=("duck", (0, 6, 1, 7)),
          south=("duck", (0, 6, 1, 7)), east=("duck", (0, 6, 2, 7)), west=("duck", (0, 6, 2, 7)))
    if filled:
        for (x0, z0, x1, z1) in merge_rects(H):
            m.box((x0, 1, z0), (x1, 8, z1), up="water")             # water surface at y = 8


# ======================================================================================
# 6. bouncy_mushroom  (squished = false / true)
# ======================================================================================
def bouncy_mushroom(squished):
    name = "bouncy_mushroom_squished" if squished else "bouncy_mushroom"
    m = new(name, dict(top="bouncy_mushroom_cap_top", side="bouncy_mushroom_cap_side", stem="bouncy_mushroom_stem",
                       gills="bouncy_mushroom_gills"), "side")
    if not squished:
        stem = ((6, 0, 6), (10, 5, 10), 5)
        layers = [("cap_n1", 5, 7, (4, 6)), ("cap_n2", 7, 9, (2, 4)), ("cap_n3", 9, 10, (1, 2))]
    else:
        stem = ((5, 0, 5), (11, 3, 11), 3)
        layers = [("cap_s1", 3, 5, (4, 6)), ("cap_s2", 5, 7, (2, 4)), ("cap_s3", 7, 8, (1, 2))]
    frm, to, h = stem
    m.box(frm, to, north=("stem", (frm[0], 0, to[0], h)), south=("stem", (frm[0], 0, to[0], h)),
          east=("stem", (frm[2], 0, to[2], h)), west=("stem", (frm[2], 0, to[2], h)), down="stem")
    for (g, ya, yb, (v0, v1)) in layers:
        for (x0, z0, x1, z1) in merge_rects(GEO[g]):
            fr, tt = (x0, ya, z0), (x1, yb, z1)
            kw = {d: ("side", side_uv(d, fr, tt, v0, v1)) for d in ("north", "south", "east", "west")}
            m.box(fr, tt, up="top", down="gills", **kw)


# ======================================================================================
# 7. running_wheel  (stand only, facing = north)
# ======================================================================================
def wheel_post_cells():
    c = set()
    for y in range(6, 10):                                         # hub plate (cells in (z, y))
        for z in range(6, 10):
            if y == 9 and z in (6, 9):
                continue
            c.add((z, y))
    legs = {5: (5, 7), 4: (4, 6), 3: (4, 6), 2: (3, 5), 1: (2, 4)}
    for y, (a, b) in legs.items():
        for z in range(a, b + 1):
            c.add((z, y))
            c.add((15 - z, y))
    for z in (7, 8):
        c.add((z, 3))
    for z in range(6, 10):
        c.add((z, 2))
    return c


def running_wheel():
    m = new("running_wheel", dict(wood="running_wheel_wood", copper="running_wheel_copper"), "wood")
    m.box((0, 0, 0), (16, 1, 16), all="wood")
    cells = wheel_post_cells()
    for (z0, y0, z1, y1) in merge_rects(cells):
        for (xa, xb) in ((1, 3), (13, 15)):
            m.box((xa, y0, z0), (xb, y1, z1), all="wood")
    m.box((0, 7, 7), (1, 9, 9), all="copper", uv={d: (0, 0, 2, 2) for d in ("north", "south", "east", "west", "up", "down")})
    m.box((15, 7, 7), (16, 9, 9), all="copper", uv={d: (0, 0, 2, 2) for d in ("north", "south", "east", "west", "up", "down")})


# ======================================================================================
# 8. scratching_post
# ======================================================================================
def scratching_post():
    m = new("scratching_post", dict(top="scratching_post_carpet_top", side="scratching_post_carpet_side",
                                   sisal="scratching_post_sisal", pom="scratching_post_pompom",
                                   string="scratching_post_string"), "side")
    m.box((2, 0, 2), (14, 2, 14), up="top", down="side", north="side", south="side", east="side", west="side")
    m.box((6, 2, 6), (10, 14, 10), all="sisal")
    m.box((3, 14, 3), (13, 16, 13), up="top", down="side", north="side", south="side", east="side", west="side")
    m.box((11, 9, 3), (12, 14, 4), all="string")
    m.box((10, 6, 2), (13, 9, 5), all="pom")


# ======================================================================================
# 9. pet_house  (facing = north, door on the north face)
# ======================================================================================
GABLE_TOP = {1: 7, 2: 9, 3: 9, 4: 11, 5: 11, 6: 13, 7: 13, 8: 13, 9: 13, 10: 11, 11: 11, 12: 9, 13: 9, 14: 7}


def pet_house():
    m = new("pet_house", dict(planks="pet_house_planks", floor="pet_house_floor", inner="pet_house_inner",
                              roof="pet_house_roof", plate="pet_house_plate"), "planks")
    m.box((1, 0, 1), (15, 1, 15), up="floor", down="floor", north="planks", south="planks", east="planks", west="planks")
    door = {(x, y) for x in range(4, 12) for y in range(1, 8)} | {(x, 8) for x in range(5, 11)} | {(x, 9) for x in range(6, 10)}
    assert max(y for _, y in door) - 1 + 1 >= 9
    wall = {(x, y) for x in range(1, 15) for y in range(1, GABLE_TOP[x])}
    # front wall (z 1..3) with the arched doorway, back wall (z 13..15) closed
    for (x0, y0, x1, y1) in merge_rects(wall - door):
        m.box((x0, y0, 1), (x1, y1, 3), north="planks", south="inner", east="planks", west="planks", up="planks", down="planks")
    for (x0, y0, x1, y1) in merge_rects(wall):
        m.box((x0, y0, 13), (x1, y1, 15), south="planks", north="inner", east="planks", west="planks", up="planks", down="planks")
    # side walls follow the roof steps; only the visible face of each piece is written
    m.box((1, 1, 3), (2, 7, 13), west="planks")
    m.box((2, 1, 3), (3, 9, 13), east="inner")
    m.box((14, 1, 3), (15, 7, 13), east="planks")
    m.box((13, 1, 3), (14, 9, 13), west="inner")
    # stepped red shingle roof, ridge along z, 1px overhang front/back/sides
    steps = [(0, 2, 7, 10), (2, 4, 9, 12), (4, 6, 11, 14), (6, 8, 13, 16)]
    for (xa, xb, ya, yb) in steps:
        m.box((xa, ya, 0), (xb, yb, 16), all="roof", down="inner")
        m.box((16 - xb, ya, 0), (16 - xa, yb, 16), all="roof", down="inner")
    # name plate above the door (protrudes 1px, flush with the roof edge)
    m.box((6, 11, 0), (10, 13, 1), north=("plate", (0, 0, 4, 2)), south=("plate", (0, 3, 4, 5)), east=("plate", (4, 4, 5, 6)),
          west=("plate", (4, 4, 5, 6)), up=("plate", (0, 4, 4, 5)), down=("plate", (0, 4, 4, 5)))


# ======================================================================================
# blockstates / items / loot
# ======================================================================================
FACING_Y = {"north": 0, "east": 90, "south": 180, "west": 270}


def model_ref(n):
    return f"{NS}:block/{n}"


def blockstates():
    bs = {}
    bs["pet_bed"] = {"variants": {"": {"model": model_ref("pet_bed")}}}
    bs["dragon_nest"] = {"variants": {"": {"model": model_ref("dragon_nest")}}}
    bs["scratching_post"] = {"variants": {"": {"model": model_ref("scratching_post")}}}
    for blk in ("pet_basket", "running_wheel", "pet_house"):
        v = {}
        for f, y in FACING_Y.items():
            e = {"model": model_ref(blk)}
            if y:
                e["y"] = y
            v[f"facing={f}"] = e
        bs[blk] = {"variants": v}
    bs["food_bowl"] = {"variants": {f"fill={i}": {"model": model_ref("food_bowl" if i == 0 else f"food_bowl_fill{i}")} for i in range(4)}}
    bs["pet_bath"] = {"variants": {"filled=false": {"model": model_ref("pet_bath")},
                                   "filled=true": {"model": model_ref("pet_bath_filled")}}}
    bs["bouncy_mushroom"] = {"variants": {"squished=false": {"model": model_ref("bouncy_mushroom")},
                                          "squished=true": {"model": model_ref("bouncy_mushroom_squished")}}}
    return bs


def loot_table(block):
    return {
        "type": "minecraft:block",
        "pools": [
            {
                "condition": {"type": "minecraft:survives_explosion"},
                "entries": [{"type": "minecraft:item", "name": f"{NS}:{block}"}],
                "rolls": 1,
            }
        ],
        "random_sequence": f"{NS}:blocks/{block}",
    }


def block_item(block):
    return {"model": {"type": "minecraft:model", "model": model_ref(block)}}


def build_models():
    pet_bed()
    pet_basket()
    dragon_nest()
    for i in range(4):
        food_bowl(i)
    pet_bath(False)
    pet_bath(True)
    bouncy_mushroom(False)
    bouncy_mushroom(True)
    running_wheel()
    scratching_post()
    pet_house()
    # bounds check (models must stay inside the collision bounds)
    for name, m in MODELS.items():
        base = name.replace("_fill1", "").replace("_fill2", "").replace("_fill3", "").replace("_filled", "").replace("_squished", "")
        lo, hi = BOUNDS[base]
        mn, mx = m.bounds()
        assert all(mn[i] >= lo[i] for i in range(3)) and all(mx[i] <= hi[i] for i in range(3)), (name, mn, mx, lo, hi)
    return MODELS


if __name__ == "__main__":
    build_models()
    for n, m in MODELS.items():
        print(n, len(m.to_json()["elements"]), m.bounds())
