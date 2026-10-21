"""Tiny block-model DSL: boxes on a 1px grid -> vanilla model JSON.

* default UVs follow vanilla's position based rule (a texture is "carved" through the 16^3 cell), but
  every face is written out with an explicit ``uv`` so the JSON never depends on engine defaults;
* faces hidden between two touching boxes are dropped, ``cullface`` is set on faces that lie on the
  outer boundary of the block cell;
* ``masks`` helpers turn ASCII footprints into merged rectangles (round-ish pixel shapes).
"""
from __future__ import annotations

from pxl import write_json

DIRS = ("down", "up", "north", "south", "west", "east")
OPP = {"down": "up", "up": "down", "north": "south", "south": "north", "west": "east", "east": "west"}


def default_uv(d, frm, to):
    fx, fy, fz = frm
    tx, ty, tz = to
    return {
        "down": [fx, 16 - tz, tx, 16 - fz],
        "up": [fx, fz, tx, tz],
        "north": [16 - tx, 16 - ty, 16 - fx, 16 - fy],
        "south": [fx, 16 - ty, tx, 16 - fy],
        "west": [fz, 16 - ty, tz, 16 - fy],
        "east": [16 - tz, 16 - ty, 16 - fz, 16 - fy],
    }[d]


def _clean(v):
    return int(v) if float(v).is_integer() else float(v)


class Box:
    def __init__(self, frm, to, faces, rotation=None, shade=True):
        self.frm = tuple(frm)
        self.to = tuple(to)
        self.faces = faces  # dir -> dict(texture=key, uv=[..], ...)
        self.rotation = rotation
        self.shade = shade

    def plane(self, d):
        f, t = self.frm, self.to
        return {"down": f[1], "up": t[1], "north": f[2], "south": t[2], "west": f[0], "east": t[0]}[d]

    def rect(self, d):
        """2D rectangle of a face in the plane (axis-aligned coordinates)."""
        f, t = self.frm, self.to
        if d in ("down", "up"):
            return (f[0], f[2], t[0], t[2])
        if d in ("north", "south"):
            return (f[0], f[1], t[0], t[1])
        return (f[2], f[1], t[2], t[1])


class Model:
    def __init__(self, name, textures, parent="minecraft:block/block", particle=None, ao=True):
        self.name = name
        self.textures = dict(textures)
        if particle:
            self.textures["particle"] = particle if particle.startswith("tamagotchi:") else self.textures[particle]
        self.parent = parent
        self.ao = ao
        self.boxes: list[Box] = []

    # ------------------------------------------------------------------
    def box(self, frm, to, all=None, sides=None, up=None, down=None, north=None, south=None, east=None, west=None,
            skip=(), uv=None, rotation=None, shade=True):
        """Add a box.  Face values: texture key, (key, uv) or dict(texture=.., uv=.., rotation=..)."""
        spec = {}
        for d in DIRS:
            spec[d] = None
        if all is not None:
            for d in DIRS:
                spec[d] = all
        if sides is not None:
            for d in ("north", "south", "east", "west"):
                spec[d] = sides
        for d, v in (("up", up), ("down", down), ("north", north), ("south", south), ("east", east), ("west", west)):
            if v is not None:
                spec[d] = v
        faces = {}
        for d in DIRS:
            if d in skip or spec[d] is None or spec[d] is False:
                continue
            v = spec[d]
            if isinstance(v, str):
                v = dict(texture=v)
            elif isinstance(v, tuple):
                v = dict(texture=v[0], uv=list(v[1]))
            else:
                v = dict(v)
            if "uv" not in v or v["uv"] is None:
                v["uv"] = default_uv(d, frm, to)
            if uv and d in uv:
                v["uv"] = list(uv[d])
            faces[d] = v
        b = Box(frm, to, faces, rotation, shade)
        self.boxes.append(b)
        return b

    # ------------------------------------------------------------------
    def _covered(self, box, d):
        """True if face d of box is completely hidden by a touching box (integer geometry only)."""
        vals = list(box.frm) + list(box.to)
        if any(not float(v).is_integer() for v in vals):
            return False
        plane = box.plane(d)
        x0, y0, x1, y1 = box.rect(d)
        cells = {(i, j) for i in range(int(x0), int(x1)) for j in range(int(y0), int(y1))}
        if not cells:
            return False
        for other in self.boxes:
            if other is box or other.rotation:
                continue
            if other.plane(OPP[d]) != plane:
                continue
            ov = list(other.frm) + list(other.to)
            if any(not float(v).is_integer() for v in ov):
                continue
            a0, b0, a1, b1 = other.rect(OPP[d])
            # `other` must lie on the far side of the plane (its opposite face sits on the plane)
            cells -= {(i, j) for i in range(int(a0), int(a1)) for j in range(int(b0), int(b1))}
            if not cells:
                return True
        return not cells

    def to_json(self, optimize=True):
        elements = []
        for b in self.boxes:
            faces = {}
            for d, spec in b.faces.items():
                if optimize and self._covered(b, d):
                    continue
                out = {"uv": [_clean(v) for v in spec["uv"]], "texture": "#" + spec["texture"]}
                plane = b.plane(d)
                if (d in ("down", "west", "north") and plane == 0) or (d in ("up", "east", "south") and plane == 16):
                    out["cullface"] = d
                if spec.get("rotation"):
                    out["rotation"] = spec["rotation"]
                if spec.get("tintindex") is not None:
                    out["tintindex"] = spec["tintindex"]
                faces[d] = out
            if not faces:
                continue
            el = {"from": [_clean(v) for v in b.frm], "to": [_clean(v) for v in b.to]}
            if b.rotation:
                el["rotation"] = b.rotation
            if not b.shade:
                el["shade"] = False
            el["faces"] = faces
            elements.append(el)
        obj = {}
        if self.parent:
            obj["parent"] = self.parent
        if not self.ao:
            obj["ambientocclusion"] = False
        obj["textures"] = self.textures
        obj["elements"] = elements
        gui = self.gui_display()
        if gui:
            obj["display"] = {"gui": gui}
        return obj

    def gui_display(self):
        """Inventory icon framing for furniture lower or narrower than a block: scale it up to fill the slot
        and lift it to the slot's centre (same view as block/block: rotation 30/225/0, scale 0.625)."""
        (x0, y0, z0), (x1, y1, z1) = self.bounds()
        span = (x1 - x0) + (z1 - z0)
        w = span * 0.7071                       # projected width at 225 degrees
        h = 0.866 * (y1 - y0) + 0.3536 * span   # projected height at a 30 degree tilt
        s = min(1.0, 0.625 * min(22.63 / w, 25.24 / h))
        lift = (8 - (y0 + y1) / 2) * s * 0.866
        if s < 0.63 and abs(lift) < 0.5:
            return None
        return {"rotation": [30, 225, 0], "translation": [0, round(lift, 2), 0], "scale": [round(s, 3)] * 3}

    def save(self, path):
        write_json(path, self.to_json())

    # ------------------------------------------------------------------
    def bounds(self):
        mn = [min(b.frm[i] for b in self.boxes) for i in range(3)]
        mx = [max(b.to[i] for b in self.boxes) for i in range(3)]
        return mn, mx


