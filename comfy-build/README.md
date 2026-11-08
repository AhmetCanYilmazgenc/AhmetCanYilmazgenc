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
| `video_ltx2_5_t2v.json` | Metinden video (sesli, 2× uzamsal büyütme) | LTX-2.5 22B distilled (int8) |
| `video_ltx2_5_i2v.json` | Görselden video (sesli) | LTX-2.5 22B distilled (int8) |

## Ortam

- ComfyUI: `v0.44.2`
- Ek node paketi: yok
- `pipDependencies`: boş (paketlerin kendi gereksinimleri base image'ın torch'u ile çözülür)
- 10 model, hepsi builder tarafından Hugging Face'ten indirilir (yerelden yükleme yok)

## Komutlar

```shell
comfy build validate comfy-build            # çevrimdışı kontrol
comfy build push comfy-build                # tanımı platforma gönder
comfy build release create comfy-build --target linux/nvidia --watch
```
