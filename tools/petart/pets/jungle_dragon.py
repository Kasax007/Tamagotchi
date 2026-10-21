"""Jungle Dragon: leaf-green dragon with a leaf crest, hibiscus flower, leaf wings and a leafy tail tip."""
from rig import Bone, box
from paint import Mat, eyes, hx
from pets.common import backpack, backpack_mats, BACKPACK_DECO, leaf_plane, shape

NAME = 'jungle_dragon'
PREVIEW_SCALE = 0.8
FACE_Y = 0.62

TORSO = (-3, -3, -5, 6, 6, 10)
BLUSH = (236, 140, 150)
PINK, PINK_D, YELLOW = hx('#F06A8C'), hx('#C4436A'), hx('#FFD84A')
L_LIGHT, L_MID, L_DARK, L_VEIN = hx('#B4EA6A'), hx('#8AD452'), hx('#3E8A2E'), hx('#5FAE3E')


def mats():
    m = {
        'body': Mat('#5DAA3C', 'smooth', 0.035),
        'belly': Mat('#CBE27E', 'smooth', 0.03),
        'stripe': Mat('#2F6B2A', 'smooth', 0.0, flat=True),
        'leaf': Mat('#86CF4E', 'none'),
        'claw': Mat('#EFE9C8', 'none', flat=True),
        'flower': Mat('#F06A8C', 'none', flat=True),
    }
    m.update(backpack_mats())
    return m


def rig():
    body = Bone('body', (0, 17, 0))
    body.add(box(*TORSO, 'body', 'torso'))
    body.add(box(-2, -4, -4, 4, 1, 8, 'body', 'torso_top'))
    for z, hgt in ((-3.5, 1), (-0.5, 2), (2.5, 1)):
        body.add(box(-0.5, -4 - hgt, z, 1, hgt, 2, 'leaf', 'spine'))

    head = Bone('head', (0, -2.5, -5))
    head.add(box(-4, -6, -6, 8, 7, 7, 'body', 'head'))
    head.add(box(-3, -7, -5, 6, 1, 5, 'body', 'head_top'))
    head.add(box(-2, -1, -8, 4, 2, 2, 'body', 'snout'))
    jaw = Bone('jaw', (0, 1, -6)).add(box(-2, 0, -2, 4, 1, 2, 'belly', 'jaw'))
    crest = Bone('crest', (0.5, -7, -1))
    crest.add(Bone('sprout_l', (0, 0, 0), (-35, -35, 0)).add(box(-1.5, 0, 0, 3, 0, 5, 'leaf', 'sprout', faces=('top', 'bottom'))))
    crest.add(Bone('sprout_r', (-1, 0, 0), (-35, 35, 0)).add(box(-1.5, 0, 0, 3, 0, 5, 'leaf', 'sprout', faces=('top', 'bottom'))))
    ear_l = Bone('ear_l', (4, -4, -2), (0, 25, -30)).add(box(0, 0, 0, 5, 0, 3, 'leaf', 'ear', faces=('top', 'bottom')))
    ear_r = Bone('ear_r', (-4, -4, -2), (0, -25, 30)).add(box(-5, 0, 0, 5, 0, 3, 'leaf', 'ear_r', faces=('top', 'bottom')))
    flower = Bone('flower', (-3, -7.05, -3), (0, 0, -12)).add(box(-2, 0, -2, 4, 0, 4, 'flower', 'flower', faces=('top', 'bottom')))
    head.add(jaw, crest, ear_l, ear_r, flower)

    wing_l = Bone('wing_l', (2.5, -3, -2), (-10, 0, 62)).add(box(0, -5, 0, 0, 5, 8, 'leaf', 'wing', faces=('right', 'left')))
    wing_r = Bone('wing_r', (-2.5, -3, -2), (-10, 0, -62)).add(box(0, -5, 0, 0, 5, 8, 'leaf', 'wing', faces=('right', 'left')))

    tail = Bone('tail', (0, -1, 5), (-15, 0, 0)).add(box(-1.5, -1.5, 0, 3, 3, 5, 'body', 'tail'))
    tail2 = Bone('tail2', (0, 0, 5), (8, 0, 0)).add(box(-1, -1, 0, 2, 2, 5, 'body', 'tail2'))
    tip = Bone('tail3', (0, 0, 5), (6, 0, 0)).add(box(-2, 0, -0.5, 4, 0, 6, 'leaf', 'tail_leaf', faces=('top', 'bottom')))
    tail2.add(tip)
    tail.add(tail2)

    body.add(head, wing_l, wing_r, tail, backpack((0, -3, 1.5), TORSO, (-1, 3)))

    legs = []
    for name, x, z in (('leg_fr', -2, -3), ('leg_fl', 2, -3), ('leg_br', -2, 3.5), ('leg_bl', 2, 3.5)):
        legs.append(Bone(name, (x, 20, z)).add(box(-1.5, 0, -1.5, 3, 4, 3, 'body', 'leg')))
    return [body] + legs


