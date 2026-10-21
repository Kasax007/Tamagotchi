"""Mimic: a living treasure chest with cute eyes on the lid, teeth at the seam and a pink tongue."""
from rig import Bone, box
from paint import Mat, eyes, hx
from pets.common import backpack_mats, BACKPACK_DECO, GOLD, GOLD_D

NAME = 'mimic'
PREVIEW_SCALE = 0.8
FACE_Y = 0.6

TOOTH, TOOTH_S = hx('#F4F1E6'), hx('#CFC8B4')
TONGUE, TONGUE_D = hx('#E8708A'), hx('#B84863')
MOUTH = hx('#3A1820')


def mats():
    m = {
        'oak': Mat('#A0703C', 'wood', 0.06),
        'dark': Mat('#6B4423', 'wood', 0.04),
        'tooth': Mat('#F4F1E6', 'none', flat=True),
        'tongue': Mat('#E8708A', 'none', flat=True),
        'mouth': Mat('#3A1820', 'none', flat=True),
    }
    m.update(backpack_mats())
    return m


def rig():
    body = Bone('body', (0, 21, 0))
    body.add(box(-5, -6, -4, 10, 6, 8, 'oak', 'base'))
    body.add(box(-4.5, -6.5, -3.5, 9, 0, 7, 'mouth', 'mouth', faces=('top',)))
    for x in (-4, -1, 2):
        body.add(box(x, -7, -4, 2, 1, 1, 'tooth', 'tooth'))
    tongue = Bone('tongue', (0, -6.6, -1)).add(box(-1.5, -0.4, -2.5, 3, 1, 5, 'tongue', 'tongue'))
    body.add(tongue)

    head = Bone('head', (0, -6, 4), (-12, 0, 0))   # lid, hinged at the back, resting a little ajar
    head.add(box(-5, -4, -8, 10, 4, 8, 'oak', 'lid'))
    head.add(box(-4.5, 0.4, -7.5, 9, 0, 7, 'mouth', 'lid_inside', faces=('bottom',)))
    for x in (-2.5, 0.5, 3):
        head.add(box(x - 0.5, 0, -8, 1, 1, 1, 'tooth', 'fang'))
    head.add(box(-1, -1, -8.5, 2, 2, 1, 'oak', 'latch'))
    # mini chest backpack rides on the lid
    from pets.common import backpack
    bp = backpack((0, -4, -4), (-5, -4, -8, 10, 4, 8), (), w=6, h=4, d=4)
    head.add(bp)
    body.add(head)

    legs = []
    for name, x, z in (('leg_fr', -3.5, -2.5), ('leg_fl', 3.5, -2.5), ('leg_br', -3.5, 2.5), ('leg_bl', 3.5, 2.5)):
        legs.append(Bone(name, (x, 21, z)).add(box(-1, 0, -1, 2, 3, 2, 'dark', 'leg')))
    return [body] + legs


def _frame(c):
    dark = c.m('dark').r
    for y in range(c.h):
        c.px(0, y, dark[2])
        c.px(c.w - 1, y, dark[2])


def _base(c, expr):
    dark = c.m('dark').r
    if c.face in ('front', 'back', 'left', 'right'):
        _frame(c)
        c.hline(0, c.w - 1, c.h - 1, dark[1])
        c.px(0, c.h - 1, GOLD_D)
        c.px(c.w - 1, c.h - 1, GOLD_D)
        c.px(0, 0, GOLD)
        c.px(c.w - 1, 0, GOLD)
    if c.face == 'front':
        c.hline(c.w // 2 - 1, c.w // 2, 0, GOLD)
    elif c.face == 'bottom':
        c.fill(dark[1])


def _lid(c, expr):
    dark, oak = c.m('dark').r, c.m('oak').r
    if c.face in ('front', 'back', 'left', 'right'):
        _frame(c)
        c.hline(0, c.w - 1, 0, dark[2])
        c.px(0, c.h - 1, GOLD)
        c.px(c.w - 1, c.h - 1, GOLD)
    if c.face == 'front':
        # cute eyes on the lid
        eyes(c, 0, expr, gap=4, size=(2, 3), iris=hx('#F2B233'), lid=dark[0], pupil=(40, 24, 16))
        if expr not in ('angry', 'sleep'):
            c.px(1, 3, (230, 140, 110))
            c.px(c.w - 2, 3, (230, 140, 110))
    elif c.face == 'top':
        c.fill(oak[3])
        for x in range(c.w):
            c.px(x, 0, dark[2])
            c.px(x, c.h - 1, dark[2])
        for y in range(c.h):
            c.px(0, y, dark[2])
            c.px(c.w - 1, y, dark[2])
        for (x, y) in ((0, 0), (c.w - 1, 0), (0, c.h - 1), (c.w - 1, c.h - 1)):
            c.px(x, y, GOLD)


def _latch(c, expr):
    c.fill(GOLD)
    if c.face == 'front':
        c.px(0, 0, (255, 236, 160))
        c.px(1, 1, GOLD_D)
        c.px(0, 1, (90, 60, 20))    # keyhole


def _tooth(c, expr):
    c.fill(TOOTH)
    if c.face in ('front', 'left', 'right', 'back'):
        c.px(0, c.h - 1, TOOTH_S)


def _tongue(c, expr):
    c.fill(TONGUE)
    if c.face == 'top':
        for y in range(c.h):
            c.px(c.w // 2, y, TONGUE_D)


def _leg(c, expr):
    if c.face == 'bottom':
        c.fill(c.m('dark').r[0])
    elif c.face == 'front':
        c.hline(0, 1, c.h - 1, GOLD_D)


DECO = {
    ('base', '*'): _base,
    ('lid', '*'): _lid,
    ('latch', '*'): _latch,
    ('tooth', '*'): _tooth,
    ('fang', '*'): _tooth,
    ('tongue', '*'): _tongue,
    ('mouth', '*'): lambda c, e: c.fill(MOUTH),
    ('lid_inside', '*'): lambda c, e: c.fill(MOUTH),
    ('leg', '*'): _leg,
}
DECO.update(BACKPACK_DECO)
