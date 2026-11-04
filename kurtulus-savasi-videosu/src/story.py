"""Videonun senaryosu: sahneler, seslendirme metinleri, olaylar, etiketler.

Seslendirme metinlerinde sayılar TTS'nin doğru okuması için yazıyla verilir;
ekranda ise rakamla gösterilir. Tarihler (yıl, ay, gün) olarak verilir.
"""

FULL_VIEW = (34.6, 38.9, 24.5)   # (boylam, enlem, görünür genişlik°)
WEST = (28.6, 39.0, 8.5)
EAST = (42.4, 40.1, 8.4)
SOUTH = (36.6, 37.2, 7.5)

AYLAR = ["OCAK", "ŞUBAT", "MART", "NİSAN", "MAYIS", "HAZİRAN", "TEMMUZ", "AĞUSTOS", "EYLÜL",
         "EKİM", "KASIM", "ARALIK"]

# Harita işaretleri:  id -> (etiket, boylam, enlem, tür)
#   tür: "win" Türk zaferi, "loss" Türk yenilgisi, "occ" işgal, "event" önemli olay
MARKERS = {
    "mondros": ("Mondros · 30 Ekim 1918", 25.27, 39.87, "event"),
    "musul": ("Musul · Kasım 1918", 43.13, 36.34, "occ"),
    "istanbul18": ("İstanbul · 13 Kasım 1918", 28.97, 41.01, "occ"),
    "adana": ("Adana · Aralık 1918", 35.32, 37.00, "occ"),
    "antalya": ("Antalya · Mart 1919", 30.71, 36.89, "occ"),
    "kars19": ("Kars · Nisan 1919", 43.10, 40.60, "occ"),
    "izmir19": ("İzmir · 15 Mayıs 1919", 27.14, 38.42, "occ"),
    "samsun": ("Samsun · 19 Mayıs 1919", 36.33, 41.29, "event"),
    "amasya": ("Amasya · 22 Haziran 1919", 35.83, 40.65, "event"),
    "erzurum": ("Erzurum Kongresi", 41.27, 39.90, "event"),
    "sivas": ("Sivas Kongresi", 37.02, 39.75, "event"),
    "maras": ("Maraş · Şubat 1920", 36.94, 37.58, "win"),
    "antep": ("Antep · 1920–21", 37.38, 37.07, "win"),
    "urfa": ("Urfa · Nisan 1920", 38.79, 37.16, "win"),
    "ankara19": ("Ankara · 27 Aralık 1919", 32.86, 39.93, "event"),
    "istanbul20": ("İstanbul · 16 Mart 1920", 28.97, 41.01, "occ"),
    "bursa20": ("Bursa · 8 Temmuz 1920", 29.06, 40.19, "occ"),
    "edirne20": ("Edirne · 25 Temmuz 1920", 26.56, 41.68, "occ"),
    "sarikamis": ("Sarıkamış · 29 Eylül 1920", 42.59, 40.33, "win"),
    "kars20": ("Kars · 30 Ekim 1920", 43.10, 40.60, "win"),
    "gumru": ("Gümrü · 3 Aralık 1920", 43.85, 40.79, "event"),
    "inonu1": ("I. İnönü · Ocak 1921", 30.14, 39.82, "win"),
    "inonu2": ("II. İnönü · Nisan 1921", 30.05, 39.70, "win"),
    "kutahya": ("Kütahya–Eskişehir · 1921", 30.30, 39.55, "loss"),
    "sakarya": ("Sakarya · 1921", 31.95, 39.55, "win"),
    "ankara21": ("Ankara Antlaşması", 32.86, 39.93, "event"),
    "kocatepe": ("Kocatepe · 26 Ağustos 1922", 30.43, 38.62, "win"),
    "dumlupinar": ("Dumlupınar · 30 Ağustos 1922", 29.98, 38.85, "win"),
    "izmir22": ("İzmir · 9 Eylül 1922", 27.14, 38.42, "win"),
    "mudanya": ("Mudanya · 11 Ekim 1922", 28.88, 40.38, "event"),
    "istanbul23": ("İstanbul · 6 Ekim 1923", 28.97, 41.01, "win"),
}


def card(tag, title, sub, desc, result="event"):
    return dict(tag=tag, title=title, sub=sub, desc=desc, result=result)


# Oklar: yol (boylam, enlem) listesi, taraf (tr / gr / route), süre
def arrow(path, side, dur=1.6, width=1.0):
    return dict(path=path, side=side, dur=dur, width=width)


IST, SAM, HAV, AMA, TOK, SIV, ERZ, ERC = ((28.98, 41.02), (36.33, 41.29), (35.66, 40.97),
                                         (35.83, 40.65), (36.55, 40.31), (37.02, 39.75),
                                         (41.27, 39.90), (39.49, 39.75))
KAY, KIR, ANK = (35.49, 38.73), (34.17, 39.15), (32.86, 39.93)

