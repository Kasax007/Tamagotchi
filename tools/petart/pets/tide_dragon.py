"""Tide Dragon: teal sea dragon with fin ears, a dorsal fin, a fluke tail and glowing aqua spots."""
from rig import Bone, box
from paint import Mat, eyes, hx
from pets.common import backpack, backpack_mats, BACKPACK_DECO, shape

NAME = 'tide_dragon'
PREVIEW_SCALE = 0.8
FACE_Y = 0.62

TORSO = (-3.5, -3, -5, 7, 6, 10)
GLOW = hx('#5FF2FF')
GLOW_D = hx('#2FC6DF')
FIN, FIN_D, FIN_L = hx('#8FE0E6'), hx('#3C8FB8'), hx('#C9F5F5')
BLUSH = (236, 150, 190)


def mats():
    m = {
        'body': Mat('#3AA7B3', 'smooth', 0.035),
        'back': Mat('#23649B', 'smooth', 0.03),
        'belly': Mat('#B4E9E4', 'smooth', 0.03),
        'fin': Mat('#8FE0E6', 'none'),
        'claw': Mat('#E8F6F4', 'none', flat=True),
    }
    m.update(backpack_mats())
    return m


def rig():
    body = Bone('body', (0, 17, 0))
    body.add(box(*TORSO, 'body', 'torso'))
    body.add(box(-2.5, -4, -4, 5, 1, 8, 'back', 'torso_top'))
    body.add(box(-0.5, -7, -3, 1, 3, 5, 'back', 'dorsal'))

    head = Bone('head', (0, -2.5, -5))
    head.add(box(-4, -6, -6, 8, 7, 7, 'body', 'head'))
    head.add(box(-3, -7, -5, 6, 1, 5, 'back', 'head_top'))
    head.add(box(-2, -1, -8, 4, 2, 2, 'body', 'snout'))
    head.add(box(-0.5, -9, -3, 1, 2, 3, 'back', 'head_fin'))
    jaw = Bone('jaw', (0, 1, -6)).add(box(-2, 0, -2, 4, 1, 2, 'belly', 'jaw'))
    ear_l = Bone('ear_l', (4, -4, -2), (0, 20, -35)).add(box(0, 0, 0, 5, 0, 4, 'fin', 'ear_fin_l', faces=('top', 'bottom')))
    ear_r = Bone('ear_r', (-4, -4, -2), (0, -20, 35)).add(box(-5, 0, 0, 5, 0, 4, 'fin', 'ear_fin_r', faces=('top', 'bottom')))
    head.add(jaw, ear_l, ear_r)

    tail = Bone('tail', (0, -1, 5), (-12, 0, 0)).add(box(-1.5, -1.5, 0, 3, 3, 5, 'body', 'tail'))
    tail2 = Bone('tail2', (0, 0, 5), (6, 0, 0)).add(box(-1, -1, 0, 2, 2, 5, 'body', 'tail2'))
    fluke = Bone('tail3', (0, 0, 5), (4, 0, 0)).add(box(-3.5, 0, -1, 7, 0, 5, 'fin', 'fluke', faces=('top', 'bottom')))
    tail2.add(fluke)
    tail.add(tail2)

    body.add(head, tail, backpack((0, -3, 1.5), TORSO, (-1, 3)))

    legs = []
    for name, x, z in (('leg_fr', -2.5, -3), ('leg_fl', 2.5, -3), ('leg_br', -2.5, 3.5), ('leg_bl', 2.5, 3.5)):
        legs.append(Bone(name, (x, 20, z)).add(box(-1.5, 0, -1.5, 3, 4, 3, 'body', 'leg')))
    return [body] + legs


def _head_front(c, expr):
    body = c.m('body').r
    eyes(c, 2, expr, gap=2, size=(2, 3), iris=hx('#3B7BE8'), lid=body[0], pupil=(20, 30, 70))
    if expr != 'angry':
        c.px(1, 5, BLUSH)
        c.px(6, 5, BLUSH)
    c.glow(0, 1, GLOW, 200)
    c.px(0, 1, GLOW_D)
    c.glow(7, 1, GLOW, 200)
    c.px(7, 1, GLOW_D)


def _head_side(c, expr):
    for x, y in ((1, 2), (3, 4), (5, 2)):
        if x < c.w:
            c.px(x, y, GLOW_D)
            c.glow(x, y, GLOW, 210)


