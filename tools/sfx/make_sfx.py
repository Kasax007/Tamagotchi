#!/usr/bin/env python3
"""Tamagotchi sound synthesizer.

Builds every custom sound of the mod from scratch (numpy only, no samples, no downloads) and encodes
each one as mono 44.1 kHz Ogg Vorbis (ffmpeg / libvorbis, -q:a 4) to

    src/main/resources/assets/tamagotchi/sounds/<group>/<name>.ogg

Afterwards it renders a spectrogram contact sheet of everything it wrote to tools/sfx/out/spectrograms.png
(read from the encoded files, so it shows what the game really plays).

The script is deterministic: every sound has its own random seed (CRC32 of its name) and the encoder runs in
bit-exact mode, so re-running it produces identical files and no git churn.

Usage (from anywhere):
    python3 tools/sfx/make_sfx.py                    # everything + contact sheet
    python3 tools/sfx/make_sfx.py --only 'pet/*'     # only matching sounds (fnmatch on group/name)
    python3 tools/sfx/make_sfx.py --list             # list all sounds
    python3 tools/sfx/make_sfx.py --no-sheet -j 1    # no sheet, single process (readable tracebacks)

Which event uses which file lives in sounds.json (see README.md); validate_sounds.py checks the wiring.

Layout of this file: 1. DSP toolkit  2. registry / mastering / encoding  3. contact sheet
4. sound recipes (creatures, talents, shared)  5. command line.
"""
import argparse
import concurrent.futures
import fnmatch
import json
import os
import subprocess
import sys
import zlib

import numpy as np

SR = 44100
TAU = 2.0 * np.pi

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
SOUND_DIR = os.path.join(REPO, 'src', 'main', 'resources', 'assets', 'tamagotchi', 'sounds')
SHEET_PNG = os.path.join(HERE, 'out', 'spectrograms.png')

# =====================================================================================================
# 1. DSP TOOLKIT
# =====================================================================================================


def N(sec):
    """Number of samples for a duration (at least 1)."""
    return max(1, int(round(sec * SR)))


def S(sec):
    """Sample offset for a time position."""
    return int(round(sec * SR))


def T(sec):
    """Time axis in seconds for a duration."""
    return np.arange(N(sec)) / SR


def g(db):
    """dB -> linear gain."""
    return 10.0 ** (db / 20.0)


def rms(x):
    return float(np.sqrt(np.mean(np.square(x)) + 1e-18))


def unit(x):
    """Scale to a peak of 1."""
    return x / (np.max(np.abs(x)) + 1e-12)


_NOTES = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def nt(name):
    """Note name -> Hz ('A4' = 440, 'C#5', 'Bb3')."""
    n = _NOTES[name[0]]
    i = 1
    while i < len(name) and name[i] in '#b':
        n += 1 if name[i] == '#' else -1
        i += 1
    octave = int(name[i:])
    return 440.0 * 2.0 ** ((n + 12 * (octave + 1) - 69) / 12.0)


def semis(x):
    """Semitones -> frequency ratio."""
    return 2.0 ** (x / 12.0)


