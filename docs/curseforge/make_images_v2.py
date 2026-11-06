"""Images of the CurseForge page of Tamagotchi 1.2 (docs/curseforge/img/*_v2.*): the header, the video card, the "at a
glance" numbers, the two flow diagrams (how it works, always at your side), the ten pet cards, the care diagram, the
furniture shelf, the "made for modpacks" diagram, the section strips and the collages cut from the footage of the
Tamagotchi videos. The images of the page before (header.png, pets.png, strip_*.png ...) are left as they are.

  python3 docs/curseforge/make_images_v2.py FOOTAGE_DIR FONT_DIR [what ...]

FOOTAGE_DIR: the footage folder of the video archive, with the shot folders tama/ and tama2/ (one portrait MP4 per
shot, 1080x1920). FONT_DIR: the archive's fonts folder (Lilita One, Press Start 2P, Inter Display Bold).
The pets are drawn with tools/petart from the textures in src/main/resources, the furniture with
tools/sprites/render.py; the vanilla models and textures they need come from the Minecraft client jar ($MC_JAR,
default: the Loom cache). Frames are cut with ffmpeg into $TAMA_FRAMES (default: a temporary folder). The length of
the showcase on the video card is read from $TAMA_VIDEO (default: FOOTAGE_DIR/../tamagotchi/longform/...).
what: header video glance flow_start pets care flow_side shelf modpack strips collages counts, or image names such as
play_v2.jpg (default: everything). Every number on the images is counted from the repository (see counts())."""
import importlib
import importlib.util
import io
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(HERE, 'img')
JAVA = os.path.join(ROOT, 'src', 'main', 'java', 'net', 'kasax', 'tamagotchi')
RES = os.path.join(ROOT, 'src', 'main', 'resources')
ASSETS = os.path.join(RES, 'assets', 'tamagotchi')
DATA = os.path.join(RES, 'data', 'tamagotchi')
FOOT = sys.argv[1]
FONTS = sys.argv[2]
CACHE = os.environ.get('TAMA_FRAMES') or os.path.join(tempfile.gettempdir(), 'tama_frames')
MC_JAR = os.environ.get('MC_JAR') or os.path.expanduser('~/.gradle/caches/fabric-loom/26.3/minecraft-client.jar')
VIDEO = os.environ.get('TAMA_VIDEO') or os.path.join(FOOT, '..', 'tamagotchi', 'longform',
                                                     'tamagotchi_showcase_clean_music.mp4')
W = 1200
MAX_BYTES = 900 * 1024

# the colours of the pet screen and the Tamacon (client/screen/PetScreen.java), plus berry and crimson for text
SHELL, SHELL_DARK, SHELL_LIGHT = (244, 175, 200), (200, 110, 146), (255, 214, 229)
LCD, LCD_DARK, LCD_MID, LCD_SHADE = (195, 214, 158), (46, 58, 33), (125, 145, 96), (174, 195, 136)
BERRY, CRIMSON, BUTTON = (150, 24, 72), (214, 52, 104), (255, 204, 77)
CREAM, INK, WHITE = (255, 250, 246), (92, 38, 62), (255, 255, 255)


def title(size):
    return ImageFont.truetype(os.path.join(FONTS, 'LilitaOne-Regular.ttf'), size)


def pixel(size):
    return ImageFont.truetype(os.path.join(FONTS, 'PressStart2P-Regular.ttf'), size)


def small(size):
    return ImageFont.truetype(os.path.join(FONTS, 'InterDisplay-Bold.otf'), size)


# ----------------------------------------------------------------------------------------------- the numbers
def read(*p):
    return open(os.path.join(*p), encoding='utf-8').read()


HOME_NAMES = {'desert_pyramid': 'Desert pyramid', 'jungle_pyramid': 'Jungle temple', 'monument': 'Ocean monument',
              'igloo': 'Igloo', 'fortress': 'Nether fortress', 'ancient_city': 'Ancient city', 'end_city': 'End city',
              'trail_ruins': 'Trail ruins', 'mineshaft': 'Mineshafts', 'swamp_hut': 'Swamp hut',
              'trial_chambers': 'Trial chambers', 'mansion': 'Woodland mansion'}


def counts():
    """Every number of the images, counted from the code and data of this repository."""
    species = read(JAVA, 'pet', 'PetSpecies.java')
    pets = re.findall(r'^ {4}([A-Z_]+)\(new Props\("(\w+)"\)(.*?)\)\)[,;]$', species, re.M | re.S)
    lang = json.loads(read(ASSETS, 'lang', 'en_us.json'))
    info = {}
    for const, pid, props in pets:
        info[pid] = dict(name=lang['entity.tamagotchi.' + pid], talent=lang['talent.tamagotchi.' + pid],
                         desc=lang['talent.tamagotchi.%s.desc' % pid],
                         color=int(re.search(r'\.color\(0x([0-9A-Fa-f]{6})\)', props).group(1), 16),
                         treat=re.search(r'ModItems\.(\w+)', props).group(1).lower(), homes=[])
    spawns = read(JAVA, 'world', 'PetSpawns.java')
    rules = re.findall(r'rule\("(\w+)", PetSpecies\.(\w+), ([\d.]+)F\)', spawns)
    vanilla, optional = set(), []
    for rule, const, chance in rules:
        tag = json.loads(read(DATA, 'tags', 'worldgen', 'structure', 'pet_home', rule + '.json'))['values']
        ids = [v for v in tag if isinstance(v, str)]
        vanilla.update(ids)
        optional += [v['id'] for v in tag if isinstance(v, dict)]
        info[const.lower()]['homes'].append((HOME_NAMES[ids[0].split(':')[1]], round(float(chance) * 100)))
    needs = read(JAVA, 'pet', 'PetNeeds.java')
    need_names = re.search(r'enum Need \{([^}]*)\}', needs).group(1).replace(' ', '').split(',')
    moods = re.search(r'enum Mood \{\s*([^;]*);', needs).group(1).replace(' ', '').replace('\n', '').split(',')
    blocks = sorted(f[:-5] for f in os.listdir(os.path.join(ASSETS, 'blockstates')))
    plush = [b for b in blocks if b.endswith('_plush')]
    items = read(JAVA, 'registry', 'ModItems.java')
    foods = re.findall(r'reg\("(\w+)", PetFoodItem::new', items)
    tama = read(JAVA, 'pet', 'TamaPet.java')
    slots = int(re.search(r'BACKPACK_SLOTS = (\d+);', tama).group(1))
    bond_div = float(re.search(r'1F - this\.needs\.bond / ([\d.]+)F', tama).group(1))
    screen = read(JAVA, 'client', 'screen', 'PetScreen.java')
    hearts = int(re.search(r'// bond hearts.*?for \(int i = 0; i < (\d+); i\+\+\)', screen, re.S).group(1))
    hatch = int(re.search(r'HATCH_TICKS = (\d+);', read(JAVA, 'block', 'PetIncubatorBlockEntity.java')).group(1)) // 20
    pager = int(re.search(r'inflate\((\d+)\)', read(JAVA, 'item', 'TamaPagerItem.java')).group(1))
    colours = len(json.loads(read(ASSETS, 'items', 'pet_bed.json'))['model']['cases'])
    log = read(ROOT, 'CHANGELOG.md')
    v12 = log.split('## 1.2.0', 1)[1].split('\n## ', 1)[0]
    fixes = len(re.findall(r'^- Fix:', v12, re.M))
    mods = sorted({o.split(':')[0] for o in optional})
    goals = read(JAVA, 'pet', 'PetGoals.java')
    bites = re.findall(r'PetSpecies\.(\w+)', re.search(r'static boolean dangerous\(PetSpecies s\) \{(.*?)\}', goals, re.S).group(1))
    for b in bites:
        info[b.lower()]['bites'] = True
    return dict(pets=len(pets), info=info, rules=len(rules), homes=len(vanilla), lookalikes=len(optional),
                lookalike_mods=mods, needs=need_names, moods=moods, slots=slots, belly=2 * slots,
                bond_faster=round(100 * 100 / bond_div), hearts=hearts, furniture=len(blocks) - len(plush),
                plushies=len(plush), blocks=len(blocks), foods=len(foods), hatch=hatch, pager=pager,
                colours=colours, fixes=fixes)


# ----------------------------------------------------------------------------------------------- sources
def frame(spec):
    """'group/shot@t': the picture at t seconds of FOOTAGE_DIR/group/shot.mp4 (1080x1920)."""
    os.makedirs(CACHE, exist_ok=True)
    clip, t = spec.split('@')
    out = os.path.join(CACHE, clip.replace('/', '_') + '_' + t + '.jpg')
    if not os.path.exists(out):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-threads', '1', '-ss', t, '-i', os.path.join(FOOT, clip + '.mp4'),
                        '-frames:v', '1', '-q:v', '2', out], check=True)
    return Image.open(out).convert('RGB')


def decross(im):
    """Removes the crosshair in the middle of a first-person picture (thin lines: a median filter of the spot)."""
    cx, cy, r = im.width // 2, im.height // 2, 22
    box = (cx - r, cy - r, cx + r, cy + r)
    im.paste(im.crop(box).filter(ImageFilter.MedianFilter(9)), box[:2])
    return im


