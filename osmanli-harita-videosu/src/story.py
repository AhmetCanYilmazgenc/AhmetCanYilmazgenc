"""Videonun senaryosu: sahneler, seslendirme metinleri, olaylar, etiketler.

Seslendirme metinlerinde sayılar TTS'nin doğru okuması için yazıyla verilir;
ekranda ise rakamla gösterilir.
"""

FULL_VIEW = (26.0, 33.8, 84.0)  # (boylam, enlem, görünür genişlik°)

# Savaş / fetih işaretleri:  id -> (etiket, boylam, enlem, sonuç)
#   sonuç: "win" zafer, "loss" yenilgi, "siege" fetih/kuşatma
BATTLES = {
    "koyunhisar": ("Koyunhisar 1302", 29.78, 40.62, "win"),
    "bursa": ("Bursa 1326", 29.06, 40.19, "siege"),
    "gelibolu": ("Gelibolu 1354", 26.67, 40.41, "siege"),
    "kosova": ("Kosova 1389", 21.10, 42.70, "win"),
    "nigbolu": ("Niğbolu 1396", 24.90, 43.70, "win"),
    "ankara": ("Ankara 1402", 33.05, 40.10, "loss"),
    "varna": ("Varna 1444", 27.85, 43.22, "win"),
    "istanbul": ("İstanbul 1453", 28.97, 41.01, "siege"),
    "caldiran": ("Çaldıran 1514", 43.90, 39.15, "win"),
    "mercidabik": ("Mercidabık 1516", 37.27, 36.53, "win"),
    "ridaniye": ("Ridaniye 1517", 31.30, 30.08, "win"),
    "mohac": ("Mohaç 1526", 18.68, 45.94, "win"),
    "preveze": ("Preveze 1538", 20.55, 38.90, "win"),
    "kandiye": ("Kandiye 1669", 25.14, 35.34, "siege"),
    "kamanice": ("Kamaniçe 1672", 26.58, 48.68, "siege"),
    "viyana": ("Viyana 1683", 16.37, 48.21, "loss"),
}


def card(tag, title, sub, desc, result="win"):
    return dict(tag=tag, title=title, sub=sub, desc=desc, result=result)


