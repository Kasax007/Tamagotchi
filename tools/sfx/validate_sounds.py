#!/usr/bin/env python3
"""Validate the Tamagotchi sound wiring.

Checks (exit code 1 if anything is an error):
  * sounds.json is valid and contains every expected event (10 pets x 5, 10 talents, shared sounds)
  * every event has a matching subtitle key in subtitles_en_us.json and 1-4 sound variants
  * every custom reference (tamagotchi:<group>/<name>) points to an existing Ogg Vorbis file
    (decoded with ffmpeg: mono, 44.1 kHz, no clipping, not silent)
  * every vanilla reference (minecraft:<path>) exists in the Minecraft asset index
    (minecraft/sounds/<path>.ogg), found under ~/.gradle/caches/fabric-loom/assets/indexes
  * pitch / volume / weight values are sane, no duplicate variants
  * no custom .ogg is unreferenced, the custom files total less than 3 MB, README.md has a line per event

Usage:  python3 tools/sfx/validate_sounds.py [--index PATH] [--wait SECONDS] [--fast]
  --index  asset index json (default: from gradle.properties minecraft_version, else the newest in the loom cache)
  --wait   if the index is not there yet (download still running), poll every 20 s for up to SECONDS
  --fast   skip decoding the .ogg files with ffmpeg (only existence + header checks)
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
ASSETS = os.path.join(REPO, 'src', 'main', 'resources', 'assets', 'tamagotchi')
SOUNDS_JSON = os.path.join(ASSETS, 'sounds.json')
SOUND_DIR = os.path.join(ASSETS, 'sounds')
SUBTITLES = os.path.join(HERE, 'subtitles_en_us.json')
README = os.path.join(HERE, 'README.md')
MOD_ID = 'tamagotchi'
MAX_TOTAL_BYTES = 3 * 1024 * 1024

SPECIES = ['desert_dragon', 'jungle_dragon', 'tide_dragon', 'frost_penguin', 'ember_pup', 'sculk_wisp', 'void_kitten',
           'pebble_golem', 'hex_toad', 'mimic']
EXPECTED = ['%s.%s' % (s, k) for s in SPECIES for k in ('ambient', 'happy', 'hurt', 'death', 'attack')]
EXPECTED += ['talent.' + t for t in ('roast', 'grow', 'blessing', 'freeze', 'warm', 'ping', 'magnet', 'sniff', 'brew', 'treasure')]
EXPECTED += ['pet.petting', 'pet.eat', 'pet.yawn', 'pet.snore', 'pet.splash', 'pet.shake', 'pet.tame', 'pet.faint', 'pet.wake',
             'pet.celebrate', 'pet.scared', 'pet.feed_owner', 'pager.beep', 'pager.open', 'toy.squeak', 'toy.laser', 'toy.feather',
             'block.bounce', 'block.wheel', 'block.bowl_fill', 'item.brush', 'backpack.equip', 'backpack.spill']

PATH_RE = re.compile(r'^[a-z0-9_./-]+$')
EVENT_RE = re.compile(r'^[a-z0-9_.]+$')


def find_index(explicit, wait):
    loom = os.path.expanduser('~/.gradle/caches/fabric-loom/assets/indexes')
    start = time.time()
    while True:
        if explicit:
            if os.path.exists(explicit):
                return explicit
        else:
            version = None
            try:
                for line in open(os.path.join(REPO, 'gradle.properties')):
                    if line.startswith('minecraft_version='):
                        version = line.split('=', 1)[1].strip()
            except OSError:
                pass
            cands = sorted(glob.glob(os.path.join(loom, '*.json')), key=os.path.getmtime, reverse=True)
            if version:
                exact = [c for c in cands if os.path.basename(c).startswith(version)]
                cands = exact or cands
            if cands:
                return cands[0]
        if time.time() - start >= wait:
            return None
        print('asset index not there yet, waiting 20 s ...')
        time.sleep(20)


def probe_ogg(path):
    """Decode with ffmpeg -> (channels, rate, seconds, peak). Returns None if ffmpeg is missing."""
    try:
        info = subprocess.run(['ffmpeg', '-hide_banner', '-i', path], capture_output=True, text=True).stderr
    except FileNotFoundError:
        return None
    m = re.search(r'Stream #0:0.*?Audio: (\w+), (\d+) Hz, (\w+)', info)
    codec, rate, layout = (m.group(1), int(m.group(2)), m.group(3)) if m else ('?', 0, '?')
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 's16le', '-ac', '1', '-ar', '44100', 'pipe:1'],
                         capture_output=True).stdout
    try:
        import numpy as np
        x = np.frombuffer(raw, dtype='<i2').astype(float) / 32768.0
        peak = float(np.max(np.abs(x))) if len(x) else 0.0
        n = len(x)
    except ImportError:
        import array
        a = array.array('h')
        a.frombytes(raw[:len(raw) // 2 * 2])
        peak = max((abs(v) for v in a), default=0) / 32768.0
        n = len(a)
    return codec, rate, layout, n / 44100.0, peak


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--index', help='Minecraft asset index json')
    ap.add_argument('--wait', type=int, default=0, help='seconds to wait (polling every 20 s) for the asset index')
    ap.add_argument('--fast', action='store_true', help='skip ffmpeg decoding of the custom files')
    a = ap.parse_args()

    errors, warnings = [], []
    err = errors.append
    warn = warnings.append

    # --- vanilla asset index -------------------------------------------------------------------------------
    index_path = find_index(a.index, a.wait)
    vanilla = None
    if index_path is None:
        err('Minecraft asset index not found (use --index PATH or --wait SECONDS)')
    else:
        vanilla = {k for k in json.load(open(index_path))['objects'] if k.startswith('minecraft/sounds/') and k.endswith('.ogg')}
        print('asset index: %s (%d vanilla sound files)' % (index_path, len(vanilla)))

    # --- sounds.json and subtitles -------------------------------------------------------------------------
    try:
        sounds = json.load(open(SOUNDS_JSON))
    except (OSError, ValueError) as e:
        print('ERROR cannot read sounds.json:', e)
        return 1
    try:
        subtitles = json.load(open(SUBTITLES))
    except (OSError, ValueError) as e:
        subtitles = {}
        err('cannot read subtitles_en_us.json: %s' % e)

    for ev in EXPECTED:
        if ev not in sounds:
            err('missing event: %s' % ev)
    for ev in sounds:
        if ev not in EXPECTED:
            warn('unexpected extra event: %s' % ev)
        if not EVENT_RE.match(ev):
            err('bad event name: %s' % ev)
    used = set()
    n_variants = n_custom = n_vanilla = 0
    for ev, body in sounds.items():
        want = 'subtitles.%s.%s' % (MOD_ID, ev)
        if body.get('subtitle') != want:
            err('%s: subtitle should be "%s", is %r' % (ev, want, body.get('subtitle')))
        if not str(subtitles.get(want, '')).strip():
            err('%s: no text for %s in subtitles_en_us.json' % (ev, want))
        lst = body.get('sounds')
        if not isinstance(lst, list) or not 1 <= len(lst) <= 4:
            err('%s: needs 1-4 sound variants, has %s' % (ev, len(lst) if isinstance(lst, list) else lst))
            continue
        seen = set()
        for s in lst:
            n_variants += 1
            d = {'name': s} if isinstance(s, str) else s
            name = d.get('name')
            if not isinstance(name, str):
                err('%s: variant without a name: %r' % (ev, s))
                continue
            for key, lo, hi in (('volume', 0.0, 1.0), ('pitch', 0.5, 2.0)):
                if key in d and not (isinstance(d[key], (int, float)) and lo < d[key] <= hi if key == 'volume' else lo <= d[key] <= hi):
                    err('%s: %s of %s out of range (%s)' % (ev, key, name, d[key]))
            if 'weight' in d and not (isinstance(d['weight'], int) and d['weight'] >= 1):
                err('%s: bad weight on %s' % (ev, name))
            sig = (name, d.get('pitch', 1.0), d.get('volume', 1.0))
            if sig in seen:
                warn('%s: duplicate variant %s' % (ev, name))
            seen.add(sig)
            ns, _, path = name.rpartition(':') if ':' in name else (MOD_ID, '', name)
            ns = ns or MOD_ID
            if not PATH_RE.match(path):
                err('%s: bad resource path %s' % (ev, name))
                continue
            if ns == MOD_ID:
                n_custom += 1
                f = os.path.join(SOUND_DIR, path + '.ogg')
                used.add(os.path.normpath(f))
                if not os.path.isfile(f):
                    err('%s: custom file missing: %s' % (ev, os.path.relpath(f, REPO)))
                elif open(f, 'rb').read(4) != b'OggS':
                    err('%s: not an Ogg file: %s' % (ev, os.path.relpath(f, REPO)))
            elif ns == 'minecraft':
                n_vanilla += 1
                key = 'minecraft/sounds/%s.ogg' % path
                if vanilla is not None and key not in vanilla:
                    err('%s: vanilla sound does not exist: %s' % (ev, key))
            else:
                err('%s: unknown namespace in %s' % (ev, name))
    for k in subtitles:
        if k not in {'subtitles.%s.%s' % (MOD_ID, e) for e in sounds}:
            warn('subtitle without event: %s' % k)

    # --- files on disk -------------------------------------------------------------------------------------
    files = [os.path.normpath(os.path.join(r, f)) for r, _, fs in os.walk(SOUND_DIR) for f in fs if f.endswith('.ogg')]
    total = sum(os.path.getsize(f) for f in files)
    for f in sorted(files):
        if f not in used:
            warn('unreferenced sound file: %s' % os.path.relpath(f, REPO))
    if total > MAX_TOTAL_BYTES:
        err('custom sounds total %.2f MB, limit is 3 MB' % (total / 1048576.0))
    if not a.fast:
        for f in sorted(used & set(files)):
            res = probe_ogg(f)
            rel = os.path.relpath(f, REPO)
            if res is None:
                warn('ffmpeg not found, skipped decoding checks')
                break
            codec, rate, layout, secs, peak = res
            if codec != 'vorbis' or rate != 44100 or layout != 'mono':
                err('%s: expected vorbis/44100 Hz/mono, got %s/%s Hz/%s' % (rel, codec, rate, layout))
            if peak >= 0.98:
                err('%s: peak %.3f is (nearly) clipping' % (rel, peak))
            if peak < 0.05 or secs < 0.05:
                err('%s: silent or too short (%.2fs, peak %.3f)' % (rel, secs, peak))
            if secs > 2.0:
                warn('%s: longer than 2 s (%.2fs)' % (rel, secs))

    # --- README has a line per event -----------------------------------------------------------------------
    try:
        readme = open(README).read()
        for ev in EXPECTED:
            if '`%s`' % ev not in readme:
                warn('README.md has no line for %s' % ev)
    except OSError:
        err('README.md missing')

    print('%d events, %d variants (%d custom, %d vanilla references), %d custom files, %.2f MB' %
          (len(sounds), n_variants, n_custom, n_vanilla, len(files), total / 1048576.0))
    for w in warnings:
        print('WARNING', w)
    for e in errors:
        print('ERROR  ', e)
    print('RESULT: %s (%d errors, %d warnings)' % ('FAILED' if errors else 'OK', len(errors), len(warnings)))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
