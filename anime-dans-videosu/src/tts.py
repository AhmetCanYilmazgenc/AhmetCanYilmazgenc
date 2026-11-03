"""Seslendirme: Kokoro TTS (yerel, Apache-2.0) + ffmpeg ile ses tasarımı.

Kadifemsi alto tını için af_bella ve bf_emma sesleri harmanlanır, perde
hafifçe düşürülür. Her replik kendi duygusuna göre (sıcak / emredici /
utangaç) farklı perde, hız ve yankıyla işlenir.
"""
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(ROOT, "assets_cache", "kokoro")
BUILD = os.path.join(ROOT, "build_cache")

# (kimlik, metin, hız, perde çarpanı, ek ffmpeg filtresi)
LINES = [
    ("warm", "Oh my... you came all this way, just to watch me dance? "
             "Then stay close. And don't you dare look away.",
     0.92, 0.93, "aecho=0.8:0.5:40:0.12"),
    ("command", "Enough playing. Now... witness the power of House Vermillion.",
     0.86, 0.88, "aecho=0.8:0.7:60|120:0.25|0.15,bass=g=3"),
    ("flustered", "W-wait! Were you recording this... the whole time?!",
     1.12, 1.05, "aecho=0.8:0.4:30:0.08"),
]


def voice_style(k):
    a = k.get_voice_style("af_bella")
    b = k.get_voice_style("bf_emma")
    return a * 0.6 + b * 0.4


def synth_all():
    from kokoro_onnx import Kokoro
    os.makedirs(BUILD, exist_ok=True)
    k = Kokoro(os.path.join(MODEL_DIR, "kokoro.onnx"), os.path.join(MODEL_DIR, "voices.bin"))
    style = voice_style(k)
    meta = {}
    for key, text, speed, pitch, fx in LINES:
        raw = os.path.join(BUILD, f"{key}_raw.wav")
        out = os.path.join(BUILD, f"{key}.wav")
        samples, sr = k.create(text, voice=style, speed=speed, lang="en-us")
        sf.write(raw, samples, sr)
        # perde değişimi: asetrate ile kaydır, atempo ile süreyi geri al
        af = (f"asetrate={int(sr * pitch)},aresample=48000,atempo={1 / pitch:.5f},"
              f"highpass=f=70,equalizer=f=220:t=q:w=1:g=2.5,equalizer=f=3200:t=q:w=1.2:g=1.5,"
              f"{fx},silenceremove=start_periods=1:start_threshold=-45dB,"
              f"areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
              f"apad=pad_dur=0.05")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", af,
                        "-ac", "1", "-ar", "48000", out], check=True)
        x, sr2 = sf.read(out)
        # dudak senkronu için 30 fps zarf
        hop = sr2 // 30
        env = [float(np.sqrt(np.mean(x[i:i + hop] ** 2))) for i in range(0, len(x), hop)]
        m = max(env) or 1
        meta[key] = {"text": text, "dur": len(x) / sr2, "env": [round(e / m, 3) for e in env]}
        print(f"  {key}: {len(x) / sr2:.2f} sn")
    with open(os.path.join(BUILD, "voice.json"), "w") as f:
        json.dump(meta, f)
    return meta


if __name__ == "__main__":
    synth_all()
