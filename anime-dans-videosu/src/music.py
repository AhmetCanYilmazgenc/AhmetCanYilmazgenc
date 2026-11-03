"""Tamamen NumPy ile sentezlenen dans müziği (120 BPM, Re minör) ve efektler.

Bölümler (saniye):
  0–8   giriş: pad + müzik kutusu arpeji
  8–16  dans A: four-on-the-floor davul, bas, pluck arpej
  16–20 yükseliş: trampet rulosu, riser, davul kesilir
  20–28 dans B (drop): ağır bas, koro pad, lead melodi
  28–30 final vuruşu ve yankı kuyruğu
  30–   kapanış: yumuşak müzik kutusu
"""
import numpy as np

SR = 48000
BPM = 120
BEAT = 60 / BPM
BAR = 4 * BEAT
RNG = np.random.default_rng(7)


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def t_arr(n):
    return np.arange(n) / SR


def lowpass(x, fc, order=2):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / np.sqrt(1 + (f / fc) ** (2 * order))
    return np.fft.irfft(X, len(x))


def highpass(x, fc, order=2):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / np.sqrt(1 + (fc / np.maximum(f, 1e-3)) ** (2 * order))
    return np.fft.irfft(X, len(x))


def reverb(x, secs=2.2, mix=0.3, seed=1):
    n = int(secs * SR)
    r = np.random.default_rng(seed)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR * 6.9 / secs)
    ir = lowpass(ir, 5000)
    ir /= np.sqrt(np.sum(ir ** 2))
    L = len(x) + n
    N = 1 << (L - 1).bit_length()
    wet = np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)[:len(x)]
    return x * (1 - mix) + wet * mix * 0.6


def adsr(n, a=0.005, d=0.1, s=0.6, r=0.1):
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    ns = max(0, n - na - nd)
    e = np.concatenate([np.linspace(0, 1, na, endpoint=False), np.linspace(1, s, nd, endpoint=False),
                        np.full(ns, s)])[:n]
    tail = np.linspace(s if len(e) == 0 else e[-1], 0, nr)
    return np.concatenate([e, tail])


def saw(f, n, detune=0.0, phase=0.0):
    t = t_arr(n)
    out = np.zeros(n)
    for d in ([0] if detune == 0 else [-detune, 0, detune]):
        ph = (t * f * (1 + d) + phase + RNG.random()) % 1
        out += 2 * ph - 1
    return out / (1 if detune == 0 else 3)


def add(buf, at, sig, gain=1.0):
    i = int(at * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[:j - i] * gain


# ---- enstrümanlar ----------------------------------------------------------
def kick(gain=1.0):
    n = int(0.45 * SR); t = t_arr(n)
    f = 45 + 120 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 7) * gain + RNG.standard_normal(n) * np.exp(-t * 300) * 0.15


def clap():
    n = int(0.3 * SR); t = t_arr(n)
    env = np.zeros(n)
    for k, d in enumerate([0, 0.011, 0.022]):
        i = int(d * SR); env[i:] += np.exp(-(t[:n - i]) * (60 if k < 2 else 18))
    return highpass(lowpass(RNG.standard_normal(n), 3500), 900) * env * 0.5


def hat(open_=False):
    n = int((0.25 if open_ else 0.06) * SR); t = t_arr(n)
    return highpass(RNG.standard_normal(n), 7000, 3) * np.exp(-t * (14 if open_ else 70)) * 0.35


def snare():
    n = int(0.2 * SR); t = t_arr(n)
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30)
    return (body * 0.5 + highpass(RNG.standard_normal(n), 1500) * np.exp(-t * 22) * 0.5)


def pluck(m, dur=0.25, bright=1.0):
    n = int(dur * SR); t = t_arr(n)
    f = mtof(m)
    x = (saw(f, n) * 0.6 + np.sin(2 * np.pi * f * t)) * np.exp(-t * 9)
    return lowpass(x, 1800 * bright) * 0.3


def musicbox(m, dur=1.2):
    n = int(dur * SR); t = t_arr(n)
    f = mtof(m)
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 4.02 * t) * np.exp(-t * 8)
    return x * np.exp(-t * 3.2) * 0.22


def pad(ms, dur, cutoff=1400, gain=0.12):
    n = int(dur * SR)
    x = sum(saw(mtof(m), n, detune=0.006) for m in ms)
    return lowpass(x, cutoff) * adsr(n, 0.4, 0.3, 0.8, 0.6)[:n] * gain


