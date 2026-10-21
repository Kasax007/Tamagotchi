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
    """64x32 texture of the running wheel's block-entity model: rim slats (3x1x12 at 0,0), spokes (1x10x1 at 32,0),
    copper hub (3x3x2 at 40,0)."""
    import random
    rnd = random.Random(7)
    img = Image.new('RGBA', (64, 32), (0, 0, 0, 0))
    px = img.load()

    def wood(u0, v0, w, h, base, dark, light):
        for y in range(v0, v0 + h):
            for x in range(u0, u0 + w):
                r = rnd.random()
                px[x, y] = (dark if r < 0.18 else light if r < 0.32 else base) + (255,)

    wood(0, 0, 30, 13, (196, 140, 84), (168, 112, 62), (214, 164, 104))
    for x in range(30):
        px[x, 12] = (140, 92, 50, 255)
    wood(32, 0, 4, 11, (150, 98, 56), (122, 78, 44), (170, 116, 70))
    for y in range(5):
        for x in range(40, 50):
            px[x, y] = ((205, 120, 72) if (x + y) % 3 else (232, 156, 100)) + (255,)
    img.save(os.path.join(TEX, 'entity/running_wheel.png'))


if __name__ == '__main__':
    icons()
    wheel()
    print('ok')
