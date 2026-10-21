"""Frost Penguin: round navy penguin chick with a white face, orange beak/feet and a red knitted scarf."""
from rig import Bone, box
from paint import Mat, eyes, hx
from pets.common import backpack_back, backpack_mats, BACKPACK_DECO, shape

NAME = 'frost_penguin'
PREVIEW_SCALE = 0.8
FACE_Y = 0.75

BODY = (-4, -7, -3.5, 8, 7, 7)
WHITE, WHITE_S = hx('#F4F6FA'), hx('#CBD5E6')
SCARF, SCARF_D, SCARF_L = hx('#D9433F'), hx('#A52A35'), hx('#F07B63')
BLUSH = (246, 160, 176)


def mats():
    m = {
        'navy': Mat('#2F3D5C', 'smooth', 0.03),
        'white': Mat('#F1F4F9', 'smooth', 0.0),
        'beak': Mat('#F2A23A', 'none'),
        'scarf': Mat('#D9433F', 'none'),
    }
    m.update(backpack_mats())
    return m


def rig():
    body = Bone('body', (0, 22, 0))
    body.add(box(*BODY, 'navy', 'torso'))
    body.add(box(-3, -1, -3, 6, 1, 6, 'navy', 'torso_bottom', inflate=0.01))
    body.add(box(-4, -7, -3.5, 8, 2, 7, 'scarf', 'scarf', inflate=0.3))

    head = Bone('head', (0, -7, 0))
    head.add(box(-4, -6, -3.5, 8, 6, 7, 'navy', 'head'))
    head.add(box(-3, -7, -2.5, 6, 1, 5, 'navy', 'head_top'))
    head.add(box(-1, -2, -5.5, 2, 1, 2, 'beak', 'beak'))

    scarf_tail = Bone('scarf_tail', (2.5, -6, -3.6), (8, 0, -6)).add(box(-1, 0, -1, 2, 5, 1, 'scarf', 'scarf_tail'))
    arm_l = Bone('arm_l', (4, -6, 0), (0, 0, -12)).add(box(0, 0, -1.5, 1, 5, 3, 'navy', 'flipper'))
    arm_r = Bone('arm_r', (-4, -6, 0), (0, 0, 12)).add(box(-1, 0, -1.5, 1, 5, 3, 'navy', 'flipper'))
    tail = Bone('tail', (0, -1, 3.5), (-25, 0, 0)).add(box(-1.5, -1, 0, 3, 1, 2, 'navy', 'tailfeather'))

    body.add(head, scarf_tail, arm_l, arm_r, tail, backpack_back((0, -3.5, 3.5), BODY, (-4,)))

    legs = []
    for name, x in (('leg_l', 2), ('leg_r', -2)):
        legs.append(Bone(name, (x, 22, -0.5)).add(box(-1, 0, -1, 2, 1, 2, 'beak', 'leg'),
                                                   box(-1.5, 1, -2.5, 3, 1, 3, 'beak', 'foot')))
    return [body] + legs


def _head_front(c, expr):
    # white heart-shaped face with navy cap
    navy = c.m('navy').r
    shape(c, ['nnnnnnnn',
              'nWWnnWWn',
              'WWWWWWWW',
              'WWWWWWWW',
              'WWWWWWWW',
              'nWWWWWWn'], {'W': WHITE, 'n': navy[2]})
    c.hline(0, 7, 0, navy[3])
    eyes(c, 2, expr, gap=2, size=(2, 2), iris=(30, 34, 58), lid=navy[1], pupil=(30, 34, 58), highlight=False)
    if expr not in ('angry', 'sleep'):
        c.px(1, 4, BLUSH)
        c.px(6, 4, BLUSH)


def _torso(c, expr):
    navy = c.m('navy').r
    if c.face == 'front':
        shape(c, ['.WWWWWW.',
                  'WWWWWWWW',
                  'WWWWWWWW',
                  'WWWWWWWW',
                  'WWWWWWWW',
                  'WWWWWWWW',
                  '.WWWWWW.'], {'W': WHITE})
        for (x, y) in ((0, 0), (7, 0), (0, 6), (7, 6)):
            c.px(x, y, navy[2])
        c.hline(1, 6, 6, WHITE_S)
        c.px(1, 5, WHITE_S)
        c.px(6, 5, WHITE_S)
    elif c.face in ('left', 'right'):
        # white belly wraps a little around the front edge
        edge = c.w - 1 if c.face == 'right' else 0
        for y in range(1, c.h - 1):
            c.px(edge, y, WHITE_S)
    elif c.face == 'bottom':
        c.fill(WHITE_S)


def _scarf(c, expr):
    c.fill(SCARF)
    if c.face in ('front', 'back', 'left', 'right'):
        c.hline(0, c.w - 1, 0, SCARF_L)
        c.hline(0, c.w - 1, c.h - 1, SCARF_D)
        for x in range(0, c.w, 2):          # knitted texture
            c.px(x, 0, SCARF)
    elif c.face == 'top':
        c.fill(SCARF_L)


def _scarf_tail(c, expr):
    c.fill(SCARF)
    if c.face in ('front', 'back'):
        c.hline(0, c.w - 1, 1, WHITE)
        c.hline(0, c.w - 1, 3, WHITE)
        c.px(0, c.h - 1, SCARF_D)
        c.px(c.w - 1, c.h - 1, SCARF_D)


def _flipper(c, expr):
    navy = c.m('navy').r
    if c.face in ('left', 'right'):
        c.px(0, c.h - 1, None)
        c.clear(0 if c.face == 'right' else c.w - 1, c.h - 1)
    if c.face == 'right' and c.w == 3:
        pass
    if c.face == 'bottom':
        c.fill(WHITE_S)


def _beak(c, expr):
    b = c.m('beak').r
    if c.face == 'front':
        c.fill(b[2])
        c.px(0, 0, b[3])
        if expr in ('happy', 'love'):
            c.px(1, 0, (160, 60, 50))
    elif c.face == 'top':
        c.fill(b[3])


def _foot(c, expr):
    b = c.m('beak').r
    if c.face == 'top':
        c.fill(b[3])
        c.px(1, 0, b[2])
    elif c.face == 'front':
        c.fill(b[2])
        c.px(1, 0, b[1])


def _tuft(c, expr):
    navy = c.m('navy').r
    shape(c, ['X.', 'XX'], {'X': navy[3]})


DECO = {
    ('head', 'front'): _head_front,
    ('torso', '*'): _torso,
    ('scarf', '*'): _scarf,
    ('scarf_tail', '*'): _scarf_tail,
    ('flipper', '*'): _flipper,
    ('beak', '*'): _beak,
    ('foot', '*'): _foot,
    ('torso_bottom', 'bottom'): lambda c, e: c.fill(WHITE_S),
    ('torso_bottom', 'front'): lambda c, e: c.fill(WHITE_S),
}
DECO.update(BACKPACK_DECO)