def choir(ms, dur, gain=0.1):
    n = int(dur * SR); t = t_arr(n)
    out = np.zeros(n)
    for m in ms:
        f = mtof(m) * (1 + 0.004 * np.sin(2 * np.pi * 5.2 * t))
        ph = 2 * np.pi * np.cumsum(f) / SR
        out += sum(np.sin(ph * h) / h ** 1.3 for h in range(1, 7))
    # "aa" formantları
    out = lowpass(out, 1100) + 0.4 * highpass(lowpass(out, 1300), 700)
    return out * adsr(n, 0.3, 0.2, 0.85, 0.5)[:n] * gain


def bass(m, dur, dist=0.0):
    n = int(dur * SR); t = t_arr(n)
    f = mtof(m)
    x = saw(f, n) * 0.7 + np.sin(2 * np.pi * f * t)
    x = lowpass(x, 500 + 900 * dist) * adsr(n, 0.004, 0.08, 0.7, 0.05)[:n]
    if dist:
        x = np.tanh(x * (1 + 4 * dist)) / np.tanh(1 + 4 * dist)
    return x * 0.32


def lead(m, dur):
    n = int(dur * SR); t = t_arr(n)
    f = mtof(m) * (1 + 0.006 * np.sin(2 * np.pi * 5.5 * t) * np.clip(t * 3, 0, 1))
    ph = np.cumsum(f) / SR
    sq = np.sign(np.sin(2 * np.pi * ph)) * 0.5 + (2 * (ph % 1) - 1) * 0.5
    return lowpass(sq, 3200) * adsr(n, 0.01, 0.1, 0.7, 0.12)[:n] * 0.11


def noise_riser(dur):
    n = int(dur * SR); t = t_arr(n)
    x = RNG.standard_normal(n)
    lo = highpass(x, 400); hi = highpass(x, 3500)
    k = (t / dur) ** 2
    return (lo * (1 - k) + hi * k) * k * 0.25


def boom():
    n = int(2.5 * SR); t = t_arr(n)
    f = 30 + 80 * np.exp(-t * 6)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    return s * 0.9 + lowpass(RNG.standard_normal(n), 900) * np.exp(-t * 3) * 0.35


def whoosh(dur=0.6, up=True):
    n = int(dur * SR); t = t_arr(n)
    env = np.sin(np.pi * t / dur) ** 2
    x = RNG.standard_normal(n)
    return (lowpass(x, 1200) if up else lowpass(x, 700)) * env * 0.35


def sparkle(dur=1.2):
    n = int(dur * SR); out = np.zeros(n)
    for k in range(9):
        m = 84 + RNG.integers(0, 14)
        add(out, k * dur / 12, musicbox(int(m), 0.6), 0.7)
    return out


# ---- aranjman --------------------------------------------------------------
PROG_A = [(50, [62, 65, 69]), (46, [62, 65, 70]), (41, [60, 65, 69]), (48, [60, 64, 67])]   # Dm Bb F C
PROG_B = [(50, [62, 65, 69]), (46, [62, 65, 70]), (43, [62, 67, 70]), (45, [61, 64, 69])]   # Dm Bb Gm A
ARP = [0, 1, 2, 1, 2, 0, 1, 2]
MELODY = [  # (vuruş, nota, uzunluk)  — B bölümü lead, 4 ölçü
    (0, 74, 1.5), (1.5, 76, 0.5), (2, 77, 1), (3, 76, 0.5), (3.5, 74, 0.5),
    (4, 74, 1), (5, 72, 1), (6, 70, 1.5), (7.5, 72, 0.5),
    (8, 70, 1), (9, 69, 1), (10, 67, 1), (11, 70, 1),
    (12, 69, 2), (14, 73, 1), (15, 76, 1),
]