SCENES = [
    dict(id="intro",
         text="Bir uç beyliğinden üç kıtaya uzanan bir cihan devleti: Osmanlı.",
         cam=FULL_VIEW, lead=0.9, tail=0.5, min_dur=4.6, title=True, events=[]),

    dict(id="kurulus",
         text="Bin iki yüz doksan dokuzda Osman Gazi, Söğüt'te küçük bir beylik kurdu.",
         cam=(29.95, 40.05, 5.0), cam_dur=2.6, lead=0.5,
         events=[dict(anchor="Bin iki yüz", year=1299,
                      card=card("KURULUŞ · 1299", "Osmanlı Beyliği", "Osman Gazi · Söğüt",
                                "Bizans sınırında, Söğüt ve Domaniç çevresinde küçük bir uç "
                                "beyliği olarak kuruldu.", "found")),
                 dict(anchor="Osman", terr="1299", terr_dur=1.8, capital="Söğüt")]),

    dict(id="bursa",
         text="Koyunhisar'da Bizans ordusu bozguna uğratıldı. Bin üç yüz yirmi altıda Bursa "
              "fethedildi ve başkent oldu.",
         cam=(29.55, 40.28, 6.6),
         events=[dict(anchor="Koyunhisar", year=1302, battle="koyunhisar",
                      card=card("SAVAŞ · 1302", "Koyunhisar Savaşı", "Osman Gazi ⚔ Bizans",
                                "Osmanlıların Bizans ordusuna karşı kazandığı ilk büyük "
                                "meydan zaferi.")),
                 dict(anchor="Bin üç yüz", year=1326,
                      card=card("FETİH · 1326", "Bursa'nın Fethi", "Orhan Gazi",
                                "Uzun bir kuşatmanın ardından alınan Bursa, devletin ilk büyük "
                                "başkenti oldu.", "siege")),
                 dict(anchor="Bursa", terr="1326", battle="bursa", capital="Bursa")]),

    dict(id="rumeli",
         text="Gelibolu'dan Rumeli'ye geçildi, Edirne alındı.",
         cam=(27.7, 40.85, 11.0),
         events=[dict(anchor="Gelibolu", year=1354, terr="1362", terr_dur=2.6, battle="gelibolu",
                      card=card("FETİH · 1354", "Rumeli'ye Geçiş", "Orhan Gazi · Süleyman Paşa",
                                "Gelibolu'nun alınmasıyla Balkanlara geçildi; ardından Edirne "
                                "fethedilerek yeni başkent yapıldı.", "siege")),
                 dict(anchor="Edirne", capital="Edirne")]),

    dict(id="balkan",
         text="Bin üç yüz seksen dokuzda Kosova'da Balkan ittifakı yenildi. Yıldırım Bayezid ise "
              "Niğbolu'da Haçlı ordusunu dağıttı.",
         cam=(25.0, 42.1, 17.0),
         events=[dict(anchor="Bin üç yüz", year=1389,
                      card=card("SAVAŞ · 1389", "I. Kosova Savaşı", "I. Murad ⚔ Sırp–Balkan ittifakı",
                                "Balkanlarda Osmanlı hakimiyeti pekişti; Sultan I. Murad savaş "
                                "alanında şehit düştü.")),
                 dict(anchor="Kosova", terr="1389", terr_dur=1.8, battle="kosova"),
                 dict(anchor="Yıldırım", year=1396,
                      card=card("SAVAŞ · 1396", "Niğbolu Savaşı", "Yıldırım Bayezid ⚔ Haçlı ordusu",
                                "Macar Kralı Sigismund'un önderlik ettiği büyük Haçlı ordusu "
                                "bozguna uğratıldı.")),
                 dict(anchor="Niğbolu", terr="1400", terr_dur=2.4, battle="nigbolu")]),

    dict(id="ankara",
         text="Ancak bin dört yüz ikide Ankara'da Timur'a yenilen devlet, Fetret Devri'ne sürüklendi.",
         cam=(30.0, 40.6, 22.0),
         events=[dict(anchor="Ancak", year=1402,
                      card=card("YENİLGİ · 1402", "Ankara Savaşı", "Yıldırım Bayezid ⚔ Timur",
                                "Sultan esir düştü; Anadolu beylikleri yeniden kuruldu ve Fetret "
                                "Devri (1402–1413) başladı.", "loss")),
                 dict(anchor="Ankara", terr="1403", terr_dur=2.6, battle="ankara")]),

    dict(id="varna",
         text="Toparlanan Osmanlılar, bin dört yüz kırk dörtte Varna'da yeni bir Haçlı ordusunu yendi.",
         cam=(27.2, 41.6, 20.0),
         events=[dict(anchor="Toparlanan", year=1444, terr="1451", terr_dur=2.6,
                      card=card("SAVAŞ · 1444", "Varna Savaşı", "II. Murad ⚔ Haçlılar",
                                "Macar-Leh Haçlı ordusu yenildi, Kral Vladislav savaşta öldü; "
                                "Balkanlar Osmanlı'da kaldı.")),
                 dict(anchor="Varna", battle="varna")]),

    dict(id="istanbul",
         text="Bin dört yüz elli üçte Fatih Sultan Mehmed İstanbul'u fethetti. "
              "Bir çağ kapandı, yeni bir çağ açıldı.",
         cam=(28.95, 41.05, 3.4), cam_dur=2.2,
         events=[dict(anchor="Bin dört yüz", year=1453,
                      card=card("FETİH · 1453", "İstanbul'un Fethi", "Fatih Sultan Mehmed ⚔ Bizans",
                                "Bin yılı aşkın Bizans İmparatorluğu sona erdi; İstanbul yeni "
                                "başkent oldu.", "siege")),
                 dict(anchor="İstanbul", terr="1453", terr_dur=1.4, battle="istanbul",
                      capital="İstanbul"),
                 dict(anchor="Bir çağ", year=1481, terr="1481", terr_dur=2.6,
                      cam=(31.0, 42.3, 30.0), cam_dur=2.2,
                      card=card("GENİŞLEME · 1453–1481", "Fatih Dönemi",
                                "Sırbistan · Mora · Trabzon · Bosna · Karaman",
                                "Anadolu ve Balkanlar'da birlik büyük ölçüde sağlandı; Kırım "
                                "Hanlığı Osmanlı'ya bağlandı.", "found"))]),

    dict(id="yavuz",
         text="Yavuz Sultan Selim, Çaldıran'da Safevileri yendi. Mercidabık ve Ridaniye "
              "zaferleriyle Suriye, Mısır ve kutsal topraklar alındı.",
         cam=(38.0, 30.0, 46.0),
         events=[dict(anchor="Yavuz", year=1514,
                      card=card("SAVAŞ · 1514", "Çaldıran Savaşı", "Yavuz Sultan Selim ⚔ Safeviler",
                                "Doğu Anadolu'nun yolu açıldı; Diyarbakır ve çevresi Osmanlı'ya "
                                "katıldı.")),
                 dict(anchor="Çaldıran", terr="1515", terr_dur=1.4, battle="caldiran"),
                 dict(anchor="Mercidabık", year=1516, terr="1520", terr_dur=3.2, battle="mercidabik",
                      card=card("SAVAŞLAR · 1516–1517", "Mercidabık ve Ridaniye",
                                "Yavuz Sultan Selim ⚔ Memlükler",
                                "Memlük Devleti yıkıldı; Suriye, Mısır ve Hicaz alındı, halifelik "
                                "Osmanlı'ya geçti.")),
                 dict(anchor="Ridaniye", year=1517, battle="ridaniye")]),

    dict(id="mohac",
         text="Kanuni Sultan Süleyman, Mohaç'ta Macar ordusunu iki saatte dağıttı. Belgrad, Rodos, "
              "Bağdat ve Budin birer birer alındı.",
         cam=(28.5, 40.0, 46.0),
         events=[dict(anchor="Kanuni", year=1526,
                      card=card("SAVAŞ · 1526", "Mohaç Meydan Muharebesi",
                                "Kanuni Sultan Süleyman ⚔ Macar Krallığı",
                                "Macar ordusu yaklaşık iki saatte yok edildi; Orta Avrupa'nın "
                                "kapıları açıldı.")),
                 dict(anchor="Mohaç", battle="mohac"),
                 dict(anchor="Belgrad", year=1541, terr="1541", terr_dur=2.8,
                      card=card("GENİŞLEME · 1521–1541", "Kanuni'nin Seferleri",
                                "Belgrad · Rodos · Bağdat · Budin",
                                "Seferlerle Macaristan'dan Irak'a uzanan geniş topraklar ele "
                                "geçirildi.", "found"))]),

    dict(id="preveze",
         text="Preveze'de Barbaros Hayreddin Paşa'nın zaferiyle Akdeniz bir Türk gölüne döndü.",
         cam=(24.0, 34.5, 64.0),
         events=[dict(anchor="Preveze", year=1538, battle="preveze",
                      card=card("DENİZ SAVAŞI · 1538", "Preveze Deniz Savaşı",
                                "Barbaros Hayreddin Paşa ⚔ Haçlı donanması",
                                "Akdeniz'de Osmanlı deniz üstünlüğü kuruldu; Cezayir, "
                                "Trablusgarp ve Yemen eyalet oldu.")),
                 dict(anchor="Akdeniz", year=1566, terr="1566", terr_dur=2.6)]),

    dict(id="zirve",
         text="Köprülüler döneminde Girit ve Kamaniçe de fethedildi. Bin altı yüz seksen üçte "
              "imparatorluk, üç kıtaya yayılan en geniş sınırlarına ulaştı.",
         cam=FULL_VIEW, cam_dur=2.4,
         events=[dict(anchor="Köprülüler", year=1669,
                      card=card("FETİHLER · 1669–1672", "Girit ve Kamaniçe",
                                "IV. Mehmed · Köprülüler dönemi",
                                "21 yıllık Kandiye kuşatması sona erdi; Bucaş Antlaşması'yla "
                                "Podolya da Osmanlı'ya geçti.", "siege")),
                 dict(anchor="Girit", terr="1683", terr_dur=3.8, battle="kandiye"),
                 dict(anchor="Kamaniçe", year=1672, battle="kamanice"),
                 dict(anchor="Bin altı yüz", year=1683, peak=True,
                      card=card("ZİRVE · 1683", "En Geniş Sınırlar",
                                "Cezayir'den Basra'ya, Budin'den Hicaz'a",
                                "Üç kıtaya yayılan imparatorluk yaklaşık 5,2 milyon km² ile "
                                "toprak bakımından zirvesine ulaştı.", "found"))]),

    dict(id="viyana",
         text="Aynı yıl Viyana önlerinde başlayan kuşatma ise bu büyük yükselişin sonu oldu.",
         cam=(21.0, 42.8, 34.0), cam_dur=2.0, tail=0.6, outro=3.8,
         events=[dict(anchor="Aynı yıl",
                      card=card("KUŞATMA · 1683", "II. Viyana Kuşatması",
                                "Merzifonlu Kara Mustafa Paşa ⚔ Habsburg–Leh",
                                "Başarısız kuşatma Osmanlı'nın Avrupa'daki ilerleyişini durdurdu; "
                                "Gerileme Dönemi başladı.", "loss")),
                 dict(anchor="Viyana", battle="viyana"),
                 dict(anchor="@end", cam=FULL_VIEW, cam_dur=2.6, outro=True)]),
]

