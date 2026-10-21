"""Mod icon: three pets on a pink rounded tile. Run: python3 tools/petart/icon.py"""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from PIL import Image, ImageDraw

import build
import render
from rig import pack

OUT = os.path.join(build.REPO, 'src/main/resources/assets/tamagotchi/icon.png')


def pet_image(name, expr, size, yaw):
    mod = importlib.import_module('pets.' + name)
    roots = mod.rig()
    tw, th = pack(roots)
    tex = build.paint_texture(mod, roots, tw, th, expr)
    return render.render(roots, tex.rgba, tex.glow, size=size, yaw=yaw, pitch=18, dist=2.4, scale=0.8,
                         hidden=('backpack', 'tongue'), shadow=False, transparent=True)


def main():
    S = 512
    tile = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    d.rounded_rectangle((8, 8, S - 8, S - 8), radius=90, fill=(244, 175, 200, 255), outline=(200, 110, 146, 255), width=14)
    d.rounded_rectangle((40, 40, S - 40, S - 40), radius=60, fill=(195, 214, 158, 255))
    for name, expr, x, y, sz, yaw in (('frost_penguin', 'happy', 20, 70, 260, 25), ('ember_pup', 'happy', 232, 80, 260, -30),
                                      ('desert_dragon', 'love', 86, 150, 340, 15)):
        img = pet_image(name, expr, sz, yaw)
        tile.alpha_composite(img, (x, y))
    # little pixel heart
    heart = ['.XX.XX.', 'XXXXXXX', 'XXXXXXX', '.XXXXX.', '..XXX..', '...X...']
    for yy, row in enumerate(heart):
        for xx, ch in enumerate(row):
            if ch == 'X':
                d.rectangle((370 + xx * 12, 70 + yy * 12, 381 + xx * 12, 81 + yy * 12), fill=(230, 60, 100, 255))
    tile.resize((128, 128), Image.LANCZOS).save(OUT)
    print('icon written')


if __name__ == '__main__':
    main()