def compose(total):
    n = int(total * SR)
    drums, bas, harm, top, fx = (np.zeros(n) for _ in range(5))

    # giriş (0–8): pad + müzik kutusu
    for b in range(4):
        root, ch = PROG_A[b]
        add(harm, b * BAR, pad([m - 12 for m in ch] + [root], BAR + 0.6, 900, 0.10))
        for k in range(8):
            add(top, b * BAR + k * BEAT / 2, musicbox(ch[ARP[k]] + 12, 1.0), 0.9 if k % 2 == 0 else 0.6)
    add(fx, 0.0, sparkle(1.4), 0.6)
    add(fx, 7.0, noise_riser(1.0), 0.6)

    # dans A (8–16)
    t0 = 8.0
    for b in range(4):
        root, ch = PROG_A[b]
        bt = t0 + b * BAR
        add(harm, bt, pad(ch, BAR + 0.5, 1600, 0.08))
        for k in range(4):
            add(drums, bt + k * BEAT, kick())
            add(drums, bt + k * BEAT + BEAT / 2, hat(open_=(k == 3)))
            if k % 2 == 1:
                add(drums, bt + k * BEAT, clap())
        for k in range(8):
            add(bas, bt + k * BEAT / 2, bass(root + (12 if k % 2 else 0), BEAT / 2 * 0.9))
        for k in range(16):
            add(top, bt + k * BEAT / 4, pluck(ch[ARP[k % 8]] + 12, 0.22), 0.8)
    add(fx, 13.0, whoosh(0.7), 0.7)   # dönüş

    # yükseliş (16–20)
    t1 = 16.0
    add(harm, t1, pad([50, 57, 62, 65], 4.2, 1000, 0.1))
    add(harm, t1, choir([62, 65, 69], 4.0, 0.05))
    for k in range(4):
        add(drums, t1 + k * BEAT, kick(0.8))
    hits = []
    tt = t1 + 2.0
    step = BEAT / 2
    while tt < 20.0 - 1e-6:
        hits.append(tt)
        tt += step
        if tt > 19.0: step = BEAT / 8
        elif tt > 18.5: step = BEAT / 4
    for i, h in enumerate(hits):
        add(drums, h, snare(), 0.3 + 0.5 * i / len(hits))
    add(fx, t1 + 0.5, noise_riser(3.5), 1.0)
    add(fx, 18.6, whoosh(1.2), 0.9)    # kanatlar açılıyor

    # drop (20–28)
    t2 = 20.0
    add(fx, t2, boom(), 1.0)
    add(fx, t2, highpass(RNG.standard_normal(int(2 * SR)), 5000) * np.exp(-t_arr(int(2 * SR)) * 2.2) * 0.3)
    for b in range(4):
        root, ch = PROG_B[b]
        bt = t2 + b * BAR
        add(harm, bt, choir([m - 12 for m in ch] + ch, BAR + 0.4, 0.06))
        add(harm, bt, pad(ch, BAR + 0.4, 2400, 0.07))
        for k in range(4):
            add(drums, bt + k * BEAT, kick(1.1))
            if k % 2 == 1:
                add(drums, bt + k * BEAT, clap(), 1.2)
        for k in range(16):
            add(drums, bt + k * BEAT / 4, hat(open_=(k % 4 == 2)), 0.8 if k % 2 else 0.5)
        for k in range(8):
            add(bas, bt + k * BEAT / 2, bass(root - 12 + (12 if k % 2 else 0), BEAT / 2 * 0.95, dist=0.6), 1.1)
        for k in range(16):
            add(top, bt + k * BEAT / 4, pluck(ch[ARP[k % 8]] + 24, 0.18, 1.6), 0.45)
    for bt, m, d in MELODY:
        add(top, t2 + bt * BEAT, lead(m, d * BEAT * 0.95))
    for k in range(4):
        add(fx, t2 + k * BAR + 1.5, whoosh(0.5), 0.35)   # kanat çırpışları

    # final vuruşu (28)
    t3 = 28.0
    add(fx, t3, boom(), 1.0)
    add(harm, t3, pad([50, 57, 62, 65, 69], 2.5, 3000, 0.12))
    add(harm, t3, choir([62, 65, 69, 74], 2.2, 0.08))
    add(bas, t3, bass(38, 1.2, 0.7), 1.2)

    # kapanış (30–): utangaç an için tatlı müzik kutusu
    for k, m in enumerate([81, 77, 74, 77, 79, 76, 73, 74]):
        add(top, 30.3 + k * 0.42, musicbox(m, 1.0), 0.7)
    add(harm, 30.2, pad([62, 65, 69], total - 30.2, 700, 0.05))
    add(fx, 30.1, sparkle(0.8), 0.5)

    harm = reverb(harm, 2.5, 0.35, 2)
    top = reverb(top, 1.8, 0.3, 3)
    fx = reverb(fx, 2.8, 0.3, 4)
    drums = reverb(drums, 0.9, 0.12, 5)
    mix = drums * 0.85 + bas * 0.9 + harm * 1.0 + top * 0.9 + fx * 0.8
    # yumuşak sınırlama
    mix = np.tanh(mix * 1.2) / 1.2
    return mix


if __name__ == "__main__":
    import soundfile as sf
    sf.write("/tmp/music_test.wav", compose(34.5), SR)
