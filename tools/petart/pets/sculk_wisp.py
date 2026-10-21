"""Sculk Wisp: floating sculk ghost with glowing cyan spots, glowing eyes and two sensor tendrils."""
from rig import Bone, box
from paint import Mat, eyes, hx
from pets.common import backpack_back, backpack_mats, BACKPACK_DECO, shape

NAME = 'sculk_wisp'
PREVIEW_SCALE = 0.8
FACE_Y = 0.9

BODY = (-3.5, -7, -3.5, 7, 7, 7)
GLOW, GLOW_P, GLOW_D = hx('#2EE6F0'), hx('#9CF7FA'), hx('#1BA5B4')


def mats():
    m = {
        'sculk': Mat('#123542', 'smooth', 0.06),
        'deep': Mat('#0B2129', 'smooth', 0.04),
        'tendril': Mat('#1B4A57', 'none'),
    }
    m.update(backpack_mats())
    return m


def rig():
    body = Bone('body', (0, 14, 0))
    body.add(box(*BODY, 'sculk', 'torso'))
    body.add(box(-2.5, -8, -2.5, 5, 1, 5, 'sculk', 'torso_top'))
    body.add(box(-2.5, 0, -2.5, 5, 2, 5, 'deep', 'skirt'))

    # the wisp's face is part of the body blob; 'head' only carries the eyes plane offsets for look-at
    head = Bone('head', (0, -4, -3.5))
    head.add(box(-3, -2, -0.1, 6, 4, 0, 'sculk', 'face', faces=('front',)))
    body.add(head)

    for side, x, rz in (('l', 2.5, 18), ('r', -2.5, -18)):
        t = Bone('antenna_' + side, (x, -8, 0), (-15, 0, rz)).add(box(-0.5, -3, -0.5, 1, 3, 1, 'tendril', 'tendril'))
        t.add(Bone('bulb_' + side, (0, -3, 0)).add(box(-1, -2, -1, 2, 2, 2, 'tendril', 'bulb')))
        body.add(t)

    arm_l = Bone('arm_l', (3.5, -3, 0), (0, 0, -20)).add(box(0, 0, -1, 1, 3, 2, 'sculk', 'arm'))
    arm_r = Bone('arm_r', (-3.5, -3, 0), (0, 0, 20)).add(box(-1, 0, -1, 1, 3, 2, 'sculk', 'arm'))
    body.add(arm_l, arm_r)

    tail = Bone('tail', (0, 2, 0.5), (20, 0, 0)).add(box(-1.5, 0, -1.5, 3, 3, 3, 'deep', 'tail'))
    tail2 = Bone('tail2', (0, 3, 0), (25, 0, 0)).add(box(-1, 0, -1, 2, 2, 2, 'deep', 'tail2'))
    tail3 = Bone('tail3', (0, 2, 0), (25, 0, 0)).add(box(-0.5, 0, -0.5, 1, 2, 1, 'deep', 'tail3'))
    tail2.add(tail3)
    tail.add(tail2)
    body.add(tail, backpack_back((0, -3.5, 3.5), BODY, (-4,)))
    return [body]


def _spots(c, pts):
    for (x, y) in pts:
        if c.inside(x, y):
            c.px(x, y, GLOW_D)
            c.glow(x, y, GLOW, 230)


def _torso(c, expr):
    deep = c.m('deep').r
    if c.face == 'front':
        # face lives on the face plane; body front gets a soft lower mouth glow
        if expr in ('happy', 'love'):
            c.hline(3, 3, 5, GLOW_D)
            c.glow(3, 5, GLOW, 200)
        else:
            c.px(3, 5, deep[0])
        _spots(c, [(0, 1), (6, 1)])
    elif c.face in ('left', 'right'):
        _spots(c, [(1, 1), (4, 2), (2, 4), (5, 5), (3, 3)])
    elif c.face == 'back':
        _spots(c, [(1, 2), (5, 1), (3, 4), (2, 6), (5, 5)])
    elif c.face == 'top':
        _spots(c, [(1, 1), (5, 2), (3, 5)])


def _face(c, expr):
    # transparent plane carrying only the eyes, so expressions don't need body pixels
    for y in range(c.h):
        for x in range(c.w):
            c.clear(x, y)
    eyes(c, 0, expr, gap=2, size=(2, 3), x=0, iris=GLOW, glow=GLOW_P, lid=(10, 30, 36), highlight=False)
    if expr in ('normal', 'angry', 'sad'):
        for x0 in (0, 4):
            c.px(x0, 0, (240, 255, 255))
            c.glow(x0, 0, (240, 255, 255))


def _bulb(c, expr):
    c.fill(GLOW_D)
    for y in range(c.h):
        for x in range(c.w):
            c.glow(x, y, GLOW if (x + y) % 2 == 0 else GLOW_P, 255)


def _tail(c, expr):
    if c.face in ('left', 'right', 'back', 'front'):
        _spots(c, [(1, 1)])


DECO = {
    ('torso', '*'): _torso,
    ('face', '*'): _face,
    ('bulb', '*'): _bulb,
    ('tail', '*'): _tail,
    ('skirt', 'front'): lambda c, e: _spots(c, [(1, 0), (3, 1)]),
    ('skirt', 'left'): lambda c, e: _spots(c, [(2, 1)]),
    ('skirt', 'right'): lambda c, e: _spots(c, [(2, 0)]),
}
DECO.update(BACKPACK_DECO)
