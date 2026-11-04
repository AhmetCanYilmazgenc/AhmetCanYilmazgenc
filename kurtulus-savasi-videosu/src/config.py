"""Proje genelindeki yollar ve sabitler."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.environ.get("KS_ASSETS", os.path.join(ROOT, "assets_cache"))
DATA_DIR = os.path.join(ASSETS, "data")
FONT_DIR = os.path.join(ASSETS, "fonts")
VOICE_DIR = os.path.join(ASSETS, "voice")
CACHE_DIR = os.environ.get("KS_CACHE", os.path.join(ROOT, "build_cache"))
OUT_DIR = os.path.join(ROOT, "output")

W, H = 1920, 1080
FPS = 30
SR = 44100  # ses örnekleme hızı

VOICE_NAME = "tr_TR-fahrettin-medium"

for d in (CACHE_DIR, OUT_DIR):
    os.makedirs(d, exist_ok=True)
