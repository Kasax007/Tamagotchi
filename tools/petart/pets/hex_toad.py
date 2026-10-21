"""Hex Toad: chubby swamp toad with bulging golden eyes, warts and a tiny purple witch hat."""
from rig import Bone, box
from paint import Mat, eyes, hx
from pets.common import backpack, backpack_mats, BACKPACK_DECO, shape

NAME = 'hex_toad'
PREVIEW_SCALE = 0.8
FACE_Y = 0.45
PREVIEW_HIDDEN = ('tongue',)

TORSO = (-4, -4, -2, 8, 4, 7)
WART, WART_L = hx('#4D6A2C'), hx('#8FB25A')
HAT, HAT_L, HAT_D, BAND, BUCKLE = hx('#5B3A82'), hx('#7B57A8'), hx('#3B2556'), hx('#2A1B3D'), hx('#E8C04A')
BELLY = hx('#E3D58A')
BLUSH = (236, 140, 120)


def mats():
    m = {
        'skin': Mat('#6E8F3E', 'smooth', 0.05),
        'belly': Mat('#E3D58A', 'smooth', 0.03),
        'hat': Mat('#5B3A82', 'none'),
        'tongue': Mat('#E8708A', 'none', flat=True),
    }
    m.update(backpack_mats())
    return m


def rig():
    body = Bone('body', (0, 22, 0))
    body.add(box(*TORSO, 'skin', 'torso'))
    body.add(box(-3, -5, -1, 6, 1, 5, 'skin', 'torso_top'))

    head = Bone('head', (0, -3, -2))
    head.add(box(-4, -3, -5, 8, 4, 5, 'skin', 'head'))
    head.add(box(-4, -5, -4.5, 3, 2, 3, 'skin', 'eye_bump'))
    head.add(box(1, -5, -4.5, 3, 2, 3, 'skin', 'eye_bump_l'))
    tongue = Bone('tongue', (0, 0.5, -5)).add(box(-1, 0, -6, 2, 1, 6, 'tongue', 'tongue'))
    hat = Bone('hat', (0, -3, -1), (-8, 0, 6))
    hat.add(box(-3.5, 0, -3.5, 7, 0, 7, 'hat', 'brim', faces=('top', 'bottom')))
    hat.add(box(-2, -2, -2, 4, 2, 4, 'hat', 'cone1'))
    hat.add(box(-1.5, -3, -1.5, 3, 1, 3, 'hat', 'cone2'))
    tip = Bone('hat_tip', (0, -3, 0), (-30, 0, 10)).add(box(-1, -2, -1, 2, 2, 2, 'hat', 'cone3'))
    hat.add(tip)
    head.add(tongue, hat)

    body.add(head, backpack((0, -4, 2.5), TORSO, (1, 3.5), w=6, h=4, d=4))

    legs = []
    for name, x in (('leg_fl', 3), ('leg_fr', -3)):
        legs.append(Bone(name, (x, 20, -5)).add(box(-1, 0, -1, 2, 4, 2, 'skin', 'arm')))
    for name, x, sx in (('leg_bl', 4, 0), ('leg_br', -4, -3)):
        legs.append(Bone(name, (x, 21, 2)).add(box(sx, -3, -3, 3, 4, 5, 'skin', 'haunch'),
                                                box(sx, 2, -5, 3, 1, 3, 'skin', 'foot')))
    return [body] + legs


def _warts(c, pts):
    for (x, y) in pts:
        if c.inside(x, y):
            c.px(x, y, WART)
            if c.inside(x, y - 1):
                c.px(x, y - 1, WART_L)


def _head(c, expr):
    skin = c.m('skin').r
    if c.face == 'front':
        # wide happy mouth line + belly-coloured chin
        c.hline(0, c.w - 1, c.h - 1, BELLY)
        mouth = (70, 40, 40)
        if expr in ('happy', 'love'):
            c.hline(1, c.w - 2, 2, mouth)
            c.px(3, 3, (200, 80, 90))
            c.px(4, 3, (200, 80, 90))
        elif expr == 'sad':
            c.hline(2, c.w - 3, 2, mouth)
            c.px(1, 3, mouth)
            c.px(c.w - 2, 3, mouth)
        else:
            c.hline(1, c.w - 2, 2, mouth)
            c.px(0, 1, mouth)
            c.px(c.w - 1, 1, mouth)
        if expr not in ('angry',):
            c.px(0, 0, BLUSH)
            c.px(c.w - 1, 0, BLUSH)
        c.px(3, 0, skin[0])
        c.px(4, 0, skin[0])
    elif c.face == 'top':
        _warts(c, [(1, 1), (6, 3), (3, 4)])
    elif c.face in ('left', 'right'):
        _warts(c, [(1, 2), (3, 1)])
    elif c.face == 'bottom':
        c.fill(BELLY)


