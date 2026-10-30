"""Block models, blockstates, block items and loot tables for the Tamagotchi blocks (nine furniture blocks + the second
batch: egg lamp, pet portrait, toy box, pet flap, treat dispenser, pet incubator; bed and basket have dyeable fabric).

Boxes are built on a 1px grid (see modelkit); footprints come from block_tex.GEO so textures, boxes and
bounds agree.  Models stay inside the bounds given by the Java collision shapes (BOUNDS below, asserted).
"""
from __future__ import annotations

import pal  # noqa: F401
from block_tex import GEO, egg_plan
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
    "running_wheel_item": ((-3, 0, 0), (19, 24, 16)),
    "scratching_post": ((2, 0, 2), (14, 16, 14)),
    "pet_house": ((0, 0, 0), (16, 16, 16)),
    "egg_lamp": ((4, 0, 4), (12, 13, 12)),
    "pet_portrait": ((0, 0, 14), (16, 16, 16)),
    "toy_box": ((1, 0, 2), (15, 11, 14)),
    "pet_flap": ((0, 0, 7), (16, 16, 9)),
    "treat_dispenser": ((3, 0, 3), (13, 15, 13)),
    "pet_incubator": ((2, 0, 2), (14, 12, 14)),
    # open states: the swung out flap / raised lid stick out of the closed shape (real extents of the model)
    "pet_flap_open": ((0, 0, 2.1), (16, 16, 9)),
    "toy_box_open": ((1, 0, 2), (15, 17, 15.5)),
}