def _snout_front(c, expr):
    body = c.m('body').r
    c.px(0, 0, body[0])
    c.px(3, 0, body[0])
    c.hline(1, 2, 0, body[3])
    if expr in ('happy', 'love'):
        c.hline(1, 2, 1, (60, 60, 120))


def _torso(c, expr):
    belly, back, body = c.m('belly').r, c.m('back').r, c.m('body').r
    if c.face == 'bottom':
        c.fill(belly[2])
        for y in range(1, c.h, 2):
            c.hline(1, c.w - 2, y, belly[1])
    elif c.face == 'front':
        c.rect(1, 1, c.w - 2, c.h - 1, belly[2])
    elif c.face in ('left', 'right'):
        c.hline(0, c.w - 1, 0, back[2])
        c.hline(1, c.w - 2, c.h - 1, belly[1])
        c.hline(1, c.w - 2, c.h - 2, belly[2])
        for x, y in ((1, 2), (3, 3), (5, 2), (7, 3), (9, 2)):
            if x < c.w:
                c.px(x, y, GLOW_D)
                c.glow(x, y, GLOW, 220)
    elif c.face == 'top':
        c.fill(back[2])


def _dorsal(c, expr):
    if c.face in ('left', 'right'):
        # fin sloping toward the tail: clear the top-front corner
        rows = ['..XXX', '.XXXX', 'XXXXX'] if c.face == 'left' else ['XXX..', 'XXXX.', 'XXXXX']
        shape(c, rows, {'X': FIN})
        for x in range(c.w):
            c.px(x, c.h - 1, FIN_D)
    elif c.face == 'top':
        c.fill(FIN_L)


def _fin_plane(c, tip):
    # webbed fin with three spines, pointing to `tip` (left/right on the canvas)
    w, h = c.w, c.h
    for y in range(h):
        for x in range(w):
            k = x if tip == 'right' else w - 1 - x          # 0 at the root
            reach = h - 1 - (k * (h - 1)) // (w - 1)
            if y <= reach + (1 if k < w - 1 else 0) and not (k == w - 1 and y > 1):
                c.px(x, y, FIN_L if y == 0 else FIN)
            else:
                c.clear(x, y)
    for k in range(0, w, 2):
        x = k if tip == 'right' else w - 1 - k
        for y in range(0, h):
            if c.tex.rgba[c.v + y, c.u + x, 3]:
                c.px(x, y, FIN_D)


def _fluke(c, expr):
    # whale-like fluke: two lobes with a notch at the back (row 0 = back on top face)
    shape(c, ['XX...XX'[:c.w],
              'XXX.XXX'[:c.w],
              'XXXXXXX'[:c.w],
              '.XXXXX.'[:c.w],
              '..XXX..'[:c.w]], {'X': FIN})
    for y in range(c.h):
        if c.tex.rgba[c.v + y, c.u + c.w // 2, 3]:
            c.px(c.w // 2, y, FIN_D)
    c.px(0, 0, FIN_L)
    c.px(c.w - 1, 0, FIN_L)


def _leg(c, expr):
    claw, body = c.m('claw').r, c.m('body').r
    if c.face == 'front':
        c.hline(0, 2, c.h - 1, hx('#7FD6DA'))
        c.px(1, c.h - 1, body[1])
    elif c.face == 'bottom':
        c.fill(body[1])


def _tail(c, expr):
    back = c.m('back').r
    if c.face == 'top':
        c.fill(back[2])
    elif c.face in ('left', 'right'):
        c.hline(0, c.w - 1, 0, back[2])
        for x in range(1, c.w, 2):
            c.px(x, c.h // 2, GLOW_D)
            c.glow(x, c.h // 2, GLOW, 200)


DECO = {
    ('head', 'front'): _head_front,
    ('head', 'left'): _head_side,
    ('head', 'right'): _head_side,
    ('snout', 'front'): _snout_front,
    ('snout', 'top'): lambda c, e: c.fill(c.m('body').r[3]),
    ('torso', '*'): _torso,
    ('dorsal', '*'): _dorsal,
    ('head_fin', '*'): _dorsal,
    ('ear_fin_l', '*'): lambda c, e: _fin_plane(c, 'right'),
    ('ear_fin_r', '*'): lambda c, e: _fin_plane(c, 'left'),
    ('fluke', '*'): _fluke,
    ('leg', '*'): _leg,
    ('tail', '*'): _tail,
    ('tail2', '*'): _tail,
    ('jaw', 'front'): lambda c, e: c.fill(c.m('belly').r[2]),
}
DECO.update(BACKPACK_DECO)
