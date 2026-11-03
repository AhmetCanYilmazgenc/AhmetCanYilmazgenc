#!/usr/bin/env bash
# Harici varlıkları indirir (git'e eklenmez): fontlar ve Kokoro TTS modeli.
set -euo pipefail
cd "$(dirname "$0")"
A=assets_cache
mkdir -p $A/fonts $A/kokoro
GF=https://raw.githubusercontent.com/google/fonts/main/ofl
dl() { [ -s "$2" ] || curl -fsSL -o "$2" "$1"; }
dl "$GF/cinzel/Cinzel%5Bwght%5D.ttf" $A/fonts/Cinzel.ttf
dl "$GF/nunito/Nunito%5Bwght%5D.ttf" $A/fonts/Nunito.ttf
dl "$GF/nunito/Nunito-Italic%5Bwght%5D.ttf" $A/fonts/Nunito-Italic.ttf
KR=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
dl "$KR/kokoro-v1.0.int8.onnx" $A/kokoro/kokoro.onnx
dl "$KR/voices-v1.0.bin" $A/kokoro/voices.bin
echo "Varlıklar hazır: $A"
