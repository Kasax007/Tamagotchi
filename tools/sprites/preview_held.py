#!/usr/bin/env python3
"""Preview of the 3D item models (items3d.py) as they are held: first person, third person (side / front /
back), on the ground and a few plain model views.

    python3 tools/sprites/preview_held.py [tama_pager_3d laser_pointer_3d]  ->  tools/sprites/out/held_<name>.png

A small software rasteriser that applies the *same* display transform chain as the game:
  third person:  arm frame -> rotateX(-90) -> rotateY(180) -> translate(+-1, 2, -10)/16 -> display transform
  first person:  camera frame -> translate(0.56, -0.52, -0.72) -> display transform
  display transform = translate(t/16) * rotate(rx, ry, rz as Rx*Ry*Rz) * scale * translate(-8,-8,-8)/16
(left-hand contexts mirror translation x and rotation y / z; the preview only draws right-hand poses).
The player is a crude Steve (arm raised 18 degrees as in the game); first person is a 70 degree, 16:9 camera.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))

import items3d  # noqa: E402
from pxl import ASSETS, OUT  # noqa: E402
from render import face_param_corners, resolve_tex  # noqa: E402

SHADE = {"up": 1.0, "down": 0.55, "north": 0.8, "south": 0.8, "east": 0.65, "west": 0.65}


# ---- small matrix helpers (column vectors) -------------------------------------------------
def rx(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def ry(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rz(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def display_matrix(t):
    """Model point (0..16 units) -> hand frame (metres)."""
    rot = t.get("rotation", [0, 0, 0])
    tr = np.array(t.get("translation", [0, 0, 0]), dtype=float) / 16.0
    sc = np.array(t.get("scale", [1, 1, 1]), dtype=float)
    R = rx(rot[0]) @ ry(rot[1]) @ rz(rot[2])

    def f(p):
        q = (np.asarray(p, dtype=float) - 8.0) / 16.0 * sc
        return R @ q + tr
    return f


# ---- textures ------------------------------------------------------------------------------
_tex = {}


def load_tex(ref):
    if ref in _tex:
        return _tex[ref]
    ns, path = ref.split(":", 1)
    p = ASSETS / "textures" / f"{path}.png"
    a = np.array(Image.open(p).convert("RGBA"))
    h = a.shape[0]
    meta = Path(str(p) + ".mcmeta")
    if meta.exists():
        an = json.load(open(meta)).get("animation", {})
        h = an.get("height", a.shape[1])
    _tex[ref] = (a, h)
    return _tex[ref]


# ---- rasteriser ----------------------------------------------------------------------------
class Scene:
    def __init__(self, W, H, bg, project):
        self.W, self.H = W, H
        self.img = np.zeros((H, W, 3), dtype=np.float64)
        self.img[:, :] = bg
        self.z = np.full((H, W), -1e18)
        self.project = project      # world point (N,3) -> (sx, sy, depth) arrays

    def quad(self, P00, P10, P01, sampler, density=None):
        P00, P10, P01 = (np.asarray(p, dtype=float) for p in (P00, P10, P01))
        a = self.project(np.array([P00, P10, P01]))
        len_s = math.hypot(a[1][0] - a[0][0], a[1][1] - a[0][1])
        len_t = math.hypot(a[2][0] - a[0][0], a[2][1] - a[0][1])
        ns = min(420, max(2, int(len_s * 1.6) + 2))
        nt = min(420, max(2, int(len_t * 1.6) + 2))
        s = (np.arange(ns) + 0.5) / ns
        t = (np.arange(nt) + 0.5) / nt
        S, T = np.meshgrid(s, t)
        pts = P00[None, None] + S[..., None] * (P10 - P00) + T[..., None] * (P01 - P00)
        col, alpha = sampler(S, T)
        sx, sy, dep = self.project(pts.reshape(-1, 3))
        xi = np.floor(sx).astype(int)
        yi = np.floor(sy).astype(int)
        ok = (xi >= 0) & (xi < self.W) & (yi >= 0) & (yi < self.H) & (alpha.reshape(-1) > 0.5)
        idx = np.nonzero(ok)[0]
        if not len(idx):
            return
        idx = idx[dep[idx] >= self.z[yi[idx], xi[idx]]]
        order = idx[np.argsort(dep[idx], kind="stable")]       # far first, the nearest sample is written last
        self.z[yi[order], xi[order]] = dep[order]
        self.img[yi[order], xi[order]] = col.reshape(-1, 3)[order]

    def box(self, lo, hi, color, shade=True):
        """Axis aligned flat coloured box in world space (lo, hi corners)."""
        (x0, y0, z0), (x1, y1, z1) = lo, hi
        faces = {
            "up": ((x0, y1, z0), (x1, y1, z0), (x0, y1, z1)),
            "down": ((x0, y0, z1), (x1, y0, z1), (x0, y0, z0)),
            "south": ((x0, y1, z1), (x1, y1, z1), (x0, y0, z1)),
            "north": ((x1, y1, z0), (x0, y1, z0), (x1, y0, z0)),
            "west": ((x0, y1, z0), (x0, y1, z1), (x0, y0, z0)),
            "east": ((x1, y1, z1), (x1, y1, z0), (x1, y0, z1)),
        }
        for d, (a, b, c) in faces.items():
            k = SHADE[d] if shade else 1.0
            col = np.array(color, dtype=float) * k
            self.quad(a, b, c, lambda S, T, col=col: (np.broadcast_to(col, S.shape + (3,)), np.ones(S.shape)))

    def model(self, elements, textures, xform):
        for el in elements:
            f, t = el["from"], el["to"]
            for d, fd in el["faces"].items():
                P00, P10, P01 = (xform(p) for p in face_param_corners(d, f, t))
                ref = resolve_tex(textures, fd["texture"])
                tex, fh = load_tex(ref)
                uv = fd["uv"]
                shade = SHADE[d] if el.get("shade", True) else 1.0
                glow = el.get("light_emission", 0) / 15.0
                k = shade + (1 - shade) * glow

                def sampler(S, T, uv=uv, tex=tex, fh=fh, k=k):
                    u = uv[0] + S * (uv[2] - uv[0])
                    v = uv[1] + T * (uv[3] - uv[1])
                    ui = np.clip(np.floor(u / 16.0 * tex.shape[1]).astype(int), 0, tex.shape[1] - 1)
                    vi = np.clip(np.floor(v / 16.0 * fh).astype(int), 0, fh - 1)
                    px = tex[vi, ui].astype(float)
                    return px[..., :3] * k, px[..., 3] / 255.0
                self.quad(P00, P10, P01, sampler)

    def save(self):
        return Image.fromarray(np.clip(self.img, 0, 255).astype(np.uint8), "RGB")


def ortho(yaw, pitch, scale, cx, cy, center=(0, 0, 0)):
    """World (right, up, forward) -> screen; yaw rotates the camera around the up axis."""
    th, ph = math.radians(yaw), math.radians(pitch)

    def project(P):
        P = np.asarray(P, dtype=float) - np.array(center)
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        x1 = x * math.cos(th) + z * math.sin(th)
        z1 = -x * math.sin(th) + z * math.cos(th)
        y2 = y * math.cos(ph) - z1 * math.sin(ph)
        z2 = y * math.sin(ph) + z1 * math.cos(ph)
        return cx + x1 * scale, cy - y2 * scale, z2
    return project


# ---- scenes --------------------------------------------------------------------------------
def third_person(m, display, yaw, W=340, H=380, arm_x=-0.5):
    """Right arm + item seen from the given yaw (0 = from the front, 90 = from the player's left ...)."""
    d = display["thirdperson_righthand"]
    disp = display_matrix(d)
    # world frame (right handed, like the game): x = player's left, y = up, z = forward.
    # Arm-local model frame: x left, y down, z back.
    arm_rot = rx(-18)

    def arm_local_to_world(p):                  # model arm-local metres -> world metres
        q = arm_rot @ np.asarray(p, dtype=float)
        return np.array([q[0], -q[1], -q[2]]) + np.array([-0.3125, 1.35, 0.0])   # right shoulder position

    def item_to_world(p):
        q = disp(p) + np.array([1 / 16, 2 / 16, -10 / 16])     # item frame after the hand translate
        arm = rx(-90) @ ry(180) @ q
        return arm_local_to_world(arm)

    scene = Scene(W, H, (118, 124, 138), ortho(yaw, 0, 150, W / 2, H * 0.62, center=(0.1, 1.15, 0.2)))
    shirt, skin, legs = (62, 160, 160), (222, 170, 140), (60, 60, 150)
    scene.box((-0.25, 0.7, -0.12), (0.25, 1.4, 0.12), shirt)              # torso
    scene.box((-0.25, 0.0, -0.12), (0.25, 0.7, 0.12), legs)
    scene.box((-0.25, 1.4, -0.25), (0.25, 1.9, 0.25), skin)               # head
    # arm: box 4 x 12 x 4 px, hanging from the shoulder, pitched forward
    corners = []
    for x in (-2, 2):
        for y in (-2, 10):
            for z in (-2, 2):
                corners.append((x, y, z))
    for (lo, hi) in [(( -2, -2, -2), (2, 10, 2))]:
        faces = {}
        pts = {}
        for ix, x in enumerate((lo[0], hi[0])):
            for iy, y in enumerate((lo[1], hi[1])):
                for iz, z in enumerate((lo[2], hi[2])):
                    pts[(ix, iy, iz)] = arm_local_to_world(np.array([x, y, z]) / 16.0)
        def q(a, b, c, col):
            scene.quad(pts[a], pts[b], pts[c], lambda S, T, col=col: (np.broadcast_to(col, S.shape + (3,)), np.ones(S.shape)))
        base = np.array(skin, dtype=float)
        q((0, 0, 0), (1, 0, 0), (0, 1, 0), base * 0.8)      # z- face
        q((0, 0, 1), (1, 0, 1), (0, 1, 1), base * 0.7)
        q((0, 0, 0), (0, 0, 1), (0, 1, 0), base * 0.85)
        q((1, 0, 0), (1, 0, 1), (1, 1, 0), base * 0.65)
        q((0, 0, 0), (1, 0, 0), (0, 0, 1), base)
        q((0, 1, 0), (1, 1, 0), (0, 1, 1), base * 0.6)
    scene.model(m["json"]["elements"], m["json"]["textures"], item_to_world)
    return scene.save()


def first_person(m, display, W=480, H=270):
    d = display["firstperson_righthand"]
    disp = display_matrix(d)
    fov = math.radians(70)
    f = (H / 2) / math.tan(fov / 2)

    def project(P):
        P = np.asarray(P, dtype=float)
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        zz = np.minimum(z, -0.05)
        return W / 2 + f * x / -zz, H / 2 - f * y / -zz, z      # nearer to the camera = larger z

    def item_to_cam(p):
        return disp(p) + np.array([0.56, -0.52, -0.72])

    scene = Scene(W, H, (126, 168, 214), project)
    # ground plane tint + a crosshair
    img = scene.img
    img[H // 2 + 20:, :] = (96, 140, 76)
    scene.model(m["json"]["elements"], m["json"]["textures"], item_to_cam)
    out = scene.save()
    d_ = ImageDraw.Draw(out)
    d_.line((W // 2 - 6, H // 2, W // 2 + 6, H // 2), fill=(255, 255, 255))
    d_.line((W // 2, H // 2 - 6, W // 2, H // 2 + 6), fill=(255, 255, 255))
    return out


def plain(m, yaw, pitch, size=300, scale=15):
    scene = Scene(size, size, (118, 124, 138), ortho(yaw, pitch, scale, size / 2, size / 2, center=(8, 8, 8)))
    # model coords: x east, y up, z south.  ortho() expects (right, up, forward): use z as forward directly
    scene.model(m["json"]["elements"], m["json"]["textures"], lambda p: np.asarray(p, dtype=float))
    return scene.save()


def ground_view(m, display, size=300):
    d = display["ground"]
    disp = display_matrix(d)
    scene = Scene(size, size, (118, 124, 138), ortho(30, 20, 220, size / 2, size * 0.62, center=(0, 0, 0)))
    scene.box((-0.4, -0.02, -0.4), (0.4, 0.0, 0.4), (96, 140, 76))
    base = np.array([0, 0.25, 0])
    scene.model(m["json"]["elements"], m["json"]["textures"], lambda p: disp(p) + base)
    return scene.save()


def fixed_view(m, display, size=300):
    d = display["fixed"]
    disp = display_matrix(d)
    scene = Scene(size, size, (150, 118, 80), ortho(0, 0, 220, size / 2, size / 2, center=(0, 0, 0)))
    # item frame viewer looks along +z at the frame: the engine adds a 180 turn, so the model's north faces the
    # viewer by default (display rotation 0) and a 180 turn shows the south (front) face, like generated items.
    scene.model(m["json"]["elements"], m["json"]["textures"], lambda p: ry(180) @ disp(p))
    return scene.save()


def sheet(name):
    models = items3d.models()
    m = models[name]
    display = m["json"]["display"]
    pieces = []
    pieces.append(("1st person", first_person(m, display)))
    pieces.append(("3rd side (from right)", third_person(m, display, -90)))
    pieces.append(("3rd front", third_person(m, display, 0)))
    pieces.append(("3rd back", third_person(m, display, 180)))
    pieces.append(("ground", ground_view(m, display)))
    pieces.append(("fixed", fixed_view(m, display)))
    for label, yaw, pitch in (("front", 0, 0), ("back", 180, 0), ("3/4 A", 30, 20), ("3/4 B", -30, 20),
                              ("side", 90, 0), ("top", 0, 60)):
        pieces.append((label, plain(m, yaw, pitch)))
    cols = 3
    cw = max(p[1].width for p in pieces)
    ch = max(p[1].height for p in pieces)
    rows = math.ceil(len(pieces) / cols)
    out = Image.new("RGB", (cols * cw, rows * (ch + 16)), (40, 40, 48))
    dr = ImageDraw.Draw(out)
    for i, (label, im) in enumerate(pieces):
        x, y = (i % cols) * cw, (i // cols) * (ch + 16)
        out.paste(im, (x, y + 16))
        dr.text((x + 4, y + 2), label, fill=(240, 240, 245))
    return out


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    names = argv or ["tama_pager_3d", "laser_pointer_3d"]
    items3d.build()
    for n in names:
        p = OUT / f"held_{n}.png"
        sheet(n).save(p)
        print("wrote", p)


if __name__ == "__main__":
    main(sys.argv[1:])
