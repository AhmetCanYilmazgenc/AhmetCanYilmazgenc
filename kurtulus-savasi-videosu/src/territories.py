"""Kurtuluş Savaşı dönemine ait işgal bölgeleri ve cephe hatları.

Tüm koordinatlar (boylam, enlem) derece cinsindendir. Çokgenler bilerek
denizlere ve komşu ülkelere taşar; Türkiye sınırı (Natural Earth) ile
kesişim alındığı için kıyılar ve kara sınırları otomatik olarak doğru çıkar.

Katmanlar:
  tr – Türk / TBMM denetimindeki topraklar (temel katman)
  gr – Yunan işgali        br – İngiliz işgali (İtilaf)
  fr – Fransız işgali      it – İtalyan işgali
  ar – Ermeni / Gürcü denetimi (doğu)
  ku – yalnızca Sevr planında: özerk Kürdistan bölgesi

Sınırlar belgesel ölçeğinde yaklaşık değerlerdir.
"""
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

LAYERS = ["tr", "ku", "ar", "it", "fr", "br", "gr"]

# ---------------------------------------------------------------- Türkiye
HATAY = [(35.70, 36.05), (35.85, 35.80), (36.40, 35.75), (36.75, 36.05), (36.70, 36.55),
         (36.55, 36.80), (36.25, 36.98), (36.00, 36.95), (35.85, 36.60)]

# ---------------------------------------------------------------- İngiliz
MOSUL = [(41.25, 36.45), (42.30, 37.10), (43.20, 37.35), (44.30, 37.25), (44.85, 37.10),
         (45.35, 36.50), (45.70, 35.70), (45.40, 35.10), (44.40, 34.80), (43.40, 34.95),
         (42.40, 35.40), (41.25, 35.80)]
# İstanbul ve Çatalca – Kocaeli kıyısı (Boğaz bölgesi)
ISTANBUL_Z = [(28.25, 41.65), (29.45, 41.35), (29.45, 40.80), (29.05, 40.78), (28.60, 40.92),
              (28.25, 40.95)]
GELIBOLU = [(26.10, 40.62), (26.80, 40.62), (26.80, 40.20), (26.48, 40.02), (26.10, 39.95)]
CANAKKALE = [(26.30, 40.20), (26.55, 40.22), (26.65, 40.05), (26.45, 39.92), (26.15, 39.90)]
# Antep – Maraş – Urfa (Şubat–Ekim 1919 arası İngiliz, sonra Fransız)
SOUTH_ANTEP = [(36.55, 36.80), (36.65, 37.20), (36.55, 37.75), (36.95, 37.95), (37.40, 37.75),
               (38.20, 37.60), (39.10, 37.60), (39.60, 37.25), (39.70, 36.60), (36.60, 36.55)]
MARAS = [(36.45, 37.25), (36.55, 37.80), (36.95, 38.00), (37.40, 37.78), (37.30, 37.30)]
URFA = [(38.30, 37.70), (39.20, 37.70), (39.70, 37.30), (39.75, 36.60), (38.30, 36.60)]

# ---------------------------------------------------------------- Fransız
CUKUROVA = [(33.70, 36.15), (33.95, 36.70), (34.45, 37.10), (34.85, 37.50), (35.40, 37.55),
            (35.95, 37.45), (36.45, 37.25), (36.65, 36.95), (36.75, 36.40), (36.40, 35.75),
            (35.80, 35.70)]
ANTEP = [(36.40, 36.60), (36.45, 37.30), (37.35, 37.40), (37.90, 37.20), (38.05, 36.60)]

# ---------------------------------------------------------------- İtalyan
ITALY_ANTALYA = [(29.20, 36.00), (29.40, 36.80), (30.10, 37.35), (30.85, 37.55), (31.70, 37.40),
                 (32.30, 36.90), (32.50, 36.00)]
ITALY_SW = [(26.80, 37.95), (27.40, 37.80), (27.95, 37.60), (28.55, 37.40), (29.30, 37.15),
            (30.10, 37.40), (30.85, 37.60), (31.70, 37.45), (32.30, 36.95), (32.50, 36.00),
            (26.80, 36.00)]

# ---------------------------------------------------------------- Yunan
# Mayıs–Haziran 1919: İzmir, Manisa, Aydın, Ayvalık (Milne hattı)
GR_1919 = [(26.40, 39.55), (27.05, 39.45), (27.55, 39.20), (27.90, 38.95), (28.20, 38.55),
           (28.25, 38.20), (28.05, 37.90), (27.55, 37.78), (27.00, 37.85), (25.90, 37.80),
           (25.90, 39.55)]
