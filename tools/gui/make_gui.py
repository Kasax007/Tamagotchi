"""LCD-style icons for the pet screen and the running-wheel texture. Run: python3 tools/gui/make_gui.py"""
import os
from PIL import Image

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TEX = os.path.join(REPO, 'src/main/resources/assets/tamagotchi/textures')
DARK, MID = (46, 58, 33, 255), (125, 145, 96, 255)

ICONS = {
    # 10x10 needs at (index*10, 0)
    (0, 0): ['....XXX...',
             '...XoooX..',
             '..XooooX..',
             '..XoooX...',
             '...XXX....',
             '..XX......',
             '.XX.......',
             'XoX.......',
             'XX........',
             '..........'],
    (10, 0): ['...XXXX...',
              '..XooooX..',
              '.XoXXXooX.',
              '.XXoooXXX.',
              '.XooooooX.',
              '.XooooooX.',
              '..XooooX..',
              '...XXXX...',
              '..........',
              '..........'],
    (20, 0): ['...XXX....',
              '..XXo.....',
              '.XXo......',
              '.XXo......',
              '.XXo...X..',
              '.XXXo.XX..',
              '..XXXXX...',
              '...XXX....',
              '..........',
              '..........'],
    (30, 0): ['....X.....',
              '...XoX....',
              '..XoooX.XX',
              '..XoooXXoX',
              '.XooooXXX.',
              '.XoooooX..',
              '.XXooooX..',
              '..XXXXX...',
              '..........',
              '..........'],
    # hearts 9x9: full, half, empty at x = 40, 50, 60
    (40, 0): ['.XX..XX..', 'XooXXooX.', 'XoooooooX'[:9], 'XoooooooX', '.XoooooX.', '..XoooX..', '...XoX...', '....X....', '.........'],
    (50, 0): ['.XX..XX..', 'XooXX..X.', 'XoooX...X', 'XoooX...X', '.XooX..X.', '..XoX.X..', '...XXX...', '....X....', '.........'],
    (60, 0): ['.XX..XX..', 'X..XX..X.', 'X.......X', 'X.......X', '.X.....X.', '..X...X..', '...X.X...', '....X....', '.........'],
    # golden apple 9x9 at x = 70
    (70, 0): ['....X....', '...X.XX..', '..XXXXX..', '.XooooXX.', 'XooXoooXX', 'XoXooooXX', 'XooooooXX', '.XooooXX.', '..XXXXX..'],
}

FACES = {   # 16x16 mood faces at (i*16, 16)
    0: ['.....XXXXXX.....', '...XXooooooXX...', '..XooooooooooX..', '.XooooooooooooX.', '.XooXXooooXXooX.', 'XoooooooooooooX'[:16] + 'X',
        'XooXooooooXoooX.'[:16], 'XooXooooooXooooX', 'XoooooXXXooooooX', 'XooooXoooXoooooX', '.XooXoooooXoooX.', '.XoooooooooooooX'[:16],
        '..XooooooooooX..', '...XXooooooXX...', '.....XXXXXX.....', '................'],
    1: ['.....XXXXXX.....', '...XXooooooXX...', '..XooooooooooX..', '.XooooooooooooX.', '.XooooooooooooX.', 'XooooXooooXoooox'[:15] + 'X',
        'XooooXooooXooooX', 'XooooooooooooooX', 'XooooooooooooooX', 'XoooooXXXXoooooX', '.XooXXooooXXooX.', '.XooooooooooooX.',
        '..XooooooooooX..', '...XXooooooXX...', '.....XXXXXX.....', '................'],
    2: ['.....XXXXXX.....', '...XXooooooXX...', '..XooooooooooX..', '.XooooooooooooX.', '.XooooooooooooX.', 'XooooXooooXooooX',
        'XooooXooooXooooX', 'XooooooooooooooX', 'XooooooooooooooX', 'XooooXXXXXXooooX', '.XooooooooooooX.', '.XooooooooooooX.',
        '..XooooooooooX..', '...XXooooooXX...', '.....XXXXXX.....', '................'],
    3: ['.....XXXXXX.....', '...XXooooooXX...', '..XooooooooooX..', '.XooooooooooooX.', '.XooooooooooooX.', 'XooooXooooXooooX',
        'XooooXooooXooooX', 'XooooooooooooooX', 'XooXooooooooXooX', 'XoooXooooooXoooX', '.XoooXXXXXXoooX.', '.XooooooooooooX.',
        '..XooooooooooX..', '...XXooooooXX...', '.....XXXXXX.....', '................'],
    4: ['.....XXXXXX.....', '...XXooooooXX...', '..XooooooooooX..', '.XooooooooooooX.', '.XooXoooooXoooX.'[:16], 'XoooXoXooXoXoooX',
        'XooXoooXXoooXooX', 'XooooooooooooooX', 'XoXXXXXXXXXXXXoX'[:16], 'XoXoooooooooXooX', '.XoXooooooooXoX.', '.XooXXooooXXooX.',
        '..XooooXXXXooX..', '...XXooooooXX...', '.....XXXXXX.....', '................'],
}


