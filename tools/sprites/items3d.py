"""3D (block-model style) item models: Tama Pager and Laser Pointer.

The inventory (gui) keeps the crisp 2D sprite from ``items.py``; every other display context (hands, ground,
item frame, head) uses the cuboid models built here.  ``build()`` writes

    textures/item/tama_pager_3d.png        shell sheet (front, back, side swatches)
    textures/item/tama_pager_3d_lcd.png    animated LCD (11x7 frames, same blink / hop cycle as the 2D sprite)
    textures/item/laser_pointer_3d.png     pen sheet
    models/item/tama_pager_3d.json, models/item/laser_pointer_3d.json
    items/tama_pager.json, items/laser_pointer.json     (select on minecraft:display_context)

Texel density is 2 texels per model unit (a 32 wide sheet spans the 16 units of the uv space), so all
geometry sits on a 0.5 unit grid.  Light comes from the top left, like everywhere else in the mod.
Run ``python3 tools/sprites/preview_held.py`` to see the models in hand.
"""
from __future__ import annotations

import numpy as np
from PIL import Image

import pal  # noqa: F401  (registers ramps)
from pxl import ASSETS, RAMPS, hex2rgb, save_png, write_json, write_mcmeta

NS = "tamagotchi"


def _c(v):
    v = round(float(v), 4)
    return int(v) if float(v).is_integer() else v


