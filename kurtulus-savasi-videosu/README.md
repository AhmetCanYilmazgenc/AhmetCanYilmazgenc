# Kurtuluş Savaşı: Mondros'tan Cumhuriyet'e (1918–1923)

Birinci Dünya Savaşı'nın ardından Mondros Ateşkesi'nden Cumhuriyet'in ilanına kadar
Türk Kurtuluş Savaşı'nın aşamalarını **animasyonlu bir harita** üzerinde anlatan,
önemli olaylar hakkında bilgi kartları gösteren ve **tamamen sentezlenmiş bir ses
bandına** (Türkçe seslendirme, müzik ve efektler) sahip bir video.

**Çıktı:** [`output/kurtulus_savasi_1918_1923.mp4`](output/kurtulus_savasi_1918_1923.mp4) — 1920×1080, 30 fps, yaklaşık 3 dakika 53 saniye.

## Aşamalar ve olaylar

| Aşama | Tarih | Olay |
|---|---|---|
| **Mondros ve İşgaller** | 30 Ekim 1918 | Mondros Ateşkes Antlaşması (7. madde) |
| | Kasım–Aralık 1918 | Musul, Boğazlar, İstanbul ve Çukurova'nın işgali |
| | Şubat–Nisan 1919 | Antep, Maraş, Urfa (İngiliz); Antalya (İtalyan); Kars (Ermeni) |
| | 15 Mayıs 1919 | İzmir'in işgali, Hasan Tahsin'in ilk kurşunu |
| **Hazırlık Dönemi** | 19 Mayıs 1919 | Mustafa Kemal Paşa'nın Samsun'a çıkışı (haritada yol çizgisi) |
| | 22 Haziran 1919 | Amasya Genelgesi |
| | Temmuz–Eylül 1919 | Erzurum ve Sivas kongreleri |
| | 1919–1921 | Güney Cephesi: Maraş, Antep, Urfa direnişi |
| | 27 Aralık 1919 – 16 Mart 1920 | Heyet-i Temsiliye Ankara'da, Misak-ı Millî, İstanbul'un resmen işgali |
| **Savaşlar Dönemi** | 23 Nisan 1920 | TBMM'nin açılışı (başkent yıldızı Ankara'ya geçer) |
| | Haziran–Temmuz 1920 | Yunan yaz taarruzu: Bursa, Balıkesir, Uşak, Doğu Trakya |
| | 10 Ağustos 1920 | Sevr Antlaşması (paylaşım planı haritada ayrıca gösterilir) |
| | Eylül–Aralık 1920 | Doğu Cephesi: Sarıkamış, Kars, Gümrü Antlaşması |
| | Ocak / Mart–Nisan 1921 | I. ve II. İnönü savaşları |
| | Temmuz 1921 | Kütahya–Eskişehir savaşları, Sakarya'nın doğusuna çekiliş |
| | 23 Ağustos – 13 Eylül 1921 | Sakarya Meydan Muharebesi |
| | Ekim 1921 | Ankara Antlaşması (Fransa) ve Kars Antlaşması |
| | 26–30 Ağustos 1922 | Büyük Taarruz, Başkomutanlık Meydan Muharebesi |
| | 9 Eylül 1922 | İzmir'in kurtuluşu |
| **Barış ve Cumhuriyet** | 11 Ekim 1922 | Mudanya Ateşkesi, Doğu Trakya; 1 Kasım 1922'de saltanatın kaldırılması |
| | 24 Temmuz 1923 | Lozan Barış Antlaşması; 6 Ekim 1923'te İstanbul'un kurtuluşu |
| | 29 Ekim 1923 | Cumhuriyet'in ilanı |

Haritada Türk/TBMM denetimindeki topraklar (kırmızı) ile Yunan (mavi), İngiliz (mor),
Fransız (yeşil-mavi), İtalyan (yeşil) işgal bölgeleri ve doğudaki Ermeni denetimi
(turuncu) ayrı renklerle gösterilir. İşgal bölgeleri dalga gibi yayılır, kurtarılan
bölgeler altın renginde parlayarak kırmızıya döner. Oklar taarruzları, kesikli altın
çizgi Mustafa Kemal Paşa'nın Samsun → Havza → Amasya → Erzurum → Sivas → Ankara yolunu
gösterir. Ekranda tarih, dönem adı (dört aşama), bilgi kartı, lejant ve zaman çizgisi
bulunur.

## Ses

* **Seslendirme:** [Piper TTS](https://github.com/rhasspy/piper) ile yerel olarak
  sentezlendi; Türkçe `tr_TR-fahrettin-medium` sesi.
* **Müzik:** Tamamen kodla (NumPy) sentezlendi. İşgal yıllarında Re Hicaz makamında
  kasvetli bordun ve titrek yaylılar; Samsun'dan itibaren ney melodisi, çello
  ostinatosu ve mehter usulünde davul (savaşlar ilerledikçe güçlenir, Sevr'de susar);
  Mudanya'dan sonra Re majöre geçen zafer ve Cumhuriyet temaları.
* **Efektler:** Savaşlarda kös ve kılıç sesleri, işgallerde koyu kös, önemli olaylarda
  zil, taarruz oklarında rüzgâr sesi. Müzik konuşma sırasında otomatik kısılır;
  son miks −16 LUFS'a normalize edilir.

## Yeniden üretme

```bash
pip install -r requirements.txt      # ffmpeg de gerekli
./fetch_assets.sh                     # harita verisi, fontlar, Türkçe ses modeli
python3 src/build.py                  # → output/kurtulus_savasi_1918_1923.mp4
python3 src/build.py --preview 20,114.5,229   # belirli saniyelerden PNG önizleme
```

## Dosya yapısı

| Dosya | Görev |
|---|---|
| `src/story.py` | Senaryo: seslendirme metinleri, tarihler, olay işaretleri, oklar, bilgi kartları, kamera, etiketler |
| `src/territories.py` | Dönemlere göre Türk toprakları ve işgal bölgeleri (Sevr planı dahil) |
| `src/sdf.py` | Bölgeleri işaretli mesafe alanına (SDF) çevirir; yumuşak geçişler için |
| `src/geo.py` | Mercator projeksiyonu, Natural Earth kara/göl/nehir/ülke katmanları |
| `src/tts.py` | Piper ile seslendirme ve kelime zamanlaması |
| `src/timeline.py` | Seslendirme sürelerinden mutlak zaman çizelgesi |
| `src/render.py` | Kare çizimi (harita + arayüz + oklar) ve paralel H.264 kodlama |
| `src/audio.py` | Müzik/efekt sentezi ve miksaj |
| `src/build.py` | Tüm üretim hattı |

## Kaynaklar ve notlar

* Kıyı şeritleri, göller, nehirler ve ülke sınırları: [Natural Earth](https://www.naturalearthdata.com/) (kamu malı).
* Fontlar: Cinzel ve EB Garamond (SIL Open Font License).
* İşgal bölgeleri ve cephe hatları belgesel ölçeğinde yaklaşık olarak elle çizilmiştir;
  kesin sınırlar için akademik atlaslara başvurulmalıdır. Türkiye sınırı olarak bugünkü
  sınırlar kullanılmış, Hatay 1921'den sonra Fransız mandası, Musul ise İngiliz
  denetiminde gösterilmiştir.
