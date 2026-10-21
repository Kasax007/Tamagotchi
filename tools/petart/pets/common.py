"""Shared parts: the chest backpack with straps, plus shared materials and decorations."""
from rig import Bone, box
from paint import Mat

GOLD = (240, 196, 72)
GOLD_D = (184, 132, 40)


def backpack_mats():
    return {
        'chest': Mat('#A8763E', 'wood', 0.08),
        'chest_lid': Mat('#B98547', 'wood', 0.06),
        'strap': Mat('#6E4A2C', 'smooth', 0.05, flat=True),
    }


def backpack(pivot, torso, straps_z, w=6, h=5, d=5, lid=2, yoff=0.0):
    """pivot: on top of the torso (body-local). torso: (x, y, z, w, h, d) of the torso box in body
    space, used to wrap the straps. straps_z: body-local z positions of the strap bands."""
    bp = Bone('backpack', pivot)
    bp.add(box(-w / 2, -h + lid + yoff, -d / 2, w, h - lid, d, 'chest', 'bp_chest'))
    bp.add(box(-w / 2, -h + yoff, -d / 2, w, lid, d, 'chest_lid', 'bp_lid', inflate=0.25))
    tx, ty, tz, tw, th, td = torso
    px, py, pz = pivot
    for i, z in enumerate(straps_z):
        bp.add(box(tx - px, ty - py, z - pz, tw, th, 1, 'strap', 'bp_strap', inflate=0.2))
    return bp


def _chest_face(c, expr):
    # vertical planks + darker edge frame
    r = c.m('chest').r
    for y in range(c.h):
        c.px(0, y, r[1])
        c.px(c.w - 1, y, r[1])
    c.hline(0, c.w - 1, c.h - 1, r[1])
    if c.face == 'back':
        # latch facing the tail
        mx = c.w // 2 - 1
        c.px(mx, 0, GOLD)
        c.px(mx + 1, 0, GOLD)
        c.px(mx, 1, GOLD_D)
        c.px(mx + 1, 1, GOLD_D)


def _lid_face(c, expr):
    r = c.m('chest_lid').r
    if c.face == 'top':
        c.rect(0, 0, c.w - 1, c.h - 1, r[3])
        for x in range(c.w):
            c.px(x, 0, r[2])
            c.px(x, c.h - 1, r[2])
        for y in range(c.h):
            c.px(0, y, r[2])
            c.px(c.w - 1, y, r[2])
        c.px(c.w // 2, c.h // 2, r[4])
    elif c.face != 'bottom':
        c.hline(0, c.w - 1, c.h - 1, r[0])
        c.px(0, 0, GOLD_D)
        c.px(c.w - 1, 0, GOLD_D)
        if c.face == 'back':
            mx = c.w // 2 - 1
            c.px(mx, c.h - 1, GOLD)
            c.px(mx + 1, c.h - 1, GOLD)


def _strap_face(c, expr):
    r = c.m('strap').r
    c.fill(r[2])
    if c.face in ('left', 'right') and c.h >= 3:
        y = c.h // 2
        c.px(0, y - 1, GOLD)
        c.px(0, y, GOLD_D)
    if c.face == 'top':
        for x in range(c.w):
            c.px(x, 0, r[3])


BACKPACK_DECO = {
    ('bp_chest', '*'): _chest_face,
    ('bp_lid', '*'): _lid_face,
    ('bp_strap', '*'): _strap_face,
}


def shape(c, rows, cmap):
    """Paint an ASCII mask onto the face: '.' clears (cutout), mapped chars paint, others keep."""
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == '.':
                c.clear(x, y)
            elif ch in cmap:
                c.px(x, y, cmap[ch])


def leaf(c, light, mid, dark, vein=True):
    """Pointed leaf filling the canvas (any size), tip at the far end (last column on 'top' faces)."""
    w, h = c.w, c.h
    for y in range(h):
        for x in range(w):
            # ellipse-ish mask, pointy at both ends along x
            t = (x + 0.5) / w
            half = (h / 2) * (1 - (2 * t - 1) ** 2) ** 0.6
            cy = (h - 1) / 2
            if abs(y - cy) <= half:
                c.px(x, y, light if y < cy else mid)
            else:
                c.clear(x, y)
    if vein:
        cy = (h - 1) // 2
        for x in range(1, w - 1):
            c.px(x, cy, dark)


def leaf_plane(c, tip, light, mid, dark, vein_col=None, stem=None):
    """Clean pointed leaf on a flat face. tip = 'right' | 'left' | 'up' | 'down' (canvas direction)."""
    import math
    W, H = c.w, c.h
    along = W if tip in ('right', 'left') else H
    across = H if tip in ('right', 'left') else W
    mask = [[False] * W for _ in range(H)]
    for i in range(along):
        t = (i + 0.5) / along                     # 0 = stem end, 1 = tip
        half = (across / 2.0) * math.sin(math.pi * min(1.0, t ** 0.85)) ** 0.75
        for j in range(across):
            if abs((j + 0.5) - across / 2.0) <= half + 0.15:
                a = i if tip in ('right', 'down') else along - 1 - i
                x, y = (a, j) if tip in ('right', 'left') else (j, a)
                mask[y][x] = True
    for y in range(H):
        for x in range(W):
            if not mask[y][x]:
                c.clear(x, y)
                continue
            edge = any(not (0 <= x + dx < W and 0 <= y + dy < H and mask[y + dy][x + dx])
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            upper = (y < H / 2.0) if tip in ('right', 'left') else (x < W / 2.0)
            c.px(x, y, dark if edge else (light if upper else mid))
    vc = vein_col or dark
    for i in range(1, along - 1):
        a = i if tip in ('right', 'down') else along - 1 - i
        mid_j = (across - 1) // 2
        x, y = (a, mid_j) if tip in ('right', 'left') else (mid_j, a)
        if mask[y][x]:
            c.px(x, y, vc)


def backpack_back(pivot, torso, strap_ys, w=6, h=5, d=4, lid=2):
    """Backpack for upright pets: chest hangs on the back (+Z), straps ring the body horizontally.
    pivot: body-local point on the middle of the back surface."""
    bp = Bone('backpack', pivot)
    bp.add(box(-w / 2, -h / 2 + lid, 0, w, h - lid, d, 'chest', 'bp_chest'))
    bp.add(box(-w / 2, -h / 2, 0, w, lid, d, 'chest_lid', 'bp_lid', inflate=0.25))
    tx, ty, tz, tw, th, td = torso
    px, py, pz = pivot
    for y in strap_ys:
        bp.add(box(tx - px, y - py, tz - pz, tw, 1, td, 'strap', 'bp_strap', inflate=0.2))
    return bp
