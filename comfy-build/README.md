# gorsel-video-studio — Comfy Build

Yüksek kaliteli görsel ve video üretimi için ComfyUI ortamı. Tanım
[`comfy-build.yaml`](comfy-build.yaml) dosyasında. Platform:
[platform.comfy.org](https://platform.comfy.org).

## Workflow'lar (`workflows/`)

Hepsi ComfyUI'nin resmi şablonlarından (`comfyui-workflow-templates` 0.11.103)
alındı ve yalnızca çekirdek ComfyUI node'larını kullanıyor; ek paket gerekmez.

| Dosya | Ne yapar | Model |
| --- | --- | --- |
| `gorsel_qwen_image_2_1_t2i.json` | Metinden görsel (1024×1024, 2K'ya kadar) | Qwen Image 2.1 (int8) |
| `video_minimax_h3_i2v.json` | Görselden video (sesli, ~15 sn'ye kadar) | MiniMax H3 (int8) + Turbo LoRA |

> `video_ltx2_5_*.json` ve `api/video_ltx2_5_i2v_api.json` release v1 içindir.
> v2'den itibaren LTX-2.5 modelleri build'den çıkarıldı; bu dosyalar yalnızca
> v1 ile çalışır.

## Ortam

- ComfyUI: `v0.44.2`
- Ek node paketi: yok
- `pipDependencies`: boş (paketlerin kendi gereksinimleri base image'ın torch'u ile çözülür)
- 9 model (yaklaşık 70 GB), hepsi builder tarafından Hugging Face'ten indirilir (yerelden yükleme yok)
- Release v1: Qwen Image 2.1 + LTX-2.5 · Release v2: Qwen Image 2.1 + MiniMax H3

## Komutlar

```shell
comfy build validate comfy-build            # çevrimdışı kontrol
comfy build push comfy-build                # tanımı platforma gönder
comfy build release create comfy-build --target linux/nvidia --watch
```