def _eye_bump(c, expr, side):
    if c.face == 'front':
        c.fill(c.m('skin').r[3])
        # big round golden eye filling the bump front (3x2)
        if expr in ('normal', 'angry', 'sad'):
            c.hline(0, 2, 0, hx('#F2C94C'))
            c.hline(0, 2, 1, hx('#D9A42E'))
            c.px(1, 0, (30, 24, 20))
            c.px(1, 1, (30, 24, 20))
            c.px(0, 0, (255, 255, 240))
            if expr == 'angry':
                c.px(2 if side == 'r' else 0, 0, c.m('skin').r[0])
            if expr == 'sad':
                c.px(0 if side == 'r' else 2, 0, c.m('skin').r[0])
        elif expr in ('blink', 'sleep'):
            c.hline(0, 2, 1, (40, 50, 30))
        elif expr == 'happy':
            c.px(0, 1, (40, 50, 30))
            c.px(1, 0, (40, 50, 30))
            c.px(2, 1, (40, 50, 30))
        elif expr == 'love':
            shape(c, ['R.R', '.R.'], {'R': (230, 50, 90)})
            c.px(0, 0, (230, 50, 90)); c.px(2, 0, (230, 50, 90)); c.px(1, 1, (230, 50, 90))
            c.px(1, 0, c.m('skin').r[3])
            c.glow(1, 1, (255, 90, 130), 160)
    elif c.face == 'top':
        c.fill(c.m('skin').r[3])
        c.px(1, 1, c.m('skin').r[4])


def _torso(c, expr):
    if c.face == 'top':
        _warts(c, [(1, 2), (5, 4), (3, 6), (6, 1)])
    elif c.face in ('left', 'right'):
        _warts(c, [(2, 1), (5, 2)])
        c.hline(0, c.w - 1, c.h - 1, BELLY)
    elif c.face == 'bottom':
        c.fill(BELLY)


def _hat(c, expr):
    c.fill(HAT)
    if c.face == 'top':
        c.fill(HAT_L)
    if c.face in ('front', 'back', 'left', 'right') and c.h >= 2:
        c.hline(0, c.w - 1, c.h - 1, BAND)
        if c.face == 'front':
            c.px(c.w // 2, c.h - 1, BUCKLE)
            c.px(c.w // 2 - 1, c.h - 1, BUCKLE)


def _brim(c, expr):
    shape(c, ['.XXXXX.',
              'XXXXXXX',
              'XXXXXXX',
              'XXXXXXX',
              'XXXXXXX',
              'XXXXXXX',
              '.XXXXX.'], {'X': HAT if c.face == 'top' else HAT_D})
    if c.face == 'top':
        for x in range(1, 6):
            c.px(x, 6, HAT_L)


def _leg(c, expr):
    if c.face == 'bottom':
        c.fill(c.m('skin').r[1])
    elif c.face in ('left', 'right'):
        _warts(c, [(1, 1)])


def _foot(c, expr):
    if c.face == 'top':
        c.fill(c.m('skin').r[3])
        c.px(0, 0, c.m('skin').r[1])
        c.px(2, 0, c.m('skin').r[1])


DECO = {
    ('head', '*'): _head,
    ('eye_bump', '*'): lambda c, e: _eye_bump(c, e, 'r'),
    ('eye_bump_l', '*'): lambda c, e: _eye_bump(c, e, 'l'),
    ('torso', '*'): _torso,
    ('cone1', '*'): _hat,
    ('cone2', '*'): lambda c, e: c.fill(HAT) if c.face != 'top' else c.fill(HAT_L),
    ('cone3', '*'): lambda c, e: c.fill(HAT_L if c.face == 'top' else HAT),
    ('brim', '*'): _brim,
    ('arm', '*'): _leg,
    ('haunch', '*'): _leg,
    ('foot', '*'): _foot,
}
DECO.update(BACKPACK_DECO)