def paint(img, x0, y0, rows):
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == 'X':
                img.putpixel((x0 + x, y0 + y), DARK)
            elif ch == 'o':
                img.putpixel((x0 + x, y0 + y), (0, 0, 0, 0) if False else MID if (x0, y0) in ((40, 0), (50, 0), (70, 0)) or y0 >= 16 and False else MID)


def icons():
    img = Image.new('RGBA', (128, 64), (0, 0, 0, 0))
    for (x0, y0), rows in ICONS.items():
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch == 'X':
                    img.putpixel((x0 + x, y0 + y), DARK)
                elif ch == 'o':
                    img.putpixel((x0 + x, y0 + y), MID)
    for i, rows in FACES.items():
        for y, row in enumerate(rows):
            for x, ch in enumerate(row[:16]):
                if ch in 'Xx':
                    img.putpixel((i * 16 + x, 16 + y), DARK)
                elif ch == 'o':
                    img.putpixel((i * 16 + x, 16 + y), (195, 214, 158, 255))
    os.makedirs(os.path.join(TEX, 'gui'), exist_ok=True)
    img.save(os.path.join(TEX, 'gui/pet_icons.png'))


def wheel():
    """32x16 texture for RunningWheelRenderer: slat box at (0,0) 10x1x4, spoke at (0,6) 1x12x1, hub at (8,6) 12x2x2."""
    img = Image.new('RGBA', (32, 16), (0, 0, 0, 0))
    light, base, dark, deep = (226, 190, 128), (201, 160, 98), (160, 117, 66), (120, 84, 46)
    copper, copper_l, copper_d = (196, 110, 70), (226, 146, 98), (140, 72, 46)
    # slat: box UV for w=10,h=1,d=4 at (0,0): top (4,0)-(14,4), bottom (14,0)-(24,4), sides row y=4
    for x in range(0, 28):
        for y in range(0, 5):
            c = base if (x + y) % 5 else light
            if y == 4:
                c = dark
            img.putpixel((x, y), c + (255,))
    for x in (4, 9, 13, 18, 23):
        for y in range(0, 4):
            img.putpixel((x, y), deep + (255,))
    # spoke (1x12x1 at 0,6): region 4 x 13
    for x in range(0, 4):
        for y in range(6, 19 if 19 < 16 else 16):
            img.putpixel((x, y), (dark if x % 2 else base) + (255,))
    # hub (12x2x2 at 8,6): region 28 x 4 -> clipped to 24 wide
    for x in range(8, 32):
        for y in range(6, 10):
            c = copper_l if y == 6 else copper if y < 9 else copper_d
            img.putpixel((x, y), c + (255,))
    os.makedirs(os.path.join(TEX, 'entity'), exist_ok=True)
    img.save(os.path.join(TEX, 'entity/running_wheel.png'))


if __name__ == '__main__':
    icons()
    wheel()
    print('ok')