MODELS: dict[str, Model] = {}
# loot tables of these blocks are written by tools/data/gen_data.py (it runs after build.py: copy_state of the dye colour
# for the dyeable ones); items/<dyeable>.json written here is the plain constant-tint version gen_data wraps into a select
LOOT_BY_GEN_DATA = {"egg_lamp", "pet_portrait", "toy_box", "pet_flap", "treat_dispenser", "pet_incubator", "pet_bed", "pet_basket"}
TRUE_BOUNDS = {"egg_lamp", "pet_portrait", "toy_box", "pet_flap", "treat_dispenser", "pet_incubator"}  # check with element rotations applied


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
    m = new("pet_bed", dict(side="pet_bed_side", top="pet_bed_top", cushion="pet_bed_cushion"), "side")
    A, B, H = GEO["bed_outerA"], GEO["bed_outerB"], GEO["bed_hollow"]
    S, T = tinted("side"), tinted("top")       # the fabric is gray and tinted with the bed's dye colour (tintindex 0)
    ring(m, A - H, H, 0, 4, S, S, T, S)
    ring(m, B - H, H, 4, 6, S, S, T, S)
    paw = GEO["bed_paw"]
    layer(m, H - paw, 0, 3, up="cushion")      # cream cushion: only its top is visible (y = 3), not dyed
    layer(m, paw, 0, 3, up=T)                  # the stitched paw print is dyed like the rim


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
    # blanket: 4x4 checks, the "blue" ones gray + tinted with the basket's dye colour (tintindex 0), the white ones untinted
    T = tinted("blanket")
    blue = lambda c: ((c[0] // 4) + (c[1] // 4)) % 2 == 0          # check at top view cell (x, z)
    f1, f2 = rect_cells(3, 3, 8, 8), rect_cells(3, 8, 13, 13)
    main = rect_cells(3, 3, 13, 13) - f1 - f2                       # what stays visible at the front rim height (y = 4)
    for cells, (y0, y1) in ((main, (1, 4)), (f1, (4, 5)), (f2, (4, 6))):
        layer(m, {c for c in cells if blue(c)}, y0, y1, up=T)
        layer(m, {c for c in cells if not blue(c)}, y0, y1, up="blanket")
    hem = tinted("blanket", uv=[1, 1, 2, 2])                        # the folded edges: plain dyed hem
    m.box((3, 4, 8), (13, 6, 9), north=hem)                         # folded back edge
    m.box((3, 4, 3), (8, 5, 4), north=hem)                          # corner fold, front
    m.box((7, 4, 3), (8, 5, 8), east=hem)                           # corner fold, side


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
# 7. running_wheel  (stand only, facing = north: the open side of the wheel faces north, the stand is behind it)
# ======================================================================================
WHEEL_HUB_Y = 12          # axle height in px; the block entity draws an 11 px radius wheel around it
CU = {d: (0, 0, 2, 2) for d in ("north", "south", "east", "west", "up", "down")}


def running_wheel(name="running_wheel", rim=False):
    m = new(name, dict(wood="running_wheel_wood", copper="running_wheel_copper"), "wood")
    # base frame
    m.box((1, 0, 1), (15, 1, 3), all="wood")
    m.box((1, 0, 13), (15, 1, 15), all="wood")
    m.box((1, 0, 3), (3, 1, 13), all="wood")
    m.box((13, 0, 3), (15, 1, 13), all="wood")
    # A-frame behind the wheel, up to the axle
    for y in range(1, WHEEL_HUB_Y):
        lx = 2 + (y - 1) * 5 // (WHEEL_HUB_Y - 1)
        m.box((lx, y, 14), (lx + 2, y + 1, 16), all="wood")
        m.box((14 - lx, y, 14), (16 - lx, y + 1, 16), all="wood")
    m.box((6, WHEEL_HUB_Y - 2, 14), (10, WHEEL_HUB_Y + 2, 16), all="wood")
    m.box((7, WHEEL_HUB_Y - 1, 13), (9, WHEEL_HUB_Y + 1, 14), all="copper", uv=CU)
    if rim:
        # the block entity spins the real wheel; the item gets a still one: 16 rim slats, back spokes
        c = WHEEL_HUB_Y
        top, bottom = ((6.5, c + 10, 2), (9.5, c + 11, 13)), ((6.5, c - 11, 2), (9.5, c - 10, 13))
        side_l, side_r = ((-3, c - 1.5, 2), (-2, c + 1.5, 13)), ((18, c - 1.5, 2), (19, c + 1.5, 13))
        rot = lambda a: {"angle": a, "axis": "z", "origin": [8, c, 8]}
        for frm, to in (top, bottom):
            for a in (-45, -22.5, 0, 22.5, 45):
                m.box(frm, to, all="wood", rotation=rot(a) if a else None)
        for frm, to in (side_l, side_r):
            for a in (-22.5, 0, 22.5):
                m.box(frm, to, all="wood", rotation=rot(a) if a else None)
        spoke_v, spoke_h = ((7.5, c - 10, 12), (8.5, c + 10, 13)), ((-2, c - 0.5, 12), (18, c + 0.5, 13))
        m.box(*spoke_v, all="wood")
        m.box(*spoke_h, all="wood")
        m.box(*spoke_v, all="wood", rotation=rot(45))
        m.box(*spoke_v, all="wood", rotation=rot(-45))


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
# 10. egg lamp  (lit = false / true).  The shell is tinted (tintindex 0) with a grayscale texture; base, screen
#     window and buttons are untinted.  Drawn for facing = north (screen on the north face).
# ======================================================================================
def tinted(key, **kw):
    return dict(texture=key, tintindex=0, **kw)


def egg_lamp(lit):
    name = "egg_lamp_lit" if lit else "egg_lamp"
    suf = "_lit" if lit else ""
    m = new(name, dict(shell=f"egg_lamp_shell{suf}", side=f"egg_lamp_side{suf}", top=f"egg_lamp_top{suf}",
                       face=f"egg_lamp_face{suf}", base="egg_lamp_base"), "shell")
    em = dict(light=15, shade=False) if lit else {}   # glows (full bright, no directional shading: the textures carry the form)
    # round-ish base: plate + collar
    layer(m, round_rect(4, 4, 12, 12, 1), 0, 1, all="base")
    layer(m, round_rect(5, 5, 11, 11, 1), 1, 2, all="base")
    mx0, my0, mx1, my1 = GEO["egg_mod"]
    buttons = {}
    for (x0, y0, x1, y1, _k, z0) in GEO["egg_btn"]:
        for x in range(x0, x1):
            for y in range(y0, y1):
                buttons[(x, y)] = z0
    for r, w in enumerate(GEO["egg_w"]):
        y = GEO["egg_y0"] + r
        cells = egg_plan(w)
        z0 = min(z for _, z in cells)
        groups = {}
        for (x, z) in cells:
            cls = "shell"
            if my0 <= y < my1 and w == 8:
                if z == z0:
                    cls = "gone"                                    # the front strip is cut away behind the screen module
                elif z == z0 + 1 and mx0 <= x < mx1:
                    cls = "face"
            elif (x, y) in buttons and z == buttons[(x, y)]:
                cls = "face"
            if cls != "gone":
                groups.setdefault(cls, set()).add((x, z))
        for cls, cs in groups.items():
            f = dict(north=tinted("shell"), south=tinted("side"), west=tinted("side"), east=tinted("side"),
                     up=tinted("top"), down=tinted("top"))
            if cls == "face":
                f["north"] = "face"
            layer(m, cs, y, y + 1, **f, **em)


# ======================================================================================
# 11. pet portrait  (facing = north: the frame hangs on the wall behind, z 14..16, and the picture faces north)
# ======================================================================================
def pet_portrait():
    m = new("pet_portrait", dict(frame="pet_portrait_frame", wood="pet_portrait_wood", back="pet_portrait_back",
                                 plaque="pet_portrait_plaque"), "wood")
    for (x0, y0, x1, y1) in merge_rects(GEO["portrait_ring"]):          # rects are (x, y) here
        m.box((x0, y0, 14), (x1, y1, 16), north="frame", south="wood", up="wood", down="wood", east="wood", west="wood")
    bx0, by0, bx1, by1 = GEO["portrait_back"]
    m.box((bx0, by0, 14.5), (bx1, by1, 16), north=tinted("back"))          # recessed canvas: tinted backdrop (tintindex 0)
    px0, py0, px1, py1 = GEO["portrait_plaque"]
    edge = dict(texture="plaque", uv=[0, 0, 1, 1])
    m.box((px0, py0, 14), (px1, py1, 15), north="plaque", up=edge, down=edge, east=edge, west=edge)
    # inventory icon: the picture seen almost straight on (the slab sits at the back of the cell, so shift it into the slot)
    m.gui = {"rotation": [8, 180, 0], "translation": [0, 0, 0], "scale": [0.9, 0.9, 0.9]}


# ======================================================================================
# 12. pet flap  (facing = north; slab z 7..9; closed / open = flap swung out 45 degrees about its top hinge)
# ======================================================================================
def pet_flap(open_):
    name = "pet_flap_open" if open_ else "pet_flap"
    m = new(name, dict(planks="pet_flap_planks", frame="pet_flap_frame", flap="pet_flap_flap"), "planks")
    hx0, hy0, hx1, hy1 = GEO["flap_hole"]
    fx0, fy0, fx1, fy1 = GEO["flap_frame"]
    outer = rect_cells(fx0, fy0, fx1, fy1)
    for (x0, y0, x1, y1) in merge_rects(rect_cells(0, 0, 16, 16) - outer):          # planks around the frame
        m.box((x0, y0, 7), (x1, y1, 9), all="planks")
    swatch = dict(texture="frame", uv=[0, 0, 1, 1])
    for (x0, y0, x1, y1) in merge_rects(outer - rect_cells(hx0, hy0, hx1, hy1)):    # frame ring around the opening
        m.box((x0, y0, 7), (x1, y1, 9), north="frame", south="frame", up=swatch, down=swatch, east=swatch, west=swatch)
    # the flap: 1 px thick plate hanging from the top of the opening, flush with the front of the slab
    x0, y0, x1, y1 = GEO["flap_flap"]
    rot = {"angle": 45, "axis": "x", "origin": [8, y1, 7.5]} if open_ else None
    edge_up, edge = dict(texture="flap", uv=[1, 0, 2, 1]), dict(texture="flap", uv=[0, 0, 1, 1])
    m.box((x0, y0, 7), (x1, y1, 8), north="flap", south="flap", up=edge_up, down=edge, east=edge, west=edge, rotation=rot)
    # inventory icon: the front seen almost straight on
    m.gui = {"rotation": [8, 180, 0], "translation": [0, 0, 0], "scale": [0.9, 0.9, 0.9]}


# ======================================================================================
# 13. treat dispenser  (facing = north: chute, coin slot and button on the north face)
# ======================================================================================
def classes(m, cells, y0, y1, classify, faces_for, **kw):
    """Boxes for a footprint split into classes: ``classify(x, z)`` -> key, ``faces_for(key)`` -> face kwargs
    (key None = leave the cell out)."""
    groups = {}
    for (x, z) in cells:
        k = classify(x, z)
        if k is not None:
            groups.setdefault(k, set()).add((x, z))
    for k, cs in groups.items():
        layer(m, cs, y0, y1, **faces_for(k), **kw)


def treat_dispenser():
    m = new("treat_dispenser", dict(front="treat_dispenser_front", body="treat_dispenser_body", trim="treat_dispenser_trim",
                                    glass="treat_dispenser_glass", treats="treat_dispenser_treats"), "body")
    B = GEO["disp_body"]
    hx0, hy0, hx1, hy1, hz0, hz1 = GEO["disp_hole"]
    dark = dict(texture="front", uv=[0, 0, 1, 1])
    floor = dict(texture="front", uv=[1, 0, 2, 1])
    allf = dict(north="front", south="body", west="body", east="body", up="body", down="body")
    # body, three slices: the middle one has the chute cut out of its front
    classes(m, B, 0, 1, lambda x, z: "tray" if (hx0 <= x < hx1 and z < hz1) else "plain",
            lambda k: dict(allf, up=floor) if k == "tray" else allf)

    def mid(x, z):
        if hx0 <= x < hx1 and z < hz1:
            return None
        if z < hz1 and x == hx0 - 1:
            return "jamb_l"
        if z < hz1 and x == hx1:
            return "jamb_r"
        if hx0 <= x < hx1 and z == hz1:
            return "back"
        return "plain"
    classes(m, B, hy0, hy1, mid, lambda k: {"plain": allf, "jamb_l": dict(allf, east=dark), "jamb_r": dict(allf, west=dark),
                                            "back": dict(allf, north=dark)}[k])
    classes(m, B, hy1, 6, lambda x, z: "lintel" if (hx0 <= x < hx1 and z < hz1) else "plain",
            lambda k: dict(allf, down=dark) if k == "lintel" else allf)
    layer(m, GEO["disp_collar"], 6, 7, all="trim")
    # glass jar: only the outward faces, cutout; the treats stand inside it
    layer(m, GEO["disp_jar"], 7, 13, north="glass", south="glass", west="glass", east="glass")
    layer(m, GEO["disp_heap"], 7, 12, all="treats")
    layer(m, GEO["disp_heap_top"], 12, 13, all="treats")
    # lid and knob
    layer(m, GEO["disp_collar"], 13, 14, all="body")
    m.box((6, 14, 6), (10, 15, 10), all="trim")


# ======================================================================================
# 14. pet incubator  (lit = false / true; facing = north: dial and LED on the north face).  The egg (drawn by Java) stands
#     on the nest pad at y = 3, 6 px wide and 8 px tall: the dome is empty above y = 3 inside x/z 5..11.
# ======================================================================================
def pet_incubator(lit):
    name = "pet_incubator_on" if lit else "pet_incubator"
    suf = "_on" if lit else ""
    m = new(name, dict(base="pet_incubator_base", front=f"pet_incubator_front{suf}", coil=f"pet_incubator_coil{suf}",
                       glass=f"pet_incubator_glass{suf}", cap="pet_incubator_cap"), "base")
    em = dict(light=12, shade=False) if lit else {}
    B, D10, D8, D6 = GEO["inc_base"], GEO["inc_d10"], GEO["inc_d8"], GEO["inc_d6"]
    led = GEO["inc_led"]
    z0 = min(z for _, z in B)
    ledf = dict(texture="front", uv=[0, 0, 1, 1])

    # base: three rows; the LED is its own cell on the middle row (emissive in the lit state)
    allb = dict(north="front", south="base", west="base", east="base", up="base", down="base")
    layer(m, B, 0, 1, **allb)
    for k, cs in {"plain": {c for c in B if not (c[1] == z0 and c[0] == led[0])}, "led": {(led[0], z0)}}.items():
        layer(m, cs, 1, 2, **(allb if k == "plain" else dict(allb, north=ledf)), **(dict(light=12, shade=False) if (lit and k == "led") else {}))
    layer(m, B, 2, 3, **allb)
    # gasket ring (cream top, pink band) and heating ring (the coil) at y 3..4, side by side
    for (x0, zz0, x1, zz1) in merge_rects(D10 - D8):
        fr, to = (x0, 3, zz0), (x1, 4, zz1)
        band = {d: ("base", side_uv(d, fr, to, 14, 15)) for d in ("north", "south", "west", "east")}
        m.box(fr, to, up="base", **band)
    layer(m, D8 - D6, 3, 4, all="coil", **em)
    # glass dome: only the outward faces (cutout); opaque ledge colour on the steps; solid cap on top
    ledge = dict(texture="glass", uv=[0, 0, 1, 1])
    layer(m, D10, 4, 9, north="glass", south="glass", west="glass", east="glass")
    layer(m, D8, 9, 11, north="glass", south="glass", west="glass", east="glass", up=None)
    layer(m, D10 - D8, 8, 9, up=ledge)
    layer(m, D8 - D6, 10, 11, up=ledge)
    layer(m, D6, 11, 12, all="cap")


# ======================================================================================
# 15. toy box  (facing = north: paw print and clasp on the north face, hinges at the back; open = lid raised 45 degrees
#     about the back hinge, toys inside)
# ======================================================================================
def toy_box(open_):
    name = "toy_box_open" if open_ else "toy_box"
    m = new(name, dict(front="toy_box_front", side="toy_box_side", back="toy_box_back", top="toy_box_top",
                       inner="toy_box_inner", toys="toy_box_toys"), "front")
    if not open_:
        m.box((1, 0, 2), (15, 7, 14), north="front", south="back", west="side", east="side", up="inner", down="inner")
    else:
        m.box((1, 0, 2), (15, 1, 14), north="front", south="back", west="side", east="side", up="inner", down="inner")
        m.box((1, 1, 2), (15, 7, 4), north="front", south="inner", west="side", east="side", up="inner")
        m.box((1, 1, 12), (15, 7, 14), north="inner", south="back", west="side", east="side", up="inner")
        m.box((1, 1, 4), (3, 7, 12), west="side", east="inner", up="inner")
        m.box((13, 1, 4), (15, 7, 12), west="inner", east="side", up="inner")

        def sw(k):
            return dict(texture="toys", uv=[k, 0, k + 1, 1])

        def solid(frm, to, side, top, **kw):
            m.box(frm, to, north=sw(side), south=sw(side), west=sw(side), east=sw(side), up=sw(top), down=sw(side), **kw)
        # a heap of toys (mosaic seen from above) filling the chest up to y 4
        m.box((3, 1, 4), (13, 4, 12), up="toys")
        # red / white ball (stepped sphere, diameter 4)
        layer(m, rect_cells(10, 6, 12, 8), 4, 5, all=sw(0), up=sw(1))
        layer(m, round_rect(9, 5, 13, 9, 1), 5, 6, all=sw(0), up=sw(1))
        layer(m, round_rect(9, 5, 13, 9, 1), 6, 7, all=sw(2), up=sw(2))
        layer(m, rect_cells(10, 6, 12, 8), 7, 8, all=sw(2), up=sw(2))
        # lilac teddy: body, head with a face, two ears
        solid((4, 4, 8), (7, 7, 11), 3, 4)
        m.box((4, 7, 8), (7, 9, 11), north=dict(texture="toys", uv=[0, 1, 3, 3]), south=sw(3), west=sw(3), east=sw(3), up=sw(4), down=sw(3))
        solid((4, 9, 8), (5, 10, 9), 3, 4)
        solid((6, 9, 8), (7, 10, 9), 3, 4)
        # a feather sticking up at the back
        solid((11, 4, 10), (12, 7, 11), 8, 9)
        solid((11, 7, 10), (13, 9, 11), 9, 9)
        solid((12, 9, 10), (13, 11, 11), 10, 10)
    # lid: lower slab + inset upper slab (stepped dome); the open lid turns about the back hinge
    rot = {"angle": 45, "axis": "x", "origin": [8, 7, 14]} if open_ else None
    lid = dict(north="front", south="back", west="side", east="side", up="top", down="inner")
    m.box((1, 7, 2), (15, 9, 14), rotation=rot, **lid)
    m.box((2, 9, 4), (14, 11, 12), rotation=rot, **lid)
    # inventory icon: the usual corner view is fine (closed model only is used for the item)


# ======================================================================================
# blockstates / items / loot
# ======================================================================================
FACING_Y = {"north": 0, "east": 90, "south": 180, "west": 270}


def model_ref(n):
    return f"{NS}:block/{n}"


def facing_states(models):
    """Blockstate with the four facings (y rotation 0/90/180/270) x the given extra property states
    ({"open=true": model name, "": model name, ...}); extra property names sort after 'facing'."""
    v = {}
    for key, mname in models.items():
        for f, y in FACING_Y.items():
            e = {"model": model_ref(mname)}
            if y:
                e["y"] = y
            v[f"facing={f}" + (f",{key}" if key else "")] = e
    return {"variants": v}


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
    bs["egg_lamp"] = facing_states({"lit=false": "egg_lamp", "lit=true": "egg_lamp_lit"})   # the screen faces the placer
    bs["pet_portrait"] = facing_states({"": "pet_portrait"})
    bs["pet_flap"] = facing_states({"open=false": "pet_flap", "open=true": "pet_flap_open"})
    bs["treat_dispenser"] = facing_states({"": "treat_dispenser"})
    bs["pet_incubator"] = facing_states({"lit=false": "pet_incubator", "lit=true": "pet_incubator_on"})
    bs["toy_box"] = facing_states({"open=false": "toy_box", "open=true": "toy_box_open"})
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


# dye colours (DyeColor diffuse colours), the default dye of the tinted blocks and how far Java whitens it
# (Dyeing.tint = ARGB.srgbLerp(whiten, dye, white); tools/data/gen_data.py applies the same formula to the 16 item models)
DYE = dict(WHITE=0xF9FFFE, ORANGE=0xF9801D, MAGENTA=0xC74EBD, LIGHT_BLUE=0x3AB3DA, YELLOW=0xFED83D, LIME=0x80C71F,
           PINK=0xF38BAA, GRAY=0x474F52, LIGHT_GRAY=0x9D9D97, CYAN=0x169C9C, PURPLE=0x8932B8, BLUE=0x3C44AA,
           BROWN=0x835432, GREEN=0x5E7C16, RED=0xB02E26, BLACK=0x1D1D21)
DEFAULT_DYE = {"pet_bed": "RED", "pet_basket": "LIGHT_BLUE", "egg_lamp": "PINK", "pet_portrait": "PINK"}
WHITEN = {"pet_bed": 0.0, "pet_basket": 0.0, "egg_lamp": 0.3, "pet_portrait": 0.55}


def dye_tint(rgb, whiten):
    """0xRRGGBB of the tint Java computes for a dye: each channel c -> c + floor(whiten * (255 - c)) (float32 like Java)."""
    import numpy as np
    out = 0
    for shift in (16, 8, 0):
        c = (rgb >> shift) & 0xFF
        out = (out << 8) | (c + int(np.floor(np.float32(whiten) * np.float32(255 - c))))
    return out


ITEM_TINT = {blk: dye_tint(DYE[DEFAULT_DYE[blk]], WHITEN[blk]) for blk in DEFAULT_DYE}


def argb(rgb):
    """0xRRGGBB -> opaque ARGB as the signed 32 bit int the item definition json wants."""
    v = 0xFF000000 | rgb
    return v - (1 << 32) if v >= 1 << 31 else v


def base_block(name):
    """'egg_lamp_lit' -> 'egg_lamp': the block a model belongs to (only for tinted blocks)."""
    for blk in sorted(ITEM_TINT, key=len, reverse=True):
        if name == blk or name.startswith(blk + "_"):
            return blk
    return None


def tint_of_model(name, dye=None):
    """(r, g, b) a model is previewed with: its block's default dye (or the dye colour name given); None if untinted."""
    blk = base_block(name)
    if blk is None:
        return None
    c = ITEM_TINT[blk] if dye is None else dye_tint(DYE[dye] if isinstance(dye, str) else dye, WHITEN[blk])
    return ((c >> 16) & 255, (c >> 8) & 255, c & 255)


def block_item(block):
    model = {"type": "minecraft:model", "model": model_ref(block + "_item" if block == "running_wheel" else block)}
    if block in ITEM_TINT:
        model["tints"] = [{"type": "minecraft:constant", "value": argb(ITEM_TINT[block])}]
    return {"model": model}


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
    running_wheel("running_wheel_item", rim=True)
    scratching_post()
    pet_house()
    egg_lamp(False)
    egg_lamp(True)
    pet_portrait()
    pet_flap(False)
    pet_flap(True)
    treat_dispenser()
    pet_incubator(False)
    pet_incubator(True)
    toy_box(False)
    toy_box(True)
    # bounds check (models must stay inside the collision bounds)
    for name, m in MODELS.items():
        base = name.replace("_fill1", "").replace("_fill2", "").replace("_fill3", "").replace("_filled", "").replace("_squished", "")
        for suffix in ("_lit", "_open", "_on"):
            if base.endswith(suffix) and base[:-len(suffix)] in BOUNDS:
                base = base[:-len(suffix)]
        lo, hi = BOUNDS.get(name, BOUNDS.get(base))
        mn, mx = m.true_bounds() if base in TRUE_BOUNDS else m.bounds()
        assert all(mn[i] >= lo[i] for i in range(3)) and all(mx[i] <= hi[i] for i in range(3)), (name, mn, mx, lo, hi)
    return MODELS


if __name__ == "__main__":
    build_models()
    for n, m in MODELS.items():
        print(n, len(m.to_json()["elements"]), m.bounds())