# Haziran–Temmuz 1920 Yunan yaz taarruzu sonrası
GR_1920 = [(26.20, 40.60), (27.20, 40.50), (28.20, 40.55), (29.00, 40.55), (29.40, 40.48),
           (29.60, 40.20), (29.55, 39.85), (29.30, 39.50), (29.70, 39.00), (29.85, 38.55),
           (29.40, 38.30), (28.70, 38.15), (28.30, 37.95), (27.75, 37.80), (27.00, 37.88),
           (25.90, 37.80), (25.90, 40.60)]
# Temmuz 1921 Kütahya–Eskişehir savaşları sonrası
GR_1921 = [(26.20, 40.60), (27.20, 40.50), (28.20, 40.55), (29.00, 40.55), (29.45, 40.55),
           (30.00, 40.40), (30.55, 40.15), (31.00, 39.85), (31.15, 39.45), (31.00, 39.00),
           (30.95, 38.60), (30.60, 38.25), (30.00, 38.15), (29.40, 38.10), (28.70, 38.05),
           (28.30, 37.95), (27.75, 37.80), (27.00, 37.88), (25.90, 37.80), (25.90, 40.60)]
# Ağustos–Eylül 1921 Sakarya önlerine kadar ilerleme
GR_SAKARYA = [(26.20, 40.60), (27.20, 40.50), (28.20, 40.55), (29.00, 40.55), (29.45, 40.55),
              (30.00, 40.40), (30.70, 40.20), (31.40, 39.95), (32.05, 39.75), (32.20, 39.45),
              (31.95, 39.10), (31.40, 38.75), (30.95, 38.50), (30.60, 38.25), (30.00, 38.15),
              (29.40, 38.10), (28.70, 38.05), (28.30, 37.95), (27.75, 37.80), (27.00, 37.88),
              (25.90, 37.80), (25.90, 40.60)]
THRACE = [(25.40, 42.40), (28.25, 42.40), (28.25, 40.95), (27.30, 40.85), (26.85, 40.62),
          (26.10, 40.62), (25.40, 40.55)]
IMBROS_TENEDOS = [box(25.55, 40.03, 26.05, 40.28), box(25.93, 39.75, 26.12, 39.89)]

# ---------------------------------------------------------------- Doğu
# 1877–78'den beri Rus yönetimindeki Kars–Ardahan–Batum ve Iğdır (Sürmeli)
KARS_REGION = [(41.52, 41.60), (41.40, 41.25), (41.50, 40.85), (41.85, 40.62), (42.20, 40.45),
               (42.45, 40.15), (42.80, 39.95), (43.25, 39.85), (43.60, 39.72), (44.20, 39.62),
               (44.70, 39.80), (45.20, 40.50), (44.20, 41.40), (43.40, 41.40), (42.70, 41.75),
               (42.00, 41.80)]

# ---------------------------------------------------------------- Sevr planı
SEVR_GR_IZMIR = [(26.30, 39.70), (27.20, 39.55), (27.80, 39.25), (28.30, 38.85), (28.55, 38.45),
                 (28.40, 38.05), (27.90, 37.85), (27.35, 37.80), (25.90, 37.80), (25.90, 39.70)]
SEVR_STRAITS = [(26.10, 40.75), (27.40, 40.95), (28.25, 41.05), (28.25, 41.65), (29.40, 41.35),
                (30.00, 41.20), (30.00, 40.70), (29.50, 40.40), (28.80, 40.30), (27.80, 40.25),
                (27.20, 40.20), (26.80, 39.75), (26.10, 39.45), (25.90, 40.20)]
SEVR_IT = [(27.35, 37.80), (27.90, 37.85), (28.40, 38.05), (28.90, 38.30), (29.90, 38.70),
           (30.80, 38.85), (31.90, 38.75), (32.90, 38.60), (33.80, 38.40), (34.40, 37.80),
           (34.30, 37.20), (33.90, 36.10), (26.80, 36.00), (26.80, 37.80)]
SEVR_FR = [(34.30, 37.20), (34.40, 37.80), (35.10, 38.30), (35.80, 38.90), (36.60, 39.50),
           (37.30, 39.70), (38.00, 39.40), (38.40, 38.80), (38.80, 38.20), (39.60, 37.90),
           (40.60, 37.60), (41.30, 37.10), (41.40, 35.80), (36.75, 35.80), (35.80, 35.40),
           (33.80, 36.10)]
