"""Desert Dragon: chubby sand-gold baby dragon, terracotta plates, blue scarab gem, little wings."""
from rig import Bone, box
from paint import Mat, eyes, hx
from pets.common import backpack, backpack_mats, BACKPACK_DECO

NAME = 'desert_dragon'
PREVIEW_SCALE = 0.8
FACE_Y = 0.62

TORSO = (-3.5, -3, -5, 7, 6, 10)
BLUSH = (242, 150, 132)


def mats():
    m = {
        'body': Mat('#E6BE80', 'smooth', 0.035),
        'belly': Mat('#F6E4BE', 'smooth', 0.03),
        'plate': Mat('#CF6A3C', 'smooth', 0.05),
        'horn': Mat('#EAD7AE', 'smooth', 0.0),
        'wing': Mat('#EE9A5C', 'smooth', 0.0),
        'claw': Mat('#F3E7D2', 'smooth', 0.0, flat=True),
    }
    m.update(backpack_mats())
    return m


def rig():
    body = Bone('body', (0, 17, 0))
    body.add(box(*TORSO, 'body', 'torso'))
    body.add(box(-2.5, -4, -4, 5, 1, 8, 'body', 'torso_top'))
    for z, hgt in ((-3.5, 1), (-0.5, 2), (2.5, 1)):
        body.add(box(-0.5, -4 - hgt, z, 1, hgt, 2, 'plate', 'spike'))

    head = Bone('head', (0, -2.5, -5))
    head.add(box(-4, -6, -6, 8, 7, 7, 'body', 'head'))
    head.add(box(-3, -7, -5, 6, 1, 5, 'body', 'head_top'))
    head.add(box(-2, -1, -8, 4, 2, 2, 'body', 'snout'))
    jaw = Bone('jaw', (0, 1, -6)).add(box(-2, 0, -2, 4, 1, 2, 'belly', 'jaw'))
    horn_l = Bone('horn_l', (2.5, -7, -2), (-35, 0, 18)).add(box(-0.5, -3, -0.5, 1, 3, 1, 'horn', 'horn'))
    horn_r = Bone('horn_r', (-2.5, -7, -2), (-35, 0, -18)).add(box(-0.5, -3, -0.5, 1, 3, 1, 'horn', 'horn'))
    ear_l = Bone('ear_l', (4, -5, -2.5), (0, 20, 15)).add(box(0, -1, 0, 1, 3, 3, 'plate', 'frill'))
    ear_r = Bone('ear_r', (-4, -5, -2.5), (0, -20, -15)).add(box(-1, -1, 0, 1, 3, 3, 'plate', 'frill'))
    head.add(jaw, horn_l, horn_r, ear_l, ear_r)

    wing_l = Bone('wing_l', (3, -3, -2), (-10, 0, 55)).add(box(0, -6, 0, 0, 6, 7, 'wing', 'wing', faces=('right', 'left')))
    wing_r = Bone('wing_r', (-3, -3, -2), (-10, 0, -55)).add(box(0, -6, 0, 0, 6, 7, 'wing', 'wing', faces=('right', 'left')))

    tail = Bone('tail', (0, -1, 5), (-18, 0, 0)).add(box(-1.5, -1.5, 0, 3, 3, 5, 'body', 'tail'))
    tail2 = Bone('tail2', (0, 0, 5), (10, 0, 0)).add(box(-1, -1, 0, 2, 2, 4, 'body', 'tail2'))
    tip = Bone('tail3', (0, 0, 4), (8, 0, 0)).add(box(-2, 0, -0.5, 4, 0, 4, 'plate', 'spade', faces=('top', 'bottom')))
    tail2.add(tip)
    tail.add(tail2)

    body.add(head, wing_l, wing_r, tail, backpack((0, -3, 1.5), TORSO, (-1, 3)))

    legs = []
    for name, x, z in (('leg_fr', -2.5, -3), ('leg_fl', 2.5, -3), ('leg_br', -2.5, 3.5), ('leg_bl', 2.5, 3.5)):
        legs.append(Bone(name, (x, 20, z)).add(box(-1.5, 0, -1.5, 3, 4, 3, 'body', 'leg')))
    return [body] + legs


# ------------------------------------------------------------------ decorations

def _head_front(c, expr):
    body = c.m('body').r
    # scarab gem on the forehead
    c.rect(3, 0, 4, 1, (47, 143, 201))
    c.px(3, 0, (160, 222, 248))
    c.px(4, 1, (28, 92, 152))
    eyes(c, 2, expr, gap=2, size=(2, 3), iris=hx('#EE9C34'), lid=body[0], pupil=(58, 34, 30))
    if expr not in ('angry',):
        c.px(1, 5, BLUSH)
        c.px(6, 5, BLUSH)


def _head_top(c, expr):
    plate = c.m('plate').r
    for y in range(c.h):
        c.px(3, y, plate[2])
        c.px(4, y, plate[1] if y % 2 else plate[2])


