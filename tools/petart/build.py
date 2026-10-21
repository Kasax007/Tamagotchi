"""Builds every pet: UV layout, painted textures (all expressions + glow), Java model code, previews.

    python3 tools/petart/build.py            # all pets
    python3 tools/petart/build.py desert_dragon frost_penguin
"""
import importlib
import os
import sys
import zlib

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from rig import FACES, pack, java_layer  # noqa: E402
from paint import Texture, Canvas, shade_face, apply_pattern, EXPRESSIONS, make_rng  # noqa: E402
import render  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
TEX_DIR = os.path.join(REPO, 'src/main/resources/assets/tamagotchi/textures/entity')
JAVA_OUT = os.path.join(REPO, 'src/main/java/net/kasax/tamagotchi/client/model/PetModels.java')
OUT = os.path.join(HERE, 'out')

ALL = ['desert_dragon', 'jungle_dragon', 'tide_dragon', 'frost_penguin', 'ember_pup',
       'sculk_wisp', 'void_kitten', 'pebble_golem', 'hex_toad', 'mimic']


def camel(name):
    p = name.split('_')
    return p[0] + ''.join(s.title() for s in p[1:])


def paint_texture(mod, roots, tw, th, expr):
    tex = Texture(tw, th)
    mats = mod.mats()
    deco = getattr(mod, 'DECO', {})
    for r in roots:
        for b in r.walk():
            for idx, c in enumerate(b.cubes):
                mat = mats[c.mat]
                for face, rect in c.regions().items():
                    if not c.has(face) or rect[2] <= 0 or rect[3] <= 0:
                        continue
                    seed = zlib.crc32(f'{mod.NAME}/{b.name}/{idx}/{face}'.encode())
                    cv = Canvas(tex, rect, face, make_rng(seed), mats)
                    shade_face(cv, mat)
                    apply_pattern(cv, mat)
                    for key in ((c.name or b.name, face), (c.name or b.name, '*')):
                        fn = deco.get(key)
                        if fn:
                            cv.rng = make_rng(seed ^ 0x5A5A)
                            fn(cv, expr)
    post = getattr(mod, 'post', None)
    if post:
        post(tex, roots, expr)
    return tex


def build(name):
    mod = importlib.import_module('pets.' + name)
    roots = mod.rig()
    tw, th = pack(roots)
    d = os.path.join(TEX_DIR, name)
    os.makedirs(d, exist_ok=True)
    glow_variants = []
    textures = {}
    base_glow = None
    for expr in EXPRESSIONS:
        tex = paint_texture(mod, roots, tw, th, expr)
        textures[expr] = tex
        suffix = '' if expr == 'normal' else '_' + expr
        Image.fromarray(tex.rgba, 'RGBA').save(os.path.join(d, f'{name}{suffix}.png'))
        if tex.glow[..., 3].any():
            if expr == 'normal':
                base_glow = tex.glow.copy()
                Image.fromarray(tex.glow, 'RGBA').save(os.path.join(d, f'{name}_glow.png'))
                glow_variants.append('normal')
            elif not np.array_equal(tex.glow, base_glow):
                Image.fromarray(tex.glow, 'RGBA').save(os.path.join(d, f'{name}_glow_{expr}.png'))
                glow_variants.append(expr)
    java = java_layer('create' + camel(name)[0].upper() + camel(name)[1:], roots, tw, th)
    # previews
    os.makedirs(OUT, exist_ok=True)
    scale = getattr(mod, 'PREVIEW_SCALE', 1.0)
    views = []
    n = textures['normal']
    hid = ('backpack',) + tuple(getattr(mod, 'PREVIEW_HIDDEN', ()))
    for yaw, pitch, h in ((35, 30, hid), (-40, 22, hid), (150, 30, hid[1:]), (0, 8, hid)):
        views.append(render.render(roots, n.rgba, n.glow, size=300, yaw=yaw, pitch=pitch, scale=scale, hidden=h))
    faces = []
    for expr in EXPRESSIONS:
        t = textures[expr]
        faces.append(render.render(roots, t.rgba, t.glow, size=150, yaw=10, pitch=8, dist=1.5, scale=scale,
                                   hidden=hid, target_y=getattr(mod, 'FACE_Y', None)))
    texview = Image.fromarray(n.rgba, 'RGBA').resize((tw * 4, th * 4), Image.NEAREST)
    sheet = render.contact_sheet(views, 4)
    fsheet = render.contact_sheet(faces, 7, labels=list(EXPRESSIONS))
    full = Image.new('RGB', (max(sheet.width, fsheet.width, texview.width + 12), sheet.height + fsheet.height + texview.height + 12), (30, 32, 40))
    full.paste(sheet, (0, 0))
    full.paste(fsheet, (0, sheet.height))
    full.paste(texview, (6, sheet.height + fsheet.height + 6), texview)
    full.save(os.path.join(OUT, f'{name}.png'))
    return java, views[0], glow_variants, (tw, th)


def write_java(parts):
    header = '''package net.kasax.tamagotchi.client.model;

import java.util.EnumSet;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.core.Direction;

/**
 * GENERATED by tools/petart/build.py - do not edit by hand, change the pet definition in
 * tools/petart/pets/ and run the build instead.
 */
@Environment(EnvType.CLIENT)
public final class PetModels {
    private PetModels() {
    }

'''
    with open(JAVA_OUT, 'w') as f:
        f.write(header + '\n\n'.join(parts) + '\n}\n')


def main():
    names = sys.argv[1:] or ALL
    os.makedirs(os.path.dirname(JAVA_OUT), exist_ok=True)
    # keep generated code for pets not rebuilt this run
    cache_dir = os.path.join(OUT, 'java')
    os.makedirs(cache_dir, exist_ok=True)
    thumbs = []
    meta = {}
    for n in names:
        java, thumb, glows, size = build(n)
        with open(os.path.join(cache_dir, n + '.java.part'), 'w') as f:
            f.write(java)
        meta[n] = (glows, size)
        thumbs.append(thumb)
        print(f'{n}: texture {size[0]}x{size[1]}, glow variants {glows}')
    parts = []
    for n in ALL:
        p = os.path.join(cache_dir, n + '.java.part')
        if os.path.exists(p):
            parts.append(open(p).read())
    write_java(parts)
    if len(names) > 1:
        render.contact_sheet(thumbs, 5, labels=names).save(os.path.join(OUT, 'contact.png'))


if __name__ == '__main__':
    main()
