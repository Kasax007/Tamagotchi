"""Pebble Golem: round mossy boulder buddy with a sprout, stubby arms and legs and ore flecks."""
from rig import Bone, box
from paint import Mat, eyes, hx
from pets.common import backpack_back, backpack_mats, BACKPACK_DECO, leaf_plane

NAME = 'pebble_golem'
PREVIEW_SCALE = 0.8
FACE_Y = 0.6

BODY = (-4, -8, -3.5, 8, 8, 7)
MOSS, MOSS_L, MOSS_D = hx('#6E9A3A'), hx('#93C255'), hx('#4A7028')
DIAMOND, GOLD, RED = hx('#5FE3E0'), hx('#F2C94C'), hx('#E0473C')
BLUSH = (236, 150, 150)
L_LIGHT, L_MID, L_DARK = hx('#B4EA6A'), hx('#86CF4E'), hx('#3E8A2E')


def mats():
    m = {
        'stone': Mat('#8E8E92', 'stone', 0.0),
        'stone_d': Mat('#6A6A70', 'stone', 0.0),
        'moss': Mat('#6E9A3A', 'smooth', 0.1),
        'leaf': Mat('#86CF4E', 'none'),
    }
    m.update(backpack_mats())
    return m


def rig():
    body = Bone('body', (0, 22, 0))
    body.add(box(*BODY, 'stone', 'torso'))
    body.add(box(-3, -9, -2.5, 6, 1, 5, 'moss', 'torso_top'))
    body.add(box(-3, 0, -2.5, 6, 1, 5, 'stone_d', 'torso_bottom'))

    # the face is the front of the boulder; 'head' carries the sprout so it bobs with "looking"
    head = Bone('head', (0, -9, 0))
    sprout = Bone('sprout', (0, 0, 0))
    sprout.add(box(-0.5, -2, -0.5, 1, 2, 1, 'leaf', 'stem'))
    sprout.add(Bone('sprout_l', (0.5, -2, 0), (0, 0, -35)).add(box(0, 0, -1, 3, 0, 2, 'leaf', 'sprout_leaf', faces=('top', 'bottom'))))
    sprout.add(Bone('sprout_r', (-0.5, -2, 0), (0, 0, 35)).add(box(-3, 0, -1, 3, 0, 2, 'leaf', 'sprout_leaf_r', faces=('top', 'bottom'))))
    head.add(sprout)
    body.add(head)

    arm_l = Bone('arm_l', (4, -5, 0), (0, 0, -8)).add(box(0, 0, -1, 2, 4, 2, 'stone_d', 'arm'))
    arm_r = Bone('arm_r', (-4, -5, 0), (0, 0, 8)).add(box(-2, 0, -1, 2, 4, 2, 'stone_d', 'arm'))
    crystal = Bone('crystal', (1.5, -6, 3.5), (25, 0, 20)).add(box(-0.5, -3, -0.5, 1, 3, 1, 'stone', 'crystal'),
                                                                box(1, -2, 0, 1, 2, 1, 'stone', 'crystal'))
    body.add(arm_l, arm_r, crystal, backpack_back((-1.5, -4, 3.5), BODY, (-5,), w=5, h=5, d=3))

    legs = []
    for name, x in (('leg_l', 2), ('leg_r', -2)):
        legs.append(Bone(name, (x, 22, 0)).add(box(-1.5, 0, -1.5, 3, 2, 3, 'stone_d', 'leg')))
    return [body] + legs


def _torso(c, expr):
    stone = c.m('stone').r
    if c.face == 'front':
        eyes(c, 2, expr, gap=2, size=(2, 3), iris=(70, 90, 120), lid=stone[0], pupil=(30, 32, 40))
        if expr not in ('angry', 'sleep'):
            c.px(1, 5, BLUSH)
            c.px(6, 5, BLUSH)
        if expr in ('happy', 'love'):
            c.hline(3, 4, 6, (60, 40, 40))
        else:
            c.px(3, 6, (60, 40, 40))
            c.px(4, 6, (60, 40, 40))
        # moss drips over the brow
        c.hline(0, c.w - 1, 0, MOSS)
        for x in (0, 2, 5, 7):
            c.px(x, 1, MOSS_D)
    elif c.face in ('left', 'right'):
        c.hline(0, c.w - 1, 0, MOSS)
        c.px(1, 1, MOSS_D)
        c.px(4, 1, MOSS_D)
        c.px(2, 4, DIAMOND)
        c.px(3, 4, (180, 250, 250))
        c.px(5, 6, GOLD)
    elif c.face == 'back':
        c.hline(0, c.w - 1, 0, MOSS)
        c.px(2, 1, MOSS_D)
        c.px(6, 6, RED)
    elif c.face == 'top':
        c.fill(MOSS)


def _moss_top(c, expr):
    if c.face == 'top':
        c.fill(MOSS)
        for (x, y) in ((1, 1), (4, 2), (2, 3), (5, 0)):
            if c.inside(x, y):
                c.px(x, y, MOSS_L)
        c.px(3, 1, (255, 230, 120))     # tiny flower
    elif c.face != 'bottom':
        c.fill(MOSS)
        c.px(0, 0, MOSS_L)


def _crystal(c, expr):
    c.fill(hx('#9A6BD8'))
    if c.face in ('front', 'left', 'top'):
        c.px(0, 0, hx('#D8B8FF'))
    c.glow(0, 0, hx('#C9A3FF'), 140)


def _arm(c, expr):
    if c.face == 'bottom':
        c.fill(c.m('stone_d').r[1])


DECO = {
    ('torso', '*'): _torso,
    ('torso_top', '*'): _moss_top,
    ('stem', '*'): lambda c, e: c.fill(L_MID),
    ('sprout_leaf', '*'): lambda c, e: leaf_plane(c, 'right', L_LIGHT, L_MID, L_DARK),
    ('sprout_leaf_r', '*'): lambda c, e: leaf_plane(c, 'left', L_LIGHT, L_MID, L_DARK),
    ('crystal', '*'): _crystal,
    ('arm', '*'): _arm,
}
DECO.update(BACKPACK_DECO)