# ------------------------------------------------------------------ Etiketler
# (ad, boylam, enlem, [yıl aralıkları], azami görünüm genişliği, önem)
CITIES = [
    ("Söğüt", 30.18, 40.02, [(1200, 2000)], 16, 2),
    ("Bilecik", 29.98, 40.14, [(1200, 2000)], 7.5, 1),
    ("İnegöl", 29.51, 40.08, [(1200, 2000)], 7.5, 1),
    ("Yenişehir", 29.65, 40.26, [(1200, 2000)], 7.5, 1),
    ("Eskişehir", 30.52, 39.78, [(1200, 2000)], 9, 1),
    ("Bursa", 29.06, 40.19, [(1200, 2000)], 30, 2),
    ("İznik", 29.72, 40.43, [(1200, 2000)], 10, 1),
    ("İzmit", 29.92, 40.77, [(1200, 2000)], 12, 1),
    ("Gelibolu", 26.67, 40.41, [(1200, 2000)], 13, 1),
    ("Edirne", 26.56, 41.68, [(1200, 2000)], 32, 2),
    ("Konstantinopolis", 28.97, 41.01, [(1200, 2000)], 40, 2),
    ("İstanbul", 28.97, 41.01, [(1200, 2000)], 999, 3),
    ("Ankara", 32.86, 39.93, [(1200, 2000)], 34, 1),
    ("Konya", 32.49, 37.87, [(1200, 2000)], 34, 1),
    ("Selanik", 22.94, 40.64, [(1200, 2000)], 26, 1),
    ("Sofya", 23.32, 42.70, [(1200, 2000)], 24, 1),
    ("Belgrad", 20.46, 44.82, [(1200, 2000)], 60, 1),
    ("Budin", 19.04, 47.50, [(1200, 2000)], 999, 2),
    ("Viyana", 16.37, 48.21, [(1200, 2000)], 999, 2),
    ("Atina", 23.73, 37.98, [(1200, 2000)], 34, 1),
    ("Trabzon", 39.72, 41.00, [(1200, 2000)], 46, 1),
    ("Tebriz", 46.29, 38.08, [(1200, 2000)], 70, 1),
    ("Halep", 37.16, 36.20, [(1200, 2000)], 50, 1),
    ("Şam", 36.29, 33.51, [(1200, 2000)], 999, 2),
    ("Kudüs", 35.23, 31.78, [(1200, 2000)], 50, 1),
    ("Kahire", 31.24, 30.04, [(1200, 2000)], 999, 2),
    ("Mekke", 39.83, 21.42, [(1200, 2000)], 999, 2),
    ("Medine", 39.61, 24.47, [(1200, 2000)], 70, 1),
    ("Bağdat", 44.37, 33.31, [(1200, 2000)], 999, 2),
    ("Basra", 47.81, 30.51, [(1200, 2000)], 999, 1),
    ("Cezayir", 3.06, 36.75, [(1200, 2000)], 999, 2),
    ("Tunus", 10.18, 36.80, [(1200, 2000)], 999, 1),
    ("Trablusgarp", 13.18, 32.89, [(1200, 2000)], 999, 1),
    ("Kefe", 35.38, 45.03, [(1200, 2000)], 50, 1),
    ("Venedik", 12.33, 45.44, [(1200, 2000)], 70, 1),
    ("Roma", 12.50, 41.90, [(1200, 2000)], 60, 1),
]