SCENES = [
    dict(id="intro",
         text="Bin dokuz yüz on sekiz. Birinci Dünya Savaşı'ndan yenik çıkan Osmanlı Devleti, "
              "tarihinin en karanlık günlerini yaşıyordu.",
         cam=FULL_VIEW, lead=1.0, tail=0.6, min_dur=6.0, title=True,
         events=[dict(anchor="Bin dokuz", date=(1918, 10, None))]),

    dict(id="mondros",
         text="Otuz Ekim'de imzalanan Mondros Ateşkes Antlaşması ile ordular terhis edildi. "
              "Yedinci madde, İtilaf Devletleri'ne güvenliklerini tehdit eden her yeri işgal "
              "etme hakkı tanıyordu.",
         cam=(29.0, 39.9, 12.0), cam_dur=2.4,
         events=[dict(anchor="Otuz Ekim", date=(1918, 10, 30), marker="mondros",
                      card=card("ATEŞKES · 30 EKİM 1918", "Mondros Ateşkes Antlaşması",
                                "Osmanlı Devleti · İtilaf Devletleri",
                                "Limni adasında, Agamemnon zırhlısında imzalandı. Ordu terhis "
                                "edildi; limanlar, demiryolları ve Boğazlar İtilaf denetimine "
                                "geçti.", "loss"))]),

    dict(id="isgal1",
         text="Kasım ayından itibaren İngilizler Musul'u ve Boğazları, Fransızlar ise "
              "Çukurova'yı işgal etti. İtilaf donanması İstanbul önlerine demirledi.",
         cam=FULL_VIEW, cam_dur=2.2,
         events=[dict(anchor="Kasım", date=(1918, 11, None), terr="k1", terr_dur=2.4,
                      card=card("İŞGALLER · KASIM 1918", "İşgaller Başlıyor",
                                "İngiltere · Fransa",
                                "Musul, İskenderun, Çanakkale ve Boğazlar işgal edildi. Halk, "
                                "yurdun dört bir yanında Müdafaa-i Hukuk cemiyetleri kurmaya "
                                "başladı.", "occ")),
                 dict(anchor="Musul", marker="musul"),
                 dict(anchor="Fransızlar", marker="adana", date=(1918, 12, None)),
                 dict(anchor="İtilaf donanması", marker="istanbul18")]),

    dict(id="isgal2",
         text="Bin dokuz yüz on dokuz baharında İngilizler Antep, Maraş ve Urfa'ya girdi. "
              "İtalyanlar Antalya'ya asker çıkardı. Doğuda ise Kars ve çevresi Ermenilere "
              "bırakıldı.",
         cam=(37.0, 38.6, 17.0), cam_dur=2.0,
         events=[dict(anchor="Bin dokuz", date=(1919, 2, None)),
                 dict(anchor="İngilizler", terr="k2a", terr_dur=1.6,
                      card=card("İŞGALLER · 1919", "Anadolu Paylaşılıyor",
                                "İngiltere · İtalya · Fransa · Ermenistan",
                                "Savaş yıllarında yapılan gizli antlaşmalar uygulanmaya "
                                "konuldu; işgal bölgeleri her geçen ay genişledi.", "occ")),
                 dict(anchor="İtalyanlar", date=(1919, 3, 28), terr="k2b", terr_dur=1.6,
                      marker="antalya"),
                 dict(anchor="Doğuda", date=(1919, 4, None), terr="k2c", terr_dur=1.6,
                      marker="kars19")]),

    dict(id="izmir",
         text="On beş Mayıs bin dokuz yüz on dokuzda Yunan ordusu İzmir'e çıktı. Düşmana ilk "
              "kurşunu gazeteci Hasan Tahsin attı. İşgal kısa sürede Manisa, Aydın ve "
              "Ayvalık'a yayıldı.",
         cam=(27.9, 38.6, 6.0), cam_dur=2.2,
         events=[dict(anchor="On beş Mayıs", date=(1919, 5, 15), marker="izmir19",
                      card=card("İŞGAL · 15 MAYIS 1919", "İzmir'in İşgali", "Yunan ordusu",
                                "Paris Barış Konferansı'nın onayıyla İzmir'e çıkan Yunan "
                                "ordusu, Batı Anadolu'yu işgale başladı. Bu olay millî "
                                "direnişin fitilini ateşledi.", "occ")),
                 dict(anchor="Düşmana", card=card(
                     "İLK KURŞUN · 15 MAYIS 1919", "Hasan Tahsin", "Gazeteci · İzmir",
                     "İşgal kuvvetlerine ilk kurşunu atarak şehit düştü; Kuva-yı Milliye "
                     "ruhunun simgesi oldu.", "event")),
                 dict(anchor="İşgal", terr="k3", terr_dur=2.6,
                      arrows=[arrow([(27.14, 38.42), (27.40, 38.60), (27.45, 38.95)], "gr", 1.4, 0.7),
                              arrow([(27.14, 38.42), (27.50, 38.12), (27.84, 37.88)], "gr", 1.4, 0.7),
                              arrow([(27.10, 38.50), (26.95, 38.95), (26.75, 39.28)], "gr", 1.4, 0.7)])]),

    dict(id="samsun",
         text="Dört gün sonra, on dokuz Mayıs'ta Mustafa Kemal Paşa, Bandırma Vapuru ile "
              "Samsun'a çıktı. Millî Mücadele başlamıştı.",
         cam=(32.6, 41.2, 11.5), cam_dur=2.4, era=1,
         events=[dict(anchor="Dört gün", date=(1919, 5, 19),
                      arrows=[arrow([IST, (29.6, 41.45), (31.2, 41.75), (33.2, 42.15),
                                     (35.15, 42.20), (35.90, 41.75), SAM], "route", 4.2)]),
                 dict(anchor="Samsun'a", marker="samsun",
                      card=card("MİLLÎ MÜCADELE · 19 MAYIS 1919", "Samsun'a Çıkış",
                                "Mustafa Kemal Paşa · 9. Ordu Müfettişi",
                                "Bandırma Vapuru ile İstanbul'dan ayrılan Mustafa Kemal, "
                                "Anadolu'da millî direnişi örgütlemeye başladı.", "event"))]),

    dict(id="amasya",
         text="Havza'dan Amasya'ya geçen Mustafa Kemal, yirmi iki Haziran'da yayımladığı "
              "genelgede, milletin bağımsızlığını yine milletin azim ve kararının "
              "kurtaracağını ilan etti.",
         cam=(36.0, 40.85, 4.6), cam_dur=2.0,
         events=[dict(anchor="Havza", date=(1919, 5, 25),
                      arrows=[arrow([SAM, (35.95, 41.18), HAV, (35.75, 40.80), AMA], "route", 3.0)]),
                 dict(anchor="yirmi iki", date=(1919, 6, 22), marker="amasya",
                      card=card("GENELGE · 22 HAZİRAN 1919", "Amasya Genelgesi",
                                "Millî Mücadele'nin ilk belgesi",
                                "“Milletin istiklâlini yine milletin azim ve kararı "
                                "kurtaracaktır.” Sivas'ta ulusal bir kongre toplanmasına "
                                "karar verildi.", "event"))]),

    dict(id="kongreler",
         text="Erzurum Kongresi'nde vatanın bir bütün olduğu ve bölünemeyeceği kabul edildi. "
              "Eylül'de toplanan Sivas Kongresi ise bütün millî cemiyetleri tek çatı altında "
              "birleştirdi.",
         cam=(38.6, 40.1, 9.5), cam_dur=2.2,
         events=[dict(anchor="Erzurum", date=(1919, 7, 23), marker="erzurum",
                      arrows=[arrow([AMA, TOK, SIV, ERC, ERZ], "route", 2.6)],
                      card=card("KONGRE · 23 TEMMUZ – 7 AĞUSTOS 1919", "Erzurum Kongresi",
                                "Doğu illerinin temsilcileri",
                                "Vatan bir bütündür, parçalanamaz. Manda ve himaye kabul "
                                "edilemez. Kuva-yı Milliye'yi etken, millî iradeyi hâkim kılmak "
                                "esastır.", "event")),
                 dict(anchor="Eylül", date=(1919, 9, 4), marker="sivas",
                      arrows=[arrow([ERZ, (40.4, 39.6), ERC, (38.2, 39.55), SIV], "route", 2.2)],
                      card=card("KONGRE · 4–11 EYLÜL 1919", "Sivas Kongresi",
                                "Ulusal kongre · Heyet-i Temsiliye",
                                "Bütün cemiyetler Anadolu ve Rumeli Müdafaa-i Hukuk Cemiyeti "
                                "adıyla birleştirildi; manda fikri kesin olarak reddedildi.",
                                "event"))]),

    dict(id="guney",
         text="Ekim ayında İngilizler, güneydeki işgal bölgelerini Fransızlara bıraktı. Maraş, "
              "Antep ve Urfa halkı, işgale karşı destansı bir direniş başlattı.",
         cam=SOUTH, cam_dur=2.2,
         events=[dict(anchor="Ekim", date=(1919, 11, None), terr="k4", terr_dur=1.8),
                 dict(anchor="Maraş", date=(1920, 2, 12), marker="maras",
                      card=card("GÜNEY CEPHESİ · 1919–1921", "Maraş, Antep ve Urfa",
                                "Kuva-yı Milliye ⚔ Fransız işgal kuvvetleri",
                                "Sütçü İmam, Şahin Bey ve halkın direnişiyle Fransızlar Maraş "
                                "ve Urfa'dan çekildi. Maraş'a Kahraman, Urfa'ya Şanlı, Antep'e "
                                "Gazi unvanı verildi.", "win")),
                 dict(anchor="Antep", marker="antep"),
                 dict(anchor="Urfa", date=(1920, 4, 11), marker="urfa", terr="k5", terr_dur=2.0)]),

    dict(id="ankara",
         text="Mustafa Kemal ve Heyet-i Temsiliye, Aralık'ta Ankara'ya geldi. Son Osmanlı Mebusan Meclisi "
              "Misak-ı Millî'yi kabul edince, İtilaf Devletleri on altı Mart bin dokuz yüz "
              "yirmide İstanbul'u resmen işgal etti.",
         cam=(31.6, 40.2, 9.0), cam_dur=2.2,
         events=[dict(anchor="Mustafa Kemal", date=(1919, 12, 27),
                      arrows=[arrow([SIV, KAY, KIR, ANK], "route", 2.4)]),
                 dict(anchor="Aralık", marker="ankara19"),
                 dict(anchor="Son Osmanlı", date=(1920, 1, 28),
                      card=card("KARAR · 28 OCAK 1920", "Misak-ı Millî",
                                "Son Osmanlı Mebusan Meclisi",
                                "Mondros'ta işgal edilmemiş, Türk çoğunluğun yaşadığı "
                                "topraklar bölünmez bir bütündür. Kapitülasyonlar kabul "
                                "edilemez.", "event")),
                 dict(anchor="on altı Mart", date=(1920, 3, 16), marker="istanbul20",
                      card=card("İŞGAL · 16 MART 1920", "İstanbul'un Resmen İşgali",
                                "İtilaf Devletleri",
                                "Meclis-i Mebusan basıldı, milletvekilleri tutuklanarak Malta'ya "
                                "sürüldü. Mustafa Kemal, Ankara'da yeni bir meclis toplanması "
                                "çağrısı yaptı.", "occ"))]),

    dict(id="tbmm",
         text="Yirmi üç Nisan bin dokuz yüz yirmide Ankara'da Türkiye Büyük Millet Meclisi "
              "açıldı. Millî iradeye dayanan yeni bir devlet doğuyordu.",
         cam=(32.6, 39.6, 8.0), cam_dur=2.0, era=2,
         events=[dict(anchor="Yirmi üç", date=(1920, 4, 23), capital="Ankara",
                      card=card("MECLİS · 23 NİSAN 1920", "TBMM'nin Açılışı",
                                "Başkan: Mustafa Kemal Paşa",
                                "Meclis, yasama ve yürütme yetkilerini kendinde topladı; millî "
                                "egemenliğe dayalı yeni Türk devletinin temelleri atıldı.",
                                "event"))]),

    dict(id="yunan20",
         text="Haziran bin dokuz yüz yirmide Yunan ordusu büyük bir taarruza geçti. Bursa, "
              "Balıkesir, Uşak ve Doğu Trakya işgal edildi.",
         cam=(28.4, 39.7, 8.0), cam_dur=2.2,
         events=[dict(anchor="Haziran", date=(1920, 6, 22),
                      card=card("TAARRUZ · HAZİRAN–TEMMUZ 1920", "Yunan Yaz Taarruzu",
                                "Yunan ordusu ⚔ Kuva-yı Milliye",
                                "Düzensiz birlikler büyük orduya karşı duramadı. Bu yenilgi, "
                                "düzenli ordunun kurulmasını hızlandırdı.", "loss"),
                      arrows=[arrow([(27.50, 38.95), (27.75, 39.40), (28.70, 39.95), (29.06, 40.19)], "gr", 1.8),
                              arrow([(27.20, 39.15), (27.60, 39.45), (27.88, 39.65)], "gr", 1.4),
                              arrow([(28.20, 38.50), (28.80, 38.62), (29.40, 38.68)], "gr", 1.4)]),
                 dict(anchor="Bursa", terr="k6", terr_dur=2.6, marker="bursa20", date=(1920, 7, 8)),
                 dict(anchor="Doğu Trakya", marker="edirne20", date=(1920, 7, 25),
                      arrows=[arrow([(25.60, 41.10), (26.10, 41.30), (26.56, 41.62)], "gr", 1.2)])]),

    dict(id="sevr",
         text="On Ağustos bin dokuz yüz yirmide imzalanan Sevr Antlaşması, Anadolu'yu "
              "paylaştırıyor, Türklere yalnızca küçük bir toprak bırakıyordu. Türkiye Büyük "
              "Millet Meclisi bu antlaşmayı asla tanımadı.",
         cam=FULL_VIEW, cam_dur=2.2, tail=1.0,
         events=[dict(anchor="On Ağustos", date=(1920, 8, 10), terr="sevr", terr_dur=2.8,
                      sevr=True,
                      card=card("ANTLAŞMA · 10 AĞUSTOS 1920", "Sevr Antlaşması",
                                "Osmanlı Hükûmeti · İtilaf Devletleri",
                                "Trakya ve İzmir Yunanistan'a, doğu illeri Ermenistan'a "
                                "verilecek; Boğazlar uluslararası yönetime geçecekti. "
                                "Hiçbir zaman yürürlüğe girmedi.", "loss")),
                 dict(anchor="asla", terr="k6", terr_dur=2.0, sevr_end=True)]),

    dict(id="dogu",
         text="Doğuda Kâzım Karabekir Paşa komutasındaki ordu, Sarıkamış'ı ve otuz Ekim'de "
              "Kars'ı geri aldı. Üç Aralık'ta Gümrü'de imzalanan antlaşma ise Meclis'in "
              "uluslararası alandaki ilk başarısı oldu.",
         cam=EAST, cam_dur=2.4,
         events=[dict(anchor="Doğuda", date=(1920, 9, 28),
                      card=card("DOĞU CEPHESİ · EYLÜL–KASIM 1920", "Kars'ın Kurtuluşu",
                                "Kâzım Karabekir Paşa ⚔ Ermenistan",
                                "Doğu sınırı güvenceye alındı; buradaki birlikler ve silahlar "
                                "Batı Cephesi'ne kaydırılabildi.", "win"),
                      arrows=[arrow([(41.27, 39.90), (41.90, 40.10), (42.55, 40.30)], "tr", 1.4)]),
                 dict(anchor="Sarıkamış", marker="sarikamis"),
                 dict(anchor="otuz Ekim", date=(1920, 10, 30), marker="kars20", terr="k7",
                      terr_dur=2.4,
                      arrows=[arrow([(42.65, 40.36), (42.90, 40.55), (43.08, 40.59)], "tr", 1.0),
                              arrow([(43.15, 40.62), (43.50, 40.72), (43.82, 40.78)], "tr", 1.2)]),
                 dict(anchor="Üç Aralık", date=(1920, 12, 3), marker="gumru",
                      card=card("ANTLAŞMA · 3 ARALIK 1920", "Gümrü Antlaşması",
                                "TBMM · Ermenistan",
                                "TBMM'nin imzaladığı ilk uluslararası antlaşma. Ermenistan, "
                                "Sevr'den vazgeçtiğini kabul etti.", "event"))]),

    dict(id="inonu1",
         text="Düzenli ordu ilk sınavını, Ocak bin dokuz yüz yirmi birde Birinci İnönü "
              "Savaşı'nda verdi. İsmet Paşa komutasındaki birlikler Yunan ilerleyişini durdurdu.",
         cam=(29.9, 39.85, 4.4), cam_dur=2.4,
         events=[dict(anchor="Ocak", date=(1921, 1, 10),
                      arrows=[arrow([(29.20, 40.15), (29.60, 40.00), (30.02, 39.86)], "gr", 1.3)]),
                 dict(anchor="Birinci İnönü", marker="inonu1",
                      card=card("BATI CEPHESİ · 6–10 OCAK 1921", "I. İnönü Savaşı",
                                "İsmet Paşa ⚔ Yunan ordusu",
                                "Düzenli ordunun ilk zaferi. Ardından Teşkilât-ı Esasiye "
                                "Kanunu ve 12 Mart 1921'de İstiklâl Marşı kabul edildi.",
                                "win"))]),

    dict(id="inonu2",
         text="Mart sonunda başlayan İkinci İnönü Savaşı da Türk zaferiyle bitti. Mustafa "
              "Kemal, İsmet Paşa'ya şöyle yazdı: Siz orada yalnız düşmanı değil, milletin "
              "makûs talihini de yendiniz.",
         cam=(30.1, 39.75, 4.8), cam_dur=1.4,
         events=[dict(anchor="Mart sonunda", date=(1921, 3, 23),
                      arrows=[arrow([(29.30, 40.10), (29.70, 39.90), (29.98, 39.74)], "gr", 1.2),
                              arrow([(29.40, 39.05), (29.75, 39.35), (30.00, 39.66)], "gr", 1.2)]),
                 dict(anchor="İkinci İnönü", date=(1921, 4, 1), marker="inonu2",
                      card=card("BATI CEPHESİ · 23 MART – 1 NİSAN 1921", "II. İnönü Savaşı",
                                "İsmet Paşa ⚔ Yunan ordusu",
                                "“Siz orada yalnız düşmanı değil, milletin makûs talihini "
                                "de yendiniz.” İtalyanlar Anadolu'dan çekilmeye başladı.",
                                "win"))]),

    dict(id="kutahya",
         text="Temmuz'da yeniden saldıran Yunan ordusu, Kütahya ve Eskişehir'i ele geçirdi. "
              "Türk ordusu Sakarya Nehri'nin doğusuna çekildi. İtalyanlar ise Anadolu'dan "
              "tamamen ayrıldı.",
         cam=(30.6, 38.9, 9.0), cam_dur=2.0,
         events=[dict(anchor="Temmuz", date=(1921, 7, 10), marker="kutahya",
                      card=card("BATI CEPHESİ · 10–24 TEMMUZ 1921", "Kütahya–Eskişehir Savaşları",
                                "Türk ordusu ⚔ Yunan ordusu",
                                "Ordunun kurtarılması için Sakarya'nın doğusuna çekilindi. "
                                "Mustafa Kemal, Başkomutanlık Kanunu ile ordunun başına geçti.",
                                "loss"),
                      arrows=[arrow([(29.50, 39.30), (29.80, 39.40), (30.00, 39.42)], "gr", 1.2),
                              arrow([(29.70, 39.95), (30.10, 39.85), (30.50, 39.78)], "gr", 1.2)]),
                 dict(anchor="Kütahya", terr="k9", terr_dur=2.4),
                 dict(anchor="Türk ordusu",
                      arrows=[arrow([(30.80, 39.70), (31.40, 39.62), (32.05, 39.55)], "retreat", 1.6)])]),

    dict(id="sakarya",
         text="Yirmi üç Ağustos'ta başlayan Sakarya Meydan Muharebesi, yirmi iki gün yirmi iki "
              "gece sürdü. Hattı müdafaa yoktur, sathı müdafaa vardır; o satıh bütün vatandır! "
              "Yunan ordusu Polatlı önlerinde durduruldu ve geri çekilmek zorunda kaldı.",
         cam=(31.4, 39.4, 5.2), cam_dur=2.2,
         events=[dict(anchor="Yirmi üç", date=(1921, 8, 23), terr="k10", terr_dur=2.4,
                      arrows=[arrow([(30.70, 39.75), (31.30, 39.70), (31.85, 39.58)], "gr", 1.6),
                              arrow([(30.90, 39.20), (31.40, 39.30), (31.85, 39.45)], "gr", 1.6)]),
                 dict(anchor="Sakarya", marker="sakarya",
                      card=card("BATI CEPHESİ · 23 AĞUSTOS – 13 EYLÜL 1921",
                                "Sakarya Meydan Muharebesi", "Mustafa Kemal Paşa ⚔ Yunan ordusu",
                                "Savunmadan taarruza geçişin dönüm noktası. TBMM, Mustafa "
                                "Kemal'e Mareşal rütbesi ve Gazi unvanı verdi.", "win")),
                 dict(anchor="Yunan ordusu", date=(1921, 9, 13), terr="k11", terr_dur=2.6,
                      arrows=[arrow([(31.90, 39.55), (31.40, 39.62), (30.95, 39.68)], "tr", 1.6)])]),

    dict(id="diplomasi",
         text="Sakarya Zaferi'nin ardından Fransa ile Ankara Antlaşması imzalandı. Fransızlar "
              "Çukurova ve Antep'ten çekildi; doğu sınırı ise Kars Antlaşması ile kesinleşti.",
         cam=(36.6, 38.4, 15.0), cam_dur=2.2,
         events=[dict(anchor="Ankara Antlaşması", date=(1921, 10, 20), marker="ankara21",
                      card=card("ANTLAŞMA · 20 EKİM 1921", "Ankara Antlaşması",
                                "TBMM · Fransa",
                                "Güney Cephesi kapandı; Hatay özel yönetimle Suriye'de kaldı. "
                                "13 Ekim 1921'deki Kars Antlaşması ile doğu sınırı çizildi.",
                                "event")),
                 dict(anchor="Fransızlar", terr="k12", terr_dur=2.4, date=(1922, 1, None))]),

    dict(id="taarruz",
         text="Yirmi altı Ağustos bin dokuz yüz yirmi iki sabahı, Kocatepe'den yönetilen Büyük "
              "Taarruz başladı. Otuz Ağustos'ta Dumlupınar'da Yunan ordusunun ana gücü "
              "çembere alınarak yok edildi.",
         cam=(30.2, 38.75, 4.6), cam_dur=2.4,
         events=[dict(anchor="Yirmi altı", date=(1922, 8, 26), marker="kocatepe", offensive=True,
                      card=card("BÜYÜK TAARRUZ · 26 AĞUSTOS 1922", "Büyük Taarruz",
                                "Başkomutan Gazi Mustafa Kemal Paşa · Kocatepe",
                                "Bir yıllık hazırlığın ardından ordu, Afyon'un güneyinden Yunan "
                                "cephesini yardı.", "win"),
                      arrows=[arrow([(30.70, 38.40), (30.55, 38.62), (30.35, 38.80)], "tr", 1.4, 1.2),
                              arrow([(30.20, 38.35), (30.05, 38.60), (29.95, 38.82)], "tr", 1.4, 1.2)]),
                 dict(anchor="Otuz Ağustos", date=(1922, 8, 30), marker="dumlupinar",
                      card=card("ZAFER · 30 AĞUSTOS 1922", "Başkomutanlık Meydan Muharebesi",
                                "Dumlupınar · Türk ordusu ⚔ Yunan ordusu",
                                "Yunan ordusunun ana kuvvetleri kuşatılarak imha edildi; "
                                "başkomutan General Trikupis esir alındı.", "win"),
                      arrows=[arrow([(30.60, 39.10), (30.30, 39.00), (30.05, 38.90)], "tr", 1.2, 1.0)])]),

    dict(id="akdeniz",
         text="Ordular, ilk hedefiniz Akdeniz'dir, ileri! Türk süvarileri dokuz Eylül'de "
              "İzmir'e girdi. Bursa ve bütün Batı Anadolu kısa sürede kurtarıldı.",
         cam=(28.7, 39.0, 7.4), cam_dur=2.0,
         events=[dict(anchor="Ordular",
                      arrows=[arrow([(29.95, 38.80), (29.40, 38.68), (28.50, 38.48), (27.70, 38.45),
                                     (27.20, 38.43)], "tr", 2.8, 1.3),
                              arrow([(30.00, 39.40), (29.70, 39.80), (29.20, 40.12)], "tr", 2.2, 1.0)]),
                 dict(anchor="dokuz Eylül", date=(1922, 9, 9), marker="izmir22", terr="k13",
                      terr_dur=3.0,
                      card=card("KURTULUŞ · 9 EYLÜL 1922", "İzmir'in Kurtuluşu",
                                "Türk süvarileri İzmir'de",
                                "18 Eylül'de Batı Anadolu tamamen kurtarıldı. Yunan ordusu "
                                "Anadolu'yu terk etti.", "win")),
                 dict(anchor="Bursa", date=(1922, 9, 18))]),

    dict(id="mudanya",
         text="On bir Ekim'de imzalanan Mudanya Ateşkes Antlaşması ile Doğu Trakya savaşmadan "
              "geri alındı. Bir Kasım'da saltanat kaldırıldı.",
         cam=(27.6, 40.75, 5.4), cam_dur=2.2, era=3,
         events=[dict(anchor="On bir Ekim", date=(1922, 10, 11), marker="mudanya",
                      card=card("ATEŞKES · 11 EKİM 1922", "Mudanya Ateşkes Antlaşması",
                                "TBMM · İngiltere, Fransa, İtalya",
                                "Savaşın askerî safhası sona erdi. İstanbul ve Boğazlar, barış "
                                "imzalanana kadar İtilaf denetiminde kaldı.", "event")),
                 dict(anchor="Doğu Trakya", terr="k14", terr_dur=2.4,
                      arrows=[arrow([(27.50, 40.98), (27.10, 41.30), (26.60, 41.62)], "tr", 1.6)]),
                 dict(anchor="Bir Kasım", date=(1922, 11, 1))]),

    dict(id="lozan",
         text="Yirmi dört Temmuz bin dokuz yüz yirmi üçte imzalanan Lozan Barış Antlaşması, "
              "yeni Türk devletinin bağımsızlığını bütün dünyaya kabul ettirdi. Altı Ekim'de "
              "İtilaf askerleri İstanbul'dan ayrıldı.",
         cam=FULL_VIEW, cam_dur=2.4,
         events=[dict(anchor="Yirmi dört", date=(1923, 7, 24),
                      card=card("BARIŞ · 24 TEMMUZ 1923", "Lozan Barış Antlaşması",
                                "İsmet Paşa · İtilaf Devletleri",
                                "Sevr hükümsüz kaldı, kapitülasyonlar kaldırıldı. Türkiye'nin "
                                "sınırları büyük ölçüde çizildi; Musul meselesi ertelendi.",
                                "win")),
                 dict(anchor="Altı Ekim", date=(1923, 10, 6), marker="istanbul23", terr="k15",
                      terr_dur=2.6)]),

    dict(id="cumhuriyet",
         text="Yirmi dokuz Ekim bin dokuz yüz yirmi üçte Cumhuriyet ilan edildi ve Gazi Mustafa "
              "Kemal Paşa ilk cumhurbaşkanı seçildi. Egemenlik, kayıtsız şartsız milletindir.",
         cam=(34.0, 39.0, 21.0), cam_dur=2.6, tail=0.8, outro=4.6,
         events=[dict(anchor="Yirmi dokuz", date=(1923, 10, 29), peak=True,
                      card=card("CUMHURİYET · 29 EKİM 1923", "Cumhuriyetin İlanı",
                                "Cumhurbaşkanı Gazi Mustafa Kemal Paşa",
                                "Ankara 13 Ekim'de başkent oldu. Dört yıllık Millî Mücadele, "
                                "bağımsız Türkiye Cumhuriyeti ile taçlandı.", "win")),
                 dict(anchor="@end", outro=True, cam=(34.6, 38.6, 23.0), cam_dur=4.0)]),
]