def smooth(y, sec):
    """Moving average with edge hold (rounds off corners of piecewise curves)."""
    k = int(sec * SR)
    if k <= 1:
        return y
    pad = np.pad(y, (k // 2, k - 1 - k // 2), mode='edge')
    c = np.cumsum(np.insert(pad, 0, 0.0))
    return (c[k:] - c[:-k]) / k


def curve(pts, dur, log=False, sm=0.0):
    """Piecewise-linear control curve through (seconds, value) points, optionally log-interpolated."""
    t = T(dur)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    y = np.exp(np.interp(t, xs, np.log(ys))) if log else np.interp(t, xs, ys)
    return smooth(y, sm) if sm else y


def bc(v, n):
    """Broadcast a scalar / array control value to n samples."""
    return np.broadcast_to(np.asarray(v, dtype=float), (n,)).copy()


def phase(f):
    """Running phase (radians) of a frequency track in Hz."""
    return TAU * np.cumsum(f) / SR


def sine(f, p0=0.0):
    return np.sin(phase(f) + p0)


def ramp_in(x, sec):
    """Raised-cosine fade-in on the first `sec` seconds (in place, returns x)."""
    k = min(len(x), S(sec))
    if k > 1:
        x[:k] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(k) / k)
    return x


def ramp_out(x, sec):
    k = min(len(x), S(sec))
    if k > 1:
        x[-k:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(k) / k)
    return x


def adsr(dur, a=0.01, d=0.05, s=0.7, r=0.08):
    """Smooth ADSR with raised-cosine segments (sustain level s, release at the end)."""
    n = N(dur)
    e = np.full(n, float(s))
    na, nd, nr = min(n, S(a)), S(d), min(n, S(r))
    if na > 1:
        e[:na] = 0.5 - 0.5 * np.cos(np.pi * np.arange(na) / na)
    nd = max(0, min(nd, n - na))
    if nd > 1:
        e[na:na + nd] = s + (1.0 - s) * (0.5 + 0.5 * np.cos(np.pi * np.arange(nd) / nd))
    if nr > 1:
        e[-nr:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(nr) / nr)
    return e


def pluck(dur, a=0.003, tau=0.08):
    """Soft attack, exponential decay."""
    n = N(dur)
    e = np.exp(-(np.arange(n) / SR) / tau)
    return ramp_in(e, a)


def swell(dur, peak=0.5, power=1.5):
    """Smooth bump: rises to the peak position (0..1 of duration), then falls."""
    x = np.linspace(0.0, 1.0, N(dur))
    left = np.sin(0.5 * np.pi * np.clip(x / peak, 0, 1)) ** power
    right = np.cos(0.5 * np.pi * np.clip((x - peak) / (1 - peak), 0, 1)) ** power
    return np.where(x < peak, left, right)


def vib(n, r, rate=5.5, cents=20.0, ramp=0.15, rate_var=0.0):
    """Vibrato as a frequency multiplier (depth fades in over `ramp` seconds)."""
    t = np.arange(n) / SR
    depth = np.clip(t / ramp, 0, 1) if ramp > 0 else 1.0
    rate_t = rate * (1.0 + rate_var * np.sin(TAU * 0.7 * t + r.uniform(0, TAU)))
    p = TAU * np.cumsum(rate_t) / SR + r.uniform(0, TAU)
    return 2.0 ** (cents / 1200.0 * depth * np.sin(p))


def drift(n, r, amount=0.004, rate=7.0):
    """Slow random pitch / level wobble around 1.0 (organic, never perfectly steady)."""
    m = int(n / SR * rate) + 3
    pts = r.standard_normal(m)
    return 1.0 + amount * np.interp(np.linspace(0, m - 1, n), np.arange(m), pts)


# ---- noise and filters -----------------------------------------------------------------------------


def white(n, r):
    return r.standard_normal(n)


def _coloured(n, r, power):
    X = np.fft.rfft(r.standard_normal(n))
    f = np.fft.rfftfreq(n, 1.0 / SR)
    f[0] = f[1]
    X /= (f / f[1]) ** power
    y = np.fft.irfft(X, n)
    return y / (np.std(y) + 1e-12)


def pink(n, r):
    return _coloured(n, r, 0.5)


def brown(n, r):
    return _coloured(n, r, 1.0)


def fft_filter(x, resp, circular=False):
    """Zero-phase filter with magnitude response resp(f). Circular mode keeps loops seamless."""
    n = len(x)
    L = n if circular else 1 << int(np.ceil(np.log2(n * 2 + 8)))
    X = np.fft.rfft(x, L)
    X *= resp(np.fft.rfftfreq(L, 1.0 / SR))
    return np.fft.irfft(X, L)[:n]


def lp(x, fc, order=2, circular=False):
    return fft_filter(x, lambda f: 1.0 / np.sqrt(1.0 + (f / fc) ** (2 * order)), circular)


def hp(x, fc, order=2, circular=False):
    return fft_filter(x, lambda f: 1.0 / np.sqrt(1.0 + (fc / np.maximum(f, 1e-3)) ** (2 * order)), circular)


def bp(x, lo, hi, order=2, circular=False):
    def resp(f):
        a = 1.0 / np.sqrt(1.0 + (f / hi) ** (2 * order))
        b = 1.0 / np.sqrt(1.0 + (lo / np.maximum(f, 1e-3)) ** (2 * order))
        return a * b
    return fft_filter(x, resp, circular)


def shelf_hi(x, fc, gain_db, circular=False):
    """Gentle high shelf (positive or negative gain)."""
    gl = g(gain_db)
    return fft_filter(x, lambda f: 1.0 + (gl - 1.0) / (1.0 + (fc / np.maximum(f, 1e-3)) ** 2.0), circular)


def peak_eq(x, fc, gain_db, width=0.5, circular=False):
    """Bell EQ; width in octaves."""
    gl = g(gain_db)
    return fft_filter(x, lambda f: 1.0 + (gl - 1.0) * np.exp(-0.5 * (np.log2(np.maximum(f, 1.0) / fc) / width) ** 2), circular)


def svf(x, fc, q=0.8, mode='bp'):
    """Time-varying state-variable filter (TPT form). fc and q may be arrays. 'bp' has unity peak gain."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    fc = np.clip(bc(fc, n), 15.0, 0.46 * SR)
    kq = 1.0 / bc(q, n)
    gg = np.tan(np.pi * fc / SR)
    a1 = 1.0 / (1.0 + gg * (gg + kq))
    a2 = gg * a1
    a3 = gg * a2
    xl, a1l, a2l, a3l, kl = x.tolist(), a1.tolist(), a2.tolist(), a3.tolist(), kq.tolist()
    out = [0.0] * n
    ic1 = ic2 = 0.0
    for i in range(n):
        v3 = xl[i] - ic2
        v1 = a1l[i] * ic1 + a2l[i] * v3
        v2 = ic2 + a2l[i] * ic1 + a3l[i] * v3
        ic1 = 2.0 * v1 - ic1
        ic2 = 2.0 * v2 - ic2
        if mode == 'bp':
            out[i] = v1 * kl[i]
        elif mode == 'lp':
            out[i] = v2
        elif mode == 'hp':
            out[i] = xl[i] - kl[i] * v1 - v2
        else:  # notch
            out[i] = xl[i] - kl[i] * v1
    return np.array(out)


def fftconv(x, h):
    n = len(x) + len(h) - 1
    L = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(h, L), L)[:n]


# ---- effects ---------------------------------------------------------------------------------------


def reverb(x, t60=0.8, wet=0.25, pre=0.006, damp=6000.0, seed=7):
    """Smooth noise-tail reverb (extends the sound by the tail). wet is the level of the tail vs the dry sound."""
    r = np.random.default_rng(seed)
    L = N(t60 * 1.05)
    t = np.arange(L) / SR
    ir = r.standard_normal(L) * np.exp(-6.91 * t / t60)
    dark = lp(ir, damp)
    k = np.clip(t / (t60 * 0.8), 0, 1)
    ir = ir * (1 - k) + dark * k
    ir = lp(ir, 9000.0)
    ramp_in(ir, 0.004)
    ir = np.concatenate([np.zeros(S(pre)), ir])
    ir /= np.sqrt(np.sum(ir ** 2)) + 1e-12
    wetsig = fftconv(x, ir)
    y = np.zeros(len(wetsig))
    y[:len(x)] += x
    y += wet * wetsig * (rms(x) / (rms(wetsig[:len(x)]) + 1e-12))
    return y


def echo(x, delay=0.25, fb=0.4, taps=4, damp=3500.0):
    """Feedback echo with a darker repeat each time."""
    d = S(delay)
    y = np.zeros(len(x) + d * taps)
    y[:len(x)] += x
    rep = x
    for i in range(1, taps + 1):
        rep = lp(rep, damp, 1) * fb
        y[i * d:i * d + len(rep)] += rep
    return y


def softclip(x, drive=1.5):
    return np.tanh(drive * x) / np.tanh(drive)


def reverse(x):
    return x[::-1].copy()


class Mix:
    """Place layers at time offsets (auto-extending)."""

    def __init__(self, dur=0.0):
        self.x = np.zeros(S(dur))

    def add(self, y, t=0.0, gain=1.0):
        i = S(t)
        end = i + len(y)
        if end > len(self.x):
            self.x = np.pad(self.x, (0, end - len(self.x)))
        self.x[i:end] += gain * np.asarray(y)
        return self

    def __len__(self):
        return len(self.x)


# ---- sound sources ---------------------------------------------------------------------------------

# vowel formants (F1, F2, F3) for small, bright creature voices
VOW = {
    'a': (900, 1500, 2900), 'e': (600, 1950, 2800), 'i': (340, 2450, 3200), 'o': (500, 950, 2800),
    'u': (360, 900, 2700), 'ae': (760, 1800, 2800), 'uh': (650, 1250, 2800), 'm': (280, 1000, 2500),
    'er': (520, 1350, 1750), 'oo': (320, 780, 2600),
}


def vowel_tracks(dur, seq, scale=1.0, sm=0.012):
    """Formant tracks that glide through [(time, 'vowel'), ...]."""
    out = []
    for k in range(3):
        pts = [(t, VOW[v][k] * scale) for t, v in seq]
        out.append(curve(pts, dur, log=True, sm=sm))
    return out


def vox(dur, f0, forms, r, amp=None, tilt=None, vibrato=(5.8, 18.0, 0.12), jitter=0.003, breath=0.0,
        rough=None, nasal=0.0, qs=(6.0, 10.0, 14.0), kmax=60):
    """Formant ("source-filter") voice by additive synthesis.

    f0:      [(sec, Hz), ...] pitch curve, or an array
    forms:   three formant tracks (arrays, e.g. from vowel_tracks)
    amp:     [(sec, level), ...] or array; default is a soft ADSR
    rough:   (rate Hz, depth) amplitude pulsing for growls (depth may be a [(sec, depth), ...] curve)
    tilt:    spectral roll-off; None = softer the higher the pitch (keeps high calls from getting shrill)
    """
    n = N(dur)
    f = curve(f0, dur, log=True, sm=0.008) if isinstance(f0, list) else bc(f0, n)
    if tilt is None:
        tilt = 1.1 + 0.7 * float(np.clip(np.log2(np.median(f) / 300.0) / 2.0, 0.0, 1.0))
    if vibrato:
        f = f * vib(n, r, vibrato[0], vibrato[1], vibrato[2], rate_var=0.08)
    if jitter:
        f = f * drift(n, r, jitter, 9.0)
    ph = phase(f)
    kk = max(2, min(kmax, int(9000.0 / max(float(np.min(f)), 40.0))))
    amps = []
    for k in range(1, kk + 1):
        fk = k * f
        w = np.clip((9500.0 - fk) / 3000.0, 0.0, 1.0)
        if not w.any():
            break
        a = (k ** -tilt) * w
        for F, Q in zip(forms, qs):
            x = fk / F
            a = a / np.sqrt((1.0 - x * x) ** 2 + (x / Q) ** 2)
        if nasal:
            a = a * (1.0 - nasal * 0.85 * np.exp(-((fk - 1000.0) / 350.0) ** 2))
        amps.append(a)
    # constant power: the formants move the timbre around but never the loudness
    pw = np.sqrt(sum(a * a for a in amps)) + 1e-12
    A = np.zeros(n)
    for k, a in enumerate(amps, start=1):
        A += (a / pw) * np.sin(k * ph)
    A *= 1.414                                   # RMS ~ 1, the same scale as rl() layers
    if breath:
        nz = svf(white(n, r), forms[1], 2.5, 'bp')
        A = (A / rms(A) + breath * nz / (rms(nz) + 1e-12)) / np.sqrt(1.0 + breath * breath)
    if rough:
        rate, depth = rough
        rt = bc(rate, n) * drift(n, r, 0.03, 11.0)
        depth = curve(depth, dur, sm=0.01) if isinstance(depth, list) else depth
        pulse = (0.5 + 0.5 * np.cos(phase(rt))) ** 2
        A = A * (1.0 - depth + depth * pulse)
    if amp is None:
        env = adsr(dur, 0.018, 0.05, 0.85, 0.07)
    elif isinstance(amp, list):
        env = curve(amp, dur, sm=0.004)
    else:
        env = bc(amp, n)
    return A * env


def fm(f, ratio=2.0, index=1.0):
    """Two-operator FM: f is the carrier track (Hz), index may be an array."""
    p = phase(f)
    return np.sin(p + index * np.sin(ratio * p))


def tone_env(dur, a=0.008, r=0.04, pts=None):
    """Level curve for a short note: soft in/out, optional body shape (sec, level) points."""
    if pts:
        e = curve(pts, dur, sm=0.003)
    else:
        e = np.ones(N(dur))
    ramp_in(e, a)
    ramp_out(e, r)
    return e


def modes(dur, partials, r=None, click=0.0, click_tau=0.002, click_band=(1500.0, 7000.0)):
    """Modal "struck object": partials = [(Hz, amp, decay tau s), ...] (+ optional noise click)."""
    t = T(dur)
    y = np.zeros(len(t))
    for fr, a, tau in partials:
        y += a * np.exp(-t / tau) * np.sin(TAU * fr * t)
    ramp_in(y, 0.0004)
    if click and r is not None:
        c = r.standard_normal(len(t)) * np.exp(-t / click_tau)
        c = bp(c, click_band[0], click_band[1], 1)
        ramp_in(c, 0.0003)
        y += click * c / (np.max(np.abs(c)) + 1e-12) * np.max(np.abs(y))
    return y


def bubble(f0, rise=0.12, amp=1.0, dur=None):
    """One liquid bubble: damped sine whose pitch climbs slightly (physical formula). f0 in Hz."""
    d = 0.043 * f0 + 0.0014 * f0 ** 1.5
    length = dur if dur else min(0.5, 7.0 / d)
    t = np.arange(N(length)) / SR
    f = f0 * (1.0 + rise * d * t)
    y = np.sin(phase(f)) * np.exp(-d * t)
    return amp * ramp_in(y, 0.0005)


def thud(dur, f_hi, f_lo, tau_pitch=0.04, tau_amp=0.12, a=0.002):
    """Low impact: pitch-dropping sine with an exponential tail."""
    t = T(dur)
    f = f_lo + (f_hi - f_lo) * np.exp(-t / tau_pitch)
    return ramp_in(np.sin(phase(f)) * np.exp(-t / tau_amp), a)


def whoosh(dur, fc_pts, r, q=1.2, env=None, body=0.0, mode='bp'):
    """Noise through a sweeping band-pass: fc_pts = [(sec, Hz), ...]."""
    n = N(dur)
    fc = curve(fc_pts, dur, log=True, sm=0.004)
    y = svf(white(n, r), fc, q, mode)
    if body:
        y = y + body * lp(white(n, r), 400.0, 2)
    if env is None:
        env = swell(dur, 0.4, 1.2)
    return y * (env if not isinstance(env, list) else curve(env, dur, sm=0.003))


def scatter(dur, times, r, freq=(1500.0, 5000.0), tau=(0.002, 0.008), amp=(0.4, 1.0), noise=0.3, kind='ping'):
    """Random tiny impacts (crackle, pebbles, kibble, coins): each onset gets a damped ping + noise tick."""
    out = np.zeros(N(dur))
    for t0 in times:
        i = S(t0)
        if i >= len(out) - 8:
            continue
        ta = r.uniform(*tau)
        L = min(N(ta * 7.0), len(out) - i)
        tt = np.arange(L) / SR
        a = r.uniform(*amp)
        if kind == 'bubble':
            gr = bubble(r.uniform(*freq), 0.25)
            L = min(len(gr), len(out) - i)
            gr = gr[:L]
        else:
            fr = r.uniform(*freq) if not isinstance(freq, (int, float)) else freq
            gr = np.exp(-tt / ta) * np.sin(TAU * fr * tt + r.uniform(0, TAU))
            if noise:
                gr = gr + noise * r.standard_normal(L) * np.exp(-tt / (ta * 0.5))
        gr = ramp_in(gr * a, 0.0002)
        out[i:i + L] += gr
    return out


def poisson(dur, rate, r, start=0.0, shape=None):
    """Random event times over [start, dur) with a (possibly time-varying) rate in events/s."""
    ts = []
    t = start
    while t < dur:
        lam = rate if shape is None else rate * float(shape(t / dur))
        lam = max(lam, 0.5)
        t += r.exponential(1.0 / lam)
        if t < dur:
            ts.append(t)
    return ts


def bell(f, dur=0.8, bright=1.0, tau=0.35, kind='glock'):
    """Struck bell / glockenspiel / music-box note."""
    t = T(dur)
    if kind == 'glock':
        idx = bright * 1.6 * np.exp(-t / (tau * 0.5))
        y = np.sin(TAU * f * t + idx * np.sin(TAU * f * 3.5 * t)) * np.exp(-t / tau)
        y += 0.25 * np.sin(TAU * f * 2.0 * t) * np.exp(-t / (tau * 0.4))
    elif kind == 'music':
        y = np.sin(TAU * f * t) * np.exp(-t / tau)
        y += 0.35 * bright * np.sin(TAU * f * 4.0 * t) * np.exp(-t / (tau * 0.25))
        y += 0.12 * bright * np.sin(TAU * f * 6.0 * t) * np.exp(-t / (tau * 0.15))
    elif kind == 'soft':
        y = np.sin(TAU * f * t + 0.8 * bright * np.exp(-t / 0.08) * np.sin(TAU * f * t)) * np.exp(-t / tau)
    else:  # 'mallet' (marimba-like)
        y = np.sin(TAU * f * t) * np.exp(-t / tau)
        y += 0.5 * np.sin(TAU * f * 3.97 * t) * np.exp(-t / (tau * 0.12))
    return ramp_in(y, 0.0015)


def sparkle(dur, r, n=12, lo=2500.0, hi=7500.0, rising=False, level=1.0, tau=(0.03, 0.09)):
    """Scattered tiny high pings (glitter)."""
    ts = np.sort(r.uniform(0.0, dur * 0.85, n))
    out = np.zeros(N(dur + 0.2))
    for i, t0 in enumerate(ts):
        fr = lo * (hi / lo) ** (i / max(1, n - 1)) if rising else r.uniform(lo, hi)
        fr *= r.uniform(0.97, 1.03)
        a = level * r.uniform(0.4, 1.0)
        tt = np.arange(N(0.25)) / SR
        ta = r.uniform(*tau)
        p = a * np.exp(-tt / ta) * (np.sin(TAU * fr * tt) + 0.3 * np.sin(TAU * fr * 2.01 * tt) * np.exp(-tt / (ta * 0.3)))
        ramp_in(p, 0.0008)
        j = S(t0)
        out[j:j + len(p)] += p[:max(0, len(out) - j)]
    return out


# =====================================================================================================
# 2. REGISTRY, MASTERING, ENCODING
# =====================================================================================================

SOUNDS = {}  # "group/name" -> (function(rng) -> np.ndarray, options)


def sfx(name, **opts):
    """Register a recipe. Options: peak (dBFS, default -3), shelf (dB above 7 kHz, default -3),
    hp (Hz, default 35), loop (no fades, circular filters), fade_out (s), fade_in (s),
    maxdur (s, default 1.5: longer renders are cut and faded)."""
    def deco(fn):
        if name in SOUNDS:
            raise ValueError('duplicate sound ' + name)
        SOUNDS[name] = (fn, opts)
        return fn
    return deco


def master(x, peak=-3.0, shelf=-3.0, hp_hz=35.0, loop=False, fade_in=0.003, fade_out=0.02):
    x = np.asarray(x, dtype=float)
    if not np.all(np.isfinite(x)):
        raise ValueError('non-finite samples')
    x = hp(x, hp_hz, 2, circular=loop)
    if shelf:
        x = shelf_hi(x, 7000.0, shelf, circular=loop)
    if not loop:
        ramp_in(x, fade_in)
        ramp_out(x, fade_out)
    return x * (g(peak) / (np.max(np.abs(x)) + 1e-12))


def render(name):
    fn, opts = SOUNDS[name]
    rng = np.random.default_rng(zlib.crc32(name.encode()))
    x = fn(rng)
    fade_out = opts.get('fade_out', 0.02)
    cap = S(opts.get('maxdur', 1.5))          # reverb tails etc. never run longer than this
    if len(x) > cap and not opts.get('loop', False):
        x = x[:cap]
        fade_out = max(fade_out, 0.12)
    return master(x, peak=opts.get('peak', -3.0), shelf=opts.get('shelf', -3.0), hp_hz=opts.get('hp', 35.0),
                  loop=opts.get('loop', False), fade_in=opts.get('fade_in', 0.003), fade_out=fade_out)


def encode_ogg(x, path):
    pcm = np.clip(np.round(x * 32767.0), -32768, 32767).astype('<i2').tobytes()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 's16le', '-ar', str(SR), '-ac', '1', '-i', 'pipe:0',
           '-map_metadata', '-1', '-fflags', '+bitexact', '-flags:a', '+bitexact',
           '-c:a', 'libvorbis', '-q:a', '4', '-ar', str(SR), '-ac', '1', path]
    subprocess.run(cmd, input=pcm, check=True)


def decode_ogg(path):
    out = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '1', '-ar', str(SR), 'pipe:1'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).astype(np.float64)


def a_weight_db(f):
    f2 = np.maximum(f, 1.0) ** 2
    ra = (12194.0 ** 2 * f2 ** 2) / ((f2 + 20.6 ** 2) * np.sqrt((f2 + 107.7 ** 2) * (f2 + 737.9 ** 2)) * (f2 + 12194.0 ** 2))
    return 20.0 * np.log10(ra + 1e-12) + 2.0


def loudness_db(x):
    """A-weighted RMS (dBFS) over the active part (frames within 30 dB of the loudest), for volume matching."""
    if len(x) < 64:
        return -99.0
    L = 1 << int(np.ceil(np.log2(len(x) * 2)))
    X = np.fft.rfft(x, L) * 10.0 ** (a_weight_db(np.fft.rfftfreq(L, 1.0 / SR)) / 20.0)
    y = np.fft.irfft(X, L)[:len(x)]
    fr = 1024
    nfr = max(1, len(y) // fr)
    e = np.array([np.mean(y[i * fr:(i + 1) * fr] ** 2) for i in range(nfr)])
    keep = e > e.max() * 1e-3
    return float(10.0 * np.log10(np.mean(e[keep]) + 1e-18))


def sound_path(out_dir, name):
    return os.path.join(out_dir, name + '.ogg')


def build_one(args):
    name, out_dir = args
    x = render(name)
    path = sound_path(out_dir, name)
    encode_ogg(x, path)
    y = decode_ogg(path)
    # closed loop: Vorbis can overshoot a little, so re-encode once if the decoded peak is off target
    target = SOUNDS[name][1].get('peak', -3.0)
    err = target - 20 * np.log10(np.max(np.abs(y)) + 1e-12)
    if abs(err) > 0.25:
        encode_ogg(x * g(err), path)
        y = decode_ogg(path)
    return dict(name=name, dur=len(x) / SR, peak_db=float(20 * np.log10(np.max(np.abs(y)) + 1e-12)),
                loud_db=loudness_db(y), bytes=os.path.getsize(path),
                lead=float(abs(y[0]) if len(y) else 0.0), tail=float(abs(y[-1]) if len(y) else 0.0))


# =====================================================================================================
# 3. SPECTROGRAM CONTACT SHEET
# =====================================================================================================

_MAGMA = [(0, 0, 4), (40, 11, 84), (101, 21, 110), (159, 42, 99), (212, 72, 66), (245, 125, 21),
          (250, 193, 39), (252, 255, 164)]


def _lut():
    xs = np.linspace(0, 1, len(_MAGMA))
    t = np.linspace(0, 1, 256)
    return np.stack([np.interp(t, xs, [c[i] for c in _MAGMA]) for i in range(3)], axis=1).astype(np.uint8)


def spectrogram_rgb(x, w, h, fmin=60.0, fmax=16000.0, dyn=72.0):
    """Log-frequency spectrogram as an (h, w, 3) uint8 image (low frequencies at the bottom)."""
    nfft = 512 if len(x) < SR * 0.25 else 1024
    xp = np.pad(x, (nfft // 2, nfft // 2))
    hop = max(16, (len(xp) - nfft) // max(1, w - 1))
    frames = np.lib.stride_tricks.sliding_window_view(xp, nfft)[::hop]
    mag = np.abs(np.fft.rfft(frames * np.hanning(nfft), axis=1))
    freqs = np.geomspace(fmin, fmax, h)
    pos = freqs / (SR / nfft)
    i0 = np.clip(np.floor(pos).astype(int), 0, mag.shape[1] - 2)
    fr = pos - i0
    rows = mag[:, i0] * (1 - fr) + mag[:, i0 + 1] * fr          # (T, h)
    db = 20 * np.log10(rows + 1e-9)
    db = np.clip((db - db.max() + dyn) / dyn, 0, 1)
    img = _lut()[(db * 255).astype(np.uint8)]                     # (T, h, 3)
    img = np.transpose(img, (1, 0, 2))[::-1]                      # (h, T, 3), high freq on top
    # resample the columns to exactly w pixels
    idx = np.clip((np.arange(w) * img.shape[1] / w).astype(int), 0, img.shape[1] - 1)
    return img[:, idx]


def render_sheet(files, out_png, title='Tamagotchi custom sounds', cols=6, cell_w=300, spec_h=96):
    """files: list of (name, path). Groups (directories) get their own header row."""
    from PIL import Image, ImageDraw, ImageFont
    try:
        font = ImageFont.load_default(size=12)
        font_s = ImageFont.load_default(size=10)
        font_h = ImageFont.load_default(size=16)
    except TypeError:
        font = font_s = font_h = ImageFont.load_default()
    wave_h, label_h, pad = 22, 15, 6
    cell_h = label_h + spec_h + wave_h + pad
    groups = {}
    for name, path in files:
        groups.setdefault(name.split('/')[0], []).append((name, path))
    rows_total = sum((len(v) + cols - 1) // cols for v in groups.values())
    head_h, top = 22, 34
    W = cols * (cell_w + pad) + pad
    H = top + len(groups) * head_h + rows_total * cell_h + pad
    sheet = Image.new('RGB', (W, H), (14, 14, 20))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 8), title + '   |   log frequency 60 Hz - 16 kHz, 72 dB range, one cell = one file '
           '(cell width = its duration), waveform strip below', fill=(220, 220, 230), font=font)
    y = top
    for gname in sorted(groups):
        d.rectangle([0, y, W, y + head_h - 4], fill=(36, 30, 56))
        d.text((pad, y + 1), gname, fill=(255, 214, 120), font=font_h)
        y += head_h
        items = sorted(groups[gname])
        for i, (name, path) in enumerate(items):
            cx = pad + (i % cols) * (cell_w + pad)
            cy = y + (i // cols) * cell_h
            x = decode_ogg(path)
            dur = len(x) / SR
            pk = 20 * np.log10(np.max(np.abs(x)) + 1e-12)
            d.text((cx, cy), '%s  %.2fs  %.1fdB' % (name.split('/', 1)[1], dur, pk), fill=(235, 235, 240), font=font_s)
            img = Image.fromarray(spectrogram_rgb(x, cell_w, spec_h))
            sheet.paste(img, (cx, cy + label_h))
            for fq, lab in ((200, '200'), (1000, '1k'), (5000, '5k')):   # frequency gridlines
                gy = cy + label_h + int(round((1.0 - np.log(fq / 60.0) / np.log(16000.0 / 60.0)) * (spec_h - 1)))
                d.line([(cx, gy), (cx + 5, gy)], fill=(255, 255, 255))
                d.text((cx + 7, gy - 5), lab, fill=(200, 200, 210), font=font_s)
            # waveform strip
            wy = cy + label_h + spec_h + 1
            d.rectangle([cx, wy, cx + cell_w - 1, wy + wave_h - 3], fill=(24, 24, 34))
            seg = np.array_split(x, cell_w)
            mid = wy + (wave_h - 3) / 2.0
            for px, s in enumerate(seg):
                if len(s):
                    hi, lo = float(np.max(s)), float(np.min(s))
                    d.line([(cx + px, mid - hi * (wave_h - 4) / 2.0), (cx + px, mid - lo * (wave_h - 4) / 2.0)],
                           fill=(110, 200, 255))
        y += ((len(items) + cols - 1) // cols) * cell_h
    os.makedirs(os.path.dirname(os.path.abspath(out_png)), exist_ok=True)
    sheet.save(out_png, optimize=True)
    return sheet.size


# =====================================================================================================
# 4. SOUND RECIPES
# =====================================================================================================

def rms_active(x):
    a = np.abs(x)
    m = a > 0.03 * (a.max() + 1e-12)
    return float(np.sqrt(np.mean(x[m] ** 2) + 1e-18))


def rl(x, db=0.0):
    """Level a layer by its RMS over the active part (sustained / noisy layers)."""
    return x / (rms_active(x) + 1e-12) * g(db)


def pl(x, db=0.0):
    """Level a layer by its peak (clicks, thuds, plucks)."""
    return x / (np.max(np.abs(x)) + 1e-12) * g(db)


def syl(r, dur, f0, vow, amp=None, scale=1.0, **kw):
    """One voiced syllable: pitch curve f0, vowel path vow = [(sec, 'vowel'), ...]."""
    return vox(dur, f0, vowel_tracks(dur, vow, scale), r, amp=amp, **kw)


def whistle(dur, f_pts, r, h=(1.0, 0.16, 0.05), vibrato=None, amp=None, a=0.006, rel=0.02):
    """Pure-ish whistle / chirp with a few soft overtones. vibrato = (rate Hz, cents, ramp s)."""
    n = N(dur)
    f = curve(f_pts, dur, log=True, sm=0.004)
    if vibrato:
        f = f * vib(n, r, vibrato[0], vibrato[1], vibrato[2])
    p = phase(f)
    y = sum(ah * np.sin((i + 1) * p) for i, ah in enumerate(h))
    env = curve(amp, dur, sm=0.003) if isinstance(amp, list) else tone_env(dur, a, rel)
    return y * env


def flutter(n, r, rate=70.0, depth=0.8):
    """Random amplitude gate (leaf / fabric / grain texture), 1.0 = open."""
    m = int(n / SR * rate) + 3
    pts = r.uniform(0.0, 1.0, m)
    return (1.0 - depth) + depth * np.interp(np.linspace(0, m - 1, n), np.arange(m), pts)


def burst(dur, r, tau=0.01, band=None, a=0.0004):
    """Noise burst with exponential decay, optionally band-limited (lo, hi)."""
    t = T(dur)
    y = r.standard_normal(len(t)) * np.exp(-t / tau)
    if band:
        y = bp(y, band[0], band[1], 1) if band[0] and band[1] else (lp(y, band[1], 2) if band[1] else hp(y, band[0], 2))
    return ramp_in(y, a)


# ---------------------------------------------------------------------------------------------------
# 4a. DESERT DRAGON - warm baby dragon: chirps with a little growl, a small fire puff to attack
# ---------------------------------------------------------------------------------------------------


@sfx('desert_dragon/ambient1')
def _(r):  # "krr-ip": a rolled growl that flips into a chirp
    m = Mix()
    m.add(syl(r, 0.17, [(0, 170), (0.06, 230), (0.17, 270)], [(0, 'uh'), (0.17, 'a')],
              amp=[(0, 0), (0.02, 0.9), (0.12, 0.8), (0.17, 0)], rough=(64, 0.65), tilt=1.0, vibrato=None), 0.0, 0.85)
    m.add(syl(r, 0.32, [(0, 640), (0.07, 1250), (0.18, 1120), (0.32, 930)], [(0, 'e'), (0.1, 'i'), (0.32, 'a')],
              scale=1.1, amp=[(0, 0), (0.012, 1), (0.22, 0.85), (0.32, 0)], breath=0.06), 0.12, 1.0)
    return m.x


@sfx('desert_dragon/ambient2')
def _(r):  # "grrr-rip": a long, soft little growl with a tiny squeak at the end
    m = Mix()
    m.add(syl(r, 0.5, [(0, 150), (0.15, 185), (0.35, 170), (0.5, 140)], [(0, 'o'), (0.2, 'uh'), (0.5, 'o')],
              amp=[(0, 0), (0.05, 0.8), (0.35, 0.9), (0.5, 0)], rough=(46, 0.55), tilt=1.0, vibrato=None, breath=0.1), 0.0, 1.0)
    m.add(syl(r, 0.14, [(0, 900), (0.05, 1150), (0.14, 1000)], [(0, 'e'), (0.14, 'i')],
              amp=[(0, 0), (0.01, 1), (0.09, 0.6), (0.14, 0)]), 0.45, 0.5)
    return m.x


@sfx('desert_dragon/happy1')
def _(r):  # "chi-chi-chirrup!": two quick chirps, then a trilling one
    m = Mix()
    m.add(syl(r, 0.12, [(0, 820), (0.04, 1250), (0.12, 1150)], [(0, 'i'), (0.12, 'e')], vibrato=None,
              amp=[(0, 0), (0.008, 1), (0.08, 0.8), (0.12, 0)]), 0.0, 0.9)
    m.add(syl(r, 0.13, [(0, 900), (0.05, 1400), (0.13, 1300)], [(0, 'i'), (0.13, 'e')], vibrato=None,
              amp=[(0, 0), (0.008, 1), (0.09, 0.8), (0.13, 0)]), 0.15, 0.95)
    m.add(syl(r, 0.32, [(0, 1000), (0.08, 1650), (0.2, 1450), (0.32, 1150)], [(0, 'e'), (0.15, 'a'), (0.32, 'u')],
              vibrato=(14, 70, 0.04), amp=[(0, 0), (0.01, 1), (0.22, 0.85), (0.32, 0)], breath=0.05), 0.31, 1.0)
    return m.x


@sfx('desert_dragon/happy2')
def _(r):  # purr into a little "mew"
    m = Mix()
    m.add(syl(r, 0.4, [(0, 190), (0.2, 225), (0.4, 205)], [(0, 'uh'), (0.4, 'o')], tilt=1.0, vibrato=None,
              amp=[(0, 0), (0.1, 0.7), (0.3, 0.8), (0.4, 0)], rough=(29, 0.45), breath=0.02), 0.0, 0.6)
    m.add(syl(r, 0.3, [(0, 780), (0.09, 1150), (0.3, 880)], [(0, 'm'), (0.05, 'e'), (0.3, 'a')],
              vibrato=(6.5, 28, 0.12), amp=[(0, 0), (0.02, 1), (0.22, 0.85), (0.3, 0)]), 0.3, 1.0)
    return m.x


@sfx('desert_dragon/hurt1')
def _(r):  # "kyeh!"
    return syl(r, 0.3, [(0, 950), (0.05, 1750), (0.14, 1500), (0.3, 1000)], [(0, 'e'), (0.1, 'ae'), (0.3, 'a')],
               amp=[(0, 0), (0.006, 1), (0.12, 0.9), (0.3, 0)], rough=(72, 0.3), breath=0.12, vibrato=None)


@sfx('desert_dragon/death1')
def _(r):  # long falling whine that turns into a growl and fades
    return syl(r, 0.95, [(0, 1100), (0.2, 980), (0.55, 720), (0.95, 430)], [(0, 'a'), (0.5, 'o'), (0.95, 'u')],
               vibrato=(6, 38, 0.25), rough=(40, [(0, 0.0), (0.4, 0.1), (0.95, 0.55)]),
               amp=[(0, 0), (0.03, 1), (0.6, 0.8), (0.95, 0)], breath=0.08)


def dpeep(r, dur, f_pts, vibrato=None, amp=None, h=(1.0, 0.2, 0.06)):
    """Warm little-dragon peep: a soft, nearly pure tone (a touch of 2nd/3rd harmonic), never noisy."""
    return whistle(dur, f_pts, r, h=h, vibrato=vibrato, amp=amp, a=0.008, rel=0.03)


@sfx('desert_dragon/ambient3')
def _(r):  # "pi-pip": two soft peeps, the second one a little higher
    m = Mix()
    m.add(dpeep(r, 0.09, [(0, 1050), (0.035, 1450), (0.09, 1350)]), 0.0, 0.9)
    m.add(dpeep(r, 0.11, [(0, 1150), (0.04, 1650), (0.11, 1500)], vibrato=(12, 40, 0.04)), 0.14, 1.0)
    return m.x


@sfx('desert_dragon/ambient4')
def _(r):  # "mrr-eep": a soft tonal coo that tips up into a peep
    m = Mix()
    m.add(syl(r, 0.24, [(0, 190), (0.1, 235), (0.24, 250)], [(0, 'uh'), (0.24, 'o')], tilt=1.3, vibrato=(5, 18, 0.05),
              amp=[(0, 0), (0.04, 0.9), (0.18, 0.85), (0.24, 0)]), 0.0, 0.7)
    m.add(dpeep(r, 0.2, [(0, 900), (0.07, 1500), (0.2, 1300)], vibrato=(9, 45, 0.06),
                amp=[(0, 0), (0.012, 1), (0.14, 0.85), (0.2, 0)]), 0.2, 1.0)
    return m.x


@sfx('desert_dragon/happy3')
def _(r):  # "pi-pi-piiii!": three rising peeps, the last one sings
    m = Mix()
    m.add(dpeep(r, 0.08, [(0, 950), (0.03, 1250), (0.08, 1200)]), 0.0, 0.85)
    m.add(dpeep(r, 0.08, [(0, 1100), (0.03, 1450), (0.08, 1400)]), 0.12, 0.92)
    m.add(dpeep(r, 0.34, [(0, 1250), (0.1, 1900), (0.22, 1750), (0.34, 1500)], vibrato=(8, 60, 0.08),
                amp=[(0, 0), (0.012, 1), (0.24, 0.85), (0.34, 0)]), 0.25, 1.0)
    m.add(rl(sparkle(0.25, r, 4, 3500, 6500, True, 1.0), -22), 0.4)
    return m.x


@sfx('desert_dragon/happy4')
def _(r):  # "wee-oo-wee": a gentle warble that swings up and down
    m = Mix()
    m.add(dpeep(r, 0.42, [(0, 950), (0.12, 1550), (0.24, 1150), (0.34, 1650), (0.42, 1400)], vibrato=(7, 35, 0.05),
                amp=[(0, 0), (0.015, 1), (0.3, 0.9), (0.42, 0)]), 0.0, 1.0)
    m.add(syl(r, 0.34, [(0, 300), (0.14, 360), (0.34, 320)], [(0, 'oo'), (0.34, 'o')], tilt=1.5, vibrato=(5, 20, 0.1),
              amp=[(0, 0), (0.06, 1), (0.24, 0.8), (0.34, 0)]), 0.0, 0.3)
    return m.x


@sfx('desert_dragon/hurt2')
def _(r):  # "eep!": one quick sliding peep
    return dpeep(r, 0.18, [(0, 1100), (0.03, 1900), (0.18, 1000)], vibrato=(16, 50, 0.02),
                 amp=[(0, 0), (0.006, 1), (0.1, 0.9), (0.18, 0)], h=(1.0, 0.3, 0.1))


@sfx('desert_dragon/hurt3')
def _(r):  # "yip-ip": two falling squeaks
    m = Mix()
    m.add(dpeep(r, 0.11, [(0, 1700), (0.11, 1000)], h=(1.0, 0.3, 0.1)), 0.0, 1.0)
    m.add(dpeep(r, 0.13, [(0, 1500), (0.13, 800)], h=(1.0, 0.3, 0.1)), 0.14, 0.85)
    return m.x


@sfx('desert_dragon/death2')
def _(r):  # a little falling "pi-pi-pii-oo" that slows down and sinks
    m = Mix()
    t = 0.0
    for i, f in enumerate([1700, 1450, 1150, 900]):
        d = 0.09 + 0.03 * i
        m.add(dpeep(r, d, [(0, f * 1.06), (d, f * 0.95)], vibrato=(7, 30, 0.0)), t, 1.0 - 0.12 * i)
        t += d + 0.05 + 0.02 * i
    m.add(syl(r, 0.4, [(0, 330), (0.4, 190)], [(0, 'o'), (0.4, 'u')], tilt=1.5, vibrato=(5, 25, 0.1),
              amp=[(0, 0), (0.08, 1), (0.28, 0.7), (0.4, 0)]), t - 0.1, 0.35)
    return m.x


@sfx('desert_dragon/attack1')
def _(r):  # small fire puff: breathy "fwoof" + warm thump + a few embers
    dur = 0.55
    puff = whoosh(dur, [(0, 500), (0.05, 1400), (0.14, 2400), (0.35, 1100), (0.55, 600)], r, q=0.9,
                  env=[(0, 0), (0.025, 1), (0.12, 0.9), (0.3, 0.35), (0.55, 0)])
    rum = lp(brown(N(dur), r), 220, 2) * curve([(0, 0), (0.04, 1), (0.3, 0.4), (0.55, 0)], dur, sm=0.01)
    cr = scatter(dur, poisson(dur, 40, r, 0.06, lambda x: 1 - x), r, freq=(2500, 6500), tau=(0.0006, 0.002), amp=(0.1, 0.5))
    m = Mix()
    m.add(rl(lp(puff, 3800, 2), 0))
    m.add(rl(rum, -3))
    m.add(1.2 * rl(thud(0.25, 140, 64, 0.05, 0.09), -2))
    m.add(rl(cr, -11))
    return m.x


@sfx('desert_dragon/attack2')
def _(r):  # shorter, snappier puff with more sparks
    dur = 0.42
    puff = whoosh(dur, [(0, 700), (0.04, 2200), (0.1, 3200), (0.25, 1300), (0.42, 700)], r, q=1.0,
                  env=[(0, 0), (0.015, 1), (0.08, 0.85), (0.22, 0.3), (0.42, 0)])
    rum = lp(brown(N(dur), r), 260, 2) * curve([(0, 0), (0.03, 1), (0.22, 0.35), (0.42, 0)], dur, sm=0.01)
    cr = scatter(dur, poisson(dur, 70, r, 0.04, lambda x: 1 - 0.6 * x), r, freq=(2800, 7000), tau=(0.0005, 0.0018), amp=(0.15, 0.6))
    m = Mix()
    m.add(rl(lp(puff, 4200, 2), 0))
    m.add(rl(rum, -3))
    m.add(1.1 * rl(thud(0.2, 160, 70, 0.04, 0.07), -2))
    m.add(rl(cr, -9))
    return m.x


# ---------------------------------------------------------------------------------------------------
# 4b. JUNGLE DRAGON - chirpy bird-like trills; a leafy snap to attack
# ---------------------------------------------------------------------------------------------------


def pip(r, f, dur=0.05, glide=1.12, amp=1.0, fm_idx=0.0):
    """One short bird note rising into pitch f."""
    y = whistle(dur, [(0, f / glide), (dur * 0.4, f * 1.03), (dur, f)], r, a=0.004, rel=0.012)
    return amp * y


@sfx('jungle_dragon/ambient1')
def _(r):  # "tit-tit-ti-tit": a short run of pips
    m = Mix()
    for i, f in enumerate([2000, 2400, 2200, 2700, 2450]):
        m.add(pip(r, f, 0.055, 1.14), i * 0.048, 1.0 - 0.06 * i)
    return m.x


@sfx('jungle_dragon/ambient2')
def _(r):  # "twee-oo": a slurred whistle with a little warble
    y = whistle(0.34, [(0, 1500), (0.1, 2500), (0.21, 2350), (0.34, 1700)], r, vibrato=(13, 70, 0.1),
                amp=[(0, 0), (0.012, 1), (0.25, 0.8), (0.34, 0)])
    pop = pip(r, 1300, 0.03, 1.3)
    m = Mix()
    m.add(y, 0.02, 1.0)
    m.add(pop, 0.0, 0.5)
    return m.x


@sfx('jungle_dragon/happy1')
def _(r):  # long warbling trill that climbs and tips over
    return whistle(0.8, [(0, 1700), (0.25, 2100), (0.55, 2500), (0.8, 2000)], r, vibrato=(15, 260, 0.0),
                   amp=[(0, 0), (0.02, 1), (0.6, 0.9), (0.8, 0)])


@sfx('jungle_dragon/happy2')
def _(r):  # "ti-ti-tweeee!"
    m = Mix()
    m.add(pip(r, 1900, 0.05, 1.12), 0.0)
    m.add(pip(r, 2200, 0.05, 1.12), 0.075)
    m.add(whistle(0.28, [(0, 1700), (0.18, 2800), (0.28, 2600)], r, vibrato=(12, 55, 0.1),
                  amp=[(0, 0), (0.012, 1), (0.2, 0.9), (0.28, 0)]), 0.16, 1.0)
    return m.x


@sfx('jungle_dragon/hurt1')
def _(r):  # sharp squawk "kyaa!"
    return syl(r, 0.24, [(0, 1400), (0.05, 2300), (0.24, 1250)], [(0, 'ae'), (0.24, 'a')],
               amp=[(0, 0), (0.005, 1), (0.1, 0.9), (0.24, 0)], rough=(95, 0.3), breath=0.14, vibrato=None)


@sfx('jungle_dragon/death1')
def _(r):  # a trill that slows down and sinks
    m = Mix()
    t = 0.0
    fs = [2600, 2350, 2050, 1750, 1450, 1200, 950]
    for i, f in enumerate(fs):
        d = 0.07 + 0.016 * i
        m.add(whistle(d, [(0, f * 1.08), (d, f * 0.94)], r, a=0.006, rel=0.03, vibrato=(7, 40, 0.0)), t, 1.0 - 0.1 * i)
        t += d + 0.025 + 0.01 * i
    return m.x


@sfx('jungle_dragon/attack1')
def _(r):  # leafy snap: rustle, a crisp snap, a woody tick and the leaves settling
    m = Mix()
    n1 = N(0.12)
    rus = hp(white(n1, r), 2500, 2) * flutter(n1, r, 90, 0.85) * curve([(0, 0), (0.07, 1), (0.12, 0.2)], 0.12, sm=0.004)
    m.add(rl(rus, -6), 0.0)
    m.add(pl(burst(0.04, r, 0.005, (1800, 7500)), 0.0), 0.095)
    m.add(pl(modes(0.1, [(700, 1.0, 0.018), (1250, 0.4, 0.01)], r), -5), 0.095)
    n2 = N(0.22)
    tail = bp(white(n2, r), 3000, 8000, 1) * flutter(n2, r, 55, 0.9) * pluck(0.22, 0.004, 0.06)
    m.add(rl(tail, -9), 0.11)
    return m.x


@sfx('jungle_dragon/attack2')
def _(r):  # double snap, a little higher
    m = Mix()
    for i, t0 in enumerate([0.0, 0.11]):
        n1 = N(0.07)
        rus = hp(white(n1, r), 3000, 2) * flutter(n1, r, 110, 0.85) * curve([(0, 0), (0.04, 1), (0.07, 0.2)], 0.07, sm=0.003)
        m.add(rl(rus, -7), t0)
        m.add(pl(burst(0.035, r, 0.004, (2200, 8000)), -1 * i), t0 + 0.05)
        m.add(pl(modes(0.08, [(820 + 90 * i, 1.0, 0.014), (1500, 0.4, 0.008)], r), -6), t0 + 0.05)
    n2 = N(0.2)
    tail = bp(white(n2, r), 3500, 9000, 1) * flutter(n2, r, 60, 0.9) * pluck(0.2, 0.004, 0.05)
    m.add(rl(tail, -10), 0.17)
    return m.x


# ---------------------------------------------------------------------------------------------------
# 4c. TIDE DRAGON - watery squeaks like a baby dolphin; a bubble burst to attack
# ---------------------------------------------------------------------------------------------------


def squeak(r, dur, f_pts, trem=(11.0, 0.25), index=0.35, ratio=1.5, amp=None, a=0.008, rel=0.03):
    """Dolphin-style whistle: smooth FM tone with a watery tremolo."""
    n = N(dur)
    f = curve(f_pts, dur, log=True, sm=0.006) * drift(n, r, 0.004, 9.0)
    y = fm(f, ratio, index)
    if trem:
        y = y * (1.0 - trem[1] + trem[1] * (0.5 + 0.5 * np.sin(TAU * trem[0] * T(dur) + r.uniform(0, TAU))))
    env = curve(amp, dur, sm=0.003) if isinstance(amp, list) else tone_env(dur, a, rel)
    return y * env


def clicks(r, k, gap=0.011, level=-4.0):
    """A short train of dolphin clicks."""
    m = Mix()
    for i in range(k):
        m.add(pl(burst(0.012, r, 0.0012, (2500, 7500)), level), i * gap)
    return m.x


@sfx('tide_dragon/ambient1')
def _(r):  # clicks, then a smooth whistle, then a tiny bubble
    m = Mix()
    m.add(clicks(r, 4), 0.0, 0.7)
    m.add(squeak(r, 0.32, [(0, 1700), (0.1, 2900), (0.2, 2500), (0.32, 2000)]), 0.05, 1.0)
    m.add(bubble(900, 0.3, 1.0), 0.32, 0.3)
    return m.x


@sfx('tide_dragon/ambient2')
def _(r):  # "blup-eee"
    m = Mix()
    m.add(bubble(650, 0.35, 1.0), 0.0, 0.9)
    m.add(squeak(r, 0.24, [(0, 1500), (0.12, 2300), (0.24, 2000)], trem=(9, 0.35)), 0.09, 0.9)
    m.add(bubble(1100, 0.3, 1.0), 0.36, 0.3)
    return m.x


@sfx('tide_dragon/happy1')
def _(r):  # "ee-ee-ee-eeeh!" with bubbles
    m = Mix()
    for t0, f in [(0.0, 1700), (0.17, 1950), (0.34, 2250)]:
        m.add(squeak(r, 0.13, [(0, f * 0.85), (0.07, f * 1.15), (0.13, f)], trem=(12, 0.2)), t0, 0.9)
    m.add(squeak(r, 0.3, [(0, 2000), (0.12, 3000), (0.3, 2300)], trem=(10, 0.3)), 0.52, 1.0)
    for i, f in enumerate([700, 950, 1300, 820]):
        m.add(bubble(f, 0.3, 1.0), 0.78 + 0.045 * i, 0.3)
    return m.x


@sfx('tide_dragon/happy2')
def _(r):  # bubbly giggle: a "bloop" and a rising two-note squeak
    m = Mix()
    m.add(bubble(500, 0.5, 1.0), 0.0, 0.8)
    m.add(squeak(r, 0.14, [(0, 1800), (0.14, 2400)], trem=(13, 0.2)), 0.1, 0.9)
    m.add(squeak(r, 0.2, [(0, 2200), (0.1, 3100), (0.2, 2700)], trem=(11, 0.3)), 0.27, 1.0)
    return m.x


@sfx('tide_dragon/hurt1')
def _(r):  # "yeek": a falling squeal with a click
    m = Mix()
    m.add(clicks(r, 2), 0.0, 0.6)
    m.add(squeak(r, 0.24, [(0, 2900), (0.05, 3000), (0.24, 1200)], trem=(15, 0.2), index=1.0,
                 amp=[(0, 0), (0.006, 1), (0.14, 0.8), (0.24, 0)]), 0.012, 1.0)
    return m.x


@sfx('tide_dragon/death1')
def _(r):  # a sad whistle that sinks, followed by a few drifting bubbles
    m = Mix()
    y = squeak(r, 0.9, [(0, 2400), (0.25, 2200), (0.6, 1300), (0.9, 700)], trem=(7.5, 0.3), index=0.3,
               amp=[(0, 0), (0.02, 1), (0.6, 0.85), (0.9, 0)])
    f = np.interp(T(0.9), [0, 0.9], [60, 160])
    m.add(y * (0.8 + 0.2 * np.sin(TAU * np.cumsum(7.0 * (1 + 0.0 * f)) / SR)), 0.0, 1.0)
    for i, fq in enumerate([1000, 800, 620]):
        m.add(bubble(fq, 0.3, 1.0), 0.8 + 0.07 * i, 0.3 - 0.07 * i)
    return m.x


@sfx('tide_dragon/attack1')
def _(r):  # bubble burst: a wet blast, a rush of bubbles and one big "bloop"
    m = Mix()
    m.add(rl(whoosh(0.3, [(0, 1800), (0.06, 900), (0.3, 350)], r, q=0.9, env=[(0, 0), (0.01, 1), (0.08, 0.6), (0.3, 0)]), -4), 0.0)
    t = 0.01
    for i in range(11):
        m.add(bubble(r.uniform(450, 2300), 0.25, 1.0), t, r.uniform(0.3, 0.9))
        t += r.uniform(0.012, 0.034)
    m.add(bubble(260, 0.4, 1.0), 0.1, 1.1)
    return m.x


@sfx('tide_dragon/attack2')
def _(r):  # "blorp-pop-pop": a fat bubble, small ones, a splash
    m = Mix()
    m.add(bubble(210, 0.5, 1.0), 0.0, 1.2)
    for i in range(5):
        m.add(bubble(r.uniform(700, 2000), 0.25, 1.0), 0.12 + 0.03 * i + r.uniform(0, 0.012), r.uniform(0.3, 0.7))
    m.add(rl(whoosh(0.25, [(0, 2500), (0.25, 600)], r, q=0.8, env=[(0, 0), (0.02, 1), (0.25, 0)]), -9), 0.1)
    m.add(1.0 * pl(thud(0.12, 520, 200, 0.02, 0.03), -3), 0.3)
    return m.x


# ---------------------------------------------------------------------------------------------------
# 4d. FROST PENGUIN - tiny honks and squeaks; a snowball throw to attack
# ---------------------------------------------------------------------------------------------------


def honk(r, dur, f0, amp=None, vibrato=None, rough=(105, 0.22), vow=None, breath=0.05):
    """A small nasal, reedy honk."""
    v = vow or [(0, 'ae'), (dur, 'er')]
    return syl(r, dur, f0, v, amp=amp, scale=1.05, tilt=0.85, nasal=0.5, rough=rough, vibrato=vibrato, breath=breath,
               qs=(8.0, 12.0, 16.0))


@sfx('frost_penguin/ambient1')
def _(r):  # "kweh-keh": a honk and a shorter honk
    m = Mix()
    m.add(honk(r, 0.2, [(0, 430), (0.05, 620), (0.12, 640), (0.2, 520)], amp=[(0, 0), (0.01, 1), (0.14, 0.85), (0.2, 0)]), 0.0)
    m.add(honk(r, 0.13, [(0, 560), (0.04, 730), (0.13, 600)], amp=[(0, 0), (0.008, 1), (0.09, 0.8), (0.13, 0)]), 0.25, 0.85)
    return m.x


@sfx('frost_penguin/ambient2')
def _(r):  # "pip-honk"
    m = Mix()
    m.add(syl(r, 0.06, [(0, 1250), (0.06, 1650)], [(0, 'i'), (0.06, 'e')], vibrato=None, amp=[(0, 0), (0.006, 1), (0.04, 0.8), (0.06, 0)]), 0.0, 0.8)
    m.add(honk(r, 0.24, [(0, 640), (0.06, 700), (0.24, 470)], amp=[(0, 0), (0.012, 1), (0.16, 0.8), (0.24, 0)]), 0.09, 1.0)
    return m.x


@sfx('frost_penguin/happy1')
def _(r):  # "kwe-kwe-kwe-kweee!"
    m = Mix()
    for i, t0 in enumerate([0.0, 0.14, 0.28]):
        b = 60 * i
        m.add(honk(r, 0.1, [(0, 480 + b), (0.04, 720 + b), (0.1, 620 + b)], amp=[(0, 0), (0.008, 1), (0.07, 0.8), (0.1, 0)]), t0, 0.9)
    m.add(honk(r, 0.32, [(0, 650), (0.07, 950), (0.32, 800)], vibrato=(6.5, 45, 0.1),
               amp=[(0, 0), (0.012, 1), (0.22, 0.85), (0.32, 0)]), 0.44, 1.0)
    return m.x


@sfx('frost_penguin/happy2')
def _(r):  # "pi-pi-pi-hweee"
    m = Mix()
    for i, t0 in enumerate([0.0, 0.085, 0.17]):
        m.add(syl(r, 0.055, [(0, 1250 + 70 * i), (0.055, 1700 + 70 * i)], [(0, 'i'), (0.055, 'e')], vibrato=None,
                  amp=[(0, 0), (0.005, 1), (0.04, 0.8), (0.055, 0)]), t0, 0.85)
    m.add(syl(r, 0.3, [(0, 900), (0.1, 1400), (0.3, 1600)], [(0, 'u'), (0.1, 'i'), (0.3, 'i')], breath=0.3,
              vibrato=(7, 30, 0.1), amp=[(0, 0), (0.03, 1), (0.22, 0.85), (0.3, 0)]), 0.26, 1.0)
    return m.x


@sfx('frost_penguin/hurt1')
def _(r):  # "kweeek!"
    return honk(r, 0.27, [(0, 700), (0.06, 1500), (0.15, 1300), (0.27, 850)], rough=(90, 0.3),
                vow=[(0, 'ae'), (0.1, 'e'), (0.27, 'er')], amp=[(0, 0), (0.007, 1), (0.14, 0.9), (0.27, 0)], breath=0.1)


@sfx('frost_penguin/death1')
def _(r):  # a sad honk that wobbles down and away
    return honk(r, 0.9, [(0, 850), (0.15, 820), (0.5, 520), (0.9, 320)], vibrato=(5.2, 45, 0.15), rough=(60, [(0, 0.1), (0.9, 0.4)]),
                vow=[(0, 'ae'), (0.5, 'er'), (0.9, 'u')], amp=[(0, 0), (0.03, 1), (0.6, 0.8), (0.9, 0)], breath=0.08)


def snow_poof(r, level=-5.0):
    m = Mix()
    m.add(rl(burst(0.13, r, 0.03, (None, 1500)), level), 0.0)
    m.add(rl(scatter(0.1, [0.0, 0.018, 0.04, 0.06], r, freq=(2500, 6000), tau=(0.001, 0.003)), level - 9.0), 0.0)
    return m.x


@sfx('frost_penguin/attack1')
def _(r):  # "hup!" + a whoosh + a soft "poff" where the snowball lands
    m = Mix()
    m.add(syl(r, 0.09, [(0, 300), (0.05, 430), (0.09, 380)], [(0, 'u'), (0.09, 'o')], vibrato=None,
              amp=[(0, 0), (0.01, 1), (0.06, 0.8), (0.09, 0)]), 0.0, 0.8)
    m.add(rl(whoosh(0.17, [(0, 900), (0.07, 3200), (0.17, 1800)], r, q=1.4, env=[(0, 0), (0.03, 1), (0.09, 0.8), (0.17, 0)]), -4), 0.07)
    m.add(snow_poof(r), 0.27)
    return m.x


@sfx('frost_penguin/attack2')
def _(r):  # a quick volley: two throws, two poofs
    m = Mix()
    for i, t0 in enumerate([0.0, 0.2]):
        m.add(rl(whoosh(0.14, [(0, 1100 + 300 * i), (0.06, 3600), (0.14, 2000)], r, q=1.4,
                        env=[(0, 0), (0.025, 1), (0.08, 0.8), (0.14, 0)]), -4), t0)
        m.add(snow_poof(r, -6.0 - 2 * i), t0 + 0.17)
    return m.x


# ---------------------------------------------------------------------------------------------------
# 4e. EMBER PUP - small yips with ember crackle, a bit growly but sweet; a fiery snap to attack
# ---------------------------------------------------------------------------------------------------


def yip(r, f=1.0, dur=0.12, amp=None):
    return syl(r, dur, [(0, 950 * f), (dur * 0.33, 1550 * f), (dur, 1250 * f)], [(0, 'i'), (dur, 'ae')], vibrato=None,
               amp=amp or [(0, 0), (0.006, 1), (dur * 0.65, 0.8), (dur, 0)])


def ember_ticks(r, dur, rate, level=-14.0, fall=True):
    ts = poisson(dur, rate, r, 0.0, (lambda x: 1.0 - 0.8 * x) if fall else None)
    return rl(scatter(dur, ts, r, freq=(2500, 7000), tau=(0.0006, 0.002), amp=(0.1, 0.6)), level)


@sfx('ember_pup/ambient1')
def _(r):  # "yip!" with a small growl behind it and a few embers
    m = Mix()
    m.add(yip(r), 0.0, 1.0)
    m.add(syl(r, 0.22, [(0, 190), (0.1, 215), (0.22, 175)], [(0, 'uh'), (0.22, 'o')], tilt=1.0, vibrato=None, rough=(58, 0.7),
              amp=[(0, 0), (0.04, 0.8), (0.14, 0.6), (0.22, 0)]), 0.1, 0.35)
    m.add(ember_ticks(r, 0.5, 26), 0.0)
    return m.x


@sfx('ember_pup/ambient2')
def _(r):  # "yip-yip" and a tiny ember pop
    m = Mix()
    m.add(yip(r, 1.0), 0.0, 1.0)
    m.add(yip(r, 1.18, 0.11), 0.17, 0.9)
    m.add(pl(modes(0.06, [(1800, 1.0, 0.012), (2900, 0.4, 0.006)], r, click=0.5), -9), 0.33)
    m.add(ember_ticks(r, 0.45, 22, -15.0), 0.05)
    return m.x


@sfx('ember_pup/happy1')
def _(r):  # excited rising yaps and a happy "wooo"
    m = Mix()
    for i, t0 in enumerate([0.0, 0.1, 0.2]):
        m.add(yip(r, 1.0 + 0.13 * i, 0.09), t0, 0.9)
    m.add(syl(r, 0.28, [(0, 1200), (0.1, 1800), (0.28, 1500)], [(0, 'o'), (0.12, 'a'), (0.28, 'o')], vibrato=(7, 35, 0.08),
              amp=[(0, 0), (0.015, 1), (0.2, 0.85), (0.28, 0)]), 0.32, 1.0)
    m.add(ember_ticks(r, 0.6, 28, -13.0, fall=False), 0.0)
    return m.x


@sfx('ember_pup/hurt1')
def _(r):  # "kyai!"
    return syl(r, 0.25, [(0, 1100), (0.05, 2000), (0.12, 1700), (0.25, 1250)], [(0, 'e'), (0.1, 'ae'), (0.25, 'a')], rough=(80, 0.25),
               vibrato=None, breath=0.1, amp=[(0, 0), (0.006, 1), (0.14, 0.9), (0.25, 0)])


@sfx('ember_pup/death1')
def _(r):  # a long whimper, embers dying out
    m = Mix()
    m.add(syl(r, 0.95, [(0, 1400), (0.2, 1250), (0.55, 800), (0.95, 470)], [(0, 'a'), (0.5, 'o'), (0.95, 'u')],
              vibrato=(6, 50, 0.2), breath=0.1, amp=[(0, 0), (0.03, 1), (0.6, 0.8), (0.95, 0)]), 0.0, 1.0)
    m.add(ember_ticks(r, 0.95, 30, -12.0), 0.0)
    return m.x


@sfx('ember_pup/attack1')
def _(r):  # fiery snap: a growly bark, a sharp snap, a flame flash and sparks
    m = Mix()
    m.add(syl(r, 0.1, [(0, 230), (0.04, 320), (0.1, 260)], [(0, 'a'), (0.1, 'o')], tilt=1.0, vibrato=None, rough=(70, 0.6),
              amp=[(0, 0), (0.008, 1), (0.06, 0.9), (0.1, 0)]), 0.0, 0.8)
    m.add(pl(burst(0.05, r, 0.006, (1800, 8000)), 0.0), 0.07)
    m.add(rl(lp(whoosh(0.3, [(0, 700), (0.05, 2400), (0.3, 900)], r, q=1.0, env=[(0, 0), (0.01, 1), (0.08, 0.8), (0.3, 0)]), 4200), -5), 0.07)
    m.add(ember_ticks(r, 0.35, 60, -10.0), 0.1)
    return m.x


@sfx('ember_pup/attack2')
def _(r):  # "chk-fwoof": two tooth clicks, then a flame swell
    m = Mix()
    for t0, f in [(0.0, 2400), (0.07, 3100)]:
        m.add(pl(burst(0.03, r, 0.004, (1500, 8000)), -1), t0)
        m.add(pl(modes(0.05, [(f, 1.0, 0.006)], r), -8), t0)
    m.add(rl(lp(whoosh(0.36, [(0, 600), (0.06, 2000), (0.36, 700)], r, q=0.9, env=[(0, 0), (0.02, 1), (0.1, 0.8), (0.36, 0)]), 3800), -3), 0.08)
    m.add(1.0 * rl(thud(0.2, 150, 70, 0.04, 0.07), -3), 0.08)
    m.add(ember_ticks(r, 0.4, 55, -10.0), 0.12)
    return m.x


# ---------------------------------------------------------------------------------------------------
# 4f. SCULK WISP - eerie whispery coos and sculk clicks; a sonic chirp to attack
# ---------------------------------------------------------------------------------------------------


def coo(r, dur, f0, vow, breath=0.5, vibrato=(4.6, 24.0, 0.2), amp=None, tilt=1.7):
    """Breathy two-voice "ooo" (a slightly detuned pair gives the ghostly choir effect)."""
    a = syl(r, dur, f0, vow, amp=amp, scale=1.1, breath=breath, vibrato=vibrato, tilt=tilt)
    f0b = [(t, f * 1.007) for t, f in f0]
    b = syl(r, dur, f0b, vow, amp=amp, scale=1.1, breath=breath, vibrato=(vibrato[0] * 0.93, vibrato[1], vibrato[2]), tilt=tilt)
    return 0.6 * (a + b)


def sculk_click(r, f=1500.0, level=-6.0):
    return pl(modes(0.07, [(f, 1.0, 0.012), (f * 1.51, 0.5, 0.008), (f * 2.3, 0.25, 0.005)], r, click=0.3), level)


@sfx('sculk_wisp/ambient1')
def _(r):  # a soft "ooo-ah" with a couple of sculk ticks
    m = Mix()
    m.add(coo(r, 0.75, [(0, 380), (0.25, 520), (0.75, 430)], [(0, 'u'), (0.3, 'o'), (0.75, 'u')],
              amp=[(0, 0), (0.12, 1), (0.5, 0.85), (0.75, 0)]), 0.0, 1.0)
    for t0, f in [(0.12, 1400), (0.19, 2000), (0.58, 1700)]:
        m.add(sculk_click(r, f, -3.0), t0, 0.9)
    return reverb(m.x, 0.5, 0.3)


@sfx('sculk_wisp/ambient2')
def _(r):  # "tk-tk-tk ... tk-tk" over a faint hum and a breath of air
    m = Mix()
    for t0, f in [(0.0, 1300), (0.075, 1900), (0.14, 1600), (0.44, 2200), (0.51, 1500)]:
        m.add(sculk_click(r, f, -4.0), t0, 0.9)
    m.add(coo(r, 0.55, [(0, 330), (0.2, 350), (0.55, 300)], [(0, 'u'), (0.55, 'oo')], breath=0.6,
              amp=[(0, 0), (0.12, 1), (0.4, 0.8), (0.55, 0)]), 0.05, 0.6)
    air = bp(white(N(0.6), r), 1800, 5200, 1) * swell(0.6, 0.4, 1.2)
    m.add(rl(air, -20.0), 0.0)
    return reverb(m.x, 0.45, 0.3)


@sfx('sculk_wisp/happy1')
def _(r):  # a rising, glittery "oo-woo!"
    m = Mix()
    m.add(coo(r, 0.62, [(0, 420), (0.2, 520), (0.42, 800), (0.62, 720)], [(0, 'u'), (0.25, 'o'), (0.62, 'a')], breath=0.35,
              amp=[(0, 0), (0.08, 1), (0.45, 0.9), (0.62, 0)]), 0.0, 1.0)
    for t0, f in [(0.42, 1500), (0.5, 2000), (0.58, 2700)]:
        m.add(sculk_click(r, f, -5.0), t0, 0.9)
    m.add(rl(sparkle(0.5, r, 9, 2500, 6500, True, 1.0), -20), 0.3)
    return reverb(m.x, 0.5, 0.3)


@sfx('sculk_wisp/hurt1')
def _(r):  # a startled, breathy "wuh!"
    m = Mix()
    m.add(coo(r, 0.3, [(0, 900), (0.08, 720), (0.3, 380)], [(0, 'o'), (0.3, 'u')], breath=0.45, vibrato=(9, 60, 0.0),
              amp=[(0, 0), (0.012, 1), (0.18, 0.7), (0.3, 0)]), 0.0, 1.0)
    m.add(sculk_click(r, 1800, -3.0), 0.0, 0.9)
    return reverb(m.x, 0.4, 0.25)


@sfx('sculk_wisp/death1')
def _(r):  # a long fading whisper that sinks away
    m = Mix()
    m.add(coo(r, 1.0, [(0, 600), (0.4, 430), (1.0, 250)], [(0, 'o'), (0.5, 'u'), (1.0, 'oo')], breath=0.45, vibrato=(5.0, 55, 0.7),
              amp=[(0, 0), (0.04, 1), (0.55, 0.7), (1.0, 0)]), 0.0, 1.0)
    for t0, f in [(0.7, 1300), (0.82, 1700), (0.97, 1200)]:
        m.add(sculk_click(r, f, -3.0), t0, 0.8)
    return reverb(m.x, 0.5, 0.3)


@sfx('sculk_wisp/attack1')
def _(r):  # sonic chirp: a quick charge-up, then a falling "pew" and a soft boom
    m = Mix()
    m.add(whistle(0.09, [(0, 600), (0.09, 2300)], r, h=(1, 0.2, 0.05), a=0.02, rel=0.012), 0.0, 0.6)
    m.add(lp(whistle(0.2, [(0, 3800), (0.03, 3000), (0.2, 750)], r, h=(1.0, 0.35, 0.12), amp=[(0, 0), (0.004, 1), (0.08, 0.7), (0.2, 0)]), 6500), 0.1, 1.0)
    m.add(rl(thud(0.25, 100, 48, 0.06, 0.1), -4), 0.1, 0.8)
    return reverb(m.x, 0.5, 0.3)


@sfx('sculk_wisp/attack2')
def _(r):  # "pi-pwoo": a ping, then a bigger falling sweep
    m = Mix()
    m.add(pl(bell(2900, 0.1, 0.6, 0.04, 'soft'), 0.0), 0.0, 0.7)
    m.add(lp(whistle(0.22, [(0, 2400), (0.04, 2200), (0.22, 500)], r, h=(1.0, 0.3, 0.1), amp=[(0, 0), (0.005, 1), (0.1, 0.7), (0.22, 0)]), 6500), 0.09, 1.0)
    m.add(rl(thud(0.2, 90, 44, 0.05, 0.08), -5), 0.1, 0.7)
    return reverb(m.x, 0.5, 0.3)


# ---------------------------------------------------------------------------------------------------
# 4g. VOID KITTEN - meows and purrs with a shimmery ender tone; a blink whoosh to attack
# ---------------------------------------------------------------------------------------------------


def meow(r, dur, f0, vow, breath=0.1, nasal=0.3, vibrato=(6.0, 20.0, 0.2), amp=None, rough=None):
    return syl(r, dur, f0, vow, amp=amp, scale=1.15, breath=breath, nasal=nasal, vibrato=vibrato, rough=rough)


def ender_shimmer(r, dur, f=2300.0, glide=0.0):
    """A glassy, slowly tremolo-ing cluster of detuned sines - the "ender" colour."""
    t = T(dur)
    fa = f * (1.0 + glide * np.linspace(0.0, 1.0, len(t)))
    y = np.zeros(len(t))
    for ratio, trate, a in [(1.0, 3.1, 1.0), (1.0127, 4.3, 0.8), (1.5, 2.6, 0.5), (2.01, 3.7, 0.25)]:
        y += a * np.sin(phase(fa * ratio) + r.uniform(0, TAU)) * (0.55 + 0.45 * np.sin(TAU * trate * t + r.uniform(0, TAU)))
    return y * swell(dur, 0.35, 1.3)


def purr(r, dur, rate=24.0, f_lo=900.0):
    """A very soft, high purr: a mostly tonal pulsing voice with just a whisper of low-passed noise.
    (Levelled by callers with rl(), so the gentleness is in the character: no low rattle, little noise.)"""
    n = N(dur)
    nz = bp(white(n, r), 350.0, f_lo, 2)
    rt = rate * drift(n, r, 0.04, 3.0)
    pulse = (0.5 + 0.5 * np.cos(phase(rt))) ** 2
    y = rl(nz * (0.3 + 0.7 * pulse), 0.0)
    v = syl(r, dur, [(0, 185), (dur, 170)], [(0, 'uh'), (dur, 'o')], tilt=1.5, vibrato=(4.5, 12, 0.1), rough=(rate, 0.45),
            amp=[(0, 0), (dur * 0.25, 1), (dur * 0.75, 1), (dur, 0)])
    return (0.25 * y + rl(v, 0.0)) * swell(dur, 0.4, 1.0)


@sfx('void_kitten/ambient1')
def _(r):  # "mi-aow" with a faint ender shimmer
    m = Mix()
    m.add(meow(r, 0.55, [(0, 520), (0.1, 820), (0.3, 760), (0.55, 520)], [(0, 'i'), (0.15, 'ae'), (0.35, 'a'), (0.55, 'u')],
               amp=[(0, 0), (0.03, 1), (0.4, 0.9), (0.55, 0)]), 0.0, 1.0)
    m.add(rl(ender_shimmer(r, 0.6, 2300.0, -0.08), -18), 0.08)
    return reverb(m.x, 0.5, 0.18)


@sfx('void_kitten/ambient2')
def _(r):  # a short questioning "mrp?"
    m = Mix()
    m.add(meow(r, 0.28, [(0, 650), (0.1, 900), (0.28, 860)], [(0, 'm'), (0.05, 'e'), (0.28, 'a')],
               amp=[(0, 0), (0.02, 1), (0.2, 0.9), (0.28, 0)], vibrato=(7, 25, 0.1)), 0.0, 1.0)
    m.add(rl(ender_shimmer(r, 0.45, 2700.0, 0.06), -19), 0.05)
    return reverb(m.x, 0.45, 0.15)


@sfx('void_kitten/happy1')
def _(r):  # purr with a happy "mrrp!" on top
    m = Mix()
    m.add(rl(purr(r, 0.6), -9), 0.0)
    m.add(meow(r, 0.22, [(0, 700), (0.07, 1000), (0.22, 850)], [(0, 'm'), (0.05, 'e'), (0.22, 'a')], amp=[(0, 0), (0.015, 1), (0.15, 0.85), (0.22, 0)]), 0.12, 1.0)
    m.add(rl(ender_shimmer(r, 0.5, 2500.0, 0.1), -19), 0.15)
    return reverb(m.x, 0.5, 0.15)


@sfx('void_kitten/happy2')
def _(r):  # "mew-mew" and a trail of stardust
    m = Mix()
    m.add(meow(r, 0.2, [(0, 700), (0.07, 1050), (0.2, 900)], [(0, 'm'), (0.05, 'e'), (0.2, 'a')], amp=[(0, 0), (0.012, 1), (0.14, 0.85), (0.2, 0)]), 0.0, 1.0)
    m.add(meow(r, 0.24, [(0, 780), (0.08, 1200), (0.24, 1000)], [(0, 'm'), (0.05, 'e'), (0.24, 'a')], amp=[(0, 0), (0.012, 1), (0.17, 0.85), (0.24, 0)]), 0.26, 1.0)
    m.add(rl(sparkle(0.45, r, 10, 3000, 7500, True, 1.0), -17), 0.3)
    return reverb(m.x, 0.5, 0.2)


@sfx('void_kitten/hurt1')
def _(r):  # a short yowl
    return meow(r, 0.3, [(0, 800), (0.06, 1600), (0.2, 1300), (0.3, 1000)], [(0, 'e'), (0.1, 'ae'), (0.3, 'a')], breath=0.15,
                nasal=0.2, vibrato=None, rough=(88, 0.25), amp=[(0, 0), (0.007, 1), (0.18, 0.9), (0.3, 0)])


@sfx('void_kitten/death1')
def _(r):  # a plaintive, fading meow with stardust falling away
    m = Mix()
    m.add(meow(r, 1.0, [(0, 900), (0.25, 700), (0.6, 500), (1.0, 380)], [(0, 'm'), (0.1, 'e'), (0.4, 'a'), (1.0, 'u')],
               vibrato=(5.5, 40, 0.3), amp=[(0, 0), (0.04, 1), (0.6, 0.8), (1.0, 0)]), 0.0, 1.0)
    m.add(rl(sparkle(0.6, r, 9, 7000, 2500, True, 1.0), -17), 0.45)
    return reverb(m.x, 0.6, 0.25)


@sfx('void_kitten/attack1')
def _(r):  # blink: a reversed shimmer swells in, a pop, glitter
    m = Mix()
    ping = pl(bell(1700, 0.12, 1.0, 0.05, 'soft'), 0.0)
    swell_in = reverse(reverb(ping, 0.4, 1.8, 0.002, 7000.0))
    m.add(rl(swell_in, 0.0), 0.0)
    L = len(swell_in) / SR
    m.add(rl(whoosh(0.2, [(0, 300), (0.18, 6500)], r, q=1.0, env=[(0, 0), (0.1, 0.7), (0.2, 1.0)]), -6), L - 0.2)
    m.add(pl(thud(0.09, 650, 220, 0.012, 0.03), -4), L)
    m.add(rl(sparkle(0.2, r, 6, 3500, 8000, False, 1.0), -18), L)
    return m.x


@sfx('void_kitten/attack2')
def _(r):  # "pip - whoosh": a flash and a fast falling sweep as it lands
    m = Mix()
    m.add(pl(bell(2600, 0.08, 0.6, 0.03, 'soft'), 0.0), 0.0, 0.6)
    m.add(rl(whoosh(0.22, [(0, 7000), (0.06, 3500), (0.22, 300)], r, q=1.0, env=[(0, 0), (0.015, 1), (0.08, 0.7), (0.22, 0)]), -3), 0.05)
    m.add(pl(thud(0.1, 520, 180, 0.015, 0.03), -6), 0.2)
    m.add(rl(sparkle(0.2, r, 5, 3500, 8000, False, 1.0), -19), 0.2)
    return reverb(m.x, 0.35, 0.2)


# ---------------------------------------------------------------------------------------------------
# 4h. PEBBLE GOLEM - stony rumbles, pebble clicks, a cute "hmm"; a heavy thud to attack
# ---------------------------------------------------------------------------------------------------


def stone_tick(r, f=None, level=-8.0, size=1.0):
    f = f or r.uniform(700, 2600)
    return pl(modes(0.05 * size + 0.01, [(f, 1.0, 0.007 * size), (f * 2.31, 0.5, 0.004 * size), (f * 3.7, 0.25, 0.003 * size)], r,
                    click=0.5, click_tau=0.0015, click_band=(1000, 6000)), level)


def rumble(r, dur, fc=150.0, am=(7.0, 0.5)):
    n = N(dur)
    y = lp(brown(n, r), fc, 2) * flutter(n, r, am[0], am[1])
    return y * swell(dur, 0.4, 1.0)


def hmm(r, dur, f0, vow, amp=None, vibrato=(4.5, 14.0, 0.2)):
    return syl(r, dur, f0, vow, amp=amp, scale=0.95, nasal=0.6, tilt=1.7, vibrato=vibrato, breath=0.04, qs=(5.0, 8.0, 10.0))


@sfx('pebble_golem/ambient1')
def _(r):  # a low, nosy "hmmm?" over a faint rumble and two pebble ticks
    m = Mix()
    m.add(hmm(r, 0.8, [(0, 150), (0.25, 172), (0.55, 160), (0.8, 138)], [(0, 'm'), (0.25, 'o'), (0.55, 'oo'), (0.8, 'm')],
              amp=[(0, 0), (0.08, 1), (0.55, 0.9), (0.8, 0)]), 0.0, 1.0)
    m.add(rl(rumble(r, 0.8), -9), 0.0)
    m.add(stone_tick(r, 1300, -10), 0.38)
    m.add(stone_tick(r, 1850, -13), 0.47)
    return m.x


@sfx('pebble_golem/ambient2')
def _(r):  # pebbles clicking around a deep, sleepy "mm"
    m = Mix()
    for t0 in [0.0, 0.11, 0.17, 0.36, 0.42, 0.55]:
        m.add(stone_tick(r, None, r.uniform(-9, -4)), t0)
    m.add(hmm(r, 0.65, [(0, 125), (0.3, 118), (0.65, 110)], [(0, 'm'), (0.4, 'o'), (0.65, 'm')], amp=[(0, 0), (0.1, 1), (0.45, 0.8), (0.65, 0)]), 0.0, 0.7)
    m.add(rl(rumble(r, 0.65, 130), -10), 0.0)
    return m.x


@sfx('pebble_golem/ambient3')
def _(r):  # "tk-tok-tk-tk": a little shuffle of pebbles and two hollow stone knocks over a faint rumble
    m = Mix()
    for t0, f, lv, sz in [(0.0, 900, -5, 1.2), (0.09, 1400, -8, 1.0), (0.31, 1100, -9, 1.0), (0.42, 820, -7, 1.2), (0.5, 1550, -12, 0.9)]:
        m.add(stone_tick(r, f, lv, sz), t0)
    m.add(pl(modes(0.14, [(250, 1.0, 0.035), (590, 0.45, 0.016), (1020, 0.2, 0.008)], r, click=0.25), -3), 0.18)
    m.add(pl(modes(0.12, [(310, 1.0, 0.03), (700, 0.4, 0.014)], r, click=0.25), -5), 0.25)
    m.add(rl(rumble(r, 0.62, 120, (9, 0.6)), -16), 0.0)
    return m.x


@sfx('pebble_golem/happy1')
def _(r):  # "hm-HM!" with a tinkle of pebbles
    m = Mix()
    m.add(hmm(r, 0.14, [(0, 150), (0.14, 168)], [(0, 'm'), (0.14, 'o')], amp=[(0, 0), (0.02, 1), (0.1, 0.8), (0.14, 0)]), 0.0, 0.8)
    m.add(hmm(r, 0.32, [(0, 190), (0.1, 265), (0.32, 240)], [(0, 'm'), (0.08, 'a'), (0.32, 'o')], amp=[(0, 0), (0.02, 1), (0.22, 0.85), (0.32, 0)],
              vibrato=(6, 25, 0.1)), 0.2, 1.0)
    for i in range(6):
        m.add(pl(modes(0.04, [(r.uniform(2500, 5000), 1.0, 0.004)], r), -12 + 0.4 * i), 0.3 + 0.045 * i + r.uniform(0, 0.015))
    return m.x


@sfx('pebble_golem/hurt1')
def _(r):  # "oof!" - a grunt, a stone clack and a few pebbles falling
    m = Mix()
    m.add(syl(r, 0.22, [(0, 260), (0.05, 300), (0.22, 150)], [(0, 'o'), (0.22, 'uh')], tilt=1.3, vibrato=None, nasal=0.3,
              amp=[(0, 0), (0.008, 1), (0.12, 0.8), (0.22, 0)]), 0.0, 1.0)
    m.add(stone_tick(r, 900, -4, 1.4), 0.0)
    for t0 in [0.1, 0.16, 0.21]:
        m.add(stone_tick(r, None, -12), t0)
    return m.x


@sfx('pebble_golem/death1')
def _(r):  # a sinking hum, crumbling rubble and a last soft thud
    m = Mix()
    m.add(hmm(r, 1.0, [(0, 220), (0.4, 160), (1.0, 85)], [(0, 'o'), (0.5, 'oo'), (1.0, 'm')], vibrato=(4.0, 40, 0.5),
              amp=[(0, 0), (0.05, 1), (0.6, 0.8), (1.0, 0)]), 0.0, 1.0)
    m.add(rl(rumble(r, 1.1, 170, (9, 0.6)), -7), 0.0)
    for t0 in poisson(1.0, 22, r, 0.05, lambda x: 1.0 - 0.9 * x):
        m.add(stone_tick(r, None, -12 - 6 * t0), t0)
    m.add(rl(thud(0.3, 95, 42, 0.05, 0.1), -4), 1.0, 0.8)
    return m.x


def stone_thud(r, f_hi=150.0, f_lo=56.0, dur=0.5, rubble=True):
    body = softclip(thud(dur, f_hi, f_lo, 0.05, 0.16), 2.2)
    crunch = bp(white(N(0.18), r), 300, 1800, 1) * pluck(0.18, 0.002, 0.03)
    m = Mix()
    m.add(rl(body, 0.0))
    m.add(rl(crunch, -2))
    if rubble:
        for t0 in [0.06, 0.13, 0.2, 0.27, 0.37]:
            m.add(stone_tick(r, None, -13), t0)
    return m.x


@sfx('pebble_golem/attack1')
def _(r):  # heavy thud: a deep stone slam with a crunch and falling rubble
    return stone_thud(r)


@sfx('pebble_golem/attack2')
def _(r):  # double slam
    m = Mix()
    m.add(stone_thud(r, 140, 60, 0.3, False), 0.0, 0.8)
    m.add(stone_thud(r, 160, 52, 0.5, True), 0.2, 1.0)
    return m.x


# ---------------------------------------------------------------------------------------------------
# 4i. HEX TOAD - croaks and ribbits; a tongue slurp to attack
# ---------------------------------------------------------------------------------------------------


def croak(r, dur, rate, f_res, tau=0.006, amp=None):
    """Pulse-train croak: each pulse rings a damped resonance (the vocal sac). rate/f_res may be [(sec, value), ...]."""
    n = N(dur)
    rt = curve(rate, dur, log=True, sm=0.01) if isinstance(rate, list) else bc(rate, n)
    fr = curve(f_res, dur, log=True, sm=0.01) if isinstance(f_res, list) else bc(f_res, n)
    env = curve(amp, dur, sm=0.004) if isinstance(amp, list) else swell(dur, 0.4, 1.0)
    ph = np.cumsum(rt * drift(n, r, 0.03, 20.0)) / SR
    idx = np.nonzero(np.diff(np.floor(ph)) > 0)[0]
    y = np.zeros(n + N(tau * 8))
    L = N(tau * 7)
    tt = np.arange(L) / SR
    for i in idx:
        y[i:i + L] += env[i] * np.exp(-tt / tau) * np.sin(TAU * fr[i] * tt)
    return y[:n]


@sfx('hex_toad/ambient1')
def _(r):  # "ri-bbit"
    m = Mix()
    m.add(croak(r, 0.17, [(0, 36), (0.17, 44)], [(0, 620), (0.17, 900)], 0.007, [(0, 0), (0.02, 1), (0.12, 0.9), (0.17, 0)]), 0.0)
    m.add(croak(r, 0.14, [(0, 50), (0.14, 58)], [(0, 1050), (0.14, 1350)], 0.005, [(0, 0), (0.015, 1), (0.1, 0.9), (0.14, 0)]), 0.21, 0.9)
    m.add(bubble(420, 0.4, 1.0), 0.37, 0.25)
    return m.x


@sfx('hex_toad/ambient2')
def _(r):  # a rolled "brrrup"
    m = Mix()
    m.add(croak(r, 0.36, [(0, 26), (0.36, 75)], [(0, 480), (0.36, 950)], 0.006, [(0, 0), (0.04, 0.8), (0.28, 1), (0.36, 0)]), 0.0)
    m.add(bubble(560, 0.4, 1.0), 0.38, 0.25)
    return m.x


@sfx('hex_toad/happy1')
def _(r):  # a bouncy double ribbit and a "bwip"
    m = Mix()
    for t0, k in [(0.0, 1.0), (0.3, 1.12)]:
        m.add(croak(r, 0.12, [(0, 40 * k), (0.12, 48 * k)], [(0, 760 * k), (0.12, 1100 * k)], 0.006, [(0, 0), (0.015, 1), (0.08, 0.9), (0.12, 0)]), t0)
        m.add(croak(r, 0.1, [(0, 55 * k), (0.1, 62 * k)], [(0, 1200 * k), (0.1, 1500 * k)], 0.005, [(0, 0), (0.012, 1), (0.07, 0.9), (0.1, 0)]), t0 + 0.14, 0.9)
    m.add(bubble(900, 0.5, 1.0), 0.62, 0.35)
    return m.x


@sfx('hex_toad/hurt1')
def _(r):  # a wet little "gwak!"
    m = Mix()
    m.add(croak(r, 0.2, 90, [(0, 1500), (0.2, 900)], 0.004, [(0, 0), (0.008, 1), (0.1, 0.8), (0.2, 0)]), 0.0)
    m.add(rl(burst(0.08, r, 0.02, (700, 3500)), -12), 0.0)
    return m.x


@sfx('hex_toad/death1')
def _(r):  # a croak that deflates, with a few popping bubbles
    m = Mix()
    m.add(croak(r, 0.95, [(0, 60), (0.95, 12)], [(0, 1200), (0.95, 300)], 0.008, [(0, 0), (0.03, 1), (0.6, 0.8), (0.95, 0)]), 0.0)
    for i, f in enumerate([900, 700, 520]):
        m.add(bubble(f, 0.3, 1.0), 0.8 + 0.07 * i, 0.4)
    return m.x


def slurp(r, steps=9, base=300.0, gap=0.016):
    m = Mix()
    t = 0.0
    for i in range(steps):
        m.add(bubble(base * (1.28 ** i) * r.uniform(0.95, 1.05), 0.3, 1.0), t, 0.5 + 0.05 * i)
        t += gap
    return m.x


@sfx('hex_toad/attack1')
def _(r):  # tongue slurp: a flick, wet rising bubbles, a smack and a gulp
    m = Mix()
    m.add(rl(whoosh(0.09, [(0, 400), (0.08, 2200)], r, q=2.0, env=[(0, 0), (0.015, 1), (0.09, 0)]), -3), 0.0)
    m.add(slurp(r), 0.09)
    m.add(rl(burst(0.05, r, 0.01, (600, 3500)), -8), 0.1)
    m.add(pl(thud(0.12, 420, 150, 0.03, 0.04), -4), 0.3)
    return m.x


@sfx('hex_toad/attack2')
def _(r):  # quicker, with a wet "pop"
    m = Mix()
    m.add(rl(whoosh(0.07, [(0, 600), (0.06, 2800)], r, q=2.0, env=[(0, 0), (0.012, 1), (0.07, 0)]), -3), 0.0)
    m.add(slurp(r, 7, 380, 0.014), 0.07)
    m.add(pl(thud(0.08, 700, 260, 0.01, 0.02), -5), 0.2)
    m.add(bubble(1500, 0.3, 1.0), 0.26, 0.5)
    return m.x


# ---------------------------------------------------------------------------------------------------
# 4j. MIMIC - wooden chest creaks, lid clacks, a playful growl; a lid-slam chomp to attack
# ---------------------------------------------------------------------------------------------------


def creak(r, dur, f0, slip=32.0, depth=0.8, formants=(430.0, 1100.0, 2400.0), jitter=0.05, breath=0.1):
    """Wooden creak: a rough, jittery voice with stick-slip pulsing through "box" formants."""
    n = N(dur)
    return vox(dur, f0, [bc(formants[0], n), bc(formants[1], n), bc(formants[2], n)], r, tilt=0.9, jitter=jitter,
               rough=(slip, depth), vibrato=None, breath=breath, qs=(5.0, 7.0, 10.0))


def knock(r, f=700.0, level=0.0, dur=0.12):
    return pl(modes(dur, [(f, 1.0, 0.025), (f * 1.87, 0.55, 0.014), (f * 3.05, 0.3, 0.008)], r, click=0.7, click_tau=0.002,
                    click_band=(1200, 5000)), level)


def box_slam(r, dur=0.4, f=190.0):
    return modes(dur, [(f, 1.0, 0.12), (f * 1.93, 0.7, 0.09), (f * 3.2, 0.5, 0.06), (f * 5.4, 0.3, 0.04)], r,
                 click=0.6, click_tau=0.003, click_band=(800, 4000))


@sfx('mimic/ambient1')
def _(r):  # a long wooden creak ending in a tiny lid tick
    m = Mix()
    m.add(creak(r, 0.5, [(0, 180), (0.2, 330), (0.5, 230)], 30, 0.8) * adsr(0.5, 0.04, 0.05, 0.9, 0.12), 0.0, 1.0)
    m.add(knock(r, 650, -6), 0.52)
    return m.x


@sfx('mimic/ambient2')
def _(r):  # a playful low growl and two little lid clacks
    m = Mix()
    m.add(syl(r, 0.4, [(0, 115), (0.15, 130), (0.4, 105)], [(0, 'o'), (0.15, 'a'), (0.4, 'o')], tilt=1.0, vibrato=None,
              rough=(38, 0.6), amp=[(0, 0), (0.04, 1), (0.28, 0.9), (0.4, 0)], breath=0.08), 0.0, 1.0)
    m.add(knock(r, 600, -4), 0.38)
    m.add(knock(r, 760, -6), 0.48)
    return m.x


@sfx('mimic/happy1')
def _(r):  # a giggle: rapid lid chatter with a squeaky creak
    m = Mix()
    for i in range(5):
        m.add(knock(r, 600 + 70 * i, -3 - 0.5 * i), 0.07 * i)
    m.add(creak(r, 0.3, [(0, 300), (0.15, 600), (0.3, 750)], 40, 0.6) * adsr(0.3, 0.03, 0.05, 0.9, 0.09), 0.1, 0.8)
    return m.x


@sfx('mimic/hurt1')
def _(r):  # a clack and a short creaky yelp
    m = Mix()
    m.add(knock(r, 850, -2), 0.0)
    m.add(creak(r, 0.22, [(0, 500), (0.08, 900), (0.22, 650)], 55, 0.5, jitter=0.03) * adsr(0.22, 0.01, 0.04, 0.9, 0.07), 0.01, 0.9)
    return m.x


@sfx('mimic/death1')
def _(r):  # a long sinking creak, then the lid drops shut
    m = Mix()
    m.add(creak(r, 0.85, [(0, 420), (0.4, 300), (0.85, 150)], 30, 0.8) * adsr(0.85, 0.05, 0.05, 0.9, 0.15), 0.0, 1.0)
    m.add(rl(box_slam(r, 0.45, 170), 0.0), 0.85, 1.0)
    m.add(knock(r, 700, -1), 0.85)
    m.add(rl(bp(white(N(0.25), r), 1500, 5000, 1) * pluck(0.25, 0.004, 0.06), -16), 0.86)
    return m.x


@sfx('mimic/attack1')
def _(r):  # chomp: a growl, then the lid slams
    m = Mix()
    m.add(syl(r, 0.12, [(0, 160), (0.1, 215)], [(0, 'o'), (0.12, 'a')], tilt=1.0, vibrato=None, rough=(55, 0.6),
              amp=[(0, 0), (0.01, 1), (0.08, 0.9), (0.12, 0)]), 0.0, 0.6)
    m.add(rl(box_slam(r, 0.35, 195), 0.0), 0.09, 1.0)
    m.add(pl(burst(0.03, r, 0.004, (1500, 7000)), -2), 0.09)
    m.add(knock(r, 800, -1), 0.09)
    return m.x


@sfx('mimic/attack2')
def _(r):  # double chomp
    m = Mix()
    for t0, f, gn in [(0.0, 200, 1.0), (0.16, 165, 1.15)]:
        m.add(rl(box_slam(r, 0.3, f), 0.0), t0, gn)
        m.add(pl(burst(0.03, r, 0.004, (1500, 7000)), -2), t0)
        m.add(knock(r, 800 - 90 * (t0 > 0), -1), t0)
    m.add(syl(r, 0.1, [(0, 190), (0.1, 150)], [(0, 'a'), (0.1, 'o')], tilt=1.0, vibrato=None, rough=(55, 0.6),
              amp=[(0, 0), (0.01, 1), (0.07, 0.9), (0.1, 0)]), 0.1, 0.5)
    return m.x


# ---------------------------------------------------------------------------------------------------
# 4k. TALENTS
# ---------------------------------------------------------------------------------------------------


def roast(r, scale=1.0):
    m = Mix()
    d = 0.6 * scale
    fl = lp(whoosh(d, [(0, 350), (0.3 * d, 1500), (0.65 * d, 2600), (d, 900)], r, q=0.8,
                   env=[(0, 0), (0.2 * d, 0.8), (0.42 * d, 1), (0.75 * d, 0.55), (d, 0)]), 4200)
    rum = lp(brown(N(d + 0.1), r), 200, 2) * swell(d + 0.1, 0.35, 1.1)
    m.add(rl(fl, 0))
    m.add(rl(rum, -4))
    ds = 0.8 * scale
    sz = bp(white(N(ds), r), 3500, 9000, 1) * flutter(N(ds), r, 140, 0.9) * curve([(0, 0), (0.1 * ds, 1), (0.55 * ds, 0.7), (ds, 0)], ds, sm=0.01)
    m.add(rl(sz, -9), 0.5 * d)
    m.add(rl(scatter(ds, poisson(ds, 30, r, 0.0, lambda x: 1 - x), r, freq=(1800, 5000), tau=(0.001, 0.004), amp=(0.2, 0.8)), -12), 0.5 * d)
    m.add(pl(bell(nt('E6'), 0.45, 0.8, 0.22, 'music'), -12), 0.5 * d + 0.7 * ds)
    return m.x


@sfx('talent/roast1')
def _(r):  # flame whoosh, then sizzling, finished with a tiny "done!" ding
    return roast(r, 1.0)


@sfx('talent/roast2')
def _(r):  # a quicker roast
    return roast(r, 0.7)


@sfx('talent/grow1')
def _(r):  # sparkly growing shimmer: rising bells, a climbing glow, rustling leaves
    m = Mix()
    for i, nm in enumerate(['C5', 'D5', 'E5', 'G5', 'A5', 'C6', 'E6']):
        m.add(bell(nt(nm), 0.55, 0.8, 0.2, 'music'), 0.075 * i, 0.55 + 0.06 * i)
    f = curve([(0, 300), (1.0, 1300)], 1.0, log=True)
    sh = (sine(f) + 0.5 * sine(f * 2.005) + 0.3 * sine(f * 3.01)) * swell(1.0, 0.75, 1.5)
    m.add(rl(sh, -14))
    rus = bp(white(N(0.9), r), 2500, 6500, 1) * flutter(N(0.9), r, 45, 0.7) * swell(0.9, 0.5, 1.2)
    m.add(rl(rus, -17))
    m.add(rl(sparkle(0.9, r, 18, 3000, 8000, True, 1.0), -16), 0.2)
    return reverb(m.x, 0.5, 0.25)


@sfx('talent/blessing1')
def _(r):  # watery magic swirl: a swirling band of water, harp-like plucks with a wobble, bubbles
    m = Mix()
    d = 1.1
    lfo = 1.0 + 0.45 * np.sin(TAU * 3.2 * T(d))
    fc = curve([(0, 500), (0.55, 1900), (d, 900)], d, log=True) * lfo
    m.add(rl(svf(white(N(d), r), fc, 4.0, 'bp') * swell(d, 0.45, 1.2), -3))
    for i, nm in enumerate(['G4', 'B4', 'D5', 'G5', 'B5', 'D6']):
        b = bell(nt(nm), 0.6, 0.6, 0.25, 'soft') * (0.7 + 0.3 * np.sin(TAU * 6.0 * T(0.6) + i))
        m.add(b, 0.09 * i, 0.6)
    for i in range(5):
        m.add(bubble(r.uniform(900, 2400), 0.3, 1.0), 0.15 + 0.15 * i + r.uniform(0, 0.05), 0.18)
    return reverb(m.x, 0.6, 0.3)


@sfx('talent/freeze1')
def _(r):  # ice crackle: a crack, a bell-shaped shower of glassy ticks, a frosty shimmer
    m = Mix()
    m.add(rl(burst(0.1, r, 0.02, (600, 3500)), -2), 0.0)
    m.add(pl(thud(0.12, 260, 120, 0.02, 0.04), -6), 0.0)
    for t0 in poisson(0.75, 60, r, 0.02, lambda x: 0.25 + np.sin(np.pi * min(1.0, x)) ** 0.7):
        f = r.uniform(2800, 7500)
        m.add(pl(modes(0.12, [(f, 1, 0.012), (f * 2.76, 0.4, 0.006), (f * 5.4, 0.2, 0.003)], r), -r.uniform(3, 15)), t0)
    t = T(0.7)
    sh = (sine(np.full(len(t), 4200.0)) + 0.7 * sine(np.full(len(t), 6130.0))) * (0.6 + 0.4 * np.sin(TAU * 5.5 * t)) * swell(0.7, 0.2, 1.3)
    m.add(rl(sh, -18), 0.1)
    return reverb(m.x, 0.4, 0.25)


@sfx('talent/warm1')
def _(r):  # soft fire "whoomph" and a warm glow
    m = Mix()
    m.add(rl(softclip(thud(0.5, 120, 58, 0.06, 0.16), 1.6), 0))
    m.add(rl(lp(white(N(0.7), r), 700, 2) * swell(0.7, 0.25, 1.2), -4))
    t = T(0.9)
    pad = (sine(np.full(len(t), 220.0)) + 0.6 * sine(np.full(len(t), 330.5)) + 0.4 * sine(np.full(len(t), 440.8))) * swell(0.9, 0.3, 1.2)
    m.add(rl(pad, -9), 0.05)
    m.add(rl(scatter(0.8, poisson(0.8, 18, r, 0.1, lambda x: 1 - x), r, freq=(1500, 4500), tau=(0.001, 0.003), amp=(0.2, 0.6)), -16), 0.1)
    return m.x


@sfx('talent/ping1')
def _(r):  # sonar ping with fading echoes
    d = 0.6
    t = T(d)
    f = 1400.0 * (1.0 + 0.2 * np.exp(-t / 0.012))
    ping = (sine(f) + 0.15 * sine(f * 2.0)) * pluck(d, 0.004, 0.16)
    return echo(ping, 0.27, 0.45, 3, 3000.0)


@sfx('talent/magnet1')
def _(r):  # magic whoosh-in: a sweep falling into the centre, a rising tone, a soft pluck
    m = Mix()
    d = 0.6
    m.add(rl(whoosh(d, [(0, 5500), (0.35, 1500), (d, 500)], r, q=1.3, env=[(0, 0), (0.3, 0.5), (0.5, 1), (0.58, 0.6), (d, 0)]), -2))
    m.add(rl(sine(curve([(0, 260), (d, 1500)], d, log=True)) * swell(d, 0.8, 1.3), -9))
    m.add(rl(sparkle(0.5, r, 9, 7000, 2500, True, 1.0), -17))
    m.add(pl(bell(nt('G5'), 0.3, 0.6, 0.1, 'mallet'), -6), d - 0.02)
    m.add(pl(thud(0.1, 450, 160, 0.015, 0.03), -9), d - 0.02)
    return reverb(m.x, 0.35, 0.2)


def sniff(r, count, gap, base=1.0):
    m = Mix()
    for i in range(count):
        d = 0.09 - 0.012 * i
        n = N(d)
        y = bp(white(n, r), 1200 * base, 4200 * base, 1) + 0.8 * svf(white(n, r), 2300 * base * (1 + 0.1 * i), 6.0, 'bp')
        m.add(rl(y * curve([(0, 0), (0.6 * d, 1), (d, 0)], d, sm=0.004), 0), i * gap, 1.0 - 0.18 * i)
    return m.x


@sfx('talent/sniff1')
def _(r):  # sniff-sniff-snf
    return sniff(r, 3, 0.15)


@sfx('talent/sniff2')
def _(r):  # sniff-sniff
    return sniff(r, 2, 0.17, 1.1)


@sfx('talent/brew1')
def _(r):  # a cauldron bubbling faster and faster, then "pop!" and a sparkle
    m = Mix()
    d = 0.9
    for t0 in poisson(d, 16, r, 0.0, lambda x: 0.4 + 3.0 * x):
        m.add(bubble(r.uniform(350, 1800), 0.25, 1.0), t0, r.uniform(0.3, 1.0))
    m.add(rl(lp(brown(N(d), r), 300, 2) * swell(d, 0.6, 1.0), -14))
    m.add(pl(thud(0.1, 380, 140, 0.015, 0.03), -3), d)
    m.add(bubble(260, 0.4, 1.0), d, 1.0)
    m.add(rl(sparkle(0.35, r, 8, 3000, 7500, True, 1.0), -14), d)
    m.add(pl(bell(nt('A6'), 0.3, 0.7, 0.12, 'music'), -10), d + 0.04)
    return m.x


@sfx('talent/treasure1')
def _(r):  # a little "ehm-hm" cough, then coins clinking
    m = Mix()
    for t0, f in [(0.0, 230), (0.17, 200)]:
        m.add(rl(burst(0.05, r, 0.012, (800, 3200)), -6), t0)
        m.add(syl(r, 0.11, [(0, f), (0.11, f * 0.8)], [(0, 'ae'), (0.11, 'uh')], breath=0.7, tilt=1.2, vibrato=None, rough=(70, 0.5),
                  amp=[(0, 0), (0.01, 1), (0.07, 0.8), (0.11, 0)]), t0 + 0.02, 0.6)
    for i, f in enumerate([1900, 2200, 2600]):
        m.add(pl(modes(0.32, [(f, 1.0, 0.09), (f * 2.32, 0.6, 0.05), (f * 3.7, 0.35, 0.03)], r, click=0.3), -2 * i), 0.5 + 0.09 * i)
    return reverb(m.x, 0.25, 0.2)


# ---------------------------------------------------------------------------------------------------
# 4l. SHARED PET SOUNDS
# ---------------------------------------------------------------------------------------------------


def soft_note(r, dur, f_pts, vibrato=(5.5, 22, 0.1), amp=None, h=(1.0, 0.12, 0.03)):
    """Round, clearly tonal petting note (sine + a trace of overtones, no noise)."""
    return whistle(dur, f_pts, r, h=h, vibrato=vibrato, amp=amp, a=0.015, rel=0.06)


@sfx('pet/petting1')
def _(r):  # "mm-hee-ip": a happy little trill that rolls up into a soft chirp, with a tiny sparkle
    m = Mix()
    m.add(soft_note(r, 0.55, [(0, 640), (0.1, 760), (0.3, 860), (0.55, 760)], vibrato=(11, 55, 0.12),
                    amp=[(0, 0), (0.06, 0.85), (0.38, 1), (0.55, 0)]), 0.0, 1.0)
    m.add(soft_note(r, 0.2, [(0, 1120), (0.08, 1500), (0.2, 1380)], vibrato=(7, 20, 0.0),
                    amp=[(0, 0), (0.02, 1), (0.13, 0.8), (0.2, 0)]), 0.36, 0.5)
    m.add(rl(sparkle(0.3, r, 4, 3000, 5200, True, 1.0), -22), 0.5)
    return m.x


@sfx('pet/petting2')
def _(r):  # "coo-coo~": two soft, bell-round notes and a gentle sparkle
    m = Mix()
    m.add(soft_note(r, 0.3, [(0, 560), (0.1, 700), (0.3, 660)], vibrato=(5.5, 18, 0.08),
                    amp=[(0, 0), (0.05, 1), (0.2, 0.85), (0.3, 0)]), 0.0, 1.0)
    m.add(soft_note(r, 0.42, [(0, 640), (0.12, 820), (0.42, 700)], vibrato=(6, 22, 0.1),
                    amp=[(0, 0), (0.06, 1), (0.28, 0.85), (0.42, 0)]), 0.33, 1.0)
    m.add(pl(bell(1750, 0.3, 0.6, 0.1, 'soft'), -16), 0.52)
    m.add(pl(bell(2300, 0.3, 0.6, 0.1, 'soft'), -19), 0.62)
    return m.x


def chew(r, f=1.0, level=0.0):
    m = Mix()
    nz = bp(white(N(0.09), r), 700 * f, 3600 * f, 1) * curve([(0, 0), (0.012, 1), (0.04, 0.5), (0.09, 0)], 0.09, sm=0.002)
    m.add(rl(nz, 0))
    m.add(rl(scatter(0.08, [0.0, 0.012, 0.03, 0.05], r, freq=(1500, 5000), tau=(0.0008, 0.003), amp=(0.3, 0.8)), -6))
    m.add(pl(thud(0.07, 240, 120, 0.015, 0.03), -8))
    return m.x * g(level)


@sfx('pet/eat1')
def _(r):  # nom nom nom
    m = Mix()
    for i, t0 in enumerate([0.0, 0.17, 0.32]):
        m.add(chew(r, 1.0 - 0.06 * i, -2.0 * i), t0)
    return m.x


@sfx('pet/eat2')
def _(r):  # quick chewing and a gulp
    m = Mix()
    for i, t0 in enumerate([0.0, 0.11, 0.22, 0.33]):
        m.add(chew(r, 1.1, -1.5 * i), t0)
    m.add(pl(thud(0.14, 380, 130, 0.04, 0.05), -4), 0.5)
    return m.x


@sfx('pet/yawn1')
def _(r):  # a big breathy "aaah-hm" with a little squeak on the way down
    m = Mix()
    m.add(syl(r, 1.0, [(0, 330), (0.25, 440), (0.65, 320), (1.0, 230)], [(0, 'uh'), (0.25, 'a'), (0.65, 'o'), (1.0, 'm')], breath=0.5, tilt=1.4,
              vibrato=(5.0, 20, 0.2), amp=[(0, 0), (0.18, 1), (0.6, 0.85), (1.0, 0)]), 0.0, 1.0)
    m.add(syl(r, 0.16, [(0, 900), (0.16, 1150)], [(0, 'i'), (0.16, 'e')], breath=0.2, vibrato=(7, 25, 0.0),
              amp=[(0, 0), (0.03, 1), (0.1, 0.7), (0.16, 0)]), 0.62, 0.35)
    return m.x


@sfx('pet/yawn2')
def _(r):  # a shorter yawn that ends in a cute rising squeak
    m = Mix()
    m.add(syl(r, 0.7, [(0, 360), (0.2, 470), (0.5, 340)], [(0, 'uh'), (0.2, 'a'), (0.7, 'o')], breath=0.5, tilt=1.4, vibrato=(5.0, 20, 0.2),
              amp=[(0, 0), (0.12, 1), (0.45, 0.85), (0.7, 0)]), 0.0, 1.0)
    m.add(syl(r, 0.2, [(0, 800), (0.2, 1350)], [(0, 'i'), (0.2, 'i')], breath=0.15, vibrato=(7, 25, 0.0),
              amp=[(0, 0), (0.03, 1), (0.14, 0.7), (0.2, 0)]), 0.6, 0.4)
    return m.x


def snore(r, squeak=False):
    m = Mix()
    m.add(syl(r, 0.45, [(0, 70), (0.3, 105), (0.45, 120)], [(0, 'uh'), (0.45, 'ae')], tilt=1.2, vibrato=None, nasal=0.4, rough=(36, 0.85),
              breath=0.35, amp=[(0, 0), (0.25, 0.8), (0.4, 1), (0.45, 0)]), 0.0, 0.9)
    m.add(rl(lp(white(N(0.5), r), 1800, 2) * swell(0.5, 0.25, 1.2), -6), 0.5)
    m.add(rl(sine(curve([(0, 880), (0.5, 640)], 0.5, log=True)) * swell(0.5, 0.3, 1.3), -24), 0.5)
    if squeak:
        m.add(pl(whistle(0.05, [(0, 1400), (0.05, 1700)], r), -16), 1.05)
    return m.x


@sfx('pet/snore1')
def _(r):  # a tiny "hnnk ... fwooo"
    return snore(r)


@sfx('pet/snore2')
def _(r):  # the same with a little whistle at the end
    return snore(r, True)


def splash(r, big=1.0):
    m = Mix()
    m.add(rl(whoosh(0.3, [(0, 3200), (0.08, 1800), (0.3, 500)], r, q=0.7, env=[(0, 0), (0.008, 1), (0.08, 0.7), (0.3, 0)]), 0.0))
    m.add(bubble(300 * big, 0.5, 1.0), 0.03, 2.0)
    for i in range(8):
        m.add(bubble(r.uniform(900, 2800), 0.25, 1.0), 0.06 + 0.04 * i + r.uniform(0, 0.03), r.uniform(0.5, 1.2))
    m.add(rl(sparkle(0.3, r, 6, 3500, 8000, False, 1.0), -18), 0.1)
    return m.x


@sfx('pet/splash1')
def _(r):
    return splash(r, 1.0)


@sfx('pet/splash2')
def _(r):
    return splash(r, 1.4)


def shake(r, rate0=22.0, dur=0.7):
    n = N(dur)
    rate = curve([(0, rate0), (dur, rate0 * 0.6)], dur)
    am = 0.35 + 0.65 * (0.5 + 0.5 * np.cos(phase(rate))) ** 2
    y = bp(white(n, r), 900, 5000, 1) * am * curve([(0, 0), (0.04, 1), (0.45 * dur, 0.8), (dur, 0)], dur, sm=0.01)
    low = lp(white(n, r), 450, 2) * am * swell(dur, 0.3, 1.0)
    m = Mix()
    m.add(rl(y, 0))
    m.add(rl(low, -8))
    m.add(rl(scatter(dur, poisson(dur, 45, r, 0.05, lambda x: 1 - 0.7 * x), r, freq=(3000, 7000), tau=(0.0008, 0.003), amp=(0.2, 0.7)), -14))
    return m.x


@sfx('pet/shake1')
def _(r):  # "brrrrr" - shaking off water
    return shake(r, 22.0, 0.7)


@sfx('pet/shake2')
def _(r):  # a quicker shake
    return shake(r, 28.0, 0.5)


@sfx('pet/tame1')
def _(r):  # magical rising chime arpeggio that blooms into a chord
    m = Mix()
    for i, nm in enumerate(['C5', 'E5', 'G5', 'C6', 'E6', 'G6']):
        m.add(bell(nt(nm), 0.8, 1.0, 0.3, 'glock'), 0.085 * i, 0.55 + 0.07 * i)
    for nm in ['C6', 'E6', 'G6']:
        m.add(bell(nt(nm), 0.8, 0.8, 0.45, 'glock'), 0.55, 0.35)
    m.add(rl(sparkle(0.9, r, 16, 3000, 8500, True, 1.0), -15), 0.15)
    return reverb(m.x, 0.6, 0.3)


@sfx('pet/tame2')
def _(r):  # a harp-like pentatonic run with a sparkling top
    m = Mix()
    for i, nm in enumerate(['G5', 'A5', 'C6', 'D6', 'G6', 'A6']):
        m.add(bell(nt(nm), 0.8, 0.9, 0.32, 'music'), 0.075 * i, 0.6 + 0.06 * i)
    for nm in ['G6', 'D7']:
        m.add(bell(nt(nm), 0.8, 0.8, 0.45, 'glock'), 0.5, 0.3)
    m.add(rl(sparkle(0.9, r, 16, 3500, 9000, True, 1.0), -15), 0.2)
    return reverb(m.x, 0.6, 0.3)


@sfx('pet/faint1')
def _(r):  # gentle sad descending tones
    m = Mix()
    for i, (nm, t0) in enumerate([('G5', 0.0), ('E5', 0.26), ('D5', 0.52)]):
        b = bell(nt(nm), 0.7, 0.5, 0.3, 'soft') * (0.8 + 0.2 * np.sin(TAU * 5.0 * T(0.7)))
        m.add(b, t0, 0.9 - 0.1 * i)
    f = curve([(0, nt('C5')), (0.2, nt('B4')), (0.6, nt('A4'))], 0.6, log=True)
    m.add((sine(f) + 0.2 * sine(f * 2.0)) * pluck(0.6, 0.01, 0.25), 0.78, 0.8)
    return reverb(m.x, 0.35, 0.2)


@sfx('pet/faint2')
def _(r):  # a slow music-box version
    m = Mix()
    for i, nm in enumerate(['A5', 'F5', 'D5', 'A4']):
        m.add(bell(nt(nm), 0.8, 0.8, 0.28, 'music'), 0.3 * i, 0.9 - 0.08 * i)
    return reverb(m.x, 0.4, 0.2)


def egg_crack(r, f=3200.0, level=0.0):
    m = Mix()
    m.add(pl(modes(0.06, [(f, 1.0, 0.004), (f * 1.62, 0.6, 0.003), (f * 2.4, 0.3, 0.002)], r, click=0.6, click_band=(2000, 9000)), level))
    m.add(rl(scatter(0.1, [0.01, 0.025, 0.045], r, freq=(2500, 6000), tau=(0.0006, 0.002)), level - 12))
    return m.x


@sfx('pet/wake1')
def _(r):  # egg cracks, the shell pops open, a sparkle chime
    m = Mix()
    for t0, f, lv in [(0.0, 3000, -3), (0.15, 3400, -2), (0.23, 2700, -3), (0.4, 3800, -1)]:
        m.add(egg_crack(r, f, lv), t0)
    m.add(rl(burst(0.12, r, 0.03, (500, 4000)), -3), 0.55)
    m.add(pl(thud(0.1, 480, 170, 0.015, 0.03), -4), 0.55)
    for i, nm in enumerate(['G5', 'C6', 'E6']):
        m.add(bell(nt(nm), 0.7, 1.0, 0.3, 'glock'), 0.58 + 0.08 * i, 0.6)
    m.add(rl(sparkle(0.7, r, 14, 3000, 8500, True, 1.0), -15), 0.6)
    return reverb(m.x, 0.5, 0.28)


@sfx('pet/wake2')
def _(r):  # a faster crack-crack-pop and a higher chime
    m = Mix()
    for t0, f, lv in [(0.0, 3300, -2), (0.1, 2900, -3), (0.17, 3600, -2)]:
        m.add(egg_crack(r, f, lv), t0)
    m.add(rl(burst(0.12, r, 0.03, (500, 4000)), -3), 0.34)
    m.add(pl(thud(0.1, 520, 180, 0.015, 0.03), -4), 0.34)
    for i, nm in enumerate(['A5', 'D6', 'F#6', 'A6']):
        m.add(bell(nt(nm), 0.7, 1.0, 0.3, 'glock'), 0.38 + 0.07 * i, 0.6)
    m.add(rl(sparkle(0.7, r, 14, 3500, 9000, True, 1.0), -15), 0.4)
    return reverb(m.x, 0.5, 0.28)


def toy_horn(f, dur, r=None, vibrato=None):
    n = N(dur)
    fa = bc(f, n)
    if vibrato:
        fa = fa * vib(n, r, vibrato[0], vibrato[1], vibrato[2])
    ph = phase(fa)
    y = sum(np.sin(k * ph) / k ** 1.1 for k in range(1, 14) if k * float(np.max(fa)) < 9000)
    return lp(y, 3800, 2) * adsr(dur, 0.012, 0.04, 0.8, 0.05)


@sfx('pet/celebrate1')
def _(r):  # "ta-ta-ta-TAAA!" - a happy little fanfare with glitter
    m = Mix()
    for t0, nm in [(0.0, 'G4'), (0.13, 'C5'), (0.26, 'E5')]:
        m.add(rl(toy_horn(nt(nm), 0.11), 0.0), t0, 0.8)
    m.add(rl(toy_horn(nt('G5'), 0.5, r, (6.0, 25, 0.15)), 0.0), 0.4, 1.0)
    for i, nm in enumerate(['C6', 'E6', 'G6']):
        m.add(bell(nt(nm), 0.6, 0.9, 0.25, 'glock'), 0.42 + 0.06 * i, 0.5)
    m.add(rl(sparkle(0.6, r, 12, 3000, 8500, True, 1.0), -15), 0.45)
    return reverb(m.x, 0.35, 0.2)


@sfx('pet/celebrate2')
def _(r):  # a bouncy rising arpeggio and a trill
    m = Mix()
    for i, nm in enumerate(['C5', 'E5', 'G5', 'C6']):
        m.add(rl(toy_horn(nt(nm), 0.1), 0.0), 0.11 * i, 0.8)
    for i in range(6):
        m.add(rl(toy_horn(nt('E6' if i % 2 else 'D6'), 0.07), 0.0), 0.5 + 0.07 * i, 0.55)
    m.add(rl(toy_horn(nt('G6'), 0.3, r, (6.5, 25, 0.1)), 0.0), 0.92, 0.7)
    m.add(rl(sparkle(0.7, r, 12, 3500, 9000, True, 1.0), -15), 0.55)
    return reverb(m.x, 0.3, 0.2)


@sfx('pet/scared1')
def _(r):  # two trembling whimpers and a sniffle
    m = Mix()
    m.add(syl(r, 0.32, [(0, 980), (0.1, 900), (0.32, 640)], [(0, 'i'), (0.32, 'u')], breath=0.2, vibrato=(9, 80, 0.05),
              amp=[(0, 0), (0.03, 1), (0.22, 0.8), (0.32, 0)]), 0.0)
    m.add(syl(r, 0.28, [(0, 880), (0.28, 560)], [(0, 'i'), (0.28, 'u')], breath=0.25, vibrato=(9, 80, 0.05),
              amp=[(0, 0), (0.03, 1), (0.2, 0.7), (0.28, 0)]), 0.4, 0.7)
    m.add(rl(burst(0.07, r, 0.02, (2000, 6000)), -16), 0.72)
    return m.x


@sfx('pet/scared2')
def _(r):  # three quick shivery whimpers
    m = Mix()
    for i, (t0, f) in enumerate([(0.0, 900), (0.2, 820), (0.4, 740)]):
        m.add(syl(r, 0.15, [(0, f), (0.15, f * 0.7)], [(0, 'i'), (0.15, 'u')], breath=0.2, vibrato=(10, 70, 0.0),
                  amp=[(0, 0), (0.02, 1), (0.1, 0.7), (0.15, 0)]), t0, 1.0 - 0.15 * i)
    return m.x


@sfx('pet/feed_owner1')
def _(r):  # "pop!" and a bright two-note chime
    m = Mix()
    m.add(pl(thud(0.08, 420, 120, 0.012, 0.02), 0.0))
    m.add(pl(burst(0.02, r, 0.003, (1500, 6000)), -6))
    m.add(bell(nt('G6'), 0.5, 0.9, 0.2, 'glock'), 0.1, 0.7)
    m.add(bell(nt('C7'), 0.5, 0.9, 0.22, 'glock'), 0.19, 0.6)
    m.add(rl(sparkle(0.4, r, 7, 4000, 9000, True, 1.0), -17), 0.15)
    return reverb(m.x, 0.3, 0.2)


@sfx('pet/feed_owner2')
def _(r):  # a softer pop and a rising chime
    m = Mix()
    m.add(pl(thud(0.08, 360, 110, 0.012, 0.02), 0.0))
    m.add(pl(burst(0.02, r, 0.003, (1500, 6000)), -7))
    m.add(bell(nt('E6'), 0.5, 0.9, 0.2, 'glock'), 0.1, 0.7)
    m.add(bell(nt('A6'), 0.5, 0.9, 0.22, 'glock'), 0.19, 0.6)
    m.add(rl(sparkle(0.4, r, 7, 4000, 9000, True, 1.0), -17), 0.15)
    return reverb(m.x, 0.3, 0.2)


# ---------------------------------------------------------------------------------------------------
# 4m. PAGER (handheld virtual pet beeps), TOYS, BLOCKS, ITEMS
# ---------------------------------------------------------------------------------------------------


def piezo(f, dur, edge=0.0015):
    """Piezo-buzzer square wave (band-limited), with a tiny soft edge so it never clicks."""
    t = T(dur)
    ph = TAU * f * t
    y = np.zeros(len(t))
    for k in range(1, 40, 2):
        if k * f > 8000:
            break
        y += np.sin(k * ph) / k
    return ramp_out(ramp_in(y * 0.8, edge), edge)


def beeps(seq):
    m = Mix()
    t = 0.0
    for f, d, gap in seq:
        m.add(piezo(f, d), t)
        t += d + gap
    return m.x


@sfx('pager/beep1', shelf=-6.0)
def _(r):  # the classic double beep, twice
    return beeps([(2400, 0.09, 0.07), (2400, 0.09, 0.22), (2400, 0.09, 0.07), (2400, 0.09, 0.0)])


@sfx('pager/beep2', shelf=-6.0)
def _(r):  # "bee-bee-beep": a rising call for attention
    return beeps([(2000, 0.07, 0.04), (2600, 0.07, 0.04), (3200, 0.12, 0.0)])


@sfx('pager/beep3', shelf=-6.0)
def _(r):  # a lower, longer "bip-bip"
    return beeps([(1700, 0.12, 0.08), (1700, 0.12, 0.0)])


def blip(f0, f1, dur, edge=0.002):
    p = phase(curve([(0, f0), (dur, f1)], dur, log=True))
    y = sum(np.sin(k * p) / k for k in (1, 3, 5, 7))
    return ramp_out(ramp_in(y * 0.8, edge), edge)


@sfx('pager/open1', shelf=-6.0)
def _(r):  # "bleep-bloop"
    m = Mix()
    m.add(blip(1500, 2100, 0.06), 0.0)
    m.add(blip(1100, 750, 0.09), 0.08)
    return m.x


@sfx('pager/open2', shelf=-6.0)
def _(r):  # "bloop-bleep"
    m = Mix()
    m.add(blip(900, 1300, 0.07), 0.0)
    m.add(blip(2000, 2700, 0.08), 0.09)
    return m.x


@sfx('toy/squeak1')
def _(r):  # a rubbery squeak
    n = N(0.22)
    return vox(0.22, [(0, 600), (0.04, 1150), (0.11, 1400), (0.22, 1200)], [bc(1500, n), bc(2900, n), bc(4200, n)], r, tilt=1.4,
               vibrato=(26, 28, 0.0), jitter=0.006, breath=0.12, qs=(5.0, 6.0, 7.0), amp=[(0, 0), (0.008, 1), (0.15, 0.85), (0.22, 0)])


@sfx('toy/squeak2')
def _(r):  # a lower double squeak, "ee-eek"
    n = N(0.4)
    m = Mix()
    for t0, f in [(0.0, 520), (0.19, 640)]:
        m.add(vox(0.2, [(0, f), (0.05, f * 1.9), (0.14, f * 2.2), (0.2, f * 1.9)], [bc(1400, N(0.2)), bc(2700, N(0.2)), bc(4000, N(0.2))], r,
                  tilt=1.4, vibrato=(24, 25, 0.0), jitter=0.006, breath=0.12, qs=(5.0, 6.0, 7.0), amp=[(0, 0), (0.01, 1), (0.13, 0.85), (0.2, 0)]), t0)
    return m.x


def bip(f, dur):
    """A soft, short electronic "bip": a round sine with a hint of 2nd harmonic and a quick fade."""
    t = T(dur)
    y = np.sin(TAU * f * t) + 0.22 * np.sin(TAU * 2 * f * t)
    return y * tone_env(dur, 0.004, 0.025)


@sfx('toy/laser1', peak=-5.0)
def _(r):  # a soft double "bip-bip" (about a tenth of a second each)
    m = Mix()
    m.add(bip(1900, 0.055), 0.0, 0.9)
    m.add(bip(2500, 0.065), 0.075, 1.0)
    return m.x


@sfx('toy/laser2', peak=-5.0)
def _(r):  # one short, slightly lower "bip"
    return bip(1700, 0.1)


@sfx('toy/feather1')
def _(r):  # soft swish: up and over
    d = 0.26
    n = N(d)
    y = svf(white(n, r), curve([(0, 2500), (0.12, 5500), (d, 3000)], d, log=True), 1.0, 'bp') * flutter(n, r, 38, 0.35) * swell(d, 0.45, 1.3)
    m = Mix()
    m.add(rl(y, 0))
    m.add(rl(lp(white(n, r), 700, 2) * swell(d, 0.4, 1.4), -14))
    return m.x


@sfx('toy/feather2')
def _(r):  # swish back the other way
    d = 0.22
    n = N(d)
    y = svf(white(n, r), curve([(0, 4800), (0.1, 2400), (d, 3400)], d, log=True), 1.0, 'bp') * flutter(n, r, 42, 0.35) * swell(d, 0.4, 1.3)
    m = Mix()
    m.add(rl(y, 0))
    m.add(rl(lp(white(n, r), 700, 2) * swell(d, 0.4, 1.4), -14))
    return m.x


def boing(base, dur=0.55, wobble=0.55):
    t = T(dur)
    rate = 16.0 * np.exp(-t / 0.35) + 5.0
    f = base * (1.0 + wobble * np.exp(-t / 0.18) * np.sin(phase(rate))) * (1.0 + 0.5 * np.exp(-t / 0.05))
    y = sine(f) + 0.3 * sine(f * 2.0) + 0.12 * sine(f * 3.0)
    return y * pluck(dur, 0.003, 0.22)


@sfx('block/bounce1')
def _(r):  # cartoony "boing-oing-oing"
    return boing(330.0)


@sfx('block/bounce2')
def _(r):  # a smaller, higher boing
    return boing(480.0, 0.38, 0.45)


@sfx('block/wheel1', loop=True)
def _(r):  # wooden wheel spinning: soft whirr, creak and spoke ticks; every part repeats per loop so it loops seamlessly
    dur = 1.5
    n = N(dur)
    t = T(dur)
    whirr = lp(white(n, r), 900, 2, circular=True) * (0.7 + 0.3 * np.cos(TAU * 16.0 * t / dur))
    cr = bp(white(n, r), 330, 520, 2, circular=True) * (0.5 + 0.5 * np.cos(TAU * t / dur + 1.0)) ** 2
    cr2 = bp(white(n, r), 700, 1100, 2, circular=True) * (0.5 + 0.5 * np.cos(TAU * 2 * t / dur + 2.0)) ** 3
    ticks = np.zeros(n)
    for i in range(16):
        gr = modes(0.06, [(520 + 40 * (i % 2), 1.0, 0.012), (1150, 0.4, 0.007)], r, click=0.4) * r.uniform(0.75, 1.0)
        idx = (S(i * dur / 16 + 0.01) + np.arange(len(gr))) % n
        ticks[idx] += gr
    return rl(whirr, -14) + rl(cr, -16) + rl(cr2, -22) + pl(ticks, -4)


def kibble(r, d=1.0, rate=110.0):
    m = Mix()
    shape = lambda x: min(1.0, x / 0.12) * (1.0 if x < 0.7 else max(0.1, (1 - x) / 0.3))
    for t0 in poisson(d, rate, r, 0.0, shape):
        if r.random() < 0.7:
            gr = modes(0.04, [(r.uniform(1800, 5200), 1.0, r.uniform(0.003, 0.009))], r, click=0.5)
        else:
            gr = modes(0.12, [(r.uniform(900, 1500), 1.0, 0.03), (r.uniform(2400, 3200), 0.4, 0.02)], r)
        m.add(gr, t0, r.uniform(0.2, 0.9))
    n = N(d)
    bed = bp(white(n, r), 1500, 5000, 1) * flutter(n, r, 60, 0.6) * curve([(0, 0), (0.1, 1), (0.7 * d, 1), (d, 0)], d, sm=0.02)
    m.add(rl(bed, -16))
    for t0, f in [(d + 0.02, 1250), (d + 0.1, 1400), (d + 0.15, 1100)]:
        m.add(modes(0.12, [(f, 1.0, 0.04), (f * 2.5, 0.4, 0.02)], r), t0, 0.4)
    return m.x


@sfx('block/bowl_fill1')
def _(r):  # kibble pouring into a bowl: a rattling shower and a few settling clinks
    return kibble(r, 1.0, 110.0)


@sfx('block/bowl_fill2')
def _(r):  # a shorter pour
    return kibble(r, 0.7, 90.0)


def brush(r, strokes):
    m = Mix()
    t = 0.0
    for d in strokes:
        n = N(d)
        y = hp(white(n, r), 2500, 2) * flutter(n, r, 110, 0.7) * swell(d, 0.5, 1.2)
        y = y + 0.5 * bp(white(n, r), 600, 1600, 1) * swell(d, 0.5, 1.2) * flutter(n, r, 30, 0.5)
        m.add(rl(y, 0), t)
        t += d + 0.04
    return m.x


@sfx('item/brush1')
def _(r):  # scritch-scritch
    return brush(r, [0.2, 0.2])


@sfx('item/brush2')
def _(r):  # three short strokes
    return brush(r, [0.13, 0.13, 0.13])


@sfx('backpack/equip1')
def _(r):  # leather rustle, a strap creak, buckle click-click, a soft settle
    m = Mix()
    m.add(rl(bp(white(N(0.2), r), 300, 2500, 1) * flutter(N(0.2), r, 40, 0.6) * swell(0.2, 0.4, 1.2), -2), 0.0)
    m.add(creak(r, 0.1, [(0, 260), (0.1, 330)], 45, 0.6) * adsr(0.1, 0.02, 0.02, 0.9, 0.04), 0.05, 0.35)
    for t0, f in [(0.22, 3300), (0.28, 4600)]:
        m.add(pl(modes(0.05, [(f, 1.0, 0.006), (f * 1.66, 0.6, 0.004)], r, click=0.3), -3), t0)
    m.add(rl(thud(0.15, 170, 90, 0.03, 0.05), -4), 0.3)
    return m.x


@sfx('backpack/equip2')
def _(r):  # a quicker strap-and-clip
    m = Mix()
    m.add(rl(bp(white(N(0.14), r), 300, 2500, 1) * flutter(N(0.14), r, 40, 0.6) * swell(0.14, 0.4, 1.2), -2), 0.0)
    for t0, f in [(0.14, 3000), (0.19, 4200)]:
        m.add(pl(modes(0.05, [(f, 1.0, 0.006), (f * 1.66, 0.6, 0.004)], r, click=0.3), -3), t0)
    m.add(rl(thud(0.12, 190, 100, 0.03, 0.05), -4), 0.21)
    return m.x


def spill(r, items=6):
    m = Mix()
    m.add(rl(lp(white(N(0.14), r), 700, 2) * swell(0.14, 0.4, 1.2), -4), 0.0)
    for i in range(items):
        kind = r.integers(0, 4)
        t = 0.08 + i * 0.09 + r.uniform(0, 0.04)
        gap = r.uniform(0.09, 0.16)
        a = r.uniform(0.7, 1.0)
        f = r.uniform(400, 900) if kind == 0 else r.uniform(1000, 2400) if kind == 1 else r.uniform(2000, 3200)
        for _ in range(r.integers(2, 5)):
            if kind == 0:
                gr = modes(0.08, [(f, 1, 0.02), (f * 1.9, 0.5, 0.01)], r, click=0.5)
            elif kind == 1:
                gr = modes(0.05, [(f, 1, 0.008), (f * 2.3, 0.4, 0.004)], r, click=0.5)
            elif kind == 2:
                gr = modes(0.2, [(f, 1, 0.06), (f * 2.32, 0.5, 0.04), (f * 3.7, 0.3, 0.02)], r, click=0.2)
            else:
                gr = thud(0.08, 260, 110, 0.02, 0.03)
            m.add(gr, t, a)
            t += gap
            gap *= 0.62
            a *= 0.66
    return m.x


@sfx('backpack/spill1')
def _(r):  # the bag opens and its contents tumble out
    return spill(r, 6)


@sfx('backpack/spill2')
def _(r):  # another tumble, a few more things
    return spill(r, 7)


# ===== END OF RECIPES =====


# =====================================================================================================
# 5. COMMAND LINE
# =====================================================================================================


def select(patterns):
    names = sorted(SOUNDS)
    if not patterns:
        return names
    return [n for n in names if any(fnmatch.fnmatch(n, p) for p in patterns)]


def main():
    ap = argparse.ArgumentParser(description='Synthesize the Tamagotchi mod sounds.')
    ap.add_argument('--only', nargs='*', help='fnmatch patterns on group/name (default: everything)')
    ap.add_argument('--out', default=SOUND_DIR, help='output directory (default: the mod resources)')
    ap.add_argument('--sheet', default=SHEET_PNG, help='path of the spectrogram contact sheet')
    ap.add_argument('--no-sheet', action='store_true')
    ap.add_argument('--list', action='store_true', help='list sound names and exit')
    ap.add_argument('--stats', help='write per-sound stats (duration, peak, loudness, size) to this JSON file')
    ap.add_argument('--clean', action='store_true', help='delete .ogg files that have no recipe any more')
    ap.add_argument('-j', '--jobs', type=int, default=os.cpu_count() or 1)
    a = ap.parse_args()

    names = select(a.only)
    if a.list:
        print('\n'.join(names))
        return 0
    if not names:
        print('nothing matches', a.only)
        return 1

    jobs = [(n, a.out) for n in names]
    if a.jobs > 1 and len(jobs) > 1:
        with concurrent.futures.ProcessPoolExecutor(max_workers=a.jobs) as ex:
            stats = list(ex.map(build_one, jobs, chunksize=2))
    else:
        stats = [build_one(j) for j in jobs]

    total = sum(s['bytes'] for s in stats)
    for s in stats:
        print('%-30s %5.2fs  peak %5.1f dB  loud %6.1f dB  %6d B' % (s['name'], s['dur'], s['peak_db'], s['loud_db'], s['bytes']))
    print('%d sounds, %.1f KB total' % (len(stats), total / 1024.0))

    problems = [s for s in stats if s['peak_db'] > -1.0 or s['lead'] > 0.02 or s['tail'] > 0.02]
    for s in problems:
        print('CHECK', s['name'], 'peak %.1f lead %.3f tail %.3f' % (s['peak_db'], s['lead'], s['tail']))

    if a.stats:
        with open(a.stats, 'w') as fh:
            json.dump({s['name']: s for s in stats}, fh, indent=1, sort_keys=True)

    if a.clean:
        known = set(SOUNDS)
        for root, _, fs in os.walk(a.out):
            for f in fs:
                if f.endswith('.ogg'):
                    rel = os.path.relpath(os.path.join(root, f), a.out)[:-4].replace(os.sep, '/')
                    if rel not in known:
                        os.remove(os.path.join(root, f))
                        print('removed stale', rel)

    if not a.no_sheet:
        files = []
        for root, _, fs in os.walk(a.out):
            for f in fs:
                if f.endswith('.ogg'):
                    p = os.path.join(root, f)
                    files.append((os.path.relpath(p, a.out)[:-4].replace(os.sep, '/'), p))
        size = render_sheet(sorted(files), a.sheet)
        print('contact sheet %dx%d -> %s' % (size[0], size[1], a.sheet))
    return 0


if __name__ == '__main__':
    sys.exit(main())
