"""Ses bandı: tamamen sentezlenmiş müzik + efektler + seslendirme miksajı.

* Müzik: Re Hicaz makamında ney benzeri melodi, bordun (drone) ve çello
  ostinatosu, mehter usulünde davul ("düm – tek – tek – düm – tek").
* Efektler: savaş anlarında kös vuruşu ve kılıç şakırtısı, zil (cymbal),
  sahne geçişlerinde rüzgâr/whoosh.
* Seslendirme: Piper TTS çıktısı; müzik konuşma sırasında otomatik kısılır.
"""
import os
import subprocess

import numpy as np
from scipy.signal import butter, sosfilt, resample_poly, fftconvolve

from config import SR

RNG = np.random.default_rng(1919)
BPM = 80.0
BEAT = 60.0 / BPM

# Re Hicaz dizisi (D4 = 293.66 Hz)
NOTE = {"D3": 146.83, "Eb3": 155.56, "F#3": 185.00, "G3": 196.00, "A3": 220.00, "Bb3": 233.08,
        "C4": 261.63, "D4": 293.66, "Eb4": 311.13, "F#4": 369.99, "G4": 392.00, "A4": 440.00,
        "Bb4": 466.16, "C5": 523.25, "D5": 587.33, "D2": 73.42, "Eb2": 77.78, "A1": 55.0,
        "C2": 65.41, "Bb1": 58.27, "G2": 98.0, "A2": 110.0, "F#2": 92.5}


def bp(lo, hi, order=2):
    return butter(order, [lo, hi], btype="band", fs=SR, output="sos")


def hp(f, order=2):
    return butter(order, f, btype="high", fs=SR, output="sos")


def lp(f, order=2):
    return butter(order, f, btype="low", fs=SR, output="sos")


def env_adsr(n, a, d, s_lvl, r):
    e = np.ones(n, np.float32) * s_lvl
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    na = max(1, min(na, n))
    e[:na] = np.linspace(0, 1, na)
    nd = max(1, min(nd, n - na))
    e[na:na + nd] = np.linspace(1, s_lvl, nd)
    nr = max(1, min(nr, n))
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


def add(buf, x, t, gain=1.0, pan=0.0):
    """Mono x'i stereo buf'a t saniyesinde ekle (pan: -1 sol, +1 sağ)."""
    i = int(t * SR)
    if i >= buf.shape[1] or i + len(x) <= 0:
        return
    if i < 0:
        x = x[-i:]
        i = 0
    j = min(buf.shape[1], i + len(x))
    x = x[:j - i] * gain
    gl = np.cos((pan + 1) * np.pi / 4)
    gr = np.sin((pan + 1) * np.pi / 4)
    buf[0, i:j] += x * gl * 1.414
    buf[1, i:j] += x * gr * 1.414


# ------------------------------------------------------------------ enstrümanlar
def saw(freq, dur, nh=24, detune=0.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    f = freq * (1 + detune)
    for k in range(1, nh + 1):
        if f * k > 9000:
            break
        out += (np.sin(2 * np.pi * f * k * t + RNG.uniform(0, 6.28)) / k ** 1.15).astype(np.float32)
    return out


def ney(freq, dur, vib=0.006):
    n = int(dur * SR)
    t = np.arange(n) / SR
    vib_env = np.clip((t - 0.18) / 0.4, 0, 1)
    f = freq * (1 + vib * vib_env * np.sin(2 * np.pi * 5.2 * t))
    # yumuşak giriş: hafif aşağıdan kayarak
    f *= 1 - 0.012 * np.exp(-t * 18)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.28 * np.sin(2 * ph + 0.3) + 0.10 * np.sin(3 * ph + 0.7) + 0.04 * np.sin(4 * ph)
    breath = sosfilt(bp(freq * 1.5, min(freq * 6, 9000)), RNG.normal(0, 1, n)) * 0.10
    e = env_adsr(n, 0.09, 0.15, 0.82, min(0.25, dur * 0.4))
    e *= 1 + 0.06 * np.sin(2 * np.pi * 0.7 * t)
    return ((x + breath) * e).astype(np.float32)


def cello(freq, dur):
    x = saw(freq, dur, 18) + 0.6 * saw(freq, dur, 18, 0.004)
    x = sosfilt(lp(1400), x)
    e = env_adsr(len(x), 0.012, 0.18, 0.35, 0.08)
    return (x * e).astype(np.float32)


def davul(strength=1.0):
    dur = 0.7
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 52 + 75 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 6.5)
    click = sosfilt(bp(900, 4000), RNG.normal(0, 1, n)) * np.exp(-t * 70) * 0.5
    skin = sosfilt(bp(150, 600), RNG.normal(0, 1, n)) * np.exp(-t * 18) * 0.35
    return ((body + click + skin) * strength).astype(np.float32)