def shot(spec, enh=None, cross=False):
    im = frame(spec)
    if cross:
        im = decross(im)
    if enh:
        b, c, s = enh
        im = ImageEnhance.Color(ImageEnhance.Contrast(ImageEnhance.Brightness(im).enhance(b)).enhance(c)).enhance(s)
    return im


def video_length(path):
    o = subprocess.run(['ffmpeg', '-hide_banner', '-i', path], capture_output=True, text=True).stderr
    h, m, s = re.search(r'Duration: (\d+):(\d+):([\d.]+)', o).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


_jar = None


def van(rel, size=None):
    """Vanilla texture 'block/x' or 'item/x' from the client jar (first frame of animated textures)."""
    global _jar
    _jar = _jar or zipfile.ZipFile(MC_JAR)
    im = Image.open(io.BytesIO(_jar.read('assets/minecraft/textures/%s.png' % rel))).convert('RGBA')
    if rel.startswith(('block/', 'item/')):
        im = im.crop((0, 0, im.width, im.width))
    return im.resize((size, size * im.height // im.width), Image.NEAREST) if size else im


def tex(rel, size=None):
    """Texture of this mod: 'item/x', 'particle/x' ... (first frame of animated textures)."""
    im = Image.open(os.path.join(ASSETS, 'textures', rel + '.png')).convert('RGBA')
    if rel.startswith('item/') or rel.startswith('particle/'):
        im = im.crop((0, 0, im.width, im.width))
    return im.resize((size, size * im.height // im.width), Image.NEAREST) if size else im


_gui = None


def gui(box, size):
    """A piece of textures/gui/pet_icons.png (LCD icons of the pet screen)."""
    global _gui
    _gui = _gui or Image.open(os.path.join(ASSETS, 'textures', 'gui', 'pet_icons.png')).convert('RGBA')
    im = _gui.crop(box)
    return im.resize((size, size * im.height // im.width), Image.NEAREST)


def need_icon(i, size):
    return gui((i * 10, 0, i * 10 + 10, 10), size)


def heart_icon(kind, size):
    """kind 0 full, 1 half, 2 empty (PetScreen: u = 40, 50, 60)."""
    return gui((40 + 10 * kind, 0, 49 + 10 * kind, 9), size)


def mood_face(i, size):
    return gui((i * 16, 16, i * 16 + 16, 32), size)


def cube(top, left, right, a=48):
    """Inventory-style block from three square textures, 2a x 2a."""
    S = top.width
    out = Image.new('RGBA', (2 * a, 2 * a), (0, 0, 0, 0))
    faces = [
        (top, (S / (2 * a), -S / a, S / 2, S / (2 * a), S / a, -S / 2), [(a, 0), (2 * a, a / 2), (a, a), (0, a / 2)], 1.0),
        (left, (S / a, 0, 0, -S / (2 * a), S / a, -S / 2), [(0, a / 2), (a, a), (a, 2 * a), (0, 1.5 * a)], 0.8),
        (right, (S / a, 0, -S, S / (2 * a), S / a, -1.5 * S), [(a, a), (2 * a, a / 2), (2 * a, 1.5 * a), (a, 2 * a)], 0.62),
    ]
    for t, aff, poly, shade in faces:
        f = t.transform((2 * a, 2 * a), Image.AFFINE, aff, resample=Image.NEAREST)
        if shade < 1:
            r, g, b, al = f.split()
            r, g, b = (c.point(lambda v, s=shade: int(v * s)) for c in (r, g, b))
            f = Image.merge('RGBA', (r, g, b, al))
        m = Image.new('L', (2 * a, 2 * a), 0)
        ImageDraw.Draw(m).polygon(poly, fill=255)
        out.paste(f, (0, 0), Image.composite(f.split()[3], Image.new('L', m.size, 0), m))
    return out


def vcube(top, side=None, front=None, a=48):
    t, s = van(top), van(side or top)
    return cube(t, van(front) if front else s, s, a)


def chest(a=48):
    """A wooden chest from the vanilla entity texture: lid and base faces stacked, with the latch."""
    t = van('entity/chest/normal')
    sq = lambda im: im.resize((16, 16), Image.NEAREST)
    front = Image.new('RGBA', (14, 15))
    front.paste(t.crop((42, 14, 56, 19)), (0, 0))
    front.paste(t.crop((42, 33, 56, 43)), (0, 5))
    front.alpha_composite(t.crop((1, 1, 3, 5)), (6, 3))
    side = Image.new('RGBA', (14, 15))
    side.paste(t.crop((0, 14, 14, 19)), (0, 0))
    side.paste(t.crop((0, 33, 14, 43)), (0, 5))
    return cube(sq(t.crop((28, 0, 42, 14))), sq(front), sq(side), a)


def premul_resize(im, size):
    return im.convert('RGBa').resize(size, Image.LANCZOS).convert('RGBA')


def trim(im):
    return im.crop(im.getbbox())


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_petart = None


def pet(pid, height, expr='happy', yaw=30, pitch=14, ss=3):
    """A pet drawn by tools/petart (the game's model and texture), trimmed and scaled to the given height."""
    global _petart
    if _petart is None:
        sys.path.insert(0, os.path.join(ROOT, 'tools', 'petart'))
        _petart = (_load('petart_render', os.path.join(ROOT, 'tools', 'petart', 'render.py')),
                   importlib.import_module('rig').pack)
    render, pack = _petart
    mod = importlib.import_module('pets.' + pid)
    roots = mod.rig()
    pack(roots)
    d = os.path.join(ASSETS, 'textures', 'entity', pid)
    t = np.asarray(Image.open(os.path.join(d, '%s_%s.png' % (pid, expr) if expr != 'normal' else pid + '.png')).convert('RGBA'))
    glow = None
    for g in ('%s_glow_%s.png' % (pid, expr), pid + '_glow.png'):
        if os.path.exists(os.path.join(d, g)):
            glow = np.asarray(Image.open(os.path.join(d, g)).convert('RGBA'))
            break
    hid = ('backpack',) + tuple(getattr(mod, 'PREVIEW_HIDDEN', ()))
    big = render.render(roots, t, glow, size=max(360, height * ss * 2), yaw=yaw, pitch=pitch,
                        scale=getattr(mod, 'PREVIEW_SCALE', 1.0), hidden=hid, transparent=True, shadow=False)
    big = trim(big)
    return premul_resize(big, (max(1, round(big.width * height / big.height)), height))


_blocks = None


def furniture(name, height, color=None, ss=3):
    """A furniture block as in the inventory (tools/sprites/render.py renders the block model of its item)."""
    global _blocks
    if _blocks is None:
        van_dir = os.path.join(tempfile.gettempdir(), 'tama_vanilla')
        if not os.path.isdir(os.path.join(van_dir, 'assets', 'minecraft', 'models')):
            z = zipfile.ZipFile(MC_JAR)
            for f in z.namelist():
                if f.startswith(('assets/minecraft/models/', 'assets/minecraft/textures/block/')) and not f.endswith('/'):
                    z.extract(f, van_dir)
        os.environ['VANILLA_ASSETS'] = os.path.join(van_dir, 'assets', 'minecraft')
        sys.path.insert(0, os.path.join(ROOT, 'tools', 'sprites'))
        _blocks = _load('sprites_render', os.path.join(ROOT, 'tools', 'sprites', 'render.py'))
    m = json.loads(read(ASSETS, 'items', name + '.json'))['model']
    while m.get('type') != 'minecraft:model':
        if 'cases' in m:
            m = next((c['model'] for c in m['cases'] if c['when'] == color), m['cases'][0]['model'])
        else:
            m = m.get('fallback') or m.get('on_false')
    tints = None
    if m.get('tints'):
        v = m['tints'][0]['value'] & 0xFFFFFF
        tints = {0: ((v >> 16) & 255, (v >> 8) & 255, v & 255)}
    big = trim(_blocks.render_model(_blocks.load_model(m['model']), scale=4 * ss, tints=tints))
    return premul_resize(big, (max(1, round(big.width * height / big.height)), height))


def plush(pid, height):
    """Plushies are small pets on the block (PlushBlock renders the pet model)."""
    return pet(pid, height, expr='happy', yaw=28, pitch=18)


# ----------------------------------------------------------------------------------------------- drawing helpers
def gradient(w, h, c0, c1, horizontal=True):
    im = Image.new('RGBA', (w, h))
    d = ImageDraw.Draw(im)
    n = w if horizontal else h
    for i in range(n):
        t = i / max(1, n - 1)
        c = tuple(int(c0[k] + (c1[k] - c0[k]) * t) for k in range(3)) + (255,)
        d.line([(i, 0), (i, h)] if horizontal else [(0, i), (w, i)], fill=c)
    return im


def dots(im, step=44, r=6, color=(255, 255, 255, 80), box=None):
    """Polka dots like the Tamagotchi shell."""
    x0, y0, x1, y1 = box or (0, 0, im.width, im.height)
    lay = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for row, y in enumerate(range(y0 + step // 2, y1 + step, step)):
        for x in range(x0 + (step // 2 if row % 2 else 0), x1 + step, step):
            d.ellipse([x - r, y - r, x + r, y + r], fill=color)
    im.alpha_composite(lay)
    return im


def candy(w, h, top=(255, 228, 239), bottom=(250, 196, 220)):
    return dots(gradient(w, h, top, bottom, horizontal=False))


def rounded(im, r):
    m = Image.new('L', im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width - 1, im.height - 1], r, fill=255)
    out = im.convert('RGBA')
    a = out.split()[3]
    out.putalpha(Image.fromarray(np.minimum(np.asarray(a), np.asarray(m))))
    return out


def outlined(d, xy, text, f, fill=WHITE, stroke=6, stroke_fill=BERRY, anchor='la', drop=True):
    if drop:
        d.text((xy[0], xy[1] + stroke // 2 + 3), text, font=f, fill=stroke_fill, stroke_width=stroke,
               stroke_fill=stroke_fill, anchor=anchor)
    d.text(xy, text, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill, anchor=anchor)


def wrap(d, s, f, width):
    lines = ['']
    for word in s.split():
        t = (lines[-1] + ' ' + word).strip()
        if d.textlength(t, font=f) <= width or not lines[-1]:
            lines[-1] = t
        else:
            lines.append(word)
    return lines


def para(d, xy, s, f, width, fill=INK, gap=5, anchor='la'):
    """Wrapped text; anchor 'ma' centres every line on x. Returns the y below the last line."""
    x, y = xy
    asc, desc = f.getmetrics()
    for ln in wrap(d, s, f, width):
        d.text((x, y), ln, font=f, fill=fill, anchor=anchor)
        y += asc + desc + gap
    return y


def shadowed(im, layer, xy, blur=10, offset=(0, 6), alpha=90, color=(120, 20, 60)):
    """Pastes an RGBA layer with a soft drop shadow."""
    sh = Image.new('RGBA', (layer.width + 4 * blur, layer.height + 4 * blur), (0, 0, 0, 0))
    a = layer.split()[3].point(lambda v: v * alpha // 255)
    sh.paste(color + (255,), (2 * blur, 2 * blur), a)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    im.alpha_composite(sh, (int(xy[0] - 2 * blur + offset[0]), int(xy[1] - 2 * blur + offset[1])))
    im.alpha_composite(layer, (int(xy[0]), int(xy[1])))


def card(w, h, r=24, fill=CREAM, outline=SHELL, width=5):
    c = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    g = gradient(w, h, fill, tuple(max(0, v - 10) for v in fill), horizontal=False)
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255)
    c.paste(g, (0, 0), m)
    if outline:
        ImageDraw.Draw(c).rounded_rectangle([0, 0, w - 1, h - 1], r, outline=outline + (255,), width=width)
    return c


def lcd(w, h, r=12, border=SHELL_DARK):
    """An LCD window of the pet screen: green glass in a pink frame."""
    c = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    d.rounded_rectangle([0, 0, w - 1, h - 1], r, fill=border + (255,))
    d.rounded_rectangle([5, 5, w - 6, h - 6], max(2, r - 4), fill=LCD_SHADE + (255,))
    d.rounded_rectangle([9, 9, w - 8, h - 8], max(2, r - 6), fill=LCD + (255,))
    return c


def arrow(d, pts, color=WHITE, width=14, head=24, outline=CRIMSON):
    """An outlined arrow along the points (head at the last one)."""
    (xa, ya), (xb, yb) = pts[-2], pts[-1]
    ang = math.atan2(yb - ya, xb - xa)
    bx, by = xb - head * math.cos(ang), yb - head * math.sin(ang)
    nx, ny = -math.sin(ang), math.cos(ang)
    line = list(pts[:-1]) + [(bx + 2 * math.cos(ang), by + 2 * math.sin(ang))]
    tri = [(xb, yb), (bx + nx * head * 0.9, by + ny * head * 0.9), (bx - nx * head * 0.9, by - ny * head * 0.9)]
    mx, my = sum(p[0] for p in tri) / 3, sum(p[1] for p in tri) / 3
    big = [(mx + (px - mx) * 1.32, my + (py - my) * 1.32) for px, py in tri]
    for col, extra, t in ((outline, 7, big), (color, 0, tri)):
        r = (width + extra) / 2
        d.ellipse([line[0][0] - r, line[0][1] - r, line[0][0] + r, line[0][1] + r], fill=col)
        d.line(line, fill=col, width=width + extra, joint='curve')
        d.polygon(t, fill=col)


def badge(im, center, n, r=20, fill=CRIMSON):
    d = ImageDraw.Draw(im)
    x, y = center
    d.ellipse([x - r - 4, y - r - 4, x + r + 4, y + r + 4], fill=WHITE)
    d.ellipse([x - r, y - r, x + r, y + r], fill=fill)
    d.text((x, y + 1), str(n), font=title(int(r * 1.45)), fill=WHITE, anchor='mm')


def keycap(im, x, y, label, w=None, h=44, f=None):
    d = ImageDraw.Draw(im)
    f = f or small(21)
    w = w or max(h, int(d.textlength(label, font=f)) + 24)
    d.rounded_rectangle([x, y + 5, x + w, y + h + 5], 9, fill=SHELL_DARK)
    d.rounded_rectangle([x, y, x + w, y + h], 9, fill=WHITE, outline=SHELL_DARK, width=2)
    d.text((x + w / 2, y + h / 2), label, font=f, fill=INK, anchor='mm')
    return w


def mouse(h=58, button='right'):
    """A computer mouse with one button lit."""
    s = 4
    w, hh = int(h * 0.68) * s, h * s
    g = Image.new('RGBA', (w + 8 * s, hh + 8 * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    box = [4 * s, 4 * s, 4 * s + w, 4 * s + hh]
    d.rounded_rectangle(box, w // 2, fill=WHITE, outline=SHELL_DARK, width=3 * s)
    mid = box[0] + w // 2
    top_h = int(hh * 0.42)
    lit = [mid, box[1], box[2], box[1] + top_h] if button == 'right' else [box[0], box[1], mid, box[1] + top_h]
    m = Image.new('L', g.size, 0)
    ImageDraw.Draw(m).rounded_rectangle(box, w // 2, fill=255)
    hl = Image.new('RGBA', g.size, (0, 0, 0, 0))
    ImageDraw.Draw(hl).rectangle(lit, fill=CRIMSON + (255,))
    g.paste(hl, (0, 0), Image.fromarray(np.minimum(np.asarray(m), np.asarray(hl.split()[3]))))
    d = ImageDraw.Draw(g)
    d.rounded_rectangle(box, w // 2, outline=SHELL_DARK, width=3 * s)
    d.line([(mid, box[1]), (mid, box[1] + top_h)], fill=SHELL_DARK, width=3 * s)
    d.line([(box[0], box[1] + top_h), (box[2], box[1] + top_h)], fill=SHELL_DARK, width=3 * s)
    return g.resize((g.width // s, g.height // s), Image.LANCZOS)


def play_glyph(size, ring=WHITE, tri=CRIMSON):
    s = 4 * size
    g = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    d.ellipse([0, 0, s - 1, s - 1], fill=ring + (245,))
    d.polygon([(s * 0.38, s * 0.27), (s * 0.38, s * 0.73), (s * 0.76, s * 0.5)], fill=tri)
    return g.resize((size, size), Image.LANCZOS)


def sticker(text, size, fill=BUTTON, ink=BERRY, angle=-12):
    """A round sticker (version number on the header)."""
    s = size * 3
    g = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    d.ellipse([6, 6, s - 7, s - 7], fill=WHITE)
    d.ellipse([18, 18, s - 19, s - 19], fill=fill)
    d.text((s / 2, s / 2 + 6), text, font=title(int(s * 0.42)), fill=ink, anchor='mm')
    return g.rotate(angle, Image.BICUBIC).resize((size, size), Image.LANCZOS)


def fit(im, w, h, focus=(0.5, 0.5), zoom=1.0, box=None):
    if box:
        im = im.crop(box)
    sw, sh = im.size
    cw = sw / zoom
    ch = cw * h / w
    if ch > sh / zoom:
        ch = sh / zoom
        cw = ch * w / h
    cx = min(max(focus[0] * sw, cw / 2), sw - cw / 2)
    cy = min(max(focus[1] * sh, ch / 2), sh - ch / 2)
    return im.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize((w, h), Image.LANCZOS)


def save(im, name):
    """JPG with falling quality, or PNG (keeps the rounded corners). A PNG that would be too big gets 255 colours
    plus one transparent colour for the corners (the pictures are Minecraft textures, they keep their look)."""
    path = os.path.join(OUT, name)
    if name.endswith('.jpg'):
        q = 90
        while True:
            im.convert('RGB').save(path, quality=q, optimize=True, progressive=True)
            if os.path.getsize(path) <= MAX_BYTES or q <= 70:
                break
            q -= 3
    else:
        im.save(path, optimize=True)
        if os.path.getsize(path) > MAX_BYTES:
            p = im.convert('RGB').quantize(255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG)
            pal = p.getpalette()[:255 * 3] + [0, 0, 0]
            a = np.array(p)
            if im.mode == 'RGBA':
                a[np.asarray(im.split()[3]) < 128] = 255
            q = Image.fromarray(a, 'P')
            q.putpalette(pal)
            q.save(path, optimize=True, transparency=255)
    size = os.path.getsize(path)
    print(f'{name:24s} {im.size[0]}x{im.size[1]}  {size // 1024} KB')
    assert size < 1024 * 1024, name


def photo(spec, w, h, focus=(0.5, 0.5), zoom=1.0, box=None, enh=(1.02, 1.04, 1.08), r=16):
    return rounded(fit(shot(spec, enh), w, h, focus, zoom, box).convert('RGBA'), r)


def floaters(im, items):
    """Hearts and sparkles of the mod's particles: (name, x, y, size)."""
    for name, x, y, size in items:
        p = tex('particle/' + name, size)
        im.alpha_composite(p, (int(x - p.width / 2), int(y - p.height / 2)))


# ----------------------------------------------------------------------------------------------- header
HEADER_PETS = [  # (pet, yaw, height, x centre, ground y): back row, then front row
    ('desert_dragon', 32, 160, 862, 296), ('jungle_dragon', 26, 160, 1026, 290), ('sculk_wisp', 18, 172, 1186, 294),
    ('tide_dragon', -26, 160, 1346, 290), ('ember_pup', -32, 166, 1508, 296),
    ('frost_penguin', 24, 160, 792, 474), ('void_kitten', 30, 146, 952, 476), ('pebble_golem', 8, 146, 1110, 478),
    ('hex_toad', -26, 138, 1270, 476), ('mimic', -22, 150, 1432, 472)]


def ground_shadow(im, x, y, w, alpha=70):
    sh = Image.new('RGBA', (w + 60, 60), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([30, 22, 30 + w, 38], fill=(150, 30, 80, alpha))
    sh = sh.filter(ImageFilter.GaussianBlur(6))
    im.alpha_composite(sh, (int(x - w / 2 - 30), int(y - 30)))


def header(name='header_v2.png', size=(1600, 500)):
    """The ten pets on the pink shell of the toy, the title on the left."""
    w, h = size
    im = candy(w, h, top=(255, 231, 241), bottom=(249, 188, 215))
    glow = Image.new('RGBA', size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([700, 60, 1640, 600], fill=(255, 244, 249, 110))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(70)))
    for pid, yaw, ph, x, y in HEADER_PETS:
        p = pet(pid, ph, yaw=yaw)
        ground_shadow(im, x, y, int(p.width * 0.8))
        im.alpha_composite(p, (int(x - p.width / 2), int(y - p.height + 8)))
    floaters(im, [('heart', 944, 240, 40), ('sparkle_2', 1270, 116, 44), ('heart', 1572, 170, 34),
                  ('sparkle_1', 1030, 368, 30), ('heart', 1190, 352, 30), ('sparkle_3', 1560, 392, 30)])
    d = ImageDraw.Draw(im)
    outlined(d, (58, 84), 'TAMAGOTCHI', title(114), stroke=10)
    tw = d.textlength('TAMAGOTCHI', font=title(114))
    st = sticker('1.2', 104)
    im.alpha_composite(st, (int(58 + tw - 34), 40))
    d = ImageDraw.Draw(im)
    outlined(d, (64, 238), 'Find them. Tame them. Love them.', title(46), fill=CRIMSON, stroke=6, stroke_fill=WHITE,
             drop=False)
    tag = 'Minecraft 26.3 · Fabric'
    f = title(34)
    pw = d.textlength(tag, font=f) + 52
    d.rounded_rectangle([64, 342, 64 + pw, 396], 27, fill=CRIMSON, outline=WHITE, width=4)
    d.text((64 + pw / 2, 370), tag, font=f, fill=WHITE, anchor='mm')
    save(rounded(im, 30), name)


# ----------------------------------------------------------------------------------------------- strips
STRIPS = [('start', 'HOW IT WORKS', lambda: tex('item/tamagotchi_heart', 64)),
          ('pets', 'THE TEN PETS', lambda: tex('item/frost_penguin_spawn_egg', 64)),
          ('care', 'A REAL PET', lambda: tex('item/tama_pager', 64)),
          ('play', 'PLAY TIME', lambda: tex('item/squeaky_ball', 64)),
          ('side', 'ALWAYS AT YOUR SIDE', lambda: van('item/golden_apple', 64)),
          ('furniture', 'FURNITURE AND GADGETS', lambda: furniture('pet_bed', 52, 'red')),
          ('new', 'NEW IN 1.2: MADE FOR MODPACKS', lambda: vcube('block/crafting_table_top', 'block/crafting_table_side',
                                                                  'block/crafting_table_front', a=30))]


def strip(name, text, icon):
    h = 104
    im = gradient(W, h, SHELL, (236, 118, 166))
    dots(im, step=34, r=5, color=(255, 255, 255, 55))
    d = ImageDraw.Draw(im)
    win = lcd(100, 84, r=18, border=WHITE)
    im.alpha_composite(win, (20, 10))
    ic = icon()
    im.alpha_composite(ic, (70 - ic.width // 2, 52 - ic.height // 2))
    d = ImageDraw.Draw(im)
    size = 58
    while d.textlength(text, font=title(size)) > W - 300 and size > 30:
        size -= 2
    outlined(d, (144, 54), text, title(size), stroke=6, anchor='lm')
    for k in range(3):
        x = W - 118 + 36 * k
        d.ellipse([x - 14, 40, x + 14, 68], fill=(200, 80, 130))
        d.ellipse([x - 13, 36, x + 13, 62], fill=BUTTON, outline=WHITE, width=3)
    save(rounded(im, 22), 'strip_%s_v2.png' % name)


def build_strips():
    for name, text, icon in STRIPS:
        strip(name, text, icon)


# ----------------------------------------------------------------------------------------------- video card
def video_card(name='video_v2.jpg'):
    """Picture under the YouTube player: four shots of the showcase as a film strip, a big play button."""
    secs = video_length(VIDEO)
    length = '%d:%02d' % (int(round(secs)) // 60, int(round(secs)) % 60)
    w, h = 1200, 675
    im = Image.new('RGBA', (w, h), SHELL + (255,))
    shots = [('tama2/tame_heart@1.9', (0.5, 0.5), 1.15), ('tama2/wheel@2.2', (0.5, 0.56), 1.2),
             ('tama2/dance@2.2', (0.42, 0.56), 1.25), ('tama2/plush_sleep@2.8', (0.62, 0.58), 1.3)]
    sw = w // len(shots)
    for k, (spec, focus, zoom) in enumerate(shots):
        im.paste(fit(shot(spec, (1.04, 1.04, 1.1)), sw, h, focus, zoom), (k * sw, 0))
    shade = Image.new('RGBA', (w, h))
    d = ImageDraw.Draw(shade)
    for y in range(h):
        t = abs(y - h * 0.52) / (h * 0.52)
        d.line([(0, y), (w, y)], fill=(120, 14, 60, int(12 + 200 * t ** 2.0)))
    for k in range(1, len(shots)):
        d.line([(k * sw, 0), (k * sw, h)], fill=WHITE + (255,), width=6)
    im = Image.alpha_composite(im, shade)
    d = ImageDraw.Draw(im)
    outlined(d, (w // 2, 82), 'MEET THE PETS', title(84), stroke=9, anchor='mm')
    outlined(d, (w // 2, 150), 'The Tamagotchi showcase', title(38), fill=SHELL_LIGHT, stroke=5, anchor='mm')
    p = play_glyph(184)
    shadowed(im, p, ((w - 184) // 2, (h - 184) // 2 + 6), blur=14, offset=(0, 8), alpha=150, color=(60, 0, 30))
    d = ImageDraw.Draw(im)
    minutes = int(round(secs / 60))
    outlined(d, (w // 2, h - 88), 'WATCH THE %d-MINUTE SHOWCASE' % minutes, title(58), stroke=8, anchor='mm')
    f = small(30)
    tw = d.textlength(length, font=f)
    d.rounded_rectangle([w - 40 - tw - 28, h - 70, w - 40, h - 28], 8, fill=(0, 0, 0, 200))
    d.text((w - 40 - 14, h - 49), length, font=f, fill=WHITE, anchor='rm')
    save(im.convert('RGB'), name)


# ----------------------------------------------------------------------------------------------- at a glance
def shears_and_chest(size):
    g = Image.new('RGBA', (int(size * 1.7), size), (0, 0, 0, 0))
    c = chest(int(size * 0.42))
    g.alpha_composite(c, (0, size - c.height))
    sh = van('item/shears', int(size * 0.8))
    g.alpha_composite(sh, (g.width - sh.width, (size - sh.height) // 2))
    return g


def need_grid(size):
    """The four need icons of the pet screen on a little LCD."""
    g = lcd(size, size, r=14)
    s = (size - 30) // 2
    for i in range(4):
        ic = need_icon(i, s - 6)
        g.alpha_composite(ic, (15 + (i % 2) * s + 3, 15 + (i // 2) * s + 3))
    return g


NEW_12 = [  # CHANGELOG.md, section 1.2.0
    (lambda: van('item/bread', 64), 'Food from\nother mods'),
    (lambda: vcube('block/diamond_ore', a=32), 'Ores from\nother mods'),
    (lambda: vcube('block/mossy_stone_bricks', a=32), '{lookalikes} more\npet homes'),
    (lambda: shears_and_chest(66), 'Any chest,\nany shears'),
    (lambda: van('item/knowledge_book', 64), 'Tooltips and\nrecipe unlocks'),
]


def glance(name='glance_v2.png'):
    c = counts()
    tiles = [
        (lambda: pet('frost_penguin', 100, yaw=24), c['pets'], 'PETS', 'each with its own home and talent'),
        (lambda: vcube('block/sandstone_top', 'block/chiseled_sandstone', a=46), c['homes'], 'HOMES',
         '+%d look-alikes from other mods' % c['lookalikes']),
        (lambda: need_grid(100), len(c['needs']), 'NEEDS', 'hunger, fun, energy, hygiene'),
        (lambda: furniture('toy_box', 76), c['blocks'], 'FURNITURE',
         '%d pieces and %d plushies' % (c['furniture'], c['plushies'])),
        (lambda: tex('item/pet_kibble', 88), c['foods'], 'PET FOODS', 'every pet has a favourite'),
        (lambda: chest(44), c['slots'], 'SLOTS', 'in every backpack (%d for the Mimic)' % c['belly']),
    ]
    cols, tw, th, gx, gy = 3, 368, 216, 16, 16
    top, band_h = 104, 178
    by = top + 2 * th + gy + 44
    h = by + band_h + 34
    im = candy(W, h)
    d = ImageDraw.Draw(im)
    outlined(d, (W // 2, 58), 'TAMAGOTCHI AT A GLANCE', title(58), stroke=8, anchor='mm')
    x0 = (W - cols * tw - (cols - 1) * gx) // 2
    for k, (ic, num, label, sub) in enumerate(tiles):
        x, y = x0 + (k % cols) * (tw + gx), top + (k // cols) * (th + gy)
        shadowed(im, card(tw, th), (x, y), blur=8, offset=(0, 5), alpha=80)
        d = ImageDraw.Draw(im)
        cx, cy = x + 84, y + 90
        d.ellipse([cx - 64, cy - 64, cx + 64, cy + 64], fill=SHELL_LIGHT)
        pic = ic()
        im.alpha_composite(pic, (cx - pic.width // 2, cy - pic.height // 2))
        d = ImageDraw.Draw(im)
        outlined(d, (x + 168, y + 108), str(num), title(104), fill=WHITE, stroke=7, stroke_fill=CRIMSON, anchor='ls')
        f = title(36)
        while d.textlength(label, font=f) > tw - 180:
            f = title(f.size - 1)
        d.text((x + 170, y + 150), label, font=f, fill=BERRY, anchor='ls')
        f = small(21)
        while d.textlength(sub, font=f) > tw - 28:
            f = small(f.size - 1)
        d.text((x + tw // 2, y + th - 26), sub, font=f, fill=INK, anchor='ms')
    band = Image.new('RGBA', (W - 32, band_h), (0, 0, 0, 0))
    ImageDraw.Draw(band).rounded_rectangle([0, 0, band.width - 1, band_h - 1], 24, fill=CRIMSON + (255,),
                                           outline=WHITE + (255,), width=4)
    dots(band, step=30, r=4, color=(255, 255, 255, 40))
    im.alpha_composite(rounded(band, 24), (16, by))
    d = ImageDraw.Draw(im)
    f = title(34)
    pill = 'NEW IN 1.2'
    pw = d.textlength(pill, font=f) + 48
    d.rounded_rectangle([W // 2 - pw / 2, by - 25, W // 2 + pw / 2, by + 25], 25, fill=BUTTON, outline=WHITE, width=4)
    d.text((W // 2, by + 1), pill, font=f, fill=BERRY, anchor='mm')
    n = len(NEW_12)
    cw = (W - 64) / n
    for k, (ic, label) in enumerate(NEW_12):
        cx = 32 + cw * k + cw / 2
        pic = ic()
        im.alpha_composite(pic, (int(cx - pic.width / 2), by + 40 + (66 - pic.height) // 2))
        d = ImageDraw.Draw(im)
        for i, ln in enumerate(label.format(**c).split('\n')):
            d.text((cx, by + 114 + 28 * i), ln, font=small(23), fill=WHITE, anchor='ma')
    save(rounded(im, 26), name)


# ----------------------------------------------------------------------------------------------- flows
def step_card(w, h, pic, n, head, text, photo_h=250, extra=None):
    """A card with a portrait picture, a step number, a title and a few lines of text."""
    c = card(w, h)
    if pic is not None:
        c.alpha_composite(pic, (8, 8))
    if extra:
        extra(c)
    d = ImageDraw.Draw(c)
    y = photo_h + 22
    badge(c, (30, y + 18), n, r=18)
    d = ImageDraw.Draw(c)
    f = title(32)
    while d.textlength(head, font=f) > w - 70 and f.size > 18:
        f = title(f.size - 1)
    d.text((58, y + 20), head, font=f, fill=BERRY, anchor='lm')
    para(d, (16, y + 50), text, small(20), w - 30)
    return c


def lcd_hearts(n_full, total, size):
    g = lcd(total * (size + 6) + 26, size + 30, r=12)
    for i in range(total):
        ic = heart_icon(0 if i < n_full else 2, size)
        g.alpha_composite(ic, (15 + i * (size + 6), 15))
    return g


def row_of_cards(im, cards, y, M=20):
    gap = (W - 2 * M - sum(k.width for k in cards)) / (len(cards) - 1)
    x, placed = M, []
    for k in cards:
        shadowed(im, k, (int(x), y), blur=9, offset=(0, 6), alpha=90)
        placed.append((int(x), y, k.width, k.height))
        x += k.width + gap
    d = ImageDraw.Draw(im)
    for (x0, y0, w0, h0), (x1, _, _, _) in zip(placed, placed[1:]):
        ya = y0 + 138
        arrow(d, [(x0 + w0 + 7, ya), (x1 - 7, ya)], width=12, head=20)
    return placed


def control(icons, label, w=184):
    """One cell of the controls row: key and mouse pictures, a label under them."""
    cell = Image.new('RGBA', (w, 118), (0, 0, 0, 0))
    parts = []
    for ic in icons:
        if isinstance(ic, str):
            k = Image.new('RGBA', (140, 56), (0, 0, 0, 0))
            kw = keycap(k, 0, 0, ic, h=44)
            parts.append(k.crop((0, 0, kw + 1, 52)))
        else:
            parts.append(ic)
    plus = 22
    total = sum(p.width for p in parts) + plus * (len(parts) - 1)
    x = (w - total) // 2
    d = ImageDraw.Draw(cell)
    for i, p in enumerate(parts):
        cell.alpha_composite(p, (int(x), int(32 - p.height / 2)))
        x += p.width
        if i < len(parts) - 1:
            d.text((x + plus / 2, 32), '+', font=title(30), fill=CRIMSON, anchor='mm')
            x += plus
    para(d, (w // 2, 74), label, small(20), w - 8, anchor='ma', gap=2)
    return cell


def flow_start(name='flow_start_v2.png'):
    """Find, tame, care, bond, talent; under them the controls on your pet (TamaPet.mobInteract)."""
    c = counts()
    cw, ch, ph = 204, 470, 250
    pic = lambda spec, focus, zoom: photo(spec, cw - 16, ph, focus, zoom)
    heart = lambda k: k.alpha_composite(tex('item/tamagotchi_heart', 56), (k.width - 72, ph - 66))
    hearts = lambda k: k.alpha_composite(lcd_hearts(c['hearts'], c['hearts'], 22), (14, ph - 58))
    cards = [
        step_card(cw, ch, pic('tama/jungle_wild@2.8', (0.52, 0.52), 1.5), 1, 'FIND',
                  'Pets hide in structures, but not every structure holds one.'),
        step_card(cw, ch, pic('tama2/tame_heart@3.1', (0.45, 0.42), 1.35), 2, 'TAME',
                  'Use a Tamagotchi Heart on a wild pet. It gets a name and follows you.', extra=heart),
        step_card(cw, ch, pic('tama2/bowl_eat@1.3', (0.44, 0.5), 1.45), 3, 'CARE',
                  'Feed it, play with it, keep it clean and let it sleep.'),
        step_card(cw, ch, pic('tama2/petting_closeups@4.5', (0.48, 0.45), 1.3), 4, 'BOND',
                  'Every bit of care grows your bond, up to %d hearts.' % c['hearts'], extra=hearts),
        step_card(cw, ch, pic('tama2/roast@1.5', (0.42, 0.56), 1.1), 5, 'TALENT',
                  'Happy pets use their talent. At full bond it recharges %d%% sooner.' % c['bond_faster']),
    ]
    band_h = 176
    h = 20 + ch + 34 + band_h + 24
    im = candy(W, h)
    row_of_cards(im, cards, 20)
    by = 20 + ch + 34
    band = card(W - 40, band_h, r=24, fill=(255, 244, 248), outline=WHITE)
    im.alpha_composite(band, (20, by))
    d = ImageDraw.Draw(im)
    pill = 'ON YOUR PET'
    f = title(30)
    pw = d.textlength(pill, font=f) + 44
    d.rounded_rectangle([W // 2 - pw / 2, by - 22, W // 2 + pw / 2, by + 22], 22, fill=CRIMSON, outline=WHITE, width=4)
    d.text((W // 2, by + 1), pill, font=f, fill=WHITE, anchor='mm')
    rc = mouse(54)
    cells = [control([rc], 'Pet it'),
             control(['Shift', rc], 'Pet screen'),
             control(['Shift', chest(22)], 'Backpack on'),
             control(['Shift', van('item/shears', 44)], 'Backpack off'),
             control([tex('item/tama_pager', 50)], 'Sit or follow'),
             control([tex('item/pet_kibble', 46)], 'Feed it')]
    cwid = (W - 80) / len(cells)
    for k, cell in enumerate(cells):
        im.alpha_composite(cell, (int(40 + cwid * k + (cwid - cell.width) / 2), by + 36))
    save(rounded(im, 26), name)


# ----------------------------------------------------------------------------------------------- the ten pets
SHORT_TALENT = {  # talent.tamagotchi.<pet>.desc in assets/tamagotchi/lang/en_us.json, shortened
    'desert_dragon': 'Roasts raw food and smelts raw ore with a puff of flame.',
    'jungle_dragon': 'Makes the crops and saplings around it grow.',
    'tide_dragon': "Water Breathing and Dolphin's Grace while you swim near it.",
    'frost_penguin': 'Water freezes under your feet while it follows you.',
    'ember_pup': 'Fire Resistance when you catch fire. Swims through lava.',
    'sculk_wisp': 'A sonar ping makes hostile mobs glow through walls.',
    'void_kitten': 'Pulls dropped items into its backpack, or to you.',
    'pebble_golem': 'Sniffs out the best ore nearby, modded ores too.',
    'hex_toad': 'Brews you a random helpful potion effect.',
    'mimic': 'A {slots}-slot belly ({belly} with a backpack) that coughs up treasure.',
}
PET_YAW = {'desert_dragon': 30, 'jungle_dragon': 30, 'tide_dragon': 30, 'frost_penguin': 22, 'ember_pup': 30,
           'sculk_wisp': 16, 'void_kitten': 30, 'pebble_golem': 12, 'hex_toad': 26, 'mimic': 20}


def mix(c, t, k):
    return tuple(int(c[i] + (t[i] - c[i]) * k) for i in range(3))


def pet_card(pid, p, c, w, h):
    k = card(w, h, r=22)
    d = ImageDraw.Draw(k)
    col = ((p['color'] >> 16) & 255, (p['color'] >> 8) & 255, p['color'] & 255)
    cx, cy, r = w // 2, 104, 88
    d.ellipse([cx - r - 5, cy - r - 5, cx + r + 5, cy + r + 5], fill=WHITE)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=mix(col, WHITE, 0.55))
    dots(k, step=26, r=3, color=(255, 255, 255, 70), box=(cx - r, cy - r, cx + r, cy + r))
    m = Image.new('L', k.size, 0)
    ImageDraw.Draw(m).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    base = k.copy()
    pic = pet(pid, 150, yaw=PET_YAW[pid])
    ground_shadow(k, cx, cy + 74, int(pic.width * 0.7), alpha=60)
    k.alpha_composite(pic, (cx - pic.width // 2, cy + 80 - pic.height))
    d = ImageDraw.Draw(k)
    if p.get('bites'):
        f = small(15)
        tw = d.textlength('BITES BACK', font=f) + 18
        d.rounded_rectangle([8, 8, 8 + tw, 34], 13, fill=CRIMSON, outline=WHITE, width=2)
        d.text((8 + tw / 2, 21), 'BITES BACK', font=f, fill=WHITE, anchor='mm')
    y = 206
    f = title(29)
    while d.textlength(p['name'], font=f) > w - 20:
        f = title(f.size - 1)
    d.text((cx, y), p['name'], font=f, fill=BERRY, anchor='mm')
    y += 26
    for home, chance in p['homes']:
        label = '%s  %d%%' % (home, chance)
        f = small(17)
        while d.textlength(label, font=f) > w - 44:
            f = small(f.size - 1)
        tw = d.textlength(label, font=f) + 26
        d.rounded_rectangle([cx - tw / 2, y, cx + tw / 2, y + 28], 14, fill=(255, 236, 244), outline=SHELL, width=2)
        d.text((cx, y + 14), label, font=f, fill=INK, anchor='mm')
        y += 33
    y = max(y + 14, 314)
    spark = tex('particle/sparkle_2', 22)
    f = title(25)
    tw = d.textlength(p['talent'], font=f)
    k.alpha_composite(spark, (int(cx - (tw + 28) / 2), y - 11))
    d = ImageDraw.Draw(k)
    d.text((cx + 14, y), p['talent'], font=f, fill=CRIMSON, anchor='mm')
    para(d, (cx, y + 20), SHORT_TALENT[pid].format(**c), small(18), w - 26, anchor='ma', gap=3)
    treat = tex('item/' + p['treat'], 34)
    tname = ' '.join(x.capitalize() for x in p['treat'].split('_'))
    f = small(17)
    tw = 38 + d.textlength(tname, font=f)
    x0 = int(cx - tw / 2)
    d.line([(18, h - 50), (w - 18, h - 50)], fill=SHELL_LIGHT, width=2)
    k.alpha_composite(treat, (x0, h - 42))
    d = ImageDraw.Draw(k)
    d.text((x0 + 40, h - 25), tname, font=f, fill=INK, anchor='lm')
    return k


def pets_image(name='pets_v2.png'):
    """The ten pets: home and chance (world/PetSpawns.java, pet_home tags), talent (lang), favourite treat
    (pet/PetSpecies.java); BITES BACK = PetGoals.dangerous()."""
    c = counts()
    cols, w, h, gx, gy = 5, 224, 470, 10, 14
    x0 = (W - cols * w - (cols - 1) * gx) // 2
    H = 20 + 2 * h + gy + 20 + 34
    im = candy(W, H)
    for i, (pid, p) in enumerate(c['info'].items()):
        k = pet_card(pid, p, c, w, h)
        shadowed(im, k, (x0 + (i % cols) * (w + gx), 20 + (i // cols) * (h + gy)), blur=8, offset=(0, 5), alpha=80)
    d = ImageDraw.Draw(im)
    note = 'Chance that a structure holds its pet.   Bottom: its favourite treat.'
    d.text((W // 2, H - 30), note, font=small(19), fill=BERRY, anchor='mm')
    save(rounded(im, 26), name)


def flow_side(name='flow_side_v2.png'):
    """Backpack, golden apple, fights, fainting and hatching (TamaPet, PetGoals, PetIncubatorBlockEntity)."""
    c = counts()
    cw, ch, ph = 204, 470, 250
    pic = lambda spec, focus, zoom: photo(spec, cw - 16, ph, focus, zoom)
    corner = lambda img: (lambda k: k.alpha_composite(img, (k.width - img.width - 14, ph - img.height - 8)))
    cards = [
        step_card(cw, ch, pic('tama2/backpack_on@2.8', (0.4, 0.58), 1.25), 1, 'BACKPACK',
                  '%d slots for your things. Shears take it off, and it all spills out.' % c['slots'],
                  extra=corner(chest(30))),
        step_card(cw, ch, pic('tama2/feed_owner@2.2', (0.6, 0.6), 1.4), 2, 'LIFESAVER',
                  'Put a golden apple in: it feeds you one when your health is low.',
                  extra=corner(van('item/golden_apple', 56))),
        step_card(cw, ch, pic('tama2/fight@1.7', (0.72, 0.4), 1.45), 3, 'FIGHTS',
                  'It fights at your side and eats from its backpack when it is hurt.'),
        step_card(cw, ch, pic('tama2/faint_egg@3.0', (0.21, 0.37), 2.8), 4, 'NEVER DIES',
                  'It faints into a Tama Egg that keeps everything.'),
        step_card(cw, ch, pic('tama2/incubator_hatch@5.6', (0.52, 0.52), 1.35), 5, 'HATCH',
                  'Use the egg on a block, or hatch it in a Pet Incubator in %d seconds.' % c['hatch']),
    ]
    h = 20 + ch + 24
    im = candy(W, h)
    row_of_cards(im, cards, 20)
    save(rounded(im, 26), name)


# ----------------------------------------------------------------------------------------------- care
def icon_row(icons, w, size=52, gap=10):
    row = Image.new('RGBA', (w, size + 8), (0, 0, 0, 0))
    total = sum(i.width for i in icons) + gap * (len(icons) - 1)
    x = (w - total) // 2
    for i in icons:
        row.alpha_composite(i, (x, (size + 8 - i.height) // 2))
        x += i.width + gap
    return row


def lcd_label(w, h, icon, text):
    g = lcd(w, h, r=14)
    g.alpha_composite(icon, (22, (h - icon.height) // 2))
    ImageDraw.Draw(g).text((22 + icon.width + 16, h // 2 + 2), text, font=pixel(22), fill=LCD_DARK, anchor='lm')
    return g


def care(name='care_v2.png'):
    """The four needs (pet/PetNeeds.java) and what fills them, the five moods with what they change
    (Talents/PetGoals: no talent below Okay, no fights when Miserable) and the pager beeps (TamaPet.checkBeeps)."""
    c = counts()
    cw, ch, gap = 276, 430, 16
    x0 = (W - 4 * cw - 3 * gap) // 2
    needs = [
        ('HUNGER', ('tama2/bowl_eat@1.3', (0.47, 0.5), 1.3),
         [tex('item/pet_kibble', 50), tex('item/dragon_fruit', 50), furniture('food_bowl', 40),
          furniture('treat_dispenser', 52)],
         'Kibble, treats and food. It eats from a Food Bowl by itself.'),
        ('FUN', ('tama2/feather_wand@4.0', (0.5, 0.43), 1.0),
         [tex('item/laser_pointer', 50), tex('item/squeaky_ball', 50), tex('item/feather_wand', 50)],
         'Toys, petting, furniture and other pets.'),
        ('ENERGY', ('tama2/plush_sleep@2.8', (0.5, 0.47), 1.05),
         [furniture('pet_bed', 40, 'red'), furniture('pet_basket', 42, 'pink'), furniture('dragon_nest', 34)],
         'Sleep in a bed, basket or nest, faster next to its own plush.'),
        ('HYGIENE', ('tama2/brush@1.5', (0.5, 0.45), 1.3),
         [tex('item/pet_brush', 50), furniture('pet_bath', 46)],
         'The Pet Brush, or a Pet Bath filled with water.'),
    ]
    mood_h = 236
    H = 20 + ch + 58 + mood_h + 22
    im = candy(W, H)
    for k, (label, spec, icons, text) in enumerate(needs):
        cd_ = card(cw, ch)
        cd_.alpha_composite(lcd_label(cw - 16, 64, need_icon(k, 40), label), (8, 8))
        cd_.alpha_composite(photo(spec[0], cw - 16, 190, spec[1], spec[2], r=14), (8, 80))
        cd_.alpha_composite(icon_row(icons, cw), (0, 282))
        para(ImageDraw.Draw(cd_), (cw // 2, 346), text, small(19), cw - 30, anchor='ma', gap=3)
        shadowed(im, cd_, (x0 + k * (cw + gap), 20), blur=8, offset=(0, 5), alpha=80)
    d = ImageDraw.Draw(im)
    my = 20 + ch + 58
    for k in range(4):
        x = x0 + k * (cw + gap) + cw // 2
        arrow(d, [(x, 20 + ch + 8), (x, my - 8)], width=10, head=18)
    pw_ = W - 2 * x0
    panel = lcd(pw_, mood_h, r=22, border=SHELL_DARK)
    pd = ImageDraw.Draw(panel)
    mw = 744
    pd.text((30, 34), 'MOOD', font=pixel(24), fill=LCD_DARK, anchor='lm')
    names = [n.capitalize() for n in c['moods']]
    names[-1] += '!'
    fw = (mw - 60) / len(names)
    for i in range(len(names)):
        cx = 30 + fw * i + fw / 2
        panel.alpha_composite(mood_face(i, 64), (int(cx - 32), 54))
        pd.text((cx, 138), names[i], font=small(20), fill=LCD_DARK, anchor='mm')
    for a, b, t in [(0, 0, "won't fight"), (1, 1, 'no talent'), (2, 4, 'uses its talent')]:
        xa, xb = 30 + fw * a + 10, 30 + fw * (b + 1) - 10
        pd.line([(xa, 164), (xb, 164)], fill=LCD_MID, width=3)
        pd.line([(xa, 158), (xa, 170)], fill=LCD_MID, width=3)
        pd.line([(xb, 158), (xb, 170)], fill=LCD_MID, width=3)
        pd.text(((xa + xb) / 2, 196), t, font=small(20), fill=CRIMSON if a == 0 else LCD_DARK, anchor='mm')
    pd.line([(mw + 6, 26), (mw + 6, mood_h - 26)], fill=LCD_MID, width=3)
    px = mw + 30
    panel.alpha_composite(tex('item/tama_pager', 96), (px, 24))
    for i, b in enumerate(['emote_hungry', 'emote_bored', 'emote_sleepy', 'emote_dirty']):
        panel.alpha_composite(tex('particle/' + b, 52), (px + 112 + (i % 2) * 60, 16 + (i // 2) * 56))
    pd = ImageDraw.Draw(panel)
    pd.text((pw_ - 30, 72), 'BEEP!', font=title(38), fill=CRIMSON, anchor='rm')
    para(pd, (px + (pw_ - 30 - px) / 2, 140), 'The Tama Pager beeps when a pet is hungry, bored, sleepy, dirty or hurt.',
         small(19), pw_ - 30 - px, anchor='ma', gap=3, fill=LCD_DARK)
    shadowed(im, panel, (x0, my), blur=8, offset=(0, 5), alpha=80)
    save(rounded(im, 26), name)


# ----------------------------------------------------------------------------------------------- collages
def T(spec, cap, w=1.0, focus=(0.5, 0.5), zoom=1.0, enh=(1.02, 1.04, 1.08), cross=False):
    return dict(spec=spec, cap=cap, w=w, focus=focus, zoom=zoom, enh=enh, cross=cross)


def caption(tile, text, size=28):
    d = ImageDraw.Draw(tile)
    while size > 16 and d.textlength(text, font=title(size)) > tile.width - 34:
        size -= 1
    band = size + 40
    shade = Image.new('RGBA', tile.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    for i in range(band):
        sd.line([(0, tile.height - band + i), (tile.width, tile.height - band + i)],
                fill=(110, 10, 50, int(170 * (i / band) ** 1.3)))
    tile.alpha_composite(shade)
    d = ImageDraw.Draw(tile)
    outlined(d, (16, tile.height - 14), text, title(size), stroke=4, anchor='ld')


def collage(name, rows, pad=16, gap=12):
    """rows: (height, [tile, ...]); white-framed tiles with a caption on a pink, dotted background."""
    inner = W - 2 * pad
    total_h = pad + sum(h for h, _ in rows) + gap * (len(rows) - 1) + pad
    im = candy(W, total_h)
    y = pad
    for h, tiles in rows:
        weights = sum(t['w'] for t in tiles)
        avail = inner - gap * (len(tiles) - 1)
        x = pad
        for i, t in enumerate(tiles):
            tw = int(avail * t['w'] / weights) if i < len(tiles) - 1 else pad + inner - x
            tile = fit(shot(t['spec'], t['enh'], t['cross']), tw, h, t['focus'], t['zoom']).convert('RGBA')
            caption(tile, t['cap'], 28 if tw > 330 else 25)
            fr = Image.new('RGBA', (tw, h), (0, 0, 0, 0))
            ImageDraw.Draw(fr).rounded_rectangle([0, 0, tw - 1, h - 1], 18, fill=WHITE + (255,))
            fr.alpha_composite(rounded(tile.crop((4, 4, tw - 4, h - 4)), 14), (4, 4))
            shadowed(im, fr, (x, y), blur=6, offset=(0, 4), alpha=70)
            x += tw + gap
        y += h + gap
    save(rounded(im, 26), name)


COLLAGES = {  # frames and crops picked from contact sheets of footage/tama2 and footage/tama
    'talents_v2.png': [
        (380, [T('tama2/roast@1.5', 'Ember Roast', focus=(0.5, 0.55)),
               T('tama2/fly_follow@2.2', 'Dragons fly', focus=(0.5, 0.45)),
               T('tama2/ore_glow@3.1', 'Ore Sniffer', focus=(0.5, 0.55)),
               T('tama2/lava_swim@2.5', 'Warm Heart', focus=(0.5, 0.48))]),
    ],
    'play_v2.png': [
        (372, [T('tama2/fetch_ball@3.4', 'Squeaky Ball', focus=(0.5, 0.5), zoom=1.1),
               T('tama2/feather_wand@4.0', 'Feather Wand', focus=(0.5, 0.45), cross=True),
               T('tama2/laser_chase@3.1', 'Laser Pointer', focus=(0.45, 0.42)),
               T('tama2/wheel@1.3', 'Running Wheel', focus=(0.5, 0.52), zoom=1.1)]),
        (372, [T('tama2/bounce@1.3', 'Bouncy Mushroom', focus=(0.5, 0.48), zoom=1.1),
               T('tama2/toy_box_play@3.1', 'Toy Box', focus=(0.5, 0.52), zoom=1.15),
               T('tama2/dance@2.2', 'Dancing', focus=(0.45, 0.5), zoom=1.1),
               T('tama2/campfire_warm@2.2', 'By the campfire', focus=(0.55, 0.5), enh=(1.25, 1.06, 1.08))]),
    ],
    'furniture_v2.png': [
        (300, [T('tama2/plush_shelf@3.1', 'Plushies of all ten pets', 1.3, focus=(0.5, 0.37)),
               T('tama2/plush_cuddle@1.9', 'Lonely pets cuddle them', 1.0, focus=(0.5, 0.45), zoom=1.1)]),
        (330, [T('tama2/portrait_paint@3.8', 'Pet Portrait', focus=(0.42, 0.5), zoom=1.3, cross=True),
               T('tama2/treat_dispenser@3.8', 'Treat Dispenser', focus=(0.55, 0.5), zoom=1.05),
               T('tama2/incubator_hatch@2.2', 'Pet Incubator', focus=(0.5, 0.5), zoom=1.4),
               T('tama2/pet_flap@3.8', 'Pet Flap', focus=(0.55, 0.5), zoom=1.2),
               T('tama2/egg_lamp@3.5', 'Egg Lamp', focus=(0.5, 0.55), zoom=1.2, enh=(1.3, 1.05, 1.08), cross=True)]),
    ],
}


def build_collages(names=None):
    for name, rows in COLLAGES.items():
        if names and name not in names:
            continue
        collage(name, rows)


# ----------------------------------------------------------------------------------------------- furniture shelf
SHELF = [['pet_bed', 'pet_basket', 'dragon_nest', 'food_bowl', 'treat_dispenser', 'pet_bath', 'pet_house', 'pet_flap'],
         ['bouncy_mushroom', 'running_wheel', 'scratching_post', 'toy_box', 'pet_portrait', 'egg_lamp', 'pet_incubator']]
SHELF_COLOUR = {'pet_bed': 'red', 'pet_basket': 'pink', 'egg_lamp': 'light_blue', 'pet_portrait': 'pink'}


def dyeable():
    """Blocks whose item model picks the colour of a block state property (color, or the portrait's backdrop)."""
    out = set()
    for f in os.listdir(os.path.join(ASSETS, 'items')):
        m = json.loads(read(ASSETS, 'items', f))['model']
        if m.get('block_state_property') in ('color', 'backdrop'):
            out.add(f[:-5])
    return out


def shelf(name='shelf_v2.png'):
    c = counts()
    lang = json.loads(read(ASSETS, 'lang', 'en_us.json'))
    dye = dyeable()
    listed = {b for row in SHELF for b in row}
    blocks = sorted(f[:-5] for f in os.listdir(os.path.join(ASSETS, 'blockstates')))
    assert listed | {b for b in blocks if b.endswith('_plush')} == set(blocks), 'shelf misses a block'
    rows_h = [212, 212, 196]
    H = 24 + sum(rows_h) + 30
    im = candy(W, H)
    d = ImageDraw.Draw(im)
    y = 24
    for r, row in enumerate(SHELF):
        cw = (W - 48) / 8
        x0 = 24 + (W - 48 - cw * len(row)) / 2
        d.rounded_rectangle([20, y + 128, W - 20, y + 146], 8, fill=(214, 160, 120), outline=(176, 112, 82), width=3)
        for i, b in enumerate(row):
            cx = x0 + cw * i + cw / 2
            pic = furniture(b, 104 if b not in ('pet_flap', 'pet_portrait', 'running_wheel', 'pet_house') else 116,
                            SHELF_COLOUR.get(b))
            if pic.width > cw - 12:
                pic = premul_resize(pic, (int(cw - 12), int(pic.height * (cw - 12) / pic.width)))
            im.alpha_composite(pic, (int(cx - pic.width / 2), y + 136 - pic.height))
            d = ImageDraw.Draw(im)
            label = lang['block.tamagotchi.' + b]
            para(d, (cx, y + 154), label, small(18), cw - 6, fill=INK, anchor='ma', gap=0)
            if b in dye:
                sw = Image.new('RGBA', (34, 34), (0, 0, 0, 0))
                sd = ImageDraw.Draw(sw)
                for k, col in enumerate([(230, 60, 70), (250, 200, 60), (80, 190, 90), (70, 140, 230)]):
                    sd.pieslice([1, 1, 32, 32], k * 90, k * 90 + 90, fill=col)
                sd.ellipse([1, 1, 32, 32], outline=WHITE, width=3)
                im.alpha_composite(sw, (int(cx + 24), y + 4))
        y += rows_h[r]
    # the plushies
    d.rounded_rectangle([20, y + 118, W - 20, y + 136], 8, fill=(214, 160, 120), outline=(176, 112, 82), width=3)
    pw = (W - 48) / 10
    for i, pid in enumerate(c['info']):
        p = plush(pid, 92)
        cx = 24 + pw * i + pw / 2
        im.alpha_composite(p, (int(cx - p.width / 2), y + 126 - p.height))
    d = ImageDraw.Draw(im)
    d.text((W // 2, y + 162), 'and a plush of every pet', font=small(20), fill=INK, anchor='mm')
    lg = Image.new('RGBA', (34, 34), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lg)
    for k, col in enumerate([(230, 60, 70), (250, 200, 60), (80, 190, 90), (70, 140, 230)]):
        ld.pieslice([1, 1, 32, 32], k * 90, k * 90 + 90, fill=col)
    ld.ellipse([1, 1, 32, 32], outline=WHITE, width=3)
    legend = 'in %d colours' % c['colours']
    lw = d.textlength(legend, font=small(20))
    im.alpha_composite(lg, (int(W - 40 - lw - 42), y + 145))
    d = ImageDraw.Draw(im)
    d.text((W - 40, y + 162), legend, font=small(20), fill=INK, anchor='rm')
    save(rounded(im, 26), name)


# ----------------------------------------------------------------------------------------------- made for modpacks
def modpack(name='modpack_v2.png'):
    """What 1.2 changed for modpacks (CHANGELOG.md 1.2.0; tags in data/tamagotchi/tags, pet/PetSpecies.Diet)."""
    c = counts()
    cw, ch, gap = 276, 330, 16
    x0 = (W - 4 * cw - 3 * gap) // 2
    golem = pet('pebble_golem', 70, yaw=12)
    cards = [
        ('FOOD', [van('item/bread', 60), van('item/cookie', 54), van('item/sweet_berries', 54)],
         'Pets eat food from other mods too.', 'c:foods'),
        ('ORES', [vcube('block/diamond_ore', a=30), golem],
         'The Pebble Golem sniffs out modded ores.', 'c:ores'),
        ('HOMES', [vcube('block/mossy_stone_bricks', a=30), vcube('block/sandstone_top', 'block/chiseled_sandstone', a=30),
                   vcube('block/snow', a=30)],
         '%d look-alike structures of other mods are pet homes too.' % c['lookalikes'], 'tamagotchi:pet_home'),
        ('BACKPACK', [chest(30), van('item/shears', 54)],
         'Any wooden chest puts it on, any shears take it off.', 'c:chests/wooden'),
    ]
    band_h = 150
    H = 20 + ch + 30 + band_h + 22
    im = candy(W, H)
    for k, (head, icons, text, tag) in enumerate(cards):
        cd_ = card(cw, ch)
        d = ImageDraw.Draw(cd_)
        d.text((cw // 2, 40), head, font=title(36), fill=BERRY, anchor='mm')
        cd_.alpha_composite(icon_row(icons, cw, size=70, gap=12), (0, 72))
        para(d, (cw // 2, 172), text, small(21), cw - 34, anchor='ma', gap=3)
        f = pixel(13)
        while d.textlength(tag, font=f) > cw - 56:
            f = pixel(f.size - 1)
        tw = d.textlength(tag, font=f) + 26
        d.rounded_rectangle([cw / 2 - tw / 2, ch - 56, cw / 2 + tw / 2, ch - 24], 10, fill=LCD, outline=LCD_MID, width=2)
        d.text((cw / 2, ch - 39), tag, font=f, fill=LCD_DARK, anchor='mm')
        shadowed(im, cd_, (x0 + k * (cw + gap), 20), blur=8, offset=(0, 5), alpha=80)
    by = 20 + ch + 30
    band = card(W - 2 * x0, band_h, r=24, fill=(255, 244, 248), outline=WHITE)
    im.alpha_composite(band, (x0, by))
    d = ImageDraw.Draw(im)
    pill = 'ALSO NEW'
    f = title(30)
    pw = d.textlength(pill, font=f) + 44
    d.rounded_rectangle([W // 2 - pw / 2, by - 22, W // 2 + pw / 2, by + 22], 22, fill=CRIMSON, outline=WHITE, width=4)
    d.text((W // 2, by + 1), pill, font=f, fill=WHITE, anchor='mm')
    extras = [(furniture('toy_box', 50), 'Furniture tooltips'),
              (van('item/knowledge_book', 52), 'Recipes unlock early'),
              (furniture('food_bowl', 40), 'Food Bowl with a bone'),
              (van('item/iron_axe', 50), 'Tools mine furniture faster'),
              (tex('item/tamagotchi_heart', 50), '%d fixes' % c['fixes'])]
    ew = (W - 2 * x0 - 20) / len(extras)
    for k, (ic, label) in enumerate(extras):
        cx = x0 + 10 + ew * k + ew / 2
        im.alpha_composite(ic, (int(cx - ic.width / 2), by + 34 + (54 - ic.height) // 2))
        d = ImageDraw.Draw(im)
        para(d, (cx, by + 96), label, small(19), ew - 12, anchor='ma', gap=2)
    save(rounded(im, 26), name)


# ----------------------------------------------------------------------------------------------- main
ALL = ['counts', 'header', 'video', 'glance', 'flow_start', 'pets', 'flow_side', 'care', 'shelf', 'modpack', 'strips',
       'collages']

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    what = sys.argv[3:] or ALL
    if 'counts' in what:
        c = counts()
        print({k: v for k, v in c.items() if k != 'info'})
        for k, v in c['info'].items():
            print(' ', k, v)
    if 'header' in what:
        header()
    if 'video' in what:
        video_card()
    if 'glance' in what:
        glance()
    if 'flow_start' in what:
        flow_start()
    if 'pets' in what:
        pets_image()
    if 'flow_side' in what:
        flow_side()
    if 'care' in what:
        care()
    if 'shelf' in what:
        shelf()
    if 'modpack' in what:
        modpack()
    if 'strips' in what:
        build_strips()
    names = [w for w in what if w in COLLAGES]
    if 'collages' in what or names:
        build_collages(names or None)
