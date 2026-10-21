#!/usr/bin/env python3
"""Regenerate every block / item / particle asset of the Tamagotchi mod and the review sheets.

    python3 tools/sprites/build.py            # everything
    python3 tools/sprites/build.py items eggs # only some groups (items, eggs, particles, blocks, sheets)

Writes into src/main/resources/{assets,data}/tamagotchi/ (see docs/ART.md) and tools/sprites/out/.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PIL import Image, ImageDraw

import block_models
import block_tex
import eggs
import items
import particles
from pxl import ASSETS, DATA, OUT, save_png, vstack, write_json, write_mcmeta
from render import load_model, render_model, textures_used
from sheets import font, scaled, small_sheet, sprite_sheet

NS = "tamagotchi"
HANDHELD = {"pet_brush", "laser_pointer", "feather_wand"}


def build_items():
    for name, d in items.ITEMS.items():
        frames = d["frames"]
        png = ASSETS / "textures/item" / f"{name}.png"
        save_png(vstack(frames) if len(frames) > 1 else frames[0], png)
        if d.get("anim"):
            write_mcmeta(png, frametime=2, frames=d["anim"]["frames"])
        write_json(ASSETS / "models/item" / f"{name}.json", {
            "parent": "minecraft:item/handheld" if d["handheld"] or name in HANDHELD else "minecraft:item/generated",
            "textures": {"layer0": f"{NS}:item/{name}"},
        })
        write_json(ASSETS / "items" / f"{name}.json", {"model": {"type": "minecraft:model", "model": f"{NS}:item/{name}"}})


def build_eggs():
    for pet in eggs.SPAWN_EGGS:
        name = f"{pet}_spawn_egg"
        save_png(eggs.EGGS[pet], ASSETS / "textures/item" / f"{name}.png")
        write_json(ASSETS / "models/item" / f"{name}.json", {
            "parent": "minecraft:item/generated", "textures": {"layer0": f"{NS}:item/{name}"}})
        write_json(ASSETS / "items" / f"{name}.json", {"model": {"type": "minecraft:model", "model": f"{NS}:item/{name}"}})


def build_particles():
    for name, im in particles.PARTICLES.items():
        save_png(im, ASSETS / "textures/particle" / f"{name}.png")
    for pname, sprites in particles.PARTICLE_JSON.items():
        write_json(ASSETS / "particles" / f"{pname}.json", {"textures": [f"{NS}:{s}" for s in sprites]})


def build_blocks():
    block_tex.build_all()
    for name, im in block_tex.TEX.items():
        png = ASSETS / "textures/block" / f"{name}.png"
        save_png(im, png)
        if name in block_tex.ANIM:
            write_mcmeta(png, **block_tex.ANIM[name])
    models = block_models.build_models()
    for name, m in models.items():
        m.save(ASSETS / "models/block" / f"{name}.json")
    for blk, bs in block_models.blockstates().items():
        write_json(ASSETS / "blockstates" / f"{blk}.json", bs)
        write_json(ASSETS / "items" / f"{blk}.json", block_models.block_item(blk))
        write_json(DATA / "loot_table/blocks" / f"{blk}.json", block_models.loot_table(blk))


# --------------------------------------------------------------------------------------------------
# review sheets
# --------------------------------------------------------------------------------------------------
def build_sheets():
    entries = [(n, d["frames"]) for n, d in items.ITEMS.items()]
    entries += [(f"{p}_spawn_egg", [eggs.EGGS[p]]) for p in eggs.SPAWN_EGGS]
    sprite_sheet(entries, OUT / "contact_items.png", k=8, cols=5, title="items + spawn eggs  (x8 on grey / dark, animation strips below)")
    small_sheet(entries, OUT / "contact_items_small.png", cols=9)
    pe = [(n, [im]) for n, im in particles.PARTICLES.items()]
    sprite_sheet(pe, OUT / "contact_particles.png", k=8, cols=8, title="particles  (8x8 and 16x16, x8)")
    blocks_sheet()


def blocks_sheet():
    f = font(13)
    if not block_models.MODELS:
        block_models.build_models()
    names = list(block_models.MODELS)
    views = [(225, 30), (135, 30), (45, 30), (225, 66)]   # (yaw, pitch)
    vs = 190
    sc = 6
    row_h = vs + 18
    tex_cols = 6
    W = 90 + len(views) * vs + 20 + tex_cols * 56
    sheet = Image.new("RGBA", (W, len(names) * row_h + 8), (84, 86, 96, 255))
    d = ImageDraw.Draw(sheet)
    for r, name in enumerate(names):
        y = r * row_h + 6
        model = load_model(f"{NS}:block/{name}")
        d.text((6, y + 4), name.replace("_", "\n", 1), fill=(240, 240, 245), font=f)
        for i, (yaw, pitch) in enumerate(views):
            tile = render_model(model, yaw=yaw, pitch=pitch, scale=sc, size=vs)
            bg = Image.new("RGBA", (vs, vs - 6), (122, 128, 140, 255) if i % 2 == 0 else (96, 102, 116, 255))
            bg.alpha_composite(tile.crop((0, 0, vs, vs - 6)))
            sheet.alpha_composite(bg, (90 + i * vs, y))
        tx = 90 + len(views) * vs + 20
        for k, t in enumerate(textures_used(model)):
            from render import load_texture
            a = load_texture(t)
            tex = Image.fromarray(a[:a.shape[1]]) if a.shape[0] > a.shape[1] else Image.fromarray(a)
            cell = scaled(tex, 3)
            bgc = Image.new("RGBA", cell.size, (60, 60, 66, 255))
            bgc.alpha_composite(cell)
            sheet.alpha_composite(bgc, (tx + (k % tex_cols) * 56, y + (k // tex_cols) * 56))
    path = OUT / "contact_blocks.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(path)
    # per-model detail renders (big, 4 views) for close review
    (OUT / "blocks").mkdir(exist_ok=True)
    for name in names:
        model = load_model(f"{NS}:block/{name}")
        big = Image.new("RGBA", (4 * 300, 300), (122, 128, 140, 255))
        for i, (yaw, pitch) in enumerate(views):
            big.alpha_composite(render_model(model, yaw=yaw, pitch=pitch, scale=10, size=300), (i * 300, 0))
        big.convert("RGB").save(OUT / "blocks" / f"{name}.png")


def main(argv):
    groups = argv or ["items", "eggs", "particles", "blocks", "sheets"]
    if "items" in groups:
        build_items()
    if "eggs" in groups:
        build_eggs()
    if "particles" in groups:
        build_particles()
    if "blocks" in groups:
        build_blocks()
    if "sheets" in groups:
        build_sheets()
    print("done:", ", ".join(groups))


if __name__ == "__main__":
    main(sys.argv[1:])