# ------------------------------------------------------------------ Etiketler
# (ad, boylam, enlem, azami görünüm genişliği, önem)
CITIES = [
    ("İstanbul", 28.97, 41.01, 999, 3),
    ("Ankara", 32.86, 39.93, 999, 3),
    ("İzmir", 27.14, 38.42, 999, 2),
    ("Bursa", 29.06, 40.19, 14, 2),
    ("Edirne", 26.56, 41.68, 30, 2),
    ("Samsun", 36.33, 41.29, 30, 2),
    ("Erzurum", 41.27, 39.90, 30, 2),
    ("Sivas", 37.02, 39.75, 30, 2),
    ("Trabzon", 39.72, 41.00, 30, 1),
    ("Kars", 43.10, 40.60, 30, 1),
    ("Adana", 35.32, 37.00, 30, 2),
    ("Konya", 32.49, 37.87, 30, 1),
    ("Antalya", 30.71, 36.89, 30, 1),
    ("Eskişehir", 30.52, 39.78, 12, 1),
    ("Kütahya", 29.98, 39.42, 10, 1),
    ("Afyon", 30.54, 38.76, 12, 1),
    ("Uşak", 29.41, 38.68, 10, 1),
    ("Manisa", 27.43, 38.61, 10, 1),
    ("Aydın", 27.84, 37.85, 10, 1),
    ("Ayvalık", 26.69, 39.32, 8, 1),
    ("Balıkesir", 27.88, 39.65, 10, 1),
    ("Çanakkale", 26.41, 40.15, 12, 1),
    ("Tekirdağ", 27.51, 40.98, 8, 1),
    ("Polatlı", 32.15, 39.58, 7, 1),
    ("Havza", 35.66, 40.97, 6, 1),
    ("Amasya", 35.83, 40.65, 12, 1),
    ("Tokat", 36.55, 40.31, 12, 1),
    ("Erzincan", 39.49, 39.75, 12, 1),
    ("Kayseri", 35.49, 38.73, 12, 1),
    ("Kırşehir", 34.17, 39.15, 10, 1),
    ("Sarıkamış", 42.59, 40.33, 9, 1),
    ("Ardahan", 42.70, 41.11, 9, 1),
    ("Iğdır", 44.04, 39.92, 9, 1),
    ("Maraş", 36.94, 37.58, 10, 1),
    ("Antep", 37.38, 37.07, 10, 1),
    ("Urfa", 38.79, 37.16, 10, 1),
    ("Mersin", 34.63, 36.80, 10, 1),
    ("Antakya", 36.16, 36.20, 10, 1),
    ("Diyarbakır", 40.23, 37.91, 30, 1),
    ("Van", 43.38, 38.50, 30, 1),
    ("Musul", 43.13, 36.34, 30, 1),
    ("Halep", 37.16, 36.20, 30, 1),
    ("Selanik", 22.94, 40.64, 30, 1),
    ("Atina", 23.73, 37.98, 30, 1),
    ("Sofya", 23.32, 42.70, 30, 1),
    ("Tiflis", 44.79, 41.72, 30, 1),
    ("Erivan", 44.51, 40.18, 30, 1),
    ("Gümrü", 43.85, 40.79, 9, 1),
    ("Mudanya", 28.88, 40.38, 7, 1),
    ("Kocatepe", 30.43, 38.62, 6, 1),
    ("Dumlupınar", 29.98, 38.85, 6, 1),
    ("İnönü", 30.14, 39.82, 6, 1),
    ("Mondros (Limni)", 25.27, 39.87, 14, 1),
]

