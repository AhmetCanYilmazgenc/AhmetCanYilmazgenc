# Osmanlı İmparatorluğu: Kuruluştan En Geniş Sınırlara (1299–1683)

Osmanlı Beyliği'nin 1299'da Söğüt'te kuruluşundan 1683'teki en geniş sınırlarına
kadar geçen dönemi **animasyonlu bir harita** üzerinde anlatan, önemli savaşlar
hakkında bilgi veren ve **tamamen sentezlenmiş ses bandına** (Türkçe seslendirme +
müzik + efektler) sahip bir video.

**Çıktı:** [`output/osmanli_1299_1683.mp4`](output/osmanli_1299_1683.mp4) — 1920×1080, 30 fps, yaklaşık 78 saniye.

> İstenen süre 40 saniyeydi. 16 savaşa/fethe ait bilgi kartlarının okunabilmesi
> için süre ~78 saniyeye çıkarıldı (her kart en az ~2,5 saniye ekranda kalıyor).
> Daha kısa bir sürüm için `src/story.py` içindeki metinleri kısaltmak yeterlidir.

## İçerik

| Yıl | Olay | Hükümdar / Komutan |
|---|---|---|
| 1299 | Osmanlı Beyliği'nin kuruluşu (Söğüt) | Osman Gazi |
| 1302 | Koyunhisar Savaşı | Osman Gazi ⚔ Bizans |
| 1326 | Bursa'nın fethi – ilk başkent | Orhan Gazi |
| 1354 | Gelibolu – Rumeli'ye geçiş, Edirne | Orhan Gazi, Süleyman Paşa |
| 1389 | I. Kosova Savaşı | I. Murad ⚔ Sırp–Balkan ittifakı |
| 1396 | Niğbolu Savaşı | Yıldırım Bayezid ⚔ Haçlılar |
| 1402 | Ankara Savaşı (yenilgi) – Fetret Devri | Yıldırım Bayezid ⚔ Timur |
| 1444 | Varna Savaşı | II. Murad ⚔ Haçlılar |
| 1453 | İstanbul'un fethi | Fatih Sultan Mehmed ⚔ Bizans |
| 1514 | Çaldıran Savaşı | Yavuz Sultan Selim ⚔ Safeviler |
| 1516–17 | Mercidabık ve Ridaniye | Yavuz Sultan Selim ⚔ Memlükler |
| 1526 | Mohaç Meydan Muharebesi | Kanuni Sultan Süleyman ⚔ Macar Krallığı |
| 1538 | Preveze Deniz Savaşı | Barbaros Hayreddin Paşa ⚔ Haçlı donanması |
| 1669–72 | Girit (Kandiye) ve Kamaniçe'nin fethi | IV. Mehmed, Köprülüler |
| 1683 | En geniş sınırlar; II. Viyana Kuşatması (yenilgi) | Merzifonlu Kara Mustafa Paşa |

Harita; doğrudan Osmanlı topraklarını (kırmızı), bağlı/haraçgüzar devletleri
(Eflak, Boğdan, Erdel, Kırım Hanlığı… — taralı) ve savaş noktalarını (altın: zafer /
fetih, gümüş: yenilgi) gösterir. Fetihler haritada dalga gibi yayılır, kayıplar geri
çekilir. Ekranda yıl sayacı, dönem adı (Kuruluş / Yükselme / Duraklama), bilgi kartı
ve zaman çizgisi bulunur.

## Ses

* **Seslendirme:** [Piper TTS](https://github.com/rhasspy/piper) ile yerel olarak
  sentezlendi; Türkçe `tr_TR-fahrettin-medium` sesi (CC0 lisanslı veri seti).
* **Müzik:** Tamamen kodla (NumPy) sentezlendi — Re Hicaz makamında ney benzeri
  melodi, bordun ve çello ostinatosu, mehter usulünde davul ("düm – tek – tek – düm –
  tek").
* **Efektler:** Savaş anlarında kös vuruşu ve kılıç şakırtısı, zirvede zil, sahne
  geçişlerinde rüzgâr sesi. Müzik konuşma sırasında otomatik kısılır (ducking);
  son miks EBU R128'e göre −16 LUFS'a normalize edilir.

## Yeniden üretme

```bash
pip install -r requirements.txt      # ffmpeg de gerekli
./fetch_assets.sh                     # harita verisi, fontlar, Türkçe ses modeli
python3 src/build.py                  # → output/osmanli_1299_1683.mp4
python3 src/build.py --preview 8,39.6,66   # belirli saniyelerden PNG önizleme
```

## Dosya yapısı

| Dosya | Görev |
|---|---|
| `src/story.py` | Senaryo: seslendirme metinleri, olaylar, bilgi kartları, kamera, etiketler |
| `src/territories.py` | 14 dönem için Osmanlı ve bağlı devlet sınırları (çokgenler + adalar) |
| `src/sdf.py` | Sınırları işaretli mesafe alanına (SDF) çevirir; yumuşak geçişler için |
| `src/geo.py` | Mercator projeksiyonu, Natural Earth kara/göl/nehir katmanları |
| `src/tts.py` | Piper ile seslendirme ve kelime zamanlaması |
| `src/timeline.py` | Seslendirme sürelerinden mutlak zaman çizelgesi |
| `src/render.py` | Kare çizimi (harita + arayüz) ve paralel H.264 kodlama |
| `src/audio.py` | Müzik/efekt sentezi ve miksaj |
| `src/build.py` | Tüm üretim hattı |

## Kaynaklar ve notlar

* Kıyı şeritleri, göller, nehirler: [Natural Earth](https://www.naturalearthdata.com/) (kamu malı).
* Fontlar: Cinzel ve EB Garamond (SIL Open Font License).
* Tarihi sınırlar belgesel ölçeğinde yaklaşık olarak elle çizilmiştir; kesin sınır
  çizgileri için akademik atlaslara başvurulmalıdır. 1683 haritasında, 1635'te
  kaybedilen Yemen ve 1670'te kaybedilen Lahsa gösterilmez.
