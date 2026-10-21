"""Tiny software renderer: draws a rig with its texture like Minecraft's entity renderer would
(cutout alpha, two directional lights, emissive glow layer), for contact-sheet reviews."""
import math

import numpy as np
from PIL import Image

from rig import quads

L0 = np.array([0.2, 1.0, -0.7]); L0 /= np.linalg.norm(L0)
L1 = np.array([-0.2, 1.0, 0.7]); L1 /= np.linalg.norm(L1)


def _to_world(p, scale):
    # model px (Y down, front -Z) -> world blocks, pet facing +Z
    return np.array([p[0] / 16.0, 1.501 - p[1] / 16.0, -p[2] / 16.0]) * scale


def render(roots, tex_rgba, glow_rgba=None, size=320, yaw=35.0, pitch=22.0, dist=2.6, scale=1.0,
           pose=None, hidden=(), bg=(58, 64, 82), target_y=None):
    qs = quads(roots, pose, hidden)
    tw, th = tex_rgba.shape[1], tex_rgba.shape[0]
    # camera
    ys = [(_to_world(v, scale))[1] for q in qs for v in q[0]]
    ty = target_y if target_y is not None else (min(ys) + max(ys)) / 2
    yr, pr = math.radians(yaw), math.radians(pitch)
    eye = np.array([math.sin(yr) * math.cos(pr) * dist, ty + math.sin(pr) * dist, math.cos(yr) * math.cos(pr) * dist])
    tgt = np.array([0.0, ty, 0.0])
    fwd = tgt - eye; fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    f = size * 1.9

    img = np.zeros((size, size, 3), np.float32)
    # background gradient + soft ground shadow
    for y in range(size):
        t = y / size
        img[y, :, :] = np.array(bg) * (1.15 - 0.35 * t)
    zbuf = np.full((size, size), np.inf, np.float32)

    def proj(p):
        d = p - eye
        x, y, z = d @ right, d @ up, d @ fwd
        return np.array([size / 2 + f * x / z, size / 2 - f * y / z, z])

    # ground shadow ellipse
    sh = []
    for a in range(24):
        ang = a / 24 * 2 * math.pi
        sh.append(proj(np.array([math.cos(ang) * 0.38 * scale, 0.0, math.sin(ang) * 0.38 * scale])))
    sh = np.array(sh)
    from PIL import ImageDraw
    shadow = Image.new('L', (size, size), 0)
    ImageDraw.Draw(shadow).polygon([(p[0], p[1]) for p in sh], fill=90)
    sa = np.asarray(shadow, np.float32)[..., None] / 255.0
    img = img * (1 - sa * 0.6)

    for verts, uvs, n in qs:
        wv = [_to_world(v, scale) for v in verts]
        nw = np.array([n[0], -n[1], -n[2]], float)
        nn = np.linalg.norm(nw)
        if nn > 0:
            nw /= nn
        P = [proj(p) for p in wv]
        if any(p[2] <= 0.05 for p in P):
            continue
        shade = min(1.0, 0.4 + 0.6 * (max(0.0, nw @ L0) + max(0.0, nw @ L1)))
        # double-sided: flip normal light if facing away
        cam_dir = (sum(wv) / 4) - eye
        if nw @ cam_dir > 0:
            shade = min(1.0, 0.4 + 0.6 * (max(0.0, -nw @ L0) + max(0.0, -nw @ L1)))
        for tri in ((0, 1, 2), (0, 2, 3)):
            _raster(img, zbuf, [P[i] for i in tri], [uvs[i] for i in tri], tex_rgba, glow_rgba, tw, th, shade)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGB')


def _raster(img, zbuf, P, UV, tex, glow, tw, th, shade):
    H, W = zbuf.shape
    xs = [p[0] for p in P]; ys = [p[1] for p in P]
    x0, x1 = max(int(math.floor(min(xs))), 0), min(int(math.ceil(max(xs))), W - 1)
    y0, y1 = max(int(math.floor(min(ys))), 0), min(int(math.ceil(max(ys))), H - 1)
    if x0 > x1 or y0 > y1:
        return
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = P
    den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    if abs(den) < 1e-9:
        return
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    w0 = ((by - cy) * (gx - cx) + (cx - bx) * (gy - cy)) / den
    w1 = ((cy - ay) * (gx - cx) + (ax - cx) * (gy - cy)) / den
    w2 = 1 - w0 - w1
    m = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
    if not m.any():
        return
    iz = w0 / az + w1 / bz + w2 / cz
    z = 1.0 / iz
    u = (w0 * UV[0][0] / az + w1 * UV[1][0] / bz + w2 * UV[2][0] / cz) * z
    v = (w0 * UV[0][1] / az + w1 * UV[1][1] / bz + w2 * UV[2][1] / cz) * z
    ui = np.clip(np.floor(u - 1e-4).astype(int), 0, tw - 1)
    vi = np.clip(np.floor(v - 1e-4).astype(int), 0, th - 1)
    texel = tex[vi, ui]
    m &= texel[..., 3] > 25
    sub = zbuf[y0:y1 + 1, x0:x1 + 1]
    m &= z < sub
    if not m.any():
        return
    col = texel[..., :3].astype(np.float32) * shade
    if glow is not None:
        g = glow[vi, ui].astype(np.float32)
        ga = g[..., 3:4] / 255.0
        col = col * (1 - ga) + g[..., :3] * ga
    region = img[y0:y1 + 1, x0:x1 + 1]
    region[m] = col[m]
    sub[m] = z[m]


def contact_sheet(images, cols, pad=6, bg=(30, 32, 40), labels=None):
    from PIL import ImageDraw
    w = max(i.width for i in images); h = max(i.height for i in images)
    rows = (len(images) + cols - 1) // cols
    lh = 14 if labels else 0
    sheet = Image.new('RGB', (cols * (w + pad) + pad, rows * (h + pad + lh) + pad), bg)
    d = ImageDraw.Draw(sheet)
    for i, im in enumerate(images):
        x = pad + (i % cols) * (w + pad)
        y = pad + (i // cols) * (h + pad + lh)
        sheet.paste(im, (x, y))
        if labels:
            d.text((x + 2, y + h + 1), labels[i], fill=(220, 220, 230))
    return sheet
