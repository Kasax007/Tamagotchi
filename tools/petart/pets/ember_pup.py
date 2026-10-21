"""Ember Pup: basalt hound with glowing lava cracks, glowing eyes and a flame-tipped tail."""
from rig import Bone, box
from paint import Mat, eyes, hx
from pets.common import backpack, backpack_mats, BACKPACK_DECO, shape

NAME = 'ember_pup'
PREVIEW_SCALE = 0.8
FACE_Y = 0.62

TORSO = (-3, -3, -5, 6, 6, 10)
LAVA, LAVA_Y, LAVA_D = hx('#FF8A2A'), hx('#FFD44A'), hx('#C4481C')


def mats():
    m = {
        'basalt': Mat('#3A2E2C', 'stone', 0.0),
        'ash': Mat('#5A4844', 'smooth', 0.03),
        'flame': Mat('#FF8A2A', 'none', flat=True),
    }
    m.update(backpack_mats())
    return m


def rig():
    body = Bone('body', (0, 16, 0))
    body.add(box(*TORSO, 'basalt', 'torso'))
    body.add(box(-2, -4, -4, 4, 1, 8, 'basalt', 'torso_top'))
    for z, hgt in ((-3, 2), (0, 3), (3, 2)):
        body.add(box(-0.5, -4 - hgt, z - 1, 1, hgt, 2, 'basalt', 'shard'))

    head = Bone('head', (0, -2, -5))
    head.add(box(-3.5, -5, -5, 7, 6, 6, 'basalt', 'head'))
    head.add(box(-2.5, -6, -4, 5, 1, 4, 'basalt', 'head_top'))
    head.add(box(-1.5, -2, -8, 3, 2, 3, 'ash', 'muzzle'))
    jaw = Bone('jaw', (0, 0, -5)).add(box(-1.5, 0, -3, 3, 1, 3, 'ash', 'jaw'))
    ear_l = Bone('ear_l', (2, -5, -2.5), (-10, 0, 12)).add(box(-1, -4, -0.5, 2, 4, 1, 'basalt', 'ear'))
    ear_r = Bone('ear_r', (-2, -5, -2.5), (-10, 0, -12)).add(box(-1, -4, -0.5, 2, 4, 1, 'basalt', 'ear'))
    head.add(jaw, ear_l, ear_r)

    tail = Bone('tail', (0, -2, 5), (35, 0, 0)).add(box(-1, -1, 0, 2, 2, 5, 'basalt', 'tail'))
    tail2 = Bone('tail2', (0, 0, 5), (-20, 0, 0)).add(box(-1, -1, 0, 2, 2, 3, 'basalt', 'tail2'))
    flame = Bone('tail3', (0, 0, 3))
    flame.add(box(-2.5, -4, 0, 5, 5, 0, 'flame', 'flame_a', faces=('front', 'back')))
    flame.add(box(0, -4, -2.5, 0, 5, 5, 'flame', 'flame_b', faces=('right', 'left')))
    tail2.add(flame)
    tail.add(tail2)

    body.add(head, tail, backpack((0, -3, 1.5), TORSO, (-1, 3)))

    legs = []
    for name, x, z in (('leg_fr', -1.75, -3.5), ('leg_fl', 1.75, -3.5), ('leg_br', -1.75, 3.5), ('leg_bl', 1.75, 3.5)):
        legs.append(Bone(name, (x, 19, z)).add(box(-1, 0, -1, 2, 5, 2, 'basalt', 'leg')))
    return [body] + legs


def _crack(c, pts):
    for (x, y) in pts:
        if c.inside(x, y):
            col = LAVA_Y if (x + y) % 3 == 0 else LAVA
            c.px(x, y, col)
            c.glow(x, y, col, 235)


def _head_front(c, expr):
    eyes(c, 2, expr, gap=1, size=(2, 2), iris=LAVA, glow=LAVA_Y, lid=(20, 14, 14), highlight=False)
    if expr in ('normal', 'angry', 'sad'):
        for x0 in (1, 4):
            c.px(x0, 2, (255, 246, 200))
            c.glow(x0, 2, (255, 246, 200))
    _crack(c, [(3, 0), (3, 1)])


def _muzzle(c, expr):
    if c.face == 'front':
        c.px(1, 0, (24, 18, 18))
        c.px(0, 0, (24, 18, 18))
        c.px(2, 0, (24, 18, 18))
        if expr in ('happy', 'love'):
            c.px(1, 1, (220, 70, 60))
            c.glow(1, 1, LAVA, 160)
    elif c.face == 'top':
        c.px(1, c.h - 1, (24, 18, 18))


def _torso(c, expr):
    ash = c.m('ash').r
    if c.face in ('left', 'right'):
        _crack(c, [(1, 1), (2, 2), (3, 2), (4, 3), (6, 1), (7, 2), (7, 3), (8, 4)])
        c.hline(1, c.w - 2, c.h - 1, ash[1])
    elif c.face == 'front':
        c.rect(1, 2, c.w - 2, c.h - 1, ash[2])
        _crack(c, [(2, 3), (3, 4)])
    elif c.face == 'bottom':
        c.fill(ash[1])
    elif c.face == 'top':
        _crack(c, [(2, 1), (3, 2), (2, 5), (3, 6), (2, 8)])


def _shard(c, expr):
    if c.face == 'top':
        c.px(0, 0, LAVA)
        c.glow(0, 0, LAVA, 200)


def _ear(c, expr):
    if c.face == 'front':
        shape(c, ['.X', 'XX', 'XX', 'XX'] if False else ['X.', 'XX', 'XX', 'XX'], {})
        c.px(0, 1, LAVA_D)
        c.px(0, 2, LAVA)
        c.glow(0, 2, LAVA, 200)
        c.px(1, 2, LAVA_D)
    elif c.face in ('left', 'right', 'back'):
        c.clear(c.w - 1 if c.face == 'back' else 0, 0)


def _leg(c, expr):
    if c.face == 'bottom':
        c.fill(LAVA)
        c.glow(0, 0, LAVA, 200)
        c.glow(1, 1, LAVA, 200)
    elif c.face == 'front':
        c.hline(0, 1, c.h - 1, LAVA_D)
        c.glow(0, c.h - 1, LAVA, 160)
        c.glow(1, c.h - 1, LAVA, 160)


def _tail(c, expr):
    if c.face in ('left', 'right'):
        _crack(c, [(1, 1), (3, 0)])


def _flame(c, expr):
    rows = ['..Y..',
            '.YYO.',
            '.YOO.',
            'OOODO',
            '.ODD.']
    cmap = {'Y': LAVA_Y, 'O': LAVA, 'D': LAVA_D}
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == '.':
                c.clear(x, y)
            else:
                c.px(x, y, cmap[ch])
                c.glow(x, y, cmap[ch], 255)


DECO = {
    ('head', 'front'): _head_front,
    ('head', 'left'): lambda c, e: _crack(c, [(1, 3), (2, 4)]),
    ('head', 'right'): lambda c, e: _crack(c, [(4, 3), (3, 4)]),
    ('muzzle', '*'): _muzzle,
    ('torso', '*'): _torso,
    ('shard', '*'): _shard,
    ('ear', '*'): _ear,
    ('leg', '*'): _leg,
    ('tail', '*'): _tail,
    ('flame_a', '*'): _flame,
    ('flame_b', '*'): _flame,
    ('jaw', 'front'): lambda c, e: c.fill(c.m('ash').r[1]),
}
DECO.update(BACKPACK_DECO)