def _head_front(c, expr):
    body = c.m('body').r
    eyes(c, 2, expr, gap=2, size=(2, 3), iris=hx('#F2C94C'), lid=body[0], pupil=(26, 40, 30))
    if expr != 'angry':
        c.px(1, 5, BLUSH)
        c.px(6, 5, BLUSH)
    # leafy freckles on the forehead
    c.px(3, 0, body[3])
    c.px(4, 1, body[3])


def _snout_front(c, expr):
    body = c.m('body').r
    c.px(0, 0, body[0])
    c.px(3, 0, body[0])
    c.hline(1, 2, 0, body[3])
    if expr in ('happy', 'love'):
        c.hline(1, 2, 1, (176, 64, 80))


def _torso(c, expr):
    belly, body, st = c.m('belly').r, c.m('body').r, c.m('stripe').r
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
        for x in range(1, c.w - 1, 3):     # gecko stripes coming down from the back
            c.px(x, 0, st[2])
            c.px(x, 1, st[2])
            c.px(x + 1, 0, st[2])
        for x in (2, 6):
            c.px(x, 3, body[4])
    elif c.face == 'top':
        for y in range(0, c.h, 3):
            c.hline(0, c.w - 1, y, st[2])


def _spine(c, expr):
    c.fill(L_MID if c.face != 'top' else L_LIGHT)
    if c.face in ('left', 'right'):
        c.px(0, 0, L_LIGHT)


def _sprout(c, expr):
    leaf_plane(c, 'up', L_LIGHT, L_MID, L_DARK, L_VEIN)


def _crest(c, expr):
    leaf_plane(c, 'left' if c.face == 'right' else 'right', L_LIGHT, L_MID, L_DARK, L_VEIN)


def _ear(c, expr):
    leaf_plane(c, 'right', L_LIGHT, L_MID, L_DARK, L_VEIN)


def _ear_r(c, expr):
    leaf_plane(c, 'left', L_LIGHT, L_MID, L_DARK, L_VEIN)


def _flower(c, expr):
    shape(c, ['.PP.',
              'PYyP',
              'PyYD',
              '.DD.'], {'P': PINK, 'Y': YELLOW, 'y': hx('#F5A623'), 'D': PINK_D})


def _wing(c, expr):
    leaf_plane(c, 'left' if c.face == 'right' else 'right', L_LIGHT, L_MID, L_DARK, L_VEIN)


def _tail_leaf(c, expr):
    lf = c.m('leaf').r
    w, h = c.w, c.h   # w = 4 (x), h = 6 (z) on top/bottom faces; tip at row 0 (back) for 'top'
    rows = ['.XX.', '.XX.', 'XXXX', 'XXXX', 'XXXX', '.XX.'] if c.face == 'top' else ['.XX.', 'XXXX', 'XXXX', 'XXXX', '.XX.', '.XX.']
    rows = ['..X.' if c.face == 'top' else '.X..'] + rows[1:]
    for y, row in enumerate(rows[:h]):
        for x, ch in enumerate(row[:w]):
            if ch == '.':
                c.clear(x, y)
            else:
                c.px(x, y, lf[3] if x in (1, 2) else lf[2])
    for y in range(1, h):
        c.px(1 if c.face == 'top' else 2, y, lf[1])


def _leg(c, expr):
    claw, body = c.m('claw').r, c.m('body').r
    if c.face == 'front':
        c.px(0, c.h - 1, claw[2])
        c.px(2, c.h - 1, claw[2])
    elif c.face == 'bottom':
        c.fill(body[1])


def _tail(c, expr):
    st = c.m('stripe').r
    if c.face == 'top':
        for y in range(0, c.h, 2):
            c.hline(0, c.w - 1, y, st[2])
    elif c.face in ('left', 'right'):
        for x in range(0, c.w, 2):
            c.px(x, 0, st[2])


DECO = {
    ('head', 'front'): _head_front,
    ('head_top', 'top'): lambda c, e: [c.px(x, y, c.m('stripe').r[2]) for y in range(c.h) for x in (2, 3) if y % 2 == 0],
    ('snout', 'front'): _snout_front,
    ('snout', 'top'): lambda c, e: c.fill(c.m('body').r[3]),
    ('torso', '*'): _torso,
    ('spine', '*'): _spine,
    ('sprout', '*'): _sprout,
    ('ear', '*'): _ear,
    ('ear_r', '*'): _ear_r,
    ('flower', '*'): _flower,
    ('wing', '*'): _wing,
    ('tail_leaf', '*'): _tail_leaf,
    ('leg', '*'): _leg,
    ('tail', '*'): _tail,
    ('tail2', '*'): _tail,
    ('jaw', 'front'): lambda c, e: c.fill(c.m('belly').r[2]),
}
DECO.update(BACKPACK_DECO)
