"""Kurtuluş Savaşı harita animasyonunun kare kare çizimi.

Katmanlar: deniz → kara (Natural Earth) → Türk toprakları ve işgal bölgeleri
(SDF, dalga şeklinde yayılan/geri çekilen geçişler) → sınırlar → nehirler ve
kıyılar → arayüz (tarih, bilgi kartı, oklar, savaş işaretleri, etiketler,
zaman çizgisi).
"""
import math
import os
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import sdf as G
from config import W, H, FPS, FONT_DIR
from geo import merc_y
from story import CITIES, RIVALS, SEAS, ERAS, SEVR_LABELS, AYLAR, TL_RANGE
from territories import LAYERS

# ------------------------------------------------------------------ renkler
C_SEA_DEEP = np.array([0.105, 0.200, 0.255], np.float32)
C_SEA = np.array([0.170, 0.310, 0.370], np.float32)
C_SEA_LIGHT = np.array([0.330, 0.510, 0.550], np.float32)
C_LAND = np.array([0.900, 0.860, 0.760], np.float32)
C_GOLD = np.array([0.965, 0.800, 0.400], np.float32)
C_GLOW = np.array([1.000, 0.780, 0.380], np.float32)
C_RIVER = np.array([0.330, 0.520, 0.600], np.float32)
C_COAST = np.array([0.300, 0.230, 0.160], np.float32)

LAYER_COL = {
    "tr": np.array([0.700, 0.105, 0.140], np.float32),
    "gr": np.array([0.200, 0.420, 0.780], np.float32),
    "br": np.array([0.470, 0.300, 0.600], np.float32),
    "fr": np.array([0.130, 0.540, 0.500], np.float32),
    "it": np.array([0.430, 0.600, 0.180], np.float32),
    "ar": np.array([0.900, 0.560, 0.180], np.float32),
    "ku": np.array([0.600, 0.560, 0.500], np.float32),
}
LAYER_NAME = {"tr": "Türk / TBMM denetimi", "gr": "Yunan işgali", "br": "İngiliz işgali",
              "fr": "Fransız işgali", "it": "İtalyan işgali", "ar": "Ermeni denetimi"}


def rgb8(c, k=1.0):
    return tuple(int(min(255, max(0, v * 255 * k))) for v in c)


GOLD = (236, 200, 112)
CREAM = (246, 236, 214)
INK = (52, 36, 24)

SS = 2  # arayüz katmanı süper örnekleme katsayısı


def clamp01(x):
    return min(1.0, max(0.0, x))


def smooth(p):
    p = clamp01(p)
    return p * p * (3 - 2 * p)


def ease_io(p):
    p = clamp01(p)
    return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


def ease_out(p):
    p = clamp01(p)
    return 1 - (1 - p) ** 3


# ------------------------------------------------------------------ kamera
def cam_state(target):
    lon, lat, w = target
    return (float(lon), float(merc_y(lat)), float(w))


def cam_interp(a, b, p):
    e = ease_io(p)
    w = math.exp(math.log(a[2]) + (math.log(b[2]) - math.log(a[2])) * e)
    if abs(b[2] - a[2]) / max(a[2], b[2]) > 1e-3:
        s = (1 / w - 1 / a[2]) / (1 / b[2] - 1 / a[2])
    else:
        s = e
    return (a[0] + (b[0] - a[0]) * s, a[1] + (b[1] - a[1]) * s, w)


class Camera:
    def __init__(self, moves):
        self.moves = sorted(moves, key=lambda m: m["t"])
        self.start = []
        cur = cam_state(self.moves[0]["target"])
        for i, m in enumerate(self.moves):
            self.start.append(self._eval(m["t"], i) if i else cur)

    def _eval(self, t, upto):
        state = cam_state(self.moves[0]["target"])
        for i in range(upto):
            m = self.moves[i]
            if t < m["t"]:
                break
            p = 1.0 if m["dur"] <= 0 else (t - m["t"]) / m["dur"]
            state = cam_interp(self.start[i], cam_state(m["target"]), p)
        return state

    def at(self, t):
        return self._eval(t, len(self.moves))


# ------------------------------------------------------------------ fontlar
_FONTS = {}


def font(name, size, var=None):
    key = (name, int(size), var)
    if key not in _FONTS:
        files = {"cinzel": "Cinzel[wght].ttf", "garamond": "EBGaramond[wght].ttf",
                 "garamond-i": "EBGaramond-Italic[wght].ttf"}
        f = ImageFont.truetype(os.path.join(FONT_DIR, files[name]), int(size))
        if var:
            try:
                f.set_variation_by_name(var)
            except Exception:
                pass
        _FONTS[key] = f
    return _FONTS[key]


def text_spaced(dr, x, y, text, fnt, fill, spacing, align="l", stroke=0, stroke_fill=None,
                anchor_v="s"):
    widths = [fnt.getlength(ch) for ch in text]
    total = sum(widths) + spacing * (len(text) - 1)
    if align == "c":
        x -= total / 2
    elif align == "r":
        x -= total
    for ch, wd in zip(text, widths):
        dr.text((x, y), ch, font=fnt, fill=fill, anchor="l" + anchor_v, stroke_width=stroke,
                stroke_fill=stroke_fill)
        x += wd + spacing
    return total


# ------------------------------------------------------------------ sprite'lar
def _sword_poly(angle_deg, size):
    """Tek kılıç parçaları (dikey kılıç, merkez etrafında döndürülmüş)."""
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)

    def tr(pts):
        return [(size / 2 + (x * ca - y * sa) * size, size / 2 + (x * sa + y * ca) * size) for x, y in pts]

    blade = tr([(0.0, -0.50), (0.045, -0.40), (0.040, 0.20), (-0.040, 0.20), (-0.045, -0.40)])
    fuller = tr([(0.0, -0.36), (0.010, -0.34), (0.010, 0.17), (-0.010, 0.17), (-0.010, -0.34)])
    guard = tr([(-0.17, 0.19), (0.17, 0.19), (0.19, 0.235), (0.17, 0.26), (-0.17, 0.26), (-0.19, 0.235)])
    grip = tr([(-0.030, 0.26), (0.030, 0.26), (0.030, 0.41), (-0.030, 0.41)])
    pc = tr([(0.0, 0.455)])[0]
    return blade, fuller, guard, grip, pc