SEVR_AR = [(39.00, 41.30), (39.20, 40.70), (39.35, 40.10), (39.70, 39.60), (40.30, 39.20),
           (41.00, 38.80), (41.80, 38.60), (42.60, 38.55), (43.30, 38.45), (44.00, 38.30),
           (44.80, 38.40), (45.60, 39.60), (45.60, 40.80), (44.20, 41.60), (42.70, 41.85), (40.50, 41.60)]
SEVR_KU = [(38.40, 38.80), (39.00, 38.75), (40.30, 39.20), (41.00, 38.80), (41.80, 38.60),
           (42.60, 38.55), (43.30, 38.45), (44.00, 38.30), (44.80, 38.40), (45.30, 37.50),
           (45.00, 36.40), (41.40, 36.40), (41.30, 37.10), (40.60, 37.60), (39.60, 37.90), (38.80, 38.20)]


def _p(coords):
    p = Polygon(coords)
    return p if p.is_valid else p.buffer(0)


def _u(*parts):
    gs = [x if not isinstance(x, list) else _p(x) for x in parts]
    return unary_union(gs) if gs else Polygon()


# Her anahtar: katman -> (Türkiye ile kesişecek parçalar, Türkiye dışı parçalar)
KEYFRAMES = {
    # Ekim 1918 – Mondros'tan hemen önce/sonra
    "k0": dict(tr="full", armenia=True),
    # Kasım–Aralık 1918: Musul, Boğazlar, İstanbul; Fransızlar Çukurova'da
    "k1": dict(tr="full", armenia=True, br=[ISTANBUL_Z, GELIBOLU, CANAKKALE], br_out=[MOSUL],
               fr=[CUKUROVA], gr=IMBROS_TENEDOS),
    # Şubat–Mart 1919: İngilizler Antep–Maraş–Urfa'da
    "k2a": dict(tr="full", armenia=True, br=[ISTANBUL_Z, GELIBOLU, CANAKKALE, SOUTH_ANTEP],
                br_out=[MOSUL], fr=[CUKUROVA], gr=IMBROS_TENEDOS),
    # Mart–Nisan 1919: İtalyanlar Antalya'da
    "k2b": dict(tr="full", armenia=True, br=[ISTANBUL_Z, GELIBOLU, CANAKKALE, SOUTH_ANTEP],
                br_out=[MOSUL], fr=[CUKUROVA], it=[ITALY_ANTALYA], gr=IMBROS_TENEDOS),
    # Nisan 1919: Kars bölgesi Ermenilere
    "k2c": dict(tr="full", armenia=True, ar=[KARS_REGION],
                br=[ISTANBUL_Z, GELIBOLU, CANAKKALE, SOUTH_ANTEP], br_out=[MOSUL], fr=[CUKUROVA],
                it=[ITALY_ANTALYA], gr=IMBROS_TENEDOS),
    # Mayıs 1919: İzmir'in işgali; İtalyanlar Muğla–Kuşadası'na yayıldı
    "k3": dict(tr="full", armenia=True, ar=[KARS_REGION],
               br=[ISTANBUL_Z, GELIBOLU, CANAKKALE, SOUTH_ANTEP], br_out=[MOSUL], fr=[CUKUROVA],
               it=[ITALY_SW], gr=[GR_1919] + IMBROS_TENEDOS),
    # Kasım 1919: güney Fransızlara devredildi
    "k4": dict(tr="full", armenia=True, ar=[KARS_REGION],
               br=[ISTANBUL_Z, GELIBOLU, CANAKKALE], br_out=[MOSUL],
               fr=[CUKUROVA, SOUTH_ANTEP, MARAS, URFA], it=[ITALY_SW], gr=[GR_1919] + IMBROS_TENEDOS),
    # Şubat–Nisan 1920: Maraş ve Urfa kurtuldu (Antep kuşatma altında)
    "k5": dict(tr="full", armenia=True, ar=[KARS_REGION],
               br=[ISTANBUL_Z, GELIBOLU, CANAKKALE], br_out=[MOSUL],
               fr=[CUKUROVA, ANTEP], it=[ITALY_SW], gr=[GR_1919] + IMBROS_TENEDOS),
    # Haziran–Temmuz 1920: Yunan yaz taarruzu, Doğu Trakya
    "k6": dict(tr="full", armenia=True, ar=[KARS_REGION],
               br=[ISTANBUL_Z, GELIBOLU, CANAKKALE], br_out=[MOSUL],
               fr=[CUKUROVA, ANTEP], it=[ITALY_SW], gr=[GR_1920, THRACE] + IMBROS_TENEDOS),
    # Ağustos 1920: Sevr Antlaşması'nın öngördüğü paylaşım
    "sevr": dict(tr="full", armenia=True, ar=[SEVR_AR], ku=[SEVR_KU],
                 br=[SEVR_STRAITS], br_out=[MOSUL], fr=[SEVR_FR], it=[SEVR_IT],
                 gr=[SEVR_GR_IZMIR, THRACE] + IMBROS_TENEDOS),
    # Aralık 1920: Doğu Cephesi zaferi (Kars, Gümrü)
    "k7": dict(tr="full", br=[ISTANBUL_Z, GELIBOLU, CANAKKALE], br_out=[MOSUL],
               fr=[CUKUROVA, ANTEP], it=[ITALY_SW], gr=[GR_1920, THRACE] + IMBROS_TENEDOS),
    # Temmuz 1921: Kütahya–Eskişehir; İtalyanlar çekiliyor
    "k9": dict(tr="full", br=[ISTANBUL_Z, GELIBOLU, CANAKKALE], br_out=[MOSUL],
               fr=[CUKUROVA, ANTEP], gr=[GR_1921, THRACE] + IMBROS_TENEDOS),
    # Ağustos 1921: Sakarya önleri
    "k10": dict(tr="full", br=[ISTANBUL_Z, GELIBOLU, CANAKKALE], br_out=[MOSUL],
                fr=[CUKUROVA, ANTEP], gr=[GR_SAKARYA, THRACE] + IMBROS_TENEDOS),
    # Eylül 1921: Sakarya sonrası geri çekilme
    "k11": dict(tr="full", br=[ISTANBUL_Z, GELIBOLU, CANAKKALE], br_out=[MOSUL],
                fr=[CUKUROVA, ANTEP], gr=[GR_1921, THRACE] + IMBROS_TENEDOS),
    # Ekim 1921 – Ocak 1922: Ankara Antlaşması; Fransızlar yalnız Hatay'da
    "k12": dict(tr="nohatay", br=[ISTANBUL_Z, GELIBOLU, CANAKKALE], br_out=[MOSUL],
                fr_out=[HATAY], gr=[GR_1921, THRACE] + IMBROS_TENEDOS),
    # Eylül 1922: Büyük Taarruz sonrası Anadolu kurtuldu
    "k13": dict(tr="nohatay", br=[ISTANBUL_Z, GELIBOLU, CANAKKALE], br_out=[MOSUL],
                fr_out=[HATAY], gr=[THRACE] + IMBROS_TENEDOS),
    # Ekim 1922: Mudanya – Doğu Trakya
    "k14": dict(tr="nohatay", br=[ISTANBUL_Z, GELIBOLU, CANAKKALE], br_out=[MOSUL],
                fr_out=[HATAY], gr=IMBROS_TENEDOS),
    # Ekim 1923: İstanbul'un kurtuluşu, Lozan sınırları
    "k15": dict(tr="nohatay", br_out=[MOSUL], fr_out=[HATAY]),
}
KEY_ORDER = list(KEYFRAMES)


def layer_geoms(country):
    """{anahtar: {katman: shapely}} – country(a3) Natural Earth sınırı döndürür."""
    tur = country("TUR")
    hatay = _p(HATAY)
    tur_nh = tur.difference(hatay)
    arm = country("ARM")
    irq = country("IRQ")
    out = {}
    for key, kf in KEYFRAMES.items():
        base = tur if kf["tr"] == "full" else tur_nh
        layers = {"tr": base}
        for ln in LAYERS[1:]:
            parts = kf.get(ln, [])
            g = _u(*parts).intersection(tur) if parts else Polygon()
            outs = list(kf.get(ln + "_out", []))
            if outs:
                g = unary_union([g, _u(*outs).difference(base.buffer(0.002))])
            if ln == "br" and outs:
                g = unary_union([g.intersection(tur), _u(*outs).intersection(irq)])
            if ln == "ar" and kf.get("armenia"):
                g = unary_union([g, arm])
            layers[ln] = g
        # çakışmalar: Boğazlar İngiliz bölgesi önceliklidir
        layers["gr"] = layers["gr"].difference(layers["br"])
        layers["it"] = layers["it"].difference(layers["gr"])
        out[key] = layers
    return out