# ======================================================================================
# texture atlas helper
# ======================================================================================
class Atlas:
    """Shelf-packed sheet.  ``uv`` converts a texel rectangle into the 0..16 uv space of the model JSON."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = np.zeros((h, w, 4), dtype=np.uint8)
        self._x = self._y = self._rowh = 0
        self._x0 = 0                       # where a new shelf row starts
        self._sw = {}

    def alloc(self, tw, th):
        if self._x + tw > self.w:
            self._x, self._y, self._rowh = self._x0, self._y + self._rowh, 0
        if self._y + th > self.h:
            raise RuntimeError("atlas full")
        pos = (self._x, self._y)
        self._x += tw
        self._rowh = max(self._rowh, th)
        return pos

    def put(self, arr, x, y):
        arr = np.asarray(arr, dtype=np.uint8)
        self.px[y:y + arr.shape[0], x:x + arr.shape[1]] = arr

    def uv(self, x0, y0, x1, y1):
        return [_c(x0 * 16 / self.w), _c(y0 * 16 / self.h), _c(x1 * 16 / self.w), _c(y1 * 16 / self.h)]

    def swatch(self, color):
        """Solid colour: a 3x3 block, sampled in the middle texel (no bleeding from neighbours)."""
        key = tuple(color)
        if key not in self._sw:
            x, y = self.alloc(3, 3)
            self.px[y:y + 3, x:x + 3] = key
            self._sw[key] = (x, y)
        x, y = self._sw[key]
        return self.uv(x + 1, y + 1, x + 2, y + 2)

    def strip(self, cols, length, vertical=True, rows=None):
        """A face painted as ``len(cols)`` colour columns (vertical strip) or rows (horizontal) repeated along
        its length; ``rows`` can override single rows: {index: colour list}.  Returns the uv rect."""
        n = len(cols)
        w, h = (n, length) if vertical else (length, n)
        x, y = self.alloc(w, h)
        a = np.zeros((h, w, 4), dtype=np.uint8)
        for i, col in enumerate(cols):
            if vertical:
                a[:, i] = col
            else:
                a[i, :] = col
        if rows:
            for r, cl in rows.items():
                for i, col in enumerate(cl):
                    if vertical:
                        a[r, i] = col
                    else:
                        a[i, r] = col
        self.put(a, x, y)
        return self.uv(x, y, x + w, y + h)

    def image(self):
        return Image.fromarray(self.px, "RGBA")


# ======================================================================================
# TAMA PAGER
# ======================================================================================
SHELL = RAMPS["shellpink"]      # highlight, light, base, shadow, deep
LCD = RAMPS["lcd"]
STEEL = RAMPS["steel"]
PURPLE_L = hex2rgb("#9B83A8")
PURPLE_D = hex2rgb("#5F4B73")
BTN = [  # light, base, shade of the three buttons (yellow, teal, blue; same colours as the 2D sprite)
    [hex2rgb("#FFF6B8"), hex2rgb("#FFC83E"), hex2rgb("#E29E2E")],
    [hex2rgb("#B8F6EA"), hex2rgb("#4CD2C0"), hex2rgb("#1F928F")],
    [hex2rgb("#BCD8FF"), hex2rgb("#6B9CF0"), hex2rgb("#3253A8")],
]

# egg outline: width in cells (0.5 unit each) per row, top to bottom; every row is centred
WIDTHS = [7, 11, 13, 15, 15, 17, 17, 17, 19, 19, 19, 19, 19, 19, 19, 19, 17, 17, 15, 11]
NW, NH = 19, len(WIDTHS)
X0 = 8 - NW * 0.25              # left edge of the egg (units)
Y_TOP = 13.0                    # top edge of the egg (units)
LCD_CELLS = (4, 6, 15, 13)      # x0, y0, x1, y1 (exclusive) in cells: 11 x 7 cells = 5.5 x 3.5 units
BEZEL_CELLS = (3, 5, 16, 14)
BUTTONS = [(5, 16), (9, 16), (13, 16)]   # plus shapes, centre cell
Z_LCD = 8.5                     # floor of the recess; the LCD slab sits on it (front face at 9.0, bezel at 9.5)
Z_BTN = 10.0

# frame the back atlas / front atlas occupy in the 64x32 sheet
FRONT_AT = (0, 0)
BACK_AT = (20, 0)


def _egg_cells():
    cells = set()
    for r, w in enumerate(WIDTHS):
        x0 = (NW - w) // 2
        for x in range(x0, x0 + w):
            cells.add((x, r))
    return cells


def _edge_depth(cells):
    """Manhattan distance to the outside minus one (0 = rim cell)."""
    d = {}
    frontier = [c for c in cells if any((c[0] + dx, c[1] + dy) not in cells for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for c in frontier:
        d[c] = 0
    k = 0
    while frontier:
        k += 1
        nxt = []
        for (x, y) in frontier:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if n in cells and n not in d:
                    d[n] = k
                    nxt.append(n)
        frontier = nxt
    return d


def _in(box, c):
    return box[0] <= c[0] < box[2] and box[1] <= c[1] < box[3]


def _cell_class(c):
    if _in(LCD_CELLS, c):
        return "lcd"
    if _in(BEZEL_CELLS, c):
        return "bezel"
    for i, (bx, by) in enumerate(BUTTONS):
        if c in ((bx, by), (bx - 1, by), (bx + 1, by), (bx, by - 1), (bx, by + 1)):
            return f"btn{i}"
    return "shell"


def _shell_color(sx, sy, d):
    """Pink shell shading in view space (sx, sy): light from the top left, darker rim."""
    t = 0.55 * sx / (NW - 1) + 0.45 * sy / (NH - 1)
    i = 1 if t < 0.30 else (2 if t < 0.62 else 3)
    if (sx, sy) in ((3, 3), (4, 3), (3, 4), (2, 5)) and d >= 1:
        i = 0
    if d == 0:
        i = min(4, i + 1) if i >= 2 else i
    return SHELL[i]


def _front_color(c, cls, d, lcd_box, bezel_box):
    cx, cy = c
    if cls == "shell":
        return _shell_color(cx, cy, d)
    if cls == "lcd":
        return PURPLE_D
    if cls == "bezel":
        x0, y0, x1, y1 = bezel_box
        return PURPLE_D if (cx == x1 - 1 or cy == y1 - 1) else PURPLE_L
    i = int(cls[3])
    bx, by = BUTTONS[i]
    lit, base, shade = BTN[i]
    if (cx, cy) == (bx, by - 1) or (cx, cy) == (bx - 1, by):
        return lit
    if (cx, cy) == (bx, by + 1):
        return shade
    return base


def _back_color(c, cls, d):
    sx = NW - 1 - c[0]
    sy = c[1]
    return _shell_color(sx, sy, d)


HEART = [
    ".HH.HH.",
    "HhHHHHH",
    "HHHHHHp",
    ".HHHHp.",
    "..HHp..",
    "...p...",
]


def _merge(cells):
    """Greedy merge of cells into rectangles (rows of runs, stacked while identical)."""
    rows = {}
    for x, y in cells:
        rows.setdefault(y, []).append(x)
    runs = {}
    for y, xs in rows.items():
        xs.sort()
        start = prev = xs[0]
        out = []
        for x in xs[1:]:
            if x == prev + 1:
                prev = x
                continue
            out.append((start, prev + 1))
            start = prev = x
        out.append((start, prev + 1))
        runs[y] = out
    rects, open_ = [], {}
    for y in range(min(rows), max(rows) + 2):
        cur = set(runs.get(y, []))
        for key in list(open_):
            if key not in cur:
                rects.append((key[0], open_.pop(key), key[1], y))
        for key in cur:
            if key not in open_:
                open_[key] = y
    return sorted(rects, key=lambda r: (r[1], r[0]))


# LCD pet frames: '#' dark pixel, 'o' mid tone, '.' background; row 0 is the shadow row under the bezel
LCD_W, LCD_H = 11, 7
LCD_FRAMES = {
    "neutral": [
        "...........",
        "..#.....#..",
        "..##...##..",
        "..#######..",
        "..#.###.#..",
        "..###.###..",
        "...#...#...",
    ],
    "blink": [
        "...........",
        "..#.....#..",
        "..##...##..",
        "..#######..",
        "..#######..",
        "..#######..",
        "...#...#...",
    ],
    "hop": [
        "...........",
        "..#.....#..",
        "..##...##..",
        "..#.###.#..",
        "..#######..",
        "...#####...",
        "....ooo....",
    ],
}


def lcd_frame(name):
    a = np.zeros((LCD_H, LCD_W, 4), dtype=np.uint8)
    for y, row in enumerate(LCD_FRAMES[name]):
        for x, ch in enumerate(row):
            col = {".": LCD[1], "#": LCD[4], "o": LCD[2]}[ch]
            if y == 0 and ch == ".":
                col = LCD[2]
            a[y, x] = col
    return a


def build_pager():
    atlas = Atlas(64, 32)
    cells = _egg_cells()
    d = _edge_depth(cells)
    cls = {c: _cell_class(c) for c in cells}

    def depth(c):
        k = cls[c]
        lvl = min(d[c], 2)
        zb = (7.5, 7.0, 6.5)[lvl]
        zf = (8.5, 9.0, 9.5)[lvl]
        if k == "lcd":
            zf = Z_LCD
        elif k.startswith("btn"):
            zf = Z_BTN
        elif k == "bezel":
            zf = 9.5
        return zb, zf

    dep = {c: depth(c) for c in cells}

    # ---- front / back atlases -----------------------------------------------------------
    fx, fy = FRONT_AT
    bx, by = BACK_AT
    front = np.zeros((NH, NW, 4), dtype=np.uint8)
    back = np.zeros((NH, NW, 4), dtype=np.uint8)
    for c in cells:
        front[c[1], c[0]] = _front_color(c, cls[c], d[c], LCD_CELLS, BEZEL_CELLS)
        back[c[1], NW - 1 - c[0]] = _back_color(c, cls[c], d[c])
    # heart sticker on the back, little reset dimple
    hp = {"H": RAMPS["heartpink"][1], "h": RAMPS["heartpink"][0], "p": RAMPS["heartpink"][2]}
    for y, row in enumerate(HEART):
        for x, ch in enumerate(row):
            if ch != ".":
                back[8 + y, 6 + x] = hp[ch]
    back[3, 9] = SHELL[4]
    back[3, 10] = SHELL[3]
    atlas.px[fy:fy + NH, fx:fx + NW] = front
    atlas.px[by:by + NH, bx:bx + NW] = back
    atlas._x = atlas._x0 = 42                      # swatches live right of the two big images

    def front_uv(cx0, cy0, cx1, cy1):
        return atlas.uv(fx + cx0, fy + cy0, fx + cx1, fy + cy1)

    def back_uv(cx0, cy0, cx1, cy1):          # the back image is stored as seen from behind (mirrored)
        return atlas.uv(bx + NW - cx1, by + cy0, bx + NW - cx0, by + cy1)

    side_col = {
        "shell": {"up": SHELL[1], "west": SHELL[2], "east": SHELL[3], "down": SHELL[3]},
        "bezel": {"up": PURPLE_L, "west": PURPLE_L, "east": PURPLE_D, "down": PURPLE_D},
        "lcd": {"up": PURPLE_D, "west": PURPLE_D, "east": PURPLE_D, "down": PURPLE_D},
    }
    for i in range(3):
        lit, base, shade = BTN[i]
        side_col[f"btn{i}"] = {"up": lit, "west": lit, "east": base, "down": shade}

    def cx_x(cx):
        return X0 + cx * 0.5

    def cy_y(cy):
        return Y_TOP - cy * 0.5

    def covered(c, n):
        """True if the neighbour cell n hides the lateral face of cell c completely."""
        if n not in dep:
            return False
        return dep[n][0] <= dep[c][0] and dep[n][1] >= dep[c][1]

    elements = []
    groups = {}
    for c in cells:
        groups.setdefault((cls[c], dep[c]), []).append(c)
    for (k, (zb, zf)), cs in sorted(groups.items(), key=lambda kv: (kv[0][1][1], kv[0][0])):
        for (x0, y0, x1, y1) in _merge(cs):
            faces = {
                "south": {"uv": front_uv(x0, y0, x1, y1), "texture": "#shell"},
                "north": {"uv": back_uv(x0, y0, x1, y1), "texture": "#shell"},
            }
            sc = side_col[k]
            if any(not covered((x, y0), (x, y0 - 1)) for x in range(x0, x1)):
                faces["up"] = {"uv": atlas.swatch(sc["up"]), "texture": "#shell"}
            if any(not covered((x, y1 - 1), (x, y1)) for x in range(x0, x1)):
                faces["down"] = {"uv": atlas.swatch(sc["down"]), "texture": "#shell"}
            if any(not covered((x0, y), (x0 - 1, y)) for y in range(y0, y1)):
                faces["west"] = {"uv": atlas.swatch(sc["west"]), "texture": "#shell"}
            if any(not covered((x1 - 1, y), (x1, y)) for y in range(y0, y1)):
                faces["east"] = {"uv": atlas.swatch(sc["east"]), "texture": "#shell"}
            elements.append({
                "from": [_c(cx_x(x0)), _c(cy_y(y1)), _c(zb)],
                "to": [_c(cx_x(x1)), _c(cy_y(y0)), _c(zf)],
                "faces": {f: faces[f] for f in ("down", "up", "north", "south", "west", "east") if f in faces},
            })

    # ---- LCD slab (animated sprite, light emitting) ------------------------------------------
    lx0, ly0, lx1, ly1 = LCD_CELLS
    elements.append({
        "from": [_c(cx_x(lx0)), _c(cy_y(ly1)), Z_LCD],
        "to": [_c(cx_x(lx1)), _c(cy_y(ly0)), Z_LCD + 0.5],
        "shade": False,
        "light_emission": 8,
        "faces": {"south": {"uv": [0, 0, 16, 16], "texture": "#lcd"}},
    })

    # ---- keychain loop on top ---------------------------------------------------------------
    ring = {"south": STEEL[1], "north": STEEL[2], "up": STEEL[0], "down": STEEL[3], "west": STEEL[0], "east": STEEL[3]}

    def ring_box(x0, y0, x1, y1, faces):
        elements.append({
            "from": [x0, y0, 7.5], "to": [x1, y1, 8.5],
            "faces": {f: {"uv": atlas.swatch(ring[f]), "texture": "#shell"} for f in faces},
        })

    ring_box(7, 13, 7.5, 15, ("south", "north", "west", "east"))
    ring_box(8.5, 13, 9, 15, ("south", "north", "west", "east"))
    ring_box(7, 15, 9, 15.5, ("south", "north", "up", "west", "east"))

    return atlas, elements


# ======================================================================================
# LASER POINTER
# ======================================================================================
LRED = RAMPS["laserred"]
LBLUE = RAMPS["laserblue"]
INK = hex2rgb("#252E48")
INK_L = hex2rgb("#3B4668")


def build_pen():
    atlas = Atlas(32, 32)
    els = []

    def tube(name, y0, y1, half, side_cols, caps=(None, None), shade=True, emission=None, rows=None):
        """A square tube centred on (8, 8).  side_cols = {'south': [...], ...} colour columns per face (left to
        right as seen from outside); caps = (down colour list or None, up colour list or None)."""
        w = int(round(half * 4))                      # texels across (2 per unit)
        length = int(round((y1 - y0) * 2))
        faces = {}
        for f in ("south", "north", "west", "east"):
            faces[f] = {"uv": atlas.strip(side_cols[f], length, True, rows), "texture": "#pen"}
        for f, col in zip(("down", "up"), caps):
            if col is not None:
                x, y = atlas.alloc(w, w)
                a = np.zeros((w, w, 4), dtype=np.uint8)
                a[:, :] = col[0]
                if len(col) > 1 and w >= 3:
                    a[1:w - 1, 1:w - 1] = col[1]
                atlas.put(a, x, y)
                faces[f] = {"uv": atlas.uv(x, y, x + w, y + w), "texture": "#pen"}
        el = {"from": [_c(8 - half), _c(y0), _c(8 - half)], "to": [_c(8 + half), _c(y1), _c(8 + half)]}
        if not shade:
            el["shade"] = False
        if emission:
            el["light_emission"] = emission
        el["faces"] = {f: faces[f] for f in ("down", "up", "north", "south", "west", "east") if f in faces}
        els.append(el)

    S0, S1, S2, S3, S4 = STEEL
    # face -> columns as seen from outside (left to right); light from the top left of the item front
    body = {"south": [S1, S0, S2], "north": [S3, S2, S3], "west": [S1, S1, S2], "east": [S3, S3, S4]}
    tube("cap", 3.0, 3.5, 0.5, {"south": [S2, S3], "north": [S3, S3], "west": [S2, S3], "east": [S3, S4]},
         caps=([S4],  None))
    tube("body", 3.5, 8.0, 0.75, body, caps=([S3], None),
         rows={3: [S3, S3, S4], 4: [S3, S3, S4]})                       # a thin engraved line low on the body
    tube("band1", 8.0, 8.5, 1.0, {"south": [INK_L, INK_L, INK, INK], "north": [INK, INK, INK, INK],
                                   "west": [INK_L, INK_L, INK, INK], "east": [INK, INK, INK, INK]},
         caps=([INK], [INK_L]))
    grip = {"south": [LBLUE[1], LBLUE[0], LBLUE[2]], "north": [LBLUE[3], LBLUE[3], LBLUE[3]],
            "west": [LBLUE[1], LBLUE[1], LBLUE[2]], "east": [LBLUE[3], LBLUE[3], LBLUE[4]]}
    tube("grip", 8.5, 10.5, 0.75, grip,
         rows={1: [LBLUE[3], LBLUE[3], LBLUE[3]], 3: [LBLUE[3], LBLUE[3], LBLUE[3]]})   # two grip grooves
    tube("band2", 10.5, 11.0, 1.0, {"south": [INK_L, INK_L, INK, INK], "north": [INK, INK, INK, INK],
                                    "west": [INK_L, INK_L, INK, INK], "east": [INK, INK, INK, INK]},
         caps=([INK], [INK_L]))
    tube("tip", 11.0, 12.5, 0.5, {"south": [S1, S3], "north": [S3, S3], "west": [S1, S2], "east": [S3, S4]})
    glow = {f: [LRED[1], LRED[1]] for f in ("south", "north", "west", "east")}
    glow["south"] = [LRED[0], LRED[1]]
    tube("lens", 12.5, 13.0, 0.5, glow, caps=(None, [LRED[0], LRED[0]]), shade=False, emission=15)

    # red push button on the front face, little silver clip on the back
    def block(frm, to, cols):
        faces = {}
        for f, col in cols.items():
            faces[f] = {"uv": atlas.swatch(col), "texture": "#pen"}
        els.append({"from": frm, "to": to, "faces": faces})

    block([7.5, 6.0, 8.75], [8.5, 7.0, 9.25],
          {"south": LRED[1], "up": LRED[0], "west": LRED[1], "east": LRED[3], "down": LRED[3]})
    block([7.5, 5.0, 6.75], [8.5, 10.5, 7.25],
          {"north": S2, "south": S3, "up": S1, "down": S3, "west": S1, "east": S4})
    return atlas, els


# ======================================================================================
# display transforms
# ======================================================================================
def mirror_left(t):
    """Explicit ``*_lefthand`` entry.  The engine mirrors translation x and rotation y / z for left-hand contexts
    by itself, so copying the right-hand values gives the mirror image of the right-hand pose.  (The poses below only
    use x rotations, or a 180 turn about y, so they are the same in both hands apart from the sideways offset.)"""
    return dict(t)


PAGER_DISPLAY = {
    "thirdperson_righthand": {"rotation": [90, 180, 0], "translation": [0, 1.5, 1.5], "scale": [0.62, 0.62, 0.62]},
    "firstperson_righthand": {"rotation": [-12, 0, 0], "translation": [-3.0, 5.0, -1.0], "scale": [0.68, 0.68, 0.68]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 1, 0], "scale": [0.6, 0.6, 0.6]},
    "fixed": {"rotation": [0, 180, 0], "translation": [0, -1, 0], "scale": [1.2, 1.2, 1.2]},
    "head": {"rotation": [0, 180, 0], "translation": [0, 13, 7], "scale": [1, 1, 1]},
}

PEN_DISPLAY = {
    "thirdperson_righthand": {"rotation": [-20, 0, 0], "translation": [0, 3.0, 0.5], "scale": [0.75, 0.75, 0.75]},
    "firstperson_righthand": {"rotation": [-50, 0, 0], "translation": [-2.0, 4.0, 0.0], "scale": [0.8, 0.8, 0.8]},
    "ground": {"rotation": [90, 0, 0], "translation": [0, -1, 0], "scale": [0.8, 0.8, 0.8]},
    "fixed": {"rotation": [0, 180, 45], "translation": [0, 0, 0], "scale": [1.1, 1.1, 1.1]},
    "head": {"rotation": [0, 180, 0], "translation": [0, 13, 7], "scale": [1, 1, 1]},
}


def with_left(display):
    d = dict(display)
    d["thirdperson_lefthand"] = mirror_left(display["thirdperson_righthand"])
    d["firstperson_lefthand"] = mirror_left(display["firstperson_righthand"])
    order = ["thirdperson_righthand", "thirdperson_lefthand", "firstperson_righthand", "firstperson_lefthand",
             "ground", "fixed", "head"]
    return {k: d[k] for k in order}


def select_item(name):
    """Item definition: the 2D sprite model in the inventory (and on shelves), the 3D model everywhere else."""
    return {"model": {
        "type": "minecraft:select",
        "cases": [{"model": {"type": "minecraft:model", "model": f"{NS}:item/{name}"}, "when": ["gui", "on_shelf"]}],
        "fallback": {"type": "minecraft:model", "model": f"{NS}:item/{name}_3d"},
        "property": "minecraft:display_context",
    }}


# ======================================================================================
# build
# ======================================================================================
def models():
    """name -> dict(model json, sheet image, extra) for the preview and for ``build``."""
    out = {}
    atlas, els = build_pager()
    out["tama_pager_3d"] = {
        "json": {
            "textures": {"particle": f"{NS}:item/tama_pager_3d", "shell": f"{NS}:item/tama_pager_3d",
                         "lcd": f"{NS}:item/tama_pager_3d_lcd"},
            "elements": els,
            "gui_light": "front",
            "display": with_left(PAGER_DISPLAY),
        },
        "sheet": atlas.image(),
    }
    atlas, els = build_pen()
    out["laser_pointer_3d"] = {
        "json": {
            "textures": {"particle": f"{NS}:item/laser_pointer_3d", "pen": f"{NS}:item/laser_pointer_3d"},
            "elements": els,
            "gui_light": "front",
            "display": with_left(PEN_DISPLAY),
        },
        "sheet": atlas.image(),
    }
    return out


def build():
    for name, m in models().items():
        save_png(m["sheet"], ASSETS / "textures/item" / f"{name}.png")
        write_json(ASSETS / "models/item" / f"{name}.json", m["json"])
    # animated LCD: neutral / blink / hop strip, the same timing as the 2D pager
    strip = np.concatenate([lcd_frame(n) for n in ("neutral", "blink", "hop")], axis=0)
    png = ASSETS / "textures/item/tama_pager_3d_lcd.png"
    save_png(Image.fromarray(strip, "RGBA"), png)
    seq = [(0, 12), (2, 3), (0, 5), (1, 3)]
    write_mcmeta(png, frametime=2, frames=[{"index": i, "time": t} for i, t in seq], width=LCD_W, height=LCD_H)
    for item in ("tama_pager", "laser_pointer"):
        write_json(ASSETS / "items" / f"{item}.json", select_item(item))


if __name__ == "__main__":
    build()
    print("3D item models written")