def make_swords(base_rgb, edge_rgb, px):
    big = px * 4
    im = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    for ang in (-42, 42):
        blade, fuller, guard, grip, pc = _sword_poly(ang, big)
        ow = max(2, big // 40)
        for poly in (blade, guard, grip):
            dr.polygon(poly, fill=base_rgb + (255,), outline=edge_rgb + (255,), width=ow)
        dr.polygon(fuller, fill=tuple(min(255, c + 40) for c in base_rgb) + (255,))
        r = big * 0.05
        dr.ellipse([pc[0] - r, pc[1] - r, pc[0] + r, pc[1] + r], fill=base_rgb + (255,),
                   outline=edge_rgb + (255,), width=ow)
    return im.resize((px, px), Image.LANCZOS)


def make_star(rgb, edge, px):
    big = px * 4
    im = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    pts = []
    for i in range(10):
        r = big * (0.48 if i % 2 == 0 else 0.20)
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((big / 2 + r * math.cos(a), big / 2 + r * math.sin(a)))
    dr.polygon(pts, fill=rgb + (255,), outline=edge + (255,), width=max(2, big // 24))
    return im.resize((px, px), Image.LANCZOS)


class Sprites:
    def __init__(self):
        self.cache = {}

    def get(self, kind, px):
        px = max(4, int(round(px)))
        key = (kind, px)
        if key not in self.cache:
            if kind == "win":
                im = make_swords((236, 196, 98), (60, 30, 10), px)
            elif kind == "loss":
                im = make_swords((200, 204, 212), (40, 30, 30), px)
            else:  # star
                im = make_star((246, 206, 96), (70, 30, 10), px)
            self.cache[key] = im
        return self.cache[key]


def with_alpha(im, a):
    if a >= 0.999:
        return im
    r, g, b, al = im.split()
    al = al.point(lambda v: int(v * a))
    return Image.merge("RGBA", (r, g, b, al))


# ------------------------------------------------------------------ yardımcılar
def to_screen(cam, X, Y):
    cx, cy, w = cam
    px = w / W
    return (np.asarray(X) - (cx - w / 2)) / px, ((cy + H / 2 * px) - np.asarray(Y)) / px


def resample(field, cam, crop):
    sl, step, base_x, top_y = crop
    cx, cy, w = cam
    px = w / W
    X0v = cx - w / 2
    Ytop = cy + H / 2 * px
    a = px / (G.RES * step)
    c = (X0v - base_x) / (G.RES * step)
    f = (top_y - Ytop) / (G.RES * step)
    im = Image.fromarray(np.ascontiguousarray(field, dtype=np.float32), "F")
    o = im.transform((W, H), Image.AFFINE, (a, 0, c, 0, a, f), resample=Image.BILINEAR,
                     fillcolor=G.CLAMP)
    return np.asarray(o)


def crop_for(cam):
    cx, cy, w = cam
    px = w / W
    step = 1 if px < 1.6 * G.RES else 2
    X0v, X1v = cx - w / 2, cx + w / 2
    Ytop, Ybot = cy + H / 2 * px, cy - H / 2 * px
    c0 = max(0, int(math.floor((X0v - G.GX0) / G.RES)) - 3)
    c1 = min(G.NX, int(math.ceil((X1v - G.GX0) / G.RES)) + 3)
    r0 = max(0, int(math.floor((G.GY1 - Ytop) / G.RES)) - 3)
    r1 = min(G.NY, int(math.ceil((G.GY1 - Ybot) / G.RES)) + 3)
    base_x = G.GX0 + c0 * G.RES + 0.5 * (1 - step) * G.RES
    top_y = G.GY1 - r0 * G.RES - 0.5 * (1 - step) * G.RES
    return (np.s_[r0:r1:step, c0:c1:step], step, base_x, top_y)


def blur(arr, radius):
    im = Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8), "L")
    return np.asarray(im.filter(ImageFilter.GaussianBlur(radius)), np.float32) / 255


# ------------------------------------------------------------------ harita katmanı
def draw_base(world, cam):
    cx, cy, w = cam
    px = w / W
    s = SS
    X0v, X1v = cx - w / 2, cx + w / 2
    Ytop, Ybot = cy + H / 2 * px, cy - H / 2 * px
    mx = 0.5 * w
    land = Image.new("L", (W * s, H * s), 0)
    coast = Image.new("L", (W * s, H * s), 0)
    dl, dc = ImageDraw.Draw(land), ImageDraw.Draw(coast)
    fine = w < 25
    lw = max(1, int(round(1.1 * s)))

    def scr(arr):
        return np.column_stack([(arr[:, 0] - X0v) / px * s, (Ytop - arr[:, 1]) / px * s]).ravel().tolist()

    def visible(bb):
        if bb[2] < X0v - mx or bb[0] > X1v + mx or bb[3] < Ybot - mx or bb[1] > Ytop + mx:
            return False
        return max(bb[2] - bb[0], bb[3] - bb[1]) / px > 0.7

    for bb, ext, holes in (world.bm.land_fine if fine else world.bm.land_coarse):
        if not visible(bb):
            continue
        pts = scr(ext)
        dl.polygon(pts, fill=255)
        dc.line(pts, fill=255, width=lw)
        for hl in holes:
            hp = scr(hl)
            dl.polygon(hp, fill=0)
            dc.line(hp, fill=255, width=lw)
    for bb, ext, holes in (world.bm.lakes_fine if fine else world.bm.lakes_coarse):
        if not visible(bb):
            continue
        pts = scr(ext)
        dl.polygon(pts, fill=0)
        dc.line(pts, fill=200, width=lw)
    rivers = Image.new("L", (W * s, H * s), 0)
    dr = ImageDraw.Draw(rivers)
    zf = min(1.5, max(0.7, 12.0 / w))
    for sr, bb, xy in world.bm.rivers:
        if not visible(bb):
            continue
        if sr >= 6 and w > 30:
            continue
        if sr >= 5 and w > 55:
            continue
        base = 2.4 if sr <= 2 else (1.8 if sr <= 4 else 1.2)
        dr.line(scr(xy), fill=255, width=max(1, int(round(base * zf * s))), joint="curve")
    L = np.asarray(land.reduce(s), np.float32) / 255
    CO = np.asarray(coast.reduce(s), np.float32) / 255
    RV = np.asarray(rivers.reduce(s), np.float32) / 255
    return L, CO, RV


def graticule(cam):
    cx, cy, w = cam
    px = w / W
    step = 5 if w < 40 else 10
    im = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(im)
    X0v = cx - w / 2
    Ytop = cy + H / 2 * px
    for lon in range(-30, 91, step):
        x = (lon - X0v) / px
        if -2 < x < W + 2:
            dr.line([(x, 0), (x, H)], fill=255, width=1)
    for lat in range(0, 66, step):
        y = (Ytop - float(merc_y(lat))) / px
        if -2 < y < H + 2:
            dr.line([(0, y), (W, y)], fill=255, width=1)
    return np.asarray(im, np.float32) / 255


# ------------------------------------------------------------------ işaretler
def make_pin(ring, fill, dot, px):
    big = px * 4
    im = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    r = big * 0.44
    c = big / 2
    dr.ellipse([c - r, c - r, c + r, c + r], fill=fill + (235,), outline=ring + (255,),
               width=max(2, big // 9))
    r2 = big * 0.15
    dr.ellipse([c - r2, c - r2, c + r2, c + r2], fill=dot + (255,))
    return im.resize((px, px), Image.LANCZOS)


class Sprites:
    def __init__(self):
        self.cache = {}

    def get(self, kind, px):
        px = max(4, int(round(px)))
        key = (kind, px)
        if key not in self.cache:
            if kind == "win":
                im = make_swords((236, 196, 98), (60, 30, 10), px)
            elif kind == "loss":
                im = make_swords((200, 204, 212), (40, 30, 30), px)
            elif kind == "occ":
                im = make_pin((150, 175, 215), (30, 36, 52), (190, 210, 240), px)
            elif kind == "event":
                im = make_pin((236, 200, 112), (60, 22, 18), (250, 236, 200), px)
            else:  # star
                im = make_star((246, 206, 96), (70, 30, 10), px)
            self.cache[key] = im
        return self.cache[key]


# ------------------------------------------------------------------ dünya
class World:
    """Çizim için gereken statik veriler (her süreçte bir kez yüklenir)."""

    def __init__(self, basemap, sdfs, tl):
        self.bm = basemap
        self.sdfs = sdfs
        self.tl = tl
        self.cam = Camera(tl["cam"])
        self.sprites = Sprites()
        self._dmax = {}
        rng = np.random.default_rng(1919)
        lo = rng.normal(0, 1, (27, 48)).astype(np.float32)
        self.noise_lo = np.asarray(Image.fromarray(lo, "F").resize((W, H), Image.BICUBIC))
        hi = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
        self.noise_hi = np.asarray(Image.fromarray(hi, "F").resize((W, H), Image.BILINEAR))
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        vig = 1 - 0.36 * np.clip(r - 0.45, 0, 1) ** 1.5
        tlc = np.exp(-(((xx - 150) / 520) ** 2 + ((yy - 100) / 220) ** 2))
        bot = np.clip((yy - 930) / 150, 0, 1) ** 1.5
        self.vignette = (vig * (1 - 0.35 * tlc) * (1 - 0.35 * bot)).astype(np.float32)
        self.xx, self.yy = xx, yy
        g = np.clip(1 - r * 0.9, 0, 1)[..., None]
        self.sea_base = (C_SEA_DEEP * (1 - g) + C_SEA * g).astype(np.float32)
        sv = tl.get("sevr") or []
        self.sevr = (sv[0], sv[1]) if len(sv) >= 2 else None
        sc = {s["id"]: s for s in tl["scenes"]}
        self.route_end = sc["yunan20"]["t0"] if "yunan20" in sc else 1e9

    # ---------- toprak alanları
    def _get(self, key, layer, sl):
        arr = self.sdfs[key][layer]
        if arr is None:
            return None
        return arr[sl].astype(np.float32) / G.SCALE

    def dmax(self, a, b, layer):
        k = (a, b, layer)
        if k not in self._dmax:
            A = self.sdfs[a][layer].astype(np.float32) / G.SCALE
            B = self.sdfs[b][layer].astype(np.float32) / G.SCALE
            gain = (B < 0) & (A > 0)
            loss = (A < 0) & (B > 0)
            dg = float(A[gain].max()) if gain.any() else 0.0
            dl = float(B[loss].max()) if loss.any() else 0.0
            self._dmax[k] = (dg + 0.02, dl + 0.02)
        return self._dmax[k]

    def terr_state(self, t):
        last = None
        for tr in self.tl["terr"]:
            if t < tr["t"]:
                break
            last = tr
        if last is None:
            return "k0", None, 1.0
        p = (t - last["t"]) / last["dur"]
        if p >= 1:
            return last["dst"], None, 1.0
        return last["src"], last["dst"], p

    def fields(self, t, sl):
        """{katman: (alan, opaklık, kaynak_alan|None, e)} kırpılmış ızgarada."""
        a, b, p = self.terr_state(t)
        out = {}
        for ln in LAYERS:
            if b is None:
                f = self._get(a, ln, sl)
                if f is not None:
                    out[ln] = (f, 1.0, None, 1.0)
                continue
            e = ease_io(p)
            SA, SB = self._get(a, ln, sl), self._get(b, ln, sl)
            if SA is None and SB is None:
                continue
            if SA is None:          # katman yeni beliriyor
                out[ln] = (SB, smooth(p * 1.6), None, e)
                continue
            if SB is None:          # katman tamamen kalkıyor
                out[ln] = (SA, 1 - smooth(p * 1.3), SA, e)
                continue
            if self.sdfs[a][ln] is self.sdfs[b][ln]:
                out[ln] = (SB, 1.0, None, 1.0)
                continue
            dg, dl = self.dmax(a, b, ln)
            rg, rl = e * dg, (1 - e) * dl
            f = np.minimum(np.maximum(SB, SA - rg), np.maximum(SA, SB - rl))
            out[ln] = (f, 1.0, SA, e)
        return out

    # ---------- tarih
    def date_at(self, t):
        cur, prev = None, None
        for d in self.tl["dates"]:
            if t < d["t"]:
                break
            prev, cur = cur, d
        return cur, prev

    def dec_year(self, t):
        cur, prev = self.date_at(t)
        if cur is None:
            return TL_RANGE[0]
        if prev is None:
            return cur["dec"]
        p = ease_io((t - cur["t"]) / 0.9)
        return prev["dec"] + (cur["dec"] - prev["dec"]) * p


# ------------------------------------------------------------------ harita katmanı
def _bbox(m, thr=0.002):
    rows = np.flatnonzero(m.max(axis=1) > thr)
    if len(rows) == 0:
        return None
    cols = np.flatnonzero(m[rows[0]:rows[-1] + 1].max(axis=0) > thr)
    return np.s_[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]


def blend(img, k, col, sl=None):
    """img[sl] = img*(1-k) + col*k  (col: renk vektörü veya HxWx3 dizi)."""
    if sl is None:
        sl = _bbox(k)
        if sl is None:
            return
    kk = k[sl][..., None]
    c = col[sl] if (isinstance(col, np.ndarray) and col.ndim == 3) else col
    sub = img[sl]
    sub += (c - sub) * kk


def render_map(world, t, cam):
    cx, cy, w = cam
    px = w / W
    L, CO, RV = draw_base(world, cam)
    crop = crop_for(cam)
    fl = world.fields(t, crop[0])

    b1, b2 = blur(L, 5), blur(L, 22)
    sea = world.sea_base * (1 + 0.035 * world.noise_lo)[..., None]
    halo = np.clip(b1 * 0.55 + b2 * 0.45, 0, 1) * (1 - L)
    sea = sea + halo[..., None] * (C_SEA_LIGHT - sea) * 0.85
    texf = (1 + 0.022 * world.noise_lo + 0.03 * world.noise_hi).astype(np.float32)
    inner = blur(1 - L, 3) * L
    landc = C_LAND[None, None, :] * (texf * (1 - 0.20 * inner))[..., None]
    img = (sea * (1 - L)[..., None] + landc * L[..., None]).astype(np.float32)
    gr = graticule(cam)
    img *= (1 - 0.07 * gr)[..., None]
    Lin = np.clip((blur(L, 2.5) - 0.72) / 0.22, 0, 1)   # kıyıdan uzak kara (sınır çizgileri için)

    hx = (cx - w / 2) / px + world.xx
    hy = (cy + H / 2 * px) / px - world.yy

    boost = 0.0
    if world.tl.get("peak") is not None and t >= world.tl["peak"]:
        boost = math.exp(-(t - world.tl["peak"]) / 1.6)

    res = {}
    for ln in LAYERS:
        if ln not in fl:
            continue
        f_c, alpha, src_c, e = fl[ln]
        f = resample(f_c, cam, crop)
        a = np.clip(0.5 - f / px, 0, 1) * L * alpha
        res[ln] = (f, a)
        col = LAYER_COL[ln]
        sl = _bbox(a)
        if sl is not None:
            ts = texf[sl][..., None]
            if ln == "tr":
                fs_ = f[sl]
                sh = np.where(fs_ > 0, np.exp(-np.maximum(fs_, 0) / (7 * px)), 0) * L[sl] * 0.20 * alpha
                img[sl] *= (1 - sh)[..., None]
                sub = img[sl]
                sub += (col * ts - sub) * (0.70 * a[sl])[..., None]
            else:
                sub = img[sl]
                sub += (col * ts - sub) * (0.78 * a[sl])[..., None]
                hatch = 0.5 + 0.5 * np.sin(2 * np.pi * (hx[sl] - hy[sl]) / 11.0)
                st = np.clip((hatch - 0.62) / 0.18, 0, 1) * a[sl] * 0.30
                sub += (col * 0.55 - sub) * st[..., None]
        if src_c is not None and e < 1.0 and ln != "tr":
            fsrc = resample(src_c, cam, crop)
            aA = np.clip(0.5 - fsrc / px, 0, 1) * L
            # kurtarılan bölgeler altın ışıkla parlar, yeni işgaller koyu yanar
            blend(img, np.clip(aA - a, 0, 1) * (1 - e) * 0.65, C_GLOW)
            blend(img, np.clip(a - aA, 0, 1) * (1 - e) * 0.35, col * 0.45)

    # sınır çizgileri
    for ln in LAYERS:
        if ln not in res:
            continue
        f, a = res[ln]
        alpha = fl[ln][1]
        af = np.abs(f)
        if ln == "tr":
            bw = 1.5 + 1.2 * boost
            if boost > 0.01:
                gl = np.exp(-af / (7 * px)) * L * 0.55 * boost
                blend(img, gl, C_GLOW)
            blend(img, np.clip(bw - af / px, 0, 1) * Lin * alpha, C_GOLD)
        else:
            blend(img, np.clip(1.25 - af / px, 0, 1) * Lin * (alpha * 0.9), LAYER_COL[ln] * 0.42)

    blend(img, RV * 0.70, C_RIVER)
    blend(img, CO * 0.55, C_COAST)
    img *= world.vignette[..., None]
    return img


# ------------------------------------------------------------------ oklar
def catmull(pts, n=10):
    pts = np.asarray(pts, np.float64)
    if len(pts) < 3:
        return np.vstack([pts[0] + (pts[-1] - pts[0]) * s for s in np.linspace(0, 1, n * 2)])
    P = np.vstack([pts[0] * 2 - pts[1], pts, pts[-1] * 2 - pts[-2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for s in np.linspace(0, 1, n, endpoint=False):
            s2, s3 = s * s, s * s * s
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * s3))
    out.append(P[-2])
    return np.asarray(out)


def partial(pts, p):
    seg = np.sqrt(((pts[1:] - pts[:-1]) ** 2).sum(1))
    cum = np.concatenate([[0], np.cumsum(seg)])
    total = cum[-1]
    if total <= 0:
        return pts[:1], 0.0
    target = total * clamp01(p)
    j = int(np.searchsorted(cum, target, side="right"))
    if j >= len(pts):
        return pts, total
    j = max(1, j)
    r = (target - cum[j - 1]) / max(1e-9, seg[j - 1])
    tip = pts[j - 1] + (pts[j] - pts[j - 1]) * r
    return np.vstack([pts[:j], tip]), target


# ------------------------------------------------------------------ arayüz
class UI:
    def __init__(self, world):
        self.w = world
        self.tl = world.tl

    def city_screen(self, cam, lon, lat):
        x, y = to_screen(cam, lon, float(merc_y(lat)))
        return float(x), float(y)

    def draw(self, t, cam):
        s = SS
        ov = Image.new("RGBA", (W * s, H * s), (0, 0, 0, 0))
        dr = ImageDraw.Draw(ov, "RGBA")
        dec = self.w.dec_year(t)
        title = self.tl["title"]
        intro_a = 1.0 - smooth((t - (title["t1"] - 0.8)) / 1.2)
        ui_a = smooth((t - (title["t1"] - 0.3)) / 0.8)
        outro_t = self.tl.get("outro")
        out_a = smooth((t - outro_t) / 1.2) if outro_t is not None else 0.0
        hide_rects = self.hide_rects(ui_a * (1 - out_a))
        if out_a > 0.01:
            hide_rects = hide_rects + [(240, 820, 1680, 1010)]
        sevr_a = 0.0
        if self.w.sevr:
            s0, s1 = self.w.sevr
            sevr_a = smooth((t - (s0 + 1.2)) / 0.8) * (1 - smooth((t - s1) / 0.6))
        lab_a = (1.0 - intro_a)
        if lab_a > 0.01:
            self.draw_seas(dr, cam, hide_rects, lab_a)
            self.draw_rivals(dr, cam, dec, hide_rects, lab_a * (1 - 0.8 * sevr_a))
        self.draw_arrows(ov, dr, cam, t)
        bl = self.draw_markers(ov, dr, cam, t, ui_a * (1 - out_a))
        if lab_a > 0.01:
            self.draw_cities(ov, dr, cam, t, hide_rects, bl, lab_a * (1 - 0.92 * sevr_a))
        if sevr_a > 0.01:
            self.draw_sevr(dr, cam, sevr_a)
        if ui_a > 0.01:
            a = ui_a * (1 - out_a)
            self.draw_date(dr, t, dec, a)
            self.draw_legend(ov, dr, a)
            self.draw_timeline(dr, t, dec, a)
            self.draw_card(ov, dr, t, a)
        if intro_a > 0.01:
            self.draw_title(dr, intro_a, t)
        if out_a > 0.01:
            self.draw_outro(dr, out_a)
        return ov, intro_a, out_a

    def hide_rects(self, a):
        if a < 0.05:
            return []
        return [(0, 0, 560, 225), (1540, 20, 1920, 345), (40, 780, 700, 1030), (700, 990, 1920, 1080)]

    @staticmethod
    def rect_fade(x, y, rects, pad=30):
        f = 1.0
        for (x0, y0, x1, y1) in rects:
            if x0 - pad < x < x1 + pad and y0 - pad < y < y1 + pad:
                f = 0.0
        if x < 40 or x > W - 40 or y < 30 or y > H - 30:
            f = 0.0
        return f

    # ----- denizler
    def draw_seas(self, dr, cam, rects, ui_a):
        s = SS
        w = cam[2]
        for name, lon, lat, (mn, mxw), size in SEAS:
            a = smooth((w - mn) / (0.25 * mn + 0.5)) * smooth((mxw - w) / (0.25 * mxw)) * ui_a
            if a < 0.02:
                continue
            x, y = self.city_screen(cam, lon, lat)
            a *= self.rect_fade(x, y, rects, 60)
            if a < 0.02:
                continue
            f = font("garamond-i", 28 * size * s, "Italic")
            text_spaced(dr, x * s, y * s, name, f, (200, 222, 230, int(170 * a)), 3 * s, "c",
                        anchor_v="m")

    # ----- komşu devletler
    def draw_rivals(self, dr, cam, dec, rects, ui_a):
        s = SS
        w = cam[2]
        for name, lon, lat, ranges, (mn, mxw) in RIVALS:
            ya = 0.0
            for y0, y1 in ranges:
                ya = max(ya, smooth((dec - y0) / 0.08 + 0.5) * smooth((y1 - dec) / 0.08 + 0.5))
            a = ya * smooth((w - mn) / (0.25 * mn + 0.5)) * smooth((mxw - w) / (0.25 * mxw)) * ui_a
            if a < 0.02:
                continue
            x, y = self.city_screen(cam, lon, lat)
            a *= self.rect_fade(x, y, rects, 40)
            if a < 0.02:
                continue
            f = font("cinzel", 19 * s, "Bold")
            text_spaced(dr, x * s, y * s, name, f, (88, 58, 38, int(160 * a)), 4 * s, "c",
                        anchor_v="m", stroke=2 * s, stroke_fill=(238, 226, 198, int(80 * a)))

    # ----- Sevr bölgeleri
    def draw_sevr(self, dr, cam, a):
        s = SS
        cx = W / 2 * s
        f = font("cinzel", 21 * s, "Bold")
        for name, lon, lat in SEVR_LABELS:
            x, y = self.city_screen(cam, lon, lat)
            text_spaced(dr, x * s, y * s, name, f, (255, 248, 232, int(240 * a)), 3 * s, "c",
                        anchor_v="m", stroke=3 * s, stroke_fill=(30, 20, 14, int(200 * a)))
        bw, bh = 640, 64
        x0, y0 = W / 2 - bw / 2, 30
        dr.rounded_rectangle([x0 * s, y0 * s, (x0 + bw) * s, (y0 + bh) * s], radius=8 * s,
                             fill=(70, 14, 18, int(220 * a)), outline=GOLD + (int(220 * a),), width=s)
        text_spaced(dr, cx, (y0 + bh / 2) * s, "SEVR ANTLAŞMASI'NIN PAYLAŞIM PLANI",
                    font("cinzel", 24 * s, "Bold"), CREAM + (int(255 * a),), 3 * s, "c", anchor_v="m")

    # ----- şehirler
    def capital_at(self, t):
        cap, tc = None, 0
        for c in self.tl["capitals"]:
            if t < c["t"]:
                break
            cap, tc = c["name"], c["t"]
        return cap, tc

    def draw_cities(self, ov, dr, cam, t, rects, marker_pos, ui_a):
        s = SS
        w = cam[2]
        cap, tc = self.capital_at(t)
        for name, lon, lat, maxw, imp in CITIES:
            is_cap = cap == name
            mw = maxw * (2.5 if is_cap else 1.0)
            a = smooth((mw - w) / (0.3 * mw)) * ui_a
            if a < 0.02:
                continue
            x, y = self.city_screen(cam, lon, lat)
            a *= self.rect_fade(x, y, rects, 10)
            for bx, by, ba in marker_pos:
                if abs(bx - x) < 150 and abs(by - y) < 44:
                    a *= 1 - smooth(ba * 4)
            if a < 0.02:
                continue
            xs, ys = x * s, y * s
            if is_cap:
                ca = smooth((t - tc) / 0.6) if tc > 0 else 1.0
                star = self.w.sprites.get("star", (30 + 12 * (1 - ca)) * s)
                ov.alpha_composite(with_alpha(star, a * ca),
                                   (int(xs - star.width / 2), int(ys - star.height / 2)))
                if ca < 1:
                    rr = (14 + 60 * ca) * s
                    dr.ellipse([xs - rr, ys - rr, xs + rr, ys + rr],
                               outline=GOLD + (int(220 * (1 - ca) * a),), width=3 * s)
            else:
                r = (4.4 if imp >= 2 else 3.5) * s
                dr.ellipse([xs - r, ys - r, xs + r, ys + r], fill=(250, 244, 228, int(255 * a)),
                           outline=INK + (int(255 * a),), width=max(2, int(1.3 * s)))
            size = 26 if (imp >= 2 or is_cap) else 21
            f = font("garamond", size * s, "SemiBold" if (imp >= 2 or is_cap) else "Medium")
            dr.text((xs + 12 * s, ys), name, font=f, fill=(42, 28, 18, int(255 * a)), anchor="lm",
                    stroke_width=3 * s, stroke_fill=(240, 230, 204, int(210 * a)))

    # ----- oklar
    def draw_arrows(self, ov, dr, cam, t):
        s = SS
        for ar in self.tl["arrows"]:
            age = t - ar["t"]
            if age < 0:
                continue
            side = ar["side"]
            end = self.w.route_end if side == "route" else ar["scene_end"] + 0.3
            fade = 1 - smooth((t - end) / 0.8)
            if fade < 0.01:
                continue
            p = ease_io(age / ar["dur"]) if side != "route" else clamp01(age / ar["dur"])
            if side == "route":
                p = 0.5 - 0.5 * math.cos(math.pi * p)
            ll = np.asarray(ar["path"], np.float64)
            X, Y = to_screen(cam, ll[:, 0], merc_y(ll[:, 1]))
            pts = catmull(np.column_stack([X, Y]), 12)
            part, length = partial(pts, p)
            if len(part) < 2 or length < 2:
                continue
            P = [(float(a * s), float(b * s)) for a, b in part]
            if side == "route":
                self._route(dr, part, fade, p < 1)
                continue
            wf = ar.get("width", 1.0)
            if side == "tr":
                body, edge = (196, 30, 40), (255, 222, 150)
            elif side == "retreat":
                body, edge = (150, 40, 44), (240, 220, 200)
            else:
                body, edge = (52, 100, 190), (16, 26, 50)
            wd = 13 * wf
            al = int(235 * fade)
            # gövde
            d = part[-1] - part[-2]
            k = 2
            while np.hypot(*d) < 1e-3 and k < len(part):
                k += 1
                d = part[-1] - part[-k]
            ang = math.atan2(d[1], d[0])
            hl = wd * 2.1
            back = (part[-1][0] - math.cos(ang) * hl * 0.8, part[-1][1] - math.sin(ang) * hl * 0.8)
            body_pts = P[:-1] + [(back[0] * s, back[1] * s)] if length > hl else P[:1] + [(back[0] * s, back[1] * s)]
            dr.line(body_pts, fill=edge + (al,), width=int((wd + 5) * s), joint="curve")
            if side == "retreat":
                self._dashes(dr, body_pts, body + (al,), int(wd * s))
            else:
                dr.line(body_pts, fill=body + (al,), width=int(wd * s), joint="curve")
            # uç
            tipx, tipy = part[-1]
            ca, sa = math.cos(ang), math.sin(ang)
            hw = wd * 1.35
            bx, by = tipx - ca * hl, tipy - sa * hl
            head = [(tipx + ca * 3, tipy + sa * 3), (bx - sa * hw, by + ca * hw), (bx + sa * hw, by - ca * hw)]
            dr.polygon([(a * s, b * s) for a, b in head], fill=body + (al,), outline=edge + (al,),
                       width=max(2, int(2.2 * s)))

    @staticmethod
    def _dashes(dr, pts, col, width, on=26, off=14):
        P = np.asarray(pts)
        seg = np.sqrt(((P[1:] - P[:-1]) ** 2).sum(1))
        pos, draw_on, left = 0.0, True, on * SS
        cur = [tuple(P[0])]
        for i in range(len(seg)):
            a, b, L = P[i], P[i + 1], seg[i]
            u = 0.0
            while L - u > left:
                u += left
                q = a + (b - a) * (u / L)
                cur.append(tuple(q))
                if draw_on and len(cur) > 1:
                    dr.line(cur, fill=col, width=width)
                draw_on = not draw_on
                left = (on if draw_on else off) * SS
                cur = [tuple(q)]
            left -= L - u
            cur.append(tuple(b))
        if draw_on and len(cur) > 1:
            dr.line(cur, fill=col, width=width)

    def _route(self, dr, part, fade, moving):
        s = SS
        P = [(float(a * s), float(b * s)) for a, b in part]
        al = int(240 * fade)
        dr.line(P, fill=(40, 20, 10, int(150 * fade)), width=int(7 * s), joint="curve")
        self._dashes(dr, P, GOLD + (al,), int(4 * s), 12, 8)
        x, y = part[-1]
        r = (9 if moving else 6) * s
        dr.ellipse([x * s - r, y * s - r, x * s + r, y * s + r], fill=(255, 236, 180, al),
                   outline=(90, 30, 20, al), width=2 * s)

    # ----- olay işaretleri
    def draw_markers(self, ov, dr, cam, t, ui_a):
        s = SS
        positions = []
        for b in self.tl["markers"]:
            age = t - b["t"]
            if age < 0:
                continue
            # aynı yerde daha yeni bir işaret varsa eskisini sil
            newer = [m for m in self.tl["markers"] if m["t"] > b["t"] and t >= m["t"]
                     and abs(m["lon"] - b["lon"]) < 0.05 and abs(m["lat"] - b["lat"]) < 0.05]
            gone = smooth((t - newer[0]["t"]) / 0.3) if newer else 0.0
            if b["kind"] in ("occ", "event"):
                gone = max(gone, smooth((t - (b["scene_end"] + 0.6)) / 0.8))
            gone = 1 - (1 - gone) * ui_a
            if gone >= 0.999:
                continue
            x, y = self.city_screen(cam, b["lon"], b["lat"])
            if not (-60 < x < W + 60 and -60 < y < H + 60):
                continue
            settle = smooth((t - (b["scene_end"] + 0.2)) / 0.7)
            pop = ease_out(age / 0.25) * (1 - gone)
            bounce = 1 + 0.30 * math.sin(math.pi * clamp01(age / 0.5)) * (age < 0.5)
            kind = b["kind"]
            big = 52 if kind in ("win", "loss") else 40
            small = 24 if cam[2] < 12 else 18
            if kind in ("occ", "event"):
                small = 16 if cam[2] < 12 else 12
            size = (big * (1 - settle) + small * settle) * pop * bounce
            if size < 2:
                continue
            ring_col = {"loss": (200, 205, 215), "occ": (120, 160, 230), "event": GOLD,
                        "win": GOLD}[kind]
            xs, ys = x * s, y * s
            for k in (0.0, 0.5):
                ra = age - k
                if 0 < ra < 1.4:
                    rr = (10 + 80 * ease_out(ra / 1.4)) * s
                    al = int(230 * (1 - ra / 1.4) * (1 - gone))
                    dr.ellipse([xs - rr, ys - rr, xs + rr, ys + rr], outline=ring_col + (al,), width=3 * s)
            if kind in ("win", "loss"):
                rd = size * 0.62 * s
                dr.ellipse([xs - rd, ys - rd, xs + rd, ys + rd], fill=(20, 14, 10, int(150 * pop)),
                           outline=ring_col + (int(200 * pop),), width=max(2, int(1.5 * s)))
            spr = self.w.sprites.get(kind, size * s)
            ov.alpha_composite(with_alpha(spr, clamp01(pop)) if pop < 0.999 else spr,
                               (int(xs - spr.width / 2), int(ys - spr.height / 2)))
            la = smooth(age / 0.35) * (1 - settle) * (1 - gone)
            if la > 0.02:
                f = font("garamond", 30 * s, "Bold")
                tx = xs + (size * 0.75 + 8) * s
                anchor = "lm"
                tw = f.getlength(b["label"]) / s
                rx0, rx1 = x + size * 0.75 + 8, x + size * 0.75 + 8 + tw
                clash_ = any(rx1 > a0 and rx0 < a1 and b0 - 22 < y < b1 + 22
                             for a0, b0, a1, b1 in self.hide_rects(1.0))
                if rx1 > W - 30 or clash_:
                    tx = xs - (size * 0.75 + 8) * s
                    anchor = "rm"
                dr.text((tx, ys), b["label"], font=f, fill=(255, 246, 226, int(255 * la)), anchor=anchor,
                        stroke_width=4 * s, stroke_fill=(30, 18, 10, int(210 * la)))
                positions.append((x, y, la))
        return positions

    # ----- tarih
    def draw_date(self, dr, t, dec, a):
        s = SS
        cur, prev = self.w.date_at(t)
        year = int(math.floor(dec + 1e-6))
        f = font("cinzel", 104 * s, "Bold")
        dr.text((62 * s, 140 * s), str(year), font=f, fill=GOLD + (int(255 * a),), anchor="ls",
                stroke_width=2 * s, stroke_fill=(40, 24, 10, int(180 * a)))
        if cur is not None:
            fm = font("cinzel", 30 * s, "Bold")
            age = t - cur["t"]
            for d, al, dy in ((prev, 1 - smooth(age / 0.3), -10 * smooth(age / 0.3)),
                              (cur, smooth(age / 0.4), 12 * (1 - ease_out(age / 0.4)))):
                if d is None or al < 0.02:
                    continue
                y_, m_, day = d["date"]
                txt = (f"{day} " if day else "") + AYLAR[m_ - 1]
                text_spaced(dr, 66 * s, (50 + dy) * s, txt, fm, CREAM + (int(240 * a * al),), 4 * s,
                            stroke=2 * s, stroke_fill=(30, 20, 10, int(140 * a * al)))
        era = ERAS[0][2]
        for e0, e1, name in ERAS:
            if e0 <= dec < e1:
                era = name
        if dec >= ERAS[-1][1]:
            era = ERAS[-1][2]
        dr.line([(66 * s, 160 * s), (470 * s, 160 * s)], fill=GOLD + (int(160 * a),), width=s)
        text_spaced(dr, 66 * s, 192 * s, era, font("cinzel", 21 * s, "Bold"),
                    CREAM + (int(235 * a),), 4 * s, stroke=2 * s, stroke_fill=(30, 20, 10, int(120 * a)))

    # ----- lejant
    def draw_legend(self, ov, dr, a):
        s = SS
        x0, y0, x1, y1 = 1568, 30, 1890, 334
        dr.rounded_rectangle([x0 * s, y0 * s, x1 * s, y1 * s], radius=8 * s,
                             fill=(16, 12, 9, int(190 * a)), outline=(196, 160, 90, int(200 * a)), width=s)
        f = font("garamond", 23 * s, "Medium")
        rows = [("tr", LAYER_NAME["tr"]), ("gr", LAYER_NAME["gr"]), ("br", LAYER_NAME["br"]),
                ("fr", LAYER_NAME["fr"]), ("it", LAYER_NAME["it"]), ("ar", LAYER_NAME["ar"])]
        for i, (ln, label) in enumerate(rows):
            cy = (y0 + 28 + i * 34) * s
            sx0, sx1 = (x0 + 18) * s, (x0 + 52) * s
            col = rgb8(LAYER_COL[ln])
            dr.rectangle([sx0, cy - 9 * s, sx1, cy + 9 * s], fill=col + (int(255 * a),),
                         outline=(GOLD if ln == "tr" else rgb8(LAYER_COL[ln], 0.45)) + (int(255 * a),),
                         width=s)
            dr.text(((x0 + 66) * s, cy), label, font=f, fill=CREAM + (int(240 * a),), anchor="lm")
        cy = (y0 + 28 + 6 * 34 + 8) * s
        dr.line([((x0 + 16) * s, cy - 18 * s), ((x1 - 16) * s, cy - 18 * s)],
                fill=(196, 160, 90, int(90 * a)), width=s)
        items = [("win", "Türk zaferi"), ("loss", "Yenilgi"), ("event", "Önemli olay"), ("occ", "İşgal")]
        fs = font("garamond", 21 * s, "Medium")
        for i, (kind, label) in enumerate(items):
            col_x = x0 + 18 + (i % 2) * 154
            yy = cy + (i // 2) * 34 * s
            spr = self.w.sprites.get(kind, (28 if kind in ("win", "loss") else 20) * s)
            ov.alpha_composite(with_alpha(spr, a), (int((col_x + 15) * s - spr.width / 2), int(yy - spr.height / 2)))
            dr.text(((col_x + 36) * s, yy), label, font=fs, fill=CREAM + (int(230 * a),), anchor="lm")

    # ----- zaman çizgisi
    def draw_timeline(self, dr, t, dec, a):
        s = SS
        x0, x1, y = 760, 1860, 1040
        y_a, y_b = TL_RANGE

        def X(yr):
            return x0 + (x1 - x0) * (yr - y_a) / (y_b - y_a)
        ef = font("cinzel", 13 * s, "Bold")
        for e0, e1, name in ERAS:
            xa, xb = X(max(e0, y_a)), X(min(e1, y_b))
            on = dec >= e0
            dr.line([(xa * s + 3 * s, (y - 14) * s), (xb * s - 3 * s, (y - 14) * s)],
                    fill=(196, 160, 90, int((150 if on else 80) * a)), width=s)
            text_spaced(dr, (xa + xb) / 2 * s, (y - 21) * s, name.replace(" DÖNEMİ", ""), ef,
                        (226, 210, 170, int((210 if on else 110) * a)), 2 * s, "c")
        dr.line([(x0 * s, y * s), (x1 * s, y * s)], fill=(255, 255, 255, int(70 * a)), width=2 * s)
        xc = X(min(max(dec, y_a), y_b))
        dr.line([(x0 * s, y * s), (xc * s, y * s)], fill=GOLD + (int(255 * a),), width=4 * s)
        seen = set()
        for d in self.tl["dates"]:
            k = round(d["dec"], 3)
            if k in seen:
                continue
            seen.add(k)
            xx = X(d["dec"]) * s
            on = dec >= d["dec"] - 0.001
            r = 3.5 * s
            dr.polygon([(xx, y * s - r), (xx + r, y * s), (xx, y * s + r), (xx - r, y * s)],
                       fill=(GOLD if on else (150, 150, 150)) + (int(255 * a),))
        lf = font("garamond", 19 * s, "Medium")
        for yr in (1919, 1920, 1921, 1922, 1923):
            dr.line([(X(yr) * s, (y + 6) * s), (X(yr) * s, (y + 11) * s)], fill=(220, 210, 190, int(150 * a)), width=s)
            dr.text((X(yr) * s, (y + 25) * s), str(yr), font=lf, fill=(220, 210, 190, int(170 * a)), anchor="mm")
        rr = 7 * s
        dr.ellipse([xc * s - rr, y * s - rr, xc * s + rr, y * s + rr], fill=CREAM + (int(255 * a),),
                   outline=GOLD + (int(255 * a),), width=2 * s)

    # ----- bilgi kartı
    def draw_card(self, ov, dr, t, a):
        cards = self.tl["cards"]
        cur, prev = None, None
        for c in cards:
            if t < c["t"]:
                break
            prev, cur = cur, c
        if cur is None:
            return
        age = t - cur["t"]
        fin = smooth(age / 0.45)
        if prev is not None and age < 0.25:
            self._card(ov, dr, prev, a * (1 - smooth(age / 0.25)), 0)
        self._card(ov, dr, cur, a * fin, (1 - ease_out(age / 0.45)) * 18)

    def _card(self, ov, dr, c, a, dy):
        if a < 0.02:
            return
        s = SS
        x0, y0, x1, y1 = 52, 782 + dy, 712, 1022 + dy
        acc = {"loss": (150, 170, 205), "occ": (120, 160, 230), "win": GOLD,
               "event": (236, 170, 120)}.get(c["result"], GOLD)
        dr.rounded_rectangle([x0 * s, y0 * s, x1 * s, y1 * s], radius=10 * s,
                             fill=(14, 11, 8, int(214 * a)), outline=(196, 160, 90, int(210 * a)), width=s)
        dr.rectangle([(x0 + 1) * s, (y0 + 14) * s, (x0 + 7) * s, (y1 - 14) * s], fill=acc + (int(255 * a),))
        tx = (x0 + 30) * s
        text_spaced(dr, tx, (y0 + 38) * s, c["tag"], font("cinzel", 18 * s, "Bold"), acc + (int(255 * a),),
                    2 * s)
        tf = font("garamond", 44 * s, "SemiBold")
        if tf.getlength(c["title"]) > (x1 - x0 - 56) * s:
            tf = font("garamond", 38 * s, "SemiBold")
        dr.text((tx, (y0 + 86) * s), c["title"], font=tf, fill=CREAM + (int(255 * a),), anchor="ls")
        fs = font("garamond-i", 26 * s, "Italic")
        parts = c["sub"].split("⚔")
        x = tx
        ys = (y0 + 124) * s
        for i, part in enumerate(parts):
            part = part.strip()
            if i > 0:
                spr = self.w.sprites.get("loss" if c["result"] == "loss" else "win", 26 * s)
                x += 8 * s
                ov.alpha_composite(with_alpha(spr, a), (int(x), int(ys - 19 * s)))
                x += spr.width + 8 * s
            dr.text((x, ys), part, font=fs, fill=(226, 206, 160, int(255 * a)), anchor="ls")
            x += fs.getlength(part)
        fd = font("garamond", 24 * s, "Regular")
        maxw = (x1 - x0 - 56) * s
        words, lines, line = c["desc"].split(), [], ""
        for wd in words:
            test = (line + " " + wd).strip()
            if fd.getlength(test) > maxw and line:
                lines.append(line)
                line = wd
            else:
                line = test
        lines.append(line)
        for i, ln in enumerate(lines[:3]):
            dr.text((tx, (y0 + 162 + i * 29) * s), ln, font=fd, fill=(214, 204, 186, int(250 * a)), anchor="ls")

    # ----- açılış / kapanış
    def draw_title(self, dr, a, t):
        s = SS
        cx = W / 2 * s
        ap = a * smooth((t - 0.2) / 1.0)
        f1 = font("cinzel", 104 * s, "Bold")
        text_spaced(dr, cx, 470 * s, "KURTULUŞ SAVAŞI", f1, GOLD + (int(255 * ap),), 8 * s, "c",
                    stroke=2 * s, stroke_fill=(30, 18, 8, int(200 * ap)))
        dr.line([(cx - 440 * s, 512 * s), (cx + 440 * s, 512 * s)], fill=GOLD + (int(200 * ap),), width=2 * s)
        f2 = font("garamond-i", 52 * s, "Italic")
        dr.text((cx, 576 * s), "Mondros'tan Cumhuriyet'e", font=f2, fill=CREAM + (int(255 * ap),),
                anchor="ms", stroke_width=2 * s, stroke_fill=(20, 12, 6, int(160 * ap)))
        f3 = font("cinzel", 40 * s, "Bold")
        text_spaced(dr, cx, 646 * s, "1918 – 1923", f3, (230, 214, 176, int(240 * ap)), 8 * s, "c")

    def draw_outro(self, dr, a):
        s = SS
        cx = W / 2 * s
        f1 = font("cinzel", 64 * s, "Bold")
        text_spaced(dr, cx, 905 * s, "TÜRKİYE CUMHURİYETİ", f1, GOLD + (int(255 * a),), 6 * s, "c",
                    stroke=2 * s, stroke_fill=(20, 12, 6, int(220 * a)))
        f2 = font("garamond-i", 40 * s, "Italic")
        dr.text((cx, 965 * s), "29 Ekim 1923 · Egemenlik kayıtsız şartsız milletindir",
                font=f2, fill=CREAM + (int(255 * a),), anchor="ms", stroke_width=2 * s,
                stroke_fill=(20, 12, 6, int(200 * a)))


# ------------------------------------------------------------------ kare
def render_frame(world, ui, t):
    cam = world.cam.at(t)
    img = render_map(world, t, cam)
    ov, intro_a, out_a = ui.draw(t, cam)
    dim = 0.45 * intro_a + 0.30 * out_a
    if world.sevr:
        s0, s1 = world.sevr
        dim += 0.10 * smooth((t - (s0 + 1.2)) / 0.8) * (1 - smooth((t - s1) / 0.6))
    if dim > 0:
        img *= (1 - dim)
    dur = world.tl["duration"]
    fade = smooth((dur - t) / 1.0) * smooth(t / 0.6)
    img *= fade
    base = Image.fromarray(np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    ovs = ov.convert("RGBa").reduce(SS).convert("RGBA")
    if fade < 0.999:
        ovs = with_alpha(ovs, fade)
    base.alpha_composite(ovs)
    return base.convert("RGB")


_WORLD = None


def _init_world(world):
    global _WORLD
    _WORLD = world


def render_segment(args):
    i0, i1, path = args
    world = _WORLD
    ui = UI(world)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
           "-crf", "18", "-pix_fmt", "yuv420p", "-threads", "2", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(i0, i1):
        fr = render_frame(world, ui, i / FPS)
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    p.wait()
    return path
