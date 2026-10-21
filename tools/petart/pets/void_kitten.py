"""Void Kitten: starry purple-black kitten with glowing magenta eyes and an ender pearl on its tail."""
from rig import Bone, box
from paint import Mat, eyes, hx
from pets.common import backpack, backpack_mats, BACKPACK_DECO, shape

NAME = 'void_kitten'
PREVIEW_SCALE = 0.8
FACE_Y = 0.55

TORSO = (-2.5, -2, -4.5, 5, 5, 9)
STAR, MAG, MAG_D, PINK = hx('#F4E9FF'), hx('#E05BFF'), hx('#9B2FC9'), hx('#F29BD2')
PEARL, PEARL_L, PEARL_D = hx('#2EB8A6'), hx('#8FF2DF'), hx('#16655E')


def mats():
    m = {
        'fur': Mat('#2E1C47', 'fur', 0.05),
        'plum': Mat('#53357A', 'fur', 0.04),
        'pearl': Mat('#2EB8A6', 'none', flat=True),
    }
    m.update(backpack_mats())
    return m


def rig():
    body = Bone('body', (0, 17, 0))
    body.add(box(*TORSO, 'fur', 'torso'))
    body.add(box(-1.5, -3, -3.5, 3, 1, 7, 'fur', 'torso_top'))

    head = Bone('head', (0, -1, -4.5))
    head.add(box(-3.5, -5, -5, 7, 6, 6, 'fur', 'head'))
    head.add(box(-2.5, -6, -4, 5, 1, 4, 'fur', 'head_top'))
    head.add(box(-1.5, -1, -6, 3, 2, 1, 'plum', 'muzzle'))
    ear_l = Bone('ear_l', (2, -6, -2.5), (-5, 0, 12)).add(box(-1.5, -2, -0.5, 3, 2, 1, 'fur', 'ear'))
    ear_r = Bone('ear_r', (-2, -6, -2.5), (-5, 0, -12)).add(box(-1.5, -2, -0.5, 3, 2, 1, 'fur', 'ear'))
    head.add(ear_l, ear_r)

    tail = Bone('tail', (0, -1.5, 4.5), (-55, 0, 0)).add(box(-1, -1, 0, 2, 2, 5, 'fur', 'tail'))
    tail2 = Bone('tail2', (0, 0, 5), (40, 0, 0)).add(box(-1, -1, 0, 2, 2, 4, 'fur', 'tail2'))
    orb = Bone('tail3', (0, 0, 4)).add(box(-1.5, -1.5, 0, 3, 3, 3, 'pearl', 'orb'))
    tail2.add(orb)
    tail.add(tail2)

    body.add(head, tail, backpack((0, -2, 1), TORSO, (-1, 2.5), w=5, h=4, d=4))

    legs = []
    for name, x, z in (('leg_fr', -1.5, -3), ('leg_fl', 1.5, -3), ('leg_br', -1.5, 3.5), ('leg_bl', 1.5, 3.5)):
        legs.append(Bone(name, (x, 20, z)).add(box(-1, 0, -1, 2, 4, 2, 'fur', 'leg')))
    return [body] + legs


def _stars(c, pts):
    for (x, y) in pts:
        if c.inside(x, y):
            c.px(x, y, STAR)
            c.glow(x, y, STAR, 200)


def _head_front(c, expr):
    fur = c.m('fur').r
    eyes(c, 2, expr, gap=1, size=(2, 2), iris=MAG, glow=MAG, lid=fur[0], highlight=False)
    if expr in ('normal', 'angry', 'sad'):
        for x0 in (1, 4):
            c.px(x0, 2, (255, 230, 255))
            c.glow(x0, 2, (255, 230, 255))
            c.px(x0 + 1, 3, (60, 10, 80))       # slit pupil
            c.glow(x0 + 1, 3, (60, 10, 80), 0)
    if expr not in ('angry',):
        c.px(0, 4, PINK)
        c.px(6, 4, PINK)
    _stars(c, [(3, 0)])


def _muzzle(c, expr):
    if c.face == 'front':
        c.px(1, 0, PINK)
        if expr in ('happy', 'love'):
            c.px(0, 1, (30, 16, 40))
            c.px(2, 1, (30, 16, 40))
        else:
            c.px(1, 1, (30, 16, 40))


def _ear(c, expr):
    fur = c.m('fur').r
    if c.face in ('front', 'back'):
        shape(c, ['.X.', 'XXX'], {'X': fur[2]})
        c.px(1, 0, fur[3])
        if c.face == 'front':
            c.px(1, 1, PINK)
    elif c.face in ('left', 'right'):
        c.clear(0, 0)
    elif c.face == 'top':
        c.clear(0, 0)
        c.clear(2, 0)


def _torso(c, expr):
    plum = c.m('plum').r
    if c.face in ('left', 'right'):
        _stars(c, [(1, 1), (5, 2), (7, 0), (3, 3)])
    elif c.face == 'top':
        _stars(c, [(1, 2), (3, 6)])
    elif c.face == 'front':
        c.rect(1, 1, c.w - 2, c.h - 1, plum[2])
    elif c.face == 'bottom':
        c.fill(plum[1])


def _orb(c, expr):
    c.fill(PEARL)
    c.px(1, 1, PEARL_D)
    c.px(0, 0, PEARL_L)
    for y in range(c.h):
        for x in range(c.w):
            c.glow(x, y, PEARL_L if (x, y) == (0, 0) else PEARL, 150)


def _leg(c, expr):
    if c.face == 'front':
        c.hline(0, 1, c.h - 1, c.m('plum').r[3])
    elif c.face == 'bottom':
        c.fill(PINK)


DECO = {
    ('head', 'front'): _head_front,
    ('head', 'left'): lambda c, e: _stars(c, [(2, 1)]),
    ('head', 'right'): lambda c, e: _stars(c, [(3, 2)]),
    ('muzzle', '*'): _muzzle,
    ('ear', '*'): _ear,
    ('torso', '*'): _torso,
    ('orb', '*'): _orb,
    ('leg', '*'): _leg,
    ('tail', 'left'): lambda c, e: _stars(c, [(2, 0)]),
    ('tail2', 'right'): lambda c, e: _stars(c, [(1, 1)]),
}
DECO.update(BACKPACK_DECO)