# (metin, boylam, enlem, [yıl aralıkları], (min_w, max_w))
RIVALS = [
    ("BİZANS", 29.45, 40.97, [(1200, 1330)], (0, 9)),
    ("BİZANS", 28.55, 41.35, [(1330, 1453)], (2.5, 16)),
    ("BİZANS", 27.20, 41.25, [(1330, 1360)], (9, 16)),
    ("GERMİYAN", 29.90, 39.30, [(1200, 1390)], (0, 14)),
    ("KARESİ", 27.70, 39.70, [(1200, 1345)], (5, 14)),
    ("KARAMANOĞULLARI", 33.20, 37.45, [(1200, 1397), (1402, 1468)], (14, 40)),
    ("SIRBİSTAN", 20.70, 43.70, [(1200, 1459)], (14, 40)),
    ("BULGARİSTAN", 25.30, 43.25, [(1200, 1393)], (14, 40)),
    ("MACARİSTAN", 19.90, 46.90, [(1200, 1526)], (15, 60)),
    ("TİMUR", 38.80, 38.70, [(1399, 1406)], (15, 40)),
    ("AKKOYUNLU", 42.30, 38.40, [(1453, 1505)], (20, 50)),
    ("MEMLÜKLER", 32.80, 27.20, [(1250, 1517)], (24, 999)),
    ("SAFEVİLER", 50.00, 34.20, [(1501, 2000)], (30, 999)),
    ("HABSBURG", 11.50, 47.00, [(1526, 2000)], (30, 999)),
    ("LEHİSTAN", 22.00, 50.60, [(1300, 2000)], (30, 999)),
    ("İSPANYA", -4.00, 40.00, [(1492, 2000)], (60, 999)),
    ("FAS", -5.50, 32.20, [(1500, 2000)], (60, 999)),
    ("KIRIM HANLIĞI", 34.80, 46.45, [(1475, 2000)], (18, 70)),
    ("EFLAK", 25.00, 44.55, [(1400, 2000)], (12, 50)),
    ("BOĞDAN", 27.20, 47.10, [(1456, 2000)], (12, 50)),
    ("ERDEL", 24.20, 46.60, [(1541, 2000)], (20, 60)),
]

# (metin, boylam, enlem, (min_w, max_w), boyut)
SEAS = [
    ("Karadeniz", 34.0, 43.3, (8, 999), 1.0),
    ("Akdeniz", 18.5, 34.3, (35, 999), 1.15),
    ("Akdeniz", 30.0, 34.4, (14, 35), 1.0),
    ("Ege Denizi", 25.2, 38.9, (9, 40), 0.85),
    ("Marmara Denizi", 28.15, 40.73, (2.5, 13), 0.8),
    ("Hazar Denizi", 50.8, 42.0, (25, 999), 0.9),
    ("Kızıldeniz", 37.6, 21.5, (30, 999), 0.85),
    ("Basra Körfezi", 51.6, 27.0, (40, 999), 0.8),
    ("Adriyatik", 15.6, 42.7, (20, 999), 0.8),
    ("Azak Denizi", 36.7, 46.1, (15, 60), 0.7),
    ("Atlas Okyanusu", -11.5, 37.5, (70, 999), 0.9),
]

ERAS = [(1299, 1453, "KURULUŞ DÖNEMİ"), (1453, 1579, "YÜKSELME DÖNEMİ"),
        (1579, 1700, "DURAKLAMA DÖNEMİ")]
