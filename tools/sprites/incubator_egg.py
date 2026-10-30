"""Texture of the egg drawn inside the Pet Incubator (IncubatorRenderer): a light speckled shell in gray, tinted with
the pet's colour in game. UV layout matches IncubatorRenderer.createLayer (32x32). Run: python3 tools/sprites/incubator_egg.py"""
import os
import random
from PIL import Image

OUT = os.path.join(os.path.dirname(__file__), '../../src/main/resources/assets/tamagotchi/textures/entity/incubator_egg.png')


def box_uv(u, v, w, h, d):
    """Pixel rects (x0, y0, x1, y1, face) of a model box with texOffs (u, v) and size w x h x d."""
    return [(u + d, v, u + d + w, v + d, 'top'), (u + d + w, v, u + d + 2 * w, v + d, 'bottom'),
            (u, v + d, u + d, v + d + h, 'side'), (u + d, v + d, u + d + w, v + d + h, 'side'),
            (u + d + w, v + d, u + 2 * d + w, v + d + h, 'side'), (u + 2 * d + w, v + d, u + 2 * d + 2 * w, v + d + h, 'side')]


def main():
    rnd = random.Random(7)
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    px = img.load()
    boxes = [(0, 0, 6, 4, 6), (0, 10, 4, 2, 4), (16, 10, 2, 1, 2), (0, 16, 4, 1, 4)]
    for (u, v, w, h, d) in boxes:
        for (x0, y0, x1, y1, face) in box_uv(u, v, w, h, d):
            for y in range(y0, y1):
                for x in range(x0, x1):
                    shade = {'top': 248, 'bottom': 200, 'side': 236}[face]
                    # a soft gradient down the sides, lighter at the top of each band
                    if face == 'side' and y1 - y0 > 1:
                        shade -= int(14 * (y - y0) / (y1 - y0 - 1))
                    shade += rnd.randint(-4, 4)
                    px[x, y] = (shade, shade, shade, 255)
    # speckles: small darker spots, a few two pixels wide
    for (u, v, w, h, d) in boxes:
        for (x0, y0, x1, y1, face) in box_uv(u, v, w, h, d):
            area = (x1 - x0) * (y1 - y0)
            for _ in range(max(1, area // 9)):
                x, y = rnd.randrange(x0, x1), rnd.randrange(y0, y1)
                dark = rnd.randint(150, 175)
                px[x, y] = (dark, dark, dark, 255)
                if rnd.random() < 0.35 and x + 1 < x1:
                    px[x + 1, y] = (dark + 15, dark + 15, dark + 15, 255)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT)
    print('wrote', os.path.normpath(OUT))


if __name__ == '__main__':
    main()