def tek(strength=1.0):
    dur = 0.18
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = sosfilt(bp(1500, 6000), RNG.normal(0, 1, n)) * np.exp(-t * 55)
    tone = np.sin(2 * np.pi * 420 * t) * np.exp(-t * 40) * 0.4
    return ((noise * 0.8 + tone) * strength).astype(np.float32)


def kos(strength=1.0, dark=False):
    dur = 3.2
    n = int(dur * SR)
    t = np.arange(n) / SR
    f0 = 36 if dark else 41
    f = f0 + 55 * np.exp(-t * 9)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 1.5) + 0.35 * np.sin(2.02 * ph) * np.exp(-t * 2.6)
    rumble = sosfilt(lp(160), RNG.normal(0, 1, n)) * np.exp(-t * 2.2) * 0.9
    hit = sosfilt(bp(300, 2500), RNG.normal(0, 1, n)) * np.exp(-t * 40) * 0.35
    return ((body + rumble + hit) * strength).astype(np.float32)


def zil(strength=1.0, dur=3.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = sosfilt(hp(3000), RNG.normal(0, 1, n)) * np.exp(-t * 1.6)
    metal = sum(np.sin(2 * np.pi * f * t + RNG.uniform(0, 6)) * np.exp(-t * d)
                for f, d in ((3150, 1.8), (4720, 2.4), (6230, 2.2), (8010, 3.0), (5370, 2.0)))
    e = np.minimum(1, t / 0.004)
    return ((noise * 0.6 + metal * 0.08) * e * strength).astype(np.float32)


def clash(strength=1.0, seed=0):
    rng = np.random.default_rng(seed)
    dur = 0.9
    n = int(dur * SR)
    out = np.zeros(n, np.float32)
    for k, off in enumerate((0.0, 0.13 + rng.uniform(0, 0.05), 0.31 + rng.uniform(0, 0.06))):
        m = n - int(off * SR)
        t = np.arange(m) / SR
        sc = rng.uniform(0.92, 1.1)
        part = sum(np.sin(2 * np.pi * f * sc * t) * np.exp(-t * d)
                   for f, d in ((2370, 9), (3810, 12), (5160, 14), (7240, 18), (9310, 22)))
        burst = sosfilt(hp(2500), rng.normal(0, 1, m)) * np.exp(-t * 60)
        out[int(off * SR):] += ((part * 0.18 + burst * 0.5) * (0.9 - 0.25 * k)).astype(np.float32)
    return out * strength


def whoosh(dur=1.6, strength=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = RNG.normal(0, 1, n)
    out = np.zeros(n)
    seg = 2048
    for i in range(0, n, seg):
        c = 300 + 2200 * np.sin(np.pi * min(1, i / n)) ** 2
        out[i:i + seg] = sosfilt(bp(c * 0.6, c * 1.6), noise[i:i + seg])
    e = np.sin(np.pi * t / dur) ** 2
    return (out * e * strength).astype(np.float32)


def reverb_ir(rt=2.4, length=3.0, seed=3):
    rng = np.random.default_rng(seed)
    n = int(length * SR)
    t = np.arange(n) / SR
    dec = np.exp(-6.9 * t / rt)
    ir = np.stack([rng.normal(0, 1, n) * dec, rng.normal(0, 1, n) * dec]).astype(np.float32)
    ir[:, :int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))
    ir = np.stack([sosfilt(lp(6000), ir[0]), sosfilt(lp(6000), ir[1])])
    return ir / np.sqrt((ir ** 2).sum(axis=1, keepdims=True))


def reverb(x, ir, wet):
    y = np.stack([fftconvolve(x[0], ir[0])[:x.shape[1]], fftconvolve(x[1], ir[1])[:x.shape[1]]])
    return x * (1 - wet * 0.3) + y * wet


# ------------------------------------------------------------------ müzik
PHRASES = {
    "A": [("A4", 1), ("Bb4", .5), ("A4", .5), ("G4", .5), ("F#4", .5), ("G4", 1), ("F#4", .5),
          ("Eb4", .5), ("D4", 2.5)],
    "B": [("D4", .5), ("Eb4", .5), ("F#4", .5), ("G4", .5), ("A4", 1.5), ("G4", .5), ("A4", .5),
          ("Bb4", .5), ("A4", 1), ("G4", .5), ("F#4", .5), ("G4", 2.5)],
    "C": [("D5", 1), ("C5", .5), ("Bb4", .5), ("A4", 1), ("Bb4", .5), ("A4", .5), ("G4", .5),
          ("F#4", .5), ("G4", .5), ("A4", .5), ("D4", 3)],
    "D": [("G4", 1), ("F#4", .5), ("Eb4", .5), ("D4", 1), ("Eb4", .5), ("F#4", .5), ("G4", 1),
          ("A4", 1), ("G4", 2.5)],
}


def play_phrase(buf, name, t0, gain, octave=1.0, pan=0.25):
    t = t0
    for note, beats in PHRASES[name]:
        d = beats * BEAT
        add(buf, ney(NOTE[note] * octave, d + 0.12), t, gain, pan)
        t += d
    return t


MAJOR = {
    "R1": [("D4", 1), ("E4", .5), ("F#4", .5), ("G4", 1), ("A4", 1), ("B4", .5), ("A4", .5),
           ("G4", .5), ("F#4", .5), ("E4", 1), ("D4", 2)],
    "R2": [("A4", 1), ("B4", .5), ("C#5", .5), ("D5", 1.5), ("C#5", .5), ("B4", 1), ("A4", .5),
           ("G4", .5), ("F#4", 1), ("E4", .5), ("F#4", .5), ("D4", 2.5)],
}
NOTE.update({"E4": 329.63, "B4": 493.88, "C#5": 554.37, "E2": 82.41, "F#2": 92.50, "B1": 61.74,
             "G1": 49.0, "E3": 164.81, "B3": 246.94})


def play_major(buf, name, t0, gain, pan=0.2):
    t = t0
    for note, beats in MAJOR[name]:
        d = beats * BEAT
        add(buf, ney(NOTE[note], d + 0.12), t, gain, pan)
        t += d
    return t


def chord_pad(notes, dur, cutoff=900):
    x = np.zeros(int(dur * SR), np.float32)
    for k, nme in enumerate(notes):
        x += saw(NOTE[nme], dur, 12, 0.002 * (k - 1)) * (1.0 if k == 0 else 0.6)
    x = sosfilt(lp(cutoff), x)
    return (x * env_adsr(len(x), 0.8, 0.5, 0.85, 1.2)).astype(np.float32)


def build_music(tl, n):
    dur = n / SR
    music = np.zeros((2, n), np.float32)
    drums = np.zeros((2, n), np.float32)
    lead = np.zeros((2, n), np.float32)
    fx = np.zeros((2, n), np.float32)

    sc = {s["id"]: s for s in tl["scenes"]}
    t_samsun = sc["samsun"]["t0"]
    t_war = sc["yunan20"]["t0"]
    t_sevr0, t_sevr1 = sc["sevr"]["t0"], sc["sevr"]["t1"]
    t_sakarya = sc["sakarya"]["t0"]
    t_taarruz = sc["taarruz"]["t0"]
    t_peace = sc["mudanya"]["t0"]
    t_peak = tl.get("peak") or sc["cumhuriyet"]["t0"]
    t_outro = tl.get("outro") or dur - 4
    tt = np.arange(n) / SR

    # --- bordun: Re Hicaz (savaş yılları) → Re majör (barış ve Cumhuriyet)
    pad = np.zeros(n, np.float32)
    for f, g, det in ((NOTE["D2"], 1.0, 0.0), (NOTE["D2"], 0.7, 0.003), (NOTE["A2"], 0.55, -0.002),
                      (NOTE["D3"], 0.35, 0.001)):
        pad += g * saw(f, dur, 14, det)
    pad = sosfilt(lp(650), pad)
    swell = 0.55 + 0.45 * np.sin(2 * np.pi * tt / (16 * BEAT)) ** 2
    ramp_in = np.clip(tt / 3.0, 0, 1)
    to_major = np.clip((tt - t_peace) / 3.0, 0, 1)
    pad_env = ramp_in * swell * (1 - 0.5 * to_major) * 0.10
    add(music, pad * pad_env, 0.0, 1.0, 0.0)

    # karanlık tremolo yaylılar: işgal yılları ve Sevr
    trem = np.zeros(n, np.float32)
    for nm in ("D3", "Eb3", "A3"):
        trem += saw(NOTE[nm], dur, 10, 0.003)
    trem = sosfilt(lp(1100), trem) * (0.6 + 0.4 * np.sin(2 * np.pi * 7.5 * tt))
    dark = (np.clip((tt - 6) / 4, 0, 1) * (1 - np.clip((tt - t_samsun) / 3, 0, 1))
            + np.clip((tt - t_sevr0) / 1.5, 0, 1) * (1 - np.clip((tt - t_sevr1) / 2, 0, 1)))
    add(music, trem * dark * 0.035, 0.0, 1.0, -0.2)

    # Barış: majör akorlar
    prog = [["D3", "F#3", "A3"], ["G3", "B3", "D4"], ["A3", "C#5", "E4"], ["D3", "F#3", "A3"]]
    NOTE["C#4"] = 277.18
    prog[2] = ["A3", "C#4", "E4"]
    t = t_peace
    i = 0
    while t < dur - 1:
        d = 4 * BEAT
        add(music, chord_pad(prog[i % 4], d + 1.0), t, 0.05, 0.1 * ((-1) ** i))
        add(music, cello(NOTE[["D2", "G2", "A2", "D2"][i % 4]], d), t, 0.06, -0.3)
        t += d
        i += 1

    # --- çello ostinatosu: savaş yılları
    pattern = ["D2", "D2", "D2", "Eb2", "D2", "D2", "C2", "D2",
               "D2", "D2", "D2", "Eb2", "D2", "Bb1", "A1", "D2"]
    t = t_samsun
    i = 0
    while t < t_peace:
        if t_sevr0 + 0.5 < t < t_sevr1 - 0.3:
            t += BEAT / 2
            i += 1
            continue
        inten = 0.45 if t < t_war else (0.75 if t < t_sakarya else (0.9 if t < t_taarruz else 1.1))
        acc = 1.0 if i % 4 == 0 else 0.7
        add(music, cello(NOTE[pattern[i % len(pattern)]], BEAT / 2 + 0.05), t, 0.07 * inten * acc, -0.3)
        t += BEAT / 2
        i += 1

    # --- mehter davulu: düm (1) tek (2) tek (2.5) düm (3) tek (4)
    bar = 4 * BEAT
    t = t_samsun + 2 * bar
    k = 0
    while t < t_peace - 0.2:
        if t_sevr0 < t < t_sevr1 - 0.5:
            t += bar
            continue
        ramp = 0.4 if t < t_war else (0.75 if t < t_sakarya else (0.9 if t < t_taarruz else 1.15))
        add(drums, davul(1.0), t, 0.40 * ramp, 0.0)
        add(drums, tek(1.0), t + BEAT, 0.18 * ramp, 0.35)
        add(drums, tek(0.8), t + 1.5 * BEAT, 0.14 * ramp, 0.35)
        add(drums, davul(0.85), t + 2 * BEAT, 0.34 * ramp, 0.0)
        add(drums, tek(1.0), t + 3 * BEAT, 0.18 * ramp, 0.35)
        if t > t_taarruz:
            add(drums, tek(0.6), t + 3.5 * BEAT, 0.12 * ramp, -0.35)
            add(drums, davul(0.6), t + 3.5 * BEAT, 0.18 * ramp, 0.0)
        t += bar
        k += 1
    # Cumhuriyet: ağır tören davulu
    t = t_peak
    while t < t_outro + 2:
        add(drums, davul(1.0), t, 0.30, 0.0)
        add(drums, davul(0.7), t + 2 * BEAT, 0.22, 0.0)
        t += bar

    # --- ney melodileri
    play_phrase(lead, "A", 1.0, 0.16, octave=0.5)
    play_phrase(lead, "D", 1.0 + 9 * BEAT, 0.13, octave=0.5)
    t = t_samsun + 0.4
    names = ["A", "B", "D", "A", "B", "C", "D", "A", "B", "D"]
    j = 0
    while t < t_peace - 6 * BEAT:
        if t_sevr0 - 4 * BEAT < t < t_sevr1:
            t = t_sevr1 + BEAT
            continue
        end = play_phrase(lead, names[j % len(names)], t, 0.12 if t < t_taarruz else 0.15)
        t = end + 3 * BEAT
        j += 1
    play_phrase(lead, "C", t_sevr0 + 1.0, 0.13, octave=0.5, pan=-0.1)
    t = t_peace + 0.3
    k = 0
    while t < t_outro + 3:
        end = play_major(lead, "R1" if k % 2 == 0 else "R2", t, 0.15 if t < t_peak else 0.19)
        t = end + BEAT
        k += 1

    # --- efektler
    for b in tl["markers"]:
        if b["kind"] in ("win", "loss"):
            dark_ = b["kind"] == "loss"
            add(fx, kos(1.0, dark_), b["t"] - 0.02, 0.40 if dark_ else 0.34, 0.0)
            add(fx, clash(1.0, seed=int(b["t"] * 100)), b["t"] + 0.05, 0.15, RNG.uniform(-0.4, 0.4))
        elif b["kind"] == "occ":
            add(fx, kos(0.8, True), b["t"] - 0.02, 0.30, 0.0)
        else:
            add(fx, zil(0.6, 2.2), b["t"], 0.05, RNG.uniform(-0.3, 0.3))
    for ar in tl["arrows"]:
        if ar["side"] in ("tr", "gr"):
            add(fx, whoosh(min(2.0, ar["dur"] + 0.4), 1.0), ar["t"], 0.035, RNG.uniform(-0.4, 0.4))
    for s in tl["scenes"][1:]:
        add(fx, whoosh(1.5), s["t0"] - 0.2, 0.04, 0.0)
    add(fx, kos(1.2, True), 0.25, 0.45, 0.0)
    add(fx, kos(1.3), t_sevr0 + 0.3, 0.42, 0.0)
    if tl.get("offensive"):
        add(fx, kos(1.4), tl["offensive"] - 0.05, 0.5, 0.0)
        add(fx, zil(1.0, 4.0), tl["offensive"], 0.10, 0.2)
    add(fx, zil(1.0, 4.0), t_peace, 0.09, -0.2)
    add(fx, zil(1.0, 5.0), t_peak, 0.14, -0.2)
    add(fx, kos(1.3), t_peak, 0.5, 0.0)
    add(fx, kos(1.2), t_outro + 0.1, 0.42, 0.0)
    add(fx, zil(0.9, 5.0), t_outro + 0.1, 0.10, 0.0)
    return music, drums, lead, fx


def build_voice(tl, n):
    v = np.zeros((2, n), np.float32)
    for seg in tl["voice"]:
        x = np.load(seg["npy"]).astype(np.float32)
        if seg["sr"] != SR:
            x = resample_poly(x, SR, seg["sr"]).astype(np.float32)
        x = sosfilt(hp(75), x).astype(np.float32)
        add(v, x, seg["t"], 1.0, 0.0)
    return v


def duck_env(voice, depth=0.6):
    mono = np.abs(voice[0]) + np.abs(voice[1])
    win = int(0.03 * SR)
    rms = np.sqrt(np.convolve(mono ** 2, np.ones(win) / win, mode="same"))
    target = np.clip(rms / (np.percentile(rms[rms > 1e-4], 70) + 1e-9), 0, 1)
    # attack 40 ms, release 450 ms
    out = np.zeros_like(target)
    a, r = np.exp(-1 / (0.04 * SR)), np.exp(-1 / (0.45 * SR))
    step = 64
    cur = 0.0
    for i in range(0, len(target), step):
        tv = target[i:i + step].max()
        coef = a ** step if tv > cur else r ** step
        cur = tv + (cur - tv) * coef
        out[i:i + step] = cur
    return 1 - depth * out


def build(tl, out_path):
    n = int((tl["duration"] + 0.5) * SR)
    music, drums, lead, fx = build_music(tl, n)
    voice = build_voice(tl, n)
    ir_big = reverb_ir(2.6, 3.2, 3)
    ir_room = reverb_ir(0.7, 1.0, 5)
    music = reverb(music, ir_big, 0.35)
    drums = reverb(drums, ir_big, 0.25)
    lead = reverb(lead, ir_big, 0.45)
    fx = reverb(fx, ir_big, 0.30)
    voice = reverb(voice, ir_room, 0.10)

    g = duck_env(voice, 0.72)
    bed = (music + drums * 0.8 + lead) * g
    fxg = fx * (1 - 0.45 * (1 - g))
    vpk = np.abs(voice).max() + 1e-9
    voice = voice / vpk * 0.80
    mix = voice + bed * 0.62 + fxg * 0.55
    # yumuşak sınırlayıcı
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    # baş/son kararması
    t = np.arange(n) / SR
    fade = np.clip(t / 0.15, 0, 1) * np.clip((tl["duration"] - t) / 1.2, 0, 1)
    mix *= fade
    raw = out_path.replace(".wav", "_raw.wav")
    _write_wav(raw, mix)
    # EBU R128 ses yüksekliği normalizasyonu (-16 LUFS)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af",
                    "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", str(SR), out_path], check=True)
    print(f"  [ses] {out_path}")
    return out_path


def _write_wav(path, x):
    import wave
    y = (np.clip(x, -1, 1).T * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(y.tobytes())
