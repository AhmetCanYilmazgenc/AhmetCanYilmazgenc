"""Üretim hattı: seslendirme → müzik → miks → kare çizimi → MP4.

  python3 src/build.py                 # tam video
  python3 src/build.py --stills 5,24   # belirli saniyelerden PNG
"""
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import music  # noqa: E402
import tts  # noqa: E402

ROOT = tts.ROOT
BUILD = tts.BUILD
OUT = os.path.join(ROOT, "output")
TOTAL = 34.5
STARTS = {"warm": 0.8, "command": 16.3, "flustered": 30.25}


def voice_meta():
    p = os.path.join(BUILD, "voice.json")
    if not os.path.exists(p):
        return tts.synth_all()
    with open(p) as f:
        return json.load(f)


def write_timeline(meta):
    tl = {"total": TOTAL, "voice": {k: {"start": STARTS[k], "dur": v["dur"], "env": v["env"]} for k, v in meta.items()}}
    with open(os.path.join(BUILD, "timeline.js"), "w") as f:
        f.write("window.TIMELINE = " + json.dumps(tl) + ";\n")


def mix_audio(meta):
    sr = music.SR
    n = int(TOTAL * sr)
    mus = music.compose(TOTAL)[:n]
    vox = np.zeros(n)
    for k, st in STARTS.items():
        x, _ = sf.read(os.path.join(BUILD, f"{k}.wav"))
        i = int(st * sr)
        vox[i:i + len(x)] += x[:n - i]
    # konuşma sırasında müziği kıs (ducking)
    e = np.abs(vox)
    w = int(0.15 * sr)
    e = np.convolve(e, np.ones(w) / w, mode="same")
    duck = 1 - 0.6 * np.clip(e / (e.max() * 0.15 + 1e-9), 0, 1)
    k = int(0.08 * sr)
    duck = np.convolve(duck, np.ones(k) / k, mode="same")
    out = mus * duck * 0.8 + vox * 1.0
    fade = np.ones(n); f = int(0.8 * sr); fade[-f:] = np.linspace(1, 0, f)
    out *= fade
    raw = os.path.join(BUILD, "mix_raw.wav")
    sf.write(raw, np.stack([out, out], 1).astype(np.float32), sr)
    final = os.path.join(BUILD, "mix.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", "loudnorm=I=-15:TP=-1.5:LRA=11",
                    "-ar", "48000", final], check=True)
    return final


def main():
    os.makedirs(BUILD, exist_ok=True); os.makedirs(OUT, exist_ok=True)
    print("1/4 Seslendirme")
    meta = voice_meta()
    write_timeline(meta)
    if len(sys.argv) > 2 and sys.argv[1] == "--stills":
        subprocess.run(["node", os.path.join(ROOT, "src", "render.js"), "--stills", os.path.join(BUILD, "stills"), sys.argv[2]], check=True)
        return
    print("2/4 Müzik ve miks")
    audio = mix_audio(meta)
    print("3/4 Kareler")
    video = os.path.join(BUILD, "video.mp4")
    subprocess.run(["node", os.path.join(ROOT, "src", "render.js"), video, "30"], check=True)
    print("4/4 Birleştirme")
    final = os.path.join(OUT, "seraphine_dans.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", audio, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", final], check=True)
    print("Hazır:", final)


if __name__ == "__main__":
    main()
