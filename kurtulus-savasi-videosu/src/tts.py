"""Türkçe seslendirme: Piper TTS (fahrettin sesi, CC0).

Her sahne metni ayrı sentezlenir. Olayların (savaş işaretleri, bilgi kartı)
konuşmayla eşzamanlı olması için metnin anahtar kelimeye kadar olan kısmı da
ayrıca sentezlenip süresi ölçülür.
"""
import json
import os
import wave
import io
import re

import numpy as np

from config import VOICE_DIR, VOICE_NAME, CACHE_DIR

LENGTH_SCALE = 0.97


def _load_voice():
    from piper import PiperVoice
    d = os.path.join(VOICE_DIR, "vits-piper-" + VOICE_NAME)
    return PiperVoice.load(os.path.join(d, VOICE_NAME + ".onnx"),
                           config_path=os.path.join(d, VOICE_NAME + ".onnx.json"))


# eSpeak'in yanlış fonemleştirdiği özel isimler için elle yazılmış fonemler
# (ör. "İnönü" → "inœnø", "Gümrü" → "ɟømrø" çıkıyordu).
PRON = [
    ("İnönü", "[[ inøːnˈyː ]]"),
    ("Gümrü'de", "[[ ɟymɾydˈe ]]"),
    ("Gümrü", "[[ ɟymɾˈy ]]"),
    ("Urfa'ya", "[[ uɾfaˈja ]]"),
    ("Urfa", "[[ ˈuɾfa ]]"),
    ("Misak ı Millî'yi", "[[ misaːkɯ milliːjˈi ]]"),
    ("Mebusan", "[[ mebuːsˈan ]]"),
    ("Bandırma Vapuru", "[[ bandɯɾmˈa vapuɾˈu ]]"),
]
NOISE_SCALE = 0.3
NOISE_W = 0.5


def tts_text(text):
    """Seslendirme için metni sadeleştir (tireler, tırnaklar, özel telaffuzlar)."""
    for a, b in (("-", " "), ("\u201c", ""), ("\u201d", ""), ("!", ".")):
        text = text.replace(a, b)
    for a, b in PRON:
        text = re.sub(r"(?<![\w\[])" + re.escape(a) + r"(?![\w'])", b, text)
    return text


def _synth(voice, text):
    from piper import SynthesisConfig
    text = tts_text(text)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        voice.synthesize_wav(text, w, syn_config=SynthesisConfig(length_scale=LENGTH_SCALE, noise_scale=NOISE_SCALE, noise_w_scale=NOISE_W))
    buf.seek(0)
    with wave.open(buf, "rb") as r:
        sr = r.getframerate()
        x = np.frombuffer(r.readframes(r.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return x, sr


def _trim(x, sr, thr=0.012):
    """Baş/son sessizliği kırp; (kırpılmış, baştan kesilen örnek sayısı)."""
    env = np.convolve(np.abs(x), np.ones(256) / 256, mode="same")
    idx = np.where(env > thr)[0]
    if len(idx) == 0:
        return x, 0
    a = max(0, idx[0] - int(0.02 * sr))
    b = min(len(x), idx[-1] + int(0.06 * sr))
    return x[a:b], a


def synthesize_all(scenes, force=False):
    """Her sahne için {'wav': yol, 'dur': sn, 'anchors': {anahtar: sn}} döndürür."""
    meta_path = os.path.join(CACHE_DIR, "narration.json")
    key = json.dumps([[s["text"], [e.get("anchor") for e in s["events"]]] for s in scenes]
                     + [LENGTH_SCALE, NOISE_SCALE, NOISE_W, PRON], ensure_ascii=False)
    if not force and os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
        if meta.get("key") == key:
            return meta["scenes"]
    voice = _load_voice()
    out = []
    for s in scenes:
        x, sr = _synth(voice, s["text"])
        x, _ = _trim(x, sr)
        path = os.path.join(CACHE_DIR, f"vo_{s['id']}.npy")
        np.save(path, x)
        dur = len(x) / sr
        anchors = {}
        for e in s["events"]:
            a = e.get("anchor")
            if not a or a.startswith("@") or a in anchors:
                continue
            i = s["text"].find(a)
            if i < 0:
                raise ValueError(f"anchor '{a}' metinde yok: {s['text']}")
            prefix = s["text"][:i].strip()
            if not prefix:
                anchors[a] = 0.0
                continue
            # anahtar kelimeye kadar olan kısmın süresi (iki ölçümün ortalaması)
            ds = []
            for _ in range(2):
                px, _sr = _synth(voice, prefix)
                px, _ = _trim(px, _sr)
                ds.append(len(px) / _sr)
            anchors[a] = float(min(dur, np.mean(ds) + 0.05))
        out.append(dict(id=s["id"], npy=path, sr=sr, dur=dur, anchors=anchors))
        print(f"  [tts] {s['id']:9s} {dur:5.2f} sn  {anchors}")
    with open(meta_path, "w") as f:
        json.dump(dict(key=key, scenes=out), f, ensure_ascii=False, indent=1)
    return out