# (metin, boylam, enlem, [(başlangıç, bitiş) ondalık yıl], (min_w, max_w))
RIVALS = [
    ("YUNANİSTAN", 22.2, 39.4, [(1900, 2000)], (10, 999)),
    ("BULGARİSTAN", 25.0, 42.75, [(1900, 2000)], (10, 999)),
    ("SURİYE", 38.4, 35.3, [(1900, 2000)], (12, 999)),
    ("IRAK", 43.2, 34.4, [(1900, 2000)], (14, 999)),
    ("İRAN", 46.6, 37.6, [(1900, 2000)], (14, 999)),
    ("GÜRCİSTAN", 43.6, 42.2, [(1918, 1921.15)], (9, 999)),
    ("ERMENİSTAN", 45.1, 40.45, [(1918, 1920.95)], (6, 999)),
    ("SOVYET RUSYA", 44.5, 42.6, [(1921.15, 2000)], (9, 999)),
    ("KIBRIS (İngiliz)", 33.2, 35.1, [(1900, 2000)], (12, 999)),
]

# Sevr planı bölge adları
SEVR_LABELS = [
    ("YUNANİSTAN'A", 27.45, 38.95), ("BOĞAZLAR BÖLGESİ", 28.6, 40.55),
    ("İTALYAN BÖLGESİ", 30.9, 37.6), ("FRANSIZ BÖLGESİ", 37.0, 38.3),
    ("ERMENİSTAN'A", 40.9, 40.55), ("ÖZERK KÜRDİSTAN", 42.7, 37.75),
    ("TÜRKLERE KALAN", 34.4, 40.55),
]

# (metin, boylam, enlem, (min_w, max_w), boyut)
SEAS = [
    ("Karadeniz", 34.5, 42.75, (6, 999), 1.0),
    ("Akdeniz", 31.0, 35.0, (10, 999), 1.1),
    ("Ege Denizi", 25.2, 38.4, (6, 999), 0.9),
    ("Marmara Denizi", 28.2, 40.72, (2.5, 12), 0.8),
    ("Hazar Denizi", 50.5, 41.5, (25, 999), 0.9),
]

# Dönemler (ondalık yıl): Kurtuluş Savaşı'nın aşamaları
ERAS = [(1918.75, 1919.38, "MONDROS VE İŞGALLER"),
        (1919.38, 1920.30, "HAZIRLIK DÖNEMİ"),
        (1920.30, 1922.78, "SAVAŞLAR DÖNEMİ"),
        (1922.78, 1923.92, "BARIŞ VE CUMHURİYET")]
TL_RANGE = (1918.75, 1923.92)
