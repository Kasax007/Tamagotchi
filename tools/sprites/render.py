"""Small software renderer for vanilla-format block models (review sheets only).

Orthographic view (yaw about Y, then pitch about X, like the GUI transform [30, 225, 0]),
z-buffered, nearest-neighbour texture sampling, vanilla directional face shading
(up 1.0, north/south 0.8, east/west 0.6, down 0.5).  Faces use exactly the vertex <-> uv assignment
of the game, so what you see here is what the model JSON produces.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

import numpy as np
from PIL import Image

from pxl import ASSETS

VANILLA = Path(os.environ.get(
    "VANILLA_ASSETS",
    "/tmp/claude-0/-home-user/4e8c5592-2e7c-59b7-a06b-12e2b7f59073/scratchpad/vanilla/assets/minecraft"))

SHADE = {"up": 1.0, "down": 0.5, "north": 0.8, "south": 0.8, "east": 0.6, "west": 0.6}


def _split(ident: str, default="minecraft"):
    if ":" in ident:
        ns, path = ident.split(":", 1)
    else:
        ns, path = default, ident
    return ns, path


def _asset_file(ns, kind, path, ext):
    if ns == "tamagotchi":
        p = ASSETS / kind / f"{path}{ext}"
    else:
        p = VANILLA / kind / f"{path}{ext}"
    return p


_tex_cache: dict[str, np.ndarray] = {}


def load_texture(ident: str) -> np.ndarray:
    if ident in _tex_cache:
        return _tex_cache[ident]
    ns, path = _split(ident)
    p = _asset_file(ns, "textures", path, ".png")
    if not p.exists():
        raise FileNotFoundError(f"texture {ident} -> {p}")
    a = np.array(Image.open(p).convert("RGBA"))
    _tex_cache[ident] = a
    return a


def load_model(ident: str) -> dict:
    ns, path = _split(ident)
    p = _asset_file(ns, "models", path, ".json")
    with open(p) as f:
        m = json.load(f)
    if "parent" in m:
        parent = load_model(m["parent"])
        textures = dict(parent.get("textures", {}))
        textures.update(m.get("textures", {}))
        merged = dict(parent)
        merged.update({k: v for k, v in m.items() if k not in ("parent", "textures")})
        merged["textures"] = textures
        if "elements" not in m and "elements" in parent:
            merged["elements"] = parent["elements"]
        return merged
    return m


def resolve_tex(textures: dict, ref: str) -> str:
    seen = 0
    while ref.startswith("#"):
        ref = textures[ref[1:]]
        seen += 1
        if seen > 20:
            raise RuntimeError("texture ref loop")
    return ref


def face_param_corners(d, f, t):
    fx, fy, fz = f
    tx, ty, tz = t
    if d == "north":
        return (tx, ty, fz), (fx, ty, fz), (tx, fy, fz)
    if d == "south":
        return (fx, ty, tz), (tx, ty, tz), (fx, fy, tz)
    if d == "west":
        return (fx, ty, fz), (fx, ty, tz), (fx, fy, fz)
    if d == "east":
        return (tx, ty, tz), (tx, ty, fz), (tx, fy, tz)
    if d == "up":
        return (fx, ty, fz), (tx, ty, fz), (fx, ty, tz)
    if d == "down":
        return (fx, fy, tz), (tx, fy, tz), (fx, fy, fz)
    raise ValueError(d)


def _rot_axis(p, axis, ang, origin):
    x, y, z = p[0] - origin[0], p[1] - origin[1], p[2] - origin[2]
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    if axis == "y":
        x, z = x * c + z * s, -x * s + z * c
    elif axis == "x":
        y, z = y * c - z * s, y * s + z * c
    else:
        x, y = x * c - y * s, x * s + y * c
    return (x + origin[0], y + origin[1], z + origin[2])


def render_model(model: dict, yaw=225.0, pitch=30.0, scale=8, size=None, frame=0, shade=True, tints=None, ambient=1.0):
    """Render ``model`` (resolved JSON) and return an RGBA PIL image (transparent background).

    ``tints`` maps a tintindex to an (r, g, b) colour that multiplies the texture of every face carrying that
    tintindex (what the game does with a block / item colour).  ``ambient`` < 1 darkens everything except faces of
    elements with ``light_emission`` (those keep max(ambient, emission / 15)): a quick night preview of lit states."""
    textures = model.get("textures", {})
    size = size or int(16 * scale * 1.75)
    W = H = size
    cx, cy = W / 2.0, H / 2.0 + 8 * scale * 0.0
    th, ph = math.radians(yaw), math.radians(pitch)

    def view(p):
        x, y, z = p[0] - 8, p[1] - 8, p[2] - 8
        x1 = x * math.cos(th) + z * math.sin(th)
        z1 = -x * math.sin(th) + z * math.cos(th)
        y2 = y * math.cos(ph) - z1 * math.sin(ph)
        z2 = y * math.sin(ph) + z1 * math.cos(ph)
        return cx + x1 * scale, cy - y2 * scale, z2

    color = np.zeros((H, W, 4), dtype=np.float64)
    zbuf = np.full((H, W), -1e9)
    trans = []  # deferred translucent texels

    faces = []
    for el in model.get("elements", []):
        f, t = el["from"], el["to"]
        rot = el.get("rotation")
        for d, fd in el.get("faces", {}).items():
            P00, P10, P01 = face_param_corners(d, f, t)
            if rot:
                o = rot["origin"]
                P00, P10, P01 = (_rot_axis(p, rot["axis"], rot["angle"], o) for p in (P00, P10, P01))
            uv = fd.get("uv") or None
            if uv is None:
                from modelkit import default_uv
                uv = default_uv(d, f, t)
            ref = resolve_tex(textures, fd["texture"])
            tex = load_texture(ref)
            tint = None
            if tints and fd.get("tintindex") is not None and fd["tintindex"] in tints:
                tint = np.array(tints[fd["tintindex"]], dtype=np.float64) / 255.0
            faces.append((d, P00, P10, P01, uv, tex, fd.get("rotation", 0), el.get("shade", True), tint,
                          el.get("light_emission", 0)))

    def raster(face, pass_):
        d, P00, P10, P01, uv, tex, frot, shd, tint, emit = face
        a, b, c = view(P00), view(P10), view(P01)
        ax, ay = b[0] - a[0], b[1] - a[1]
        bx, by = c[0] - a[0], c[1] - a[1]
        det = ax * by - ay * bx
        if abs(det) < 1e-6:
            return
        xs = [a[0], b[0], c[0], b[0] + c[0] - a[0]]
        ys = [a[1], b[1], c[1], b[1] + c[1] - a[1]]
        x0, x1 = max(0, int(math.floor(min(xs))) - 1), min(W, int(math.ceil(max(xs))) + 2)
        y0, y1 = max(0, int(math.floor(min(ys))) - 1), min(H, int(math.ceil(max(ys))) + 2)
        if x0 >= x1 or y0 >= y1:
            return
        px, py = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        dx, dy = px - a[0], py - a[1]
        s = (dx * by - dy * bx) / det
        t = (ax * dy - ay * dx) / det
        inside = (s >= 0) & (s < 1) & (t >= 0) & (t < 1)
        if not inside.any():
            return
        if frot == 90:
            s, t = t, 1 - s
        elif frot == 180:
            s, t = 1 - s, 1 - t
        elif frot == 270:
            s, t = 1 - t, s
        u = uv[0] + s * (uv[2] - uv[0])
        v = uv[1] + s * 0 + t * (uv[3] - uv[1])
        th_, tw_ = tex.shape[0], tex.shape[1]
        fh = tw_  # frames are square
        ui = np.clip(np.floor(u / 16.0 * tw_).astype(int), 0, tw_ - 1)
        vi = np.clip(np.floor(v / 16.0 * fh).astype(int), 0, fh - 1) + frame * fh
        vi = np.clip(vi, 0, th_ - 1)
        texel = tex[vi, ui].astype(np.float64)
        depth = a[2] + s * (b[2] - a[2]) + t * (c[2] - a[2])
        sh = SHADE[d] if (shade and shd) else 1.0
        sh *= max(ambient, emit / 15.0) if emit else ambient
        if tint is not None:
            texel[:, :, :3] *= tint
        alpha = texel[:, :, 3]
        sub = (slice(y0, y1), slice(x0, x1))
        if pass_ == 0:
            ok = inside & (alpha >= 255) & (depth > zbuf[sub] + 1e-6)
            if ok.any():
                zs = zbuf[sub]
                cs = color[sub]
                zs[ok] = depth[ok]
                rgb = texel[:, :, :3] * sh
                cs[ok, :3] = rgb[ok]
                cs[ok, 3] = 255
        else:
            ok = inside & (alpha > 0) & (alpha < 255)
            if ok.any():
                ys_, xs_ = np.nonzero(ok)
                for yy, xx in zip(ys_, xs_):
                    trans.append((float(depth[yy, xx]), y0 + yy, x0 + xx, texel[yy, xx, :3] * sh, float(alpha[yy, xx])))

    for fc in faces:
        raster(fc, 0)
    for fc in faces:
        raster(fc, 1)
    trans.sort(key=lambda r: r[0])
    for dep, yy, xx, rgb, al in trans:
        if dep + 1e-6 < zbuf[yy, xx]:
            continue  # behind opaque geometry
        a_ = al / 255.0
        if color[yy, xx, 3] > 0:
            color[yy, xx, :3] = color[yy, xx, :3] * (1 - a_) + rgb * a_
            color[yy, xx, 3] = max(color[yy, xx, 3], 255 if a_ > 0.5 else color[yy, xx, 3])
        else:
            color[yy, xx, :3] = rgb
            color[yy, xx, 3] = al
    return Image.fromarray(np.clip(color, 0, 255).astype(np.uint8), "RGBA")


def textures_used(model: dict):
    out = []
    textures = model.get("textures", {})
    for el in model.get("elements", []):
        for fd in el.get("faces", {}).values():
            ref = resolve_tex(textures, fd["texture"])
            if ref not in out:
                out.append(ref)
    return out
