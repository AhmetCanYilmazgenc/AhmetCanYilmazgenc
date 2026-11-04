#!/usr/bin/env bash
# Harici varlıkları (harita verisi, fontlar, Türkçe ses modeli) indirir.
# Hepsi assets_cache/ altına iner ve git'e eklenmez.
set -euo pipefail
cd "$(dirname "$0")"
A=assets_cache
mkdir -p $A/data $A/fonts $A/voice

NE=https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson
for f in ne_10m_land ne_10m_lakes ne_10m_rivers_lake_centerlines; do
  [ -s $A/data/$f.geojson ] || curl -fsSL -o $A/data/$f.geojson "$NE/$f.geojson"
done

GF=https://raw.githubusercontent.com/google/fonts/main/ofl
dl_font() { [ -s "$A/fonts/$2" ] || curl -fsSL -o "$A/fonts/$2" "$GF/$1"; }
dl_font "cinzel/Cinzel%5Bwght%5D.ttf" "Cinzel[wght].ttf"
dl_font "ebgaramond/EBGaramond%5Bwght%5D.ttf" "EBGaramond[wght].ttf"
dl_font "ebgaramond/EBGaramond-Italic%5Bwght%5D.ttf" "EBGaramond-Italic[wght].ttf"

# Piper TTS – Türkçe "fahrettin" sesi (CC0), sherpa-onnx sürümleri üzerinden
V=vits-piper-tr_TR-fahrettin-medium
if [ ! -s $A/voice/$V/tr_TR-fahrettin-medium.onnx ]; then
  curl -fsSL -o /tmp/$V.tar.bz2 "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/$V.tar.bz2"
  tar xjf /tmp/$V.tar.bz2 -C $A/voice && rm /tmp/$V.tar.bz2
fi
echo "Varlıklar hazır: $A"