# ----------------------------------------------------------------------------------------
# footprint masks: ASCII -> set of (x, z) cells -> merged rectangles
# ----------------------------------------------------------------------------------------


def mask_cells(text, ox=0, oz=0, on="#"):
    """ASCII footprint -> set of (x, z) cells.  Row index = z, column index = x (offset by ox/oz)."""
    cells = set()
    for z, row in enumerate(text.strip("\n").split("\n")):
        for x, ch in enumerate(row.strip()):
            if ch in on:
                cells.add((x + ox, z + oz))
    return cells


def rect_cells(x0, z0, x1, z1):
    return {(x, z) for x in range(x0, x1) for z in range(z0, z1)}


def round_rect(x0, z0, x1, z1, cut):
    """Rectangle with the four corners chamfered by ``cut`` (pixel-art round-ish footprint).
    ``cut`` is the number of px removed at the very corner (list/tuple = per-row inset profile)."""
    cells = set()
    prof = list(range(cut, 0, -1)) if isinstance(cut, int) else list(cut)
    for z in range(z0, z1):
        for x in range(x0, x1):
            dz = min(z - z0, z1 - 1 - z)
            dx = min(x - x0, x1 - 1 - x)
            ok = True
            if dz < len(prof) and dx < prof[dz]:
                ok = False
            if dx < len(prof) and dz < prof[dx]:
                ok = False
            if ok:
                cells.add((x, z))
    return cells


def merge_rects(cells):
    """Greedy merge of 1px cells into rectangles: rows of runs, stacked while identical.
    Returns list of (x0, z0, x1, z1)."""
    cells = set(cells)
    rows = {}
    for x, z in cells:
        rows.setdefault(z, []).append(x)
    runs = {}
    for z, xs in rows.items():
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
        runs[z] = out
    rects = []
    open_ = {}  # (x0,x1) -> z0
    for z in range(min(rows), max(rows) + 2):
        cur = set(runs.get(z, []))
        for key in list(open_):
            if key not in cur:
                rects.append((key[0], open_.pop(key), key[1], z))
        for key in cur:
            if key not in open_:
                open_[key] = z
    return sorted(rects, key=lambda r: (r[1], r[0]))