def _head_side(c, expr):
    # soft cheek shading toward the jaw line
    body = c.m('body').r
    c.hline(0, c.w - 1, c.h - 1, body[1])


def _snout_front(c, expr):
    body = c.m('body').r
    c.px(0, 0, body[0])
    c.px(3, 0, body[0])
    c.hline(1, 2, 0, body[3])
    if expr in ('happy', 'love'):
        c.px(1, 1, (186, 72, 72))
        c.px(2, 1, (186, 72, 72))
    else:
        c.px(2, 1, (255, 255, 255))      # tiny fang


def _snout_top(c, expr):
    c.fill(c.m('body').r[3])


def _torso(c, expr):
    belly, plate, body = c.m('belly').r, c.m('plate').r, c.m('body').r
    if c.face == 'bottom':
        c.fill(belly[2])
        for y in range(1, c.h, 2):
            c.hline(1, c.w - 2, y, belly[1])
    elif c.face == 'front':
        c.rect(1, 1, c.w - 2, c.h - 1, belly[2])
        c.hline(2, c.w - 3, 1, belly[3])
    elif c.face in ('left', 'right'):
        c.hline(1, c.w - 2, c.h - 1, belly[1])
        c.hline(1, c.w - 2, c.h - 2, belly[2])
    elif c.face == 'top':
        mid = c.w // 2
        for y in range(c.h):
            c.px(mid - 1, y, plate[2])
            c.px(mid, y, plate[2] if y % 3 else plate[1])
            # light scale arcs either side of the spine
            if y % 3 == 1:
                c.px(mid - 3, y, body[4])
                c.px(mid + 2, y, body[4])


def _leg(c, expr):
    claw, body = c.m('claw').r, c.m('body').r
    if c.face == 'front':
        c.px(0, c.h - 1, claw[2])
        c.px(2, c.h - 1, claw[2])
        c.px(1, c.h - 1, body[2])
    elif c.face == 'bottom':
        c.fill(body[1])


def _tail(c, expr):
    plate = c.m('plate').r
    if c.face in ('left', 'right'):
        for i in range(1, c.w, 2):
            if i % 4 == 1:
                c.vline(i, 0, c.h - 1, plate[3])
    elif c.face in ('top', 'bottom'):
        for i in range(1, c.h, 2):
            if i % 4 == 1:
                c.hline(0, c.w - 1, i, plate[3] if c.face == 'top' else plate[2])


def _spade(c, expr):
    plate = c.m('plate').r
    shape = ['.XX.',
             'XXXX',
             'XXXX',
             '.XX.']
    for y, row in enumerate(shape):
        for x, ch in enumerate(row):
            if ch == '.':
                c.clear(x, y)
            else:
                c.px(x, y, plate[3] if (c.face == 'top' and 0 < x < 3) else plate[2])


def _wing(c, expr):
    wing, horn = c.m('wing').r, c.m('horn').r
    w, h = c.w, c.h
    front_col = w - 1 if c.face == 'right' else 0
    step = -1 if c.face == 'right' else 1
    for y in range(h):
        for x in range(w):
            c.px(x, y, wing[3] if y <= 2 else wing[2])
    c.hline(0, w - 1, 0, horn[3])
    for x in (front_col + step * 2, front_col + step * 4, front_col + step * 6):
        if 0 <= x < w:
            for y in range(1, h - 1):
                c.px(x, y, horn[2] if y < 3 else wing[4])
    for x in range(w):
        if (x - front_col) * step % 2 == 1:
            c.clear(x, h - 1)
    c.px(front_col, 0, horn[4])


def _frill(c, expr):
    plate = c.m('plate').r
    if c.face in ('left', 'right'):
        c.fill(plate[2])
        c.px(0, 0, plate[3])
        c.clear(c.w - 1, c.h - 1)


def _horn(c, expr):
    horn = c.m('horn').r
    if c.face != 'bottom':
        c.px(0, 0, horn[4])
        c.px(0, c.h - 1, horn[1])


def _jaw(c, expr):
    if c.face == 'front':
        c.fill(c.m('belly').r[2])


DECO = {
    ('head', 'front'): _head_front,
    ('head_top', 'top'): _head_top,
    ('head_top', 'front'): lambda c, e: c.fill(c.m('body').r[3]),
    ('head', 'left'): _head_side,
    ('head', 'right'): _head_side,
    ('snout', 'front'): _snout_front,
    ('snout', 'top'): _snout_top,
    ('torso', '*'): _torso,
    ('torso_top', 'top'): _torso,
    ('leg', '*'): _leg,
    ('tail', '*'): _tail,
    ('tail2', '*'): _tail,
    ('spade', '*'): _spade,
    ('wing', '*'): _wing,
    ('frill', '*'): _frill,
    ('horn', '*'): _horn,
    ('jaw', '*'): _jaw,
}
DECO.update(BACKPACK_DECO)
