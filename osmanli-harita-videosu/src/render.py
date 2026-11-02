"""Harita animasyonunun kare kare çizimi.

Katmanlar: deniz → kara (Natural Earth, vektör) → Osmanlı toprakları (SDF,
dalga şeklinde yayılan geçişler) → sınırlar → nehirler/kıyılar → arayüz
(yıl, bilgi kartı, savaş işaretleri, etiketler, zaman çizgisi).
"""
import math
import os
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import sdf as G
from config import W, H, FPS, FONT_DIR
from geo import merc_y
from story import CITIES, RIVALS, SEAS, ERAS, FULL_VIEW

# ------------------------------------------------------------------ renkler
C_SEA_DEEP = np.array([0.105, 0.215, 0.270], np.float32)
C_SEA = np.array([0.165, 0.315, 0.375], np.float32)
C_SEA_LIGHT = np.array([0.330, 0.520, 0.560], np.float32)
C_LAND = np.array([0.905, 0.855, 0.735], np.float32)
C_CORE = np.array([0.660, 0.075, 0.130], np.float32)
C_VAS = np.array([0.870, 0.480, 0.360], np.float32)
C_VAS_DARK = np.array([0.700, 0.200, 0.180], np.float32)
C_GOLD = np.array([0.965, 0.800, 0.400], np.float32)
C_GLOW = np.array([1.000, 0.760, 0.360], np.float32)
C_LOSS = np.array([0.220, 0.050, 0.070], np.float32)
C_RIVER = np.array([0.330, 0.520, 0.600], np.float32)
C_COAST = np.array([0.300, 0.230, 0.160], np.float32)

GOLD = (236, 200, 112)
CREAM = (246, 236, 214)
INK = (52, 36, 24)
PARCH = (238, 226, 198)

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
        self.city = {c[0]: c for c in CITIES}
        rng = np.random.default_rng(7)
        lo = rng.normal(0, 1, (27, 48)).astype(np.float32)
        self.noise_lo = np.asarray(Image.fromarray(lo, "F").resize((W, H), Image.BICUBIC))
        hi = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
        self.noise_hi = np.asarray(Image.fromarray(hi, "F").resize((W, H), Image.BILINEAR))
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        vig = 1 - 0.38 * np.clip(r - 0.45, 0, 1) ** 1.5
        # arayüz arkasında hafif koyulaştırma (okunabilirlik)
        tlc = np.exp(-(((xx - 150) / 520) ** 2 + ((yy - 90) / 210) ** 2))
        bot = np.clip((yy - 930) / 150, 0, 1) ** 1.5
        self.vignette = (vig * (1 - 0.35 * tlc) * (1 - 0.35 * bot)).astype(np.float32)
        self.xx, self.yy = xx, yy
        g = np.clip(1 - r * 0.9, 0, 1)[..., None]
        self.sea_base = (C_SEA_DEEP * (1 - g) + C_SEA * g).astype(np.float32)

    # ---------- toprak alanları
    def _get(self, key, layer, sl):
        arr = self.sdfs[key][0 if layer == "core" else 1]
        return arr[sl].astype(np.float32) / G.SCALE

    def dmax(self, a, b, layer):
        k = (a, b, layer)
        if k not in self._dmax:
            Ac, Av = [x.astype(np.float32) / G.SCALE for x in self.sdfs[a]]
            Bc, Bv = [x.astype(np.float32) / G.SCALE for x in self.sdfs[b]]
            if layer == "core":
                SA, SB, src, dst = Ac, Bc, Ac, Bc
            else:
                SA, SB, src, dst = Av, Bv, np.minimum(Av, Ac), np.minimum(Bv, Bc)
            gain = (SB < 0) & (src > 0)
            loss = (SA < 0) & (dst > 0)
            dg = float(src[gain].max()) if gain.any() else 0.0
            dl = float(dst[loss].max()) if loss.any() else 0.0
            self._dmax[k] = (dg + 0.02, dl + 0.02)
        return self._dmax[k]

    def terr_state(self, t):
        last = None
        for tr in self.tl["terr"]:
            if t < tr["t"]:
                break
            last = tr
        if last is None:
            return "empty", None, 1.0
        p = (t - last["t"]) / last["dur"]
        if p >= 1:
            return last["dst"], None, 1.0
        return last["src"], last["dst"], p

    def fields(self, t, sl):
        """(core, vassal, kaynak_core, r_g, Dg, e) kırpılmış alanlar."""
        a, b, p = self.terr_state(t)
        if b is None:
            return self._get(a, "core", sl), self._get(a, "vassal", sl), None, 0, 0, 1.0
        e = ease_io(p)
        out = []
        info = None
        for layer in ("core", "vassal"):
            SA = self._get(a, layer, sl)
            SB = self._get(b, layer, sl)
            if layer == "core":
                src, dst = SA, SB
            else:
                src = np.minimum(SA, self._get(a, "core", sl))
                dst = np.minimum(SB, self._get(b, "core", sl))
            dg, dl = self.dmax(a, b, layer)
            rg, rl = e * dg, (1 - e) * dl
            f = np.minimum(np.maximum(SB, src - rg), np.maximum(SA, dst - rl))
            out.append(f)
            if layer == "core":
                info = (SA, rg, dg)
        return out[0], out[1], info[0], info[1], info[2], e

    # ---------- yıl
    def display_year(self, t):
        ys = self.tl["years"]
        prev, cur, t0 = 1299, None, None
        for y in ys:
            if t < y["t"]:
                break
            prev = cur if cur is not None else prev
            cur, t0 = y["year"], y["t"]
        if cur is None:
            return 1299.0
        p = (t - t0) / 0.9
        if p >= 1:
            return float(cur)
        return prev + (cur - prev) * ease_io(p)


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


def render_map(world, t, cam):
    cx, cy, w = cam
    px = w / W
    L, CO, RV = draw_base(world, cam)
    crop = crop_for(cam)
    fcore_c, fvas_c, src_c, rg, dg, e = world.fields(t, crop[0])
    fcore = resample(fcore_c, cam, crop)
    fvas = resample(fvas_c, cam, crop)

    b1, b2 = blur(L, 5), blur(L, 22)
    sea = world.sea_base * (1 + 0.035 * world.noise_lo)[..., None]
    halo = np.clip(b1 * 0.55 + b2 * 0.45, 0, 1) * (1 - L)
    sea = sea + halo[..., None] * (C_SEA_LIGHT - sea) * 0.85
    texf = (1 + 0.022 * world.noise_lo + 0.03 * world.noise_hi)
    inner = blur(1 - L, 3) * L
    landc = C_LAND[None, None, :] * (texf * (1 - 0.20 * inner))[..., None]
    img = sea * (1 - L)[..., None] + landc * L[..., None]

    gr = graticule(cam)
    img *= (1 - 0.07 * gr)[..., None]

    # toprak katmanları
    ac = np.clip(0.5 - fcore / px, 0, 1)
    av = np.clip(0.5 - fvas / px, 0, 1) * (1 - ac)
    cc = ac * L
    cv = av * L
    tex = texf[..., None]
    # dış gölge
    sh = np.where(fcore > 0, np.exp(-np.maximum(fcore, 0) / (7 * px)), 0) * L * 0.22
    img *= (1 - sh)[..., None]
    k = 0.38 * cv
    img = img * (1 - k)[..., None] + (C_VAS * tex) * k[..., None]
    hx = (cx - w / 2) / px + world.xx
    hy = (cy + H / 2 * px) / px - world.yy
    hatch = 0.5 + 0.5 * np.sin(2 * np.pi * (hx + hy) / 13.0)
    stripe = np.clip((hatch - 0.55) / 0.2, 0, 1) * cv * 0.38
    img = img * (1 - stripe)[..., None] + C_VAS_DARK * stripe[..., None]
    k = 0.82 * cc
    img = img * (1 - k)[..., None] + (C_CORE * tex) * k[..., None]

    if src_c is not None:
        fsrc = resample(src_c, cam, crop)
        aA = np.clip(0.5 - fsrc / px, 0, 1)
        new = np.clip(ac - aA, 0, 1) * L
        T = max(0.12 * dg, 30 * px)
        trail = np.clip(1 - (rg - fsrc) / T, 0, 1)
        glow = new * (0.2 * (1 - e) + 0.8 * trail) * 0.55
        img = img * (1 - glow)[..., None] + C_GLOW * glow[..., None]
        lost = np.clip(aA - ac, 0, 1) * L * (1 - e) * 0.55
        img = img * (1 - lost)[..., None] + C_LOSS * lost[..., None]

    # zirve anında sınır parlaması
    boost = 0.0
    if world.tl.get("peak") is not None and t >= world.tl["peak"]:
        boost = math.exp(-(t - world.tl["peak"]) / 1.4)
    bw = 1.45 + 1.0 * boost
    bc = np.clip(bw - np.abs(fcore) / px, 0, 1) * L
    if boost > 0.01:
        gl = np.exp(-np.abs(fcore) / (6 * px)) * L * 0.5 * boost
        img = img * (1 - gl)[..., None] + C_GLOW * gl[..., None]
    img = img * (1 - bc)[..., None] + C_GOLD * bc[..., None]
    bv = np.clip(1.0 - np.abs(fvas) / px, 0, 1) * L * (1 - ac) * 0.65
    img = img * (1 - bv)[..., None] + np.array([0.98, 0.88, 0.70], np.float32) * bv[..., None]

    rv = RV * 0.75
    img = img * (1 - rv)[..., None] + C_RIVER * rv[..., None]
    co = CO * 0.55
    img = img * (1 - co)[..., None] + C_COAST * co[..., None]
    img *= world.vignette[..., None]
    return img


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
        year = self.w.display_year(t)
        title = self.tl["title"]
        intro_a = 1.0 - smooth((t - (title["t1"] - 0.7)) / 1.1)
        ui_a = smooth((t - (title["t1"] - 0.3)) / 0.8)
        outro_t = self.tl.get("outro")
        out_a = smooth((t - outro_t) / 1.2) if outro_t is not None else 0.0
        hide_rects = self.hide_rects(ui_a * (1 - out_a))
        if out_a > 0.01:
            hide_rects = hide_rects + [(260, 830, 1660, 1000)]
        lab_a = 1.0 - intro_a
        if lab_a > 0.01:
            self.draw_seas(dr, cam, t, hide_rects, lab_a)
            self.draw_rivals(dr, cam, t, year, hide_rects, lab_a)
        bl = self.draw_battles(ov, dr, cam, t, ui_a)
        if lab_a > 0.01:
            self.draw_cities(ov, dr, cam, t, year, hide_rects, bl, lab_a)
        if ui_a > 0.01:
            self.draw_year(dr, year, ui_a * (1 - out_a))
            self.draw_legend(ov, dr, ui_a * (1 - out_a))
            self.draw_timeline(dr, year, ui_a * (1 - out_a))
            self.draw_card(ov, dr, t, ui_a * (1 - out_a))
        if intro_a > 0.01:
            self.draw_title(dr, intro_a, t)
        if out_a > 0.01:
            self.draw_outro(dr, out_a)
        return ov, intro_a, out_a

    # ----- gizleme alanları (arayüz panelleri)
    def hide_rects(self, a):
        if a < 0.05:
            return []
        return [(0, 0, 560, 210), (1560, 20, 1920, 200), (40, 780, 700, 1030), (700, 1000, 1920, 1080)]

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
    def draw_seas(self, dr, cam, t, rects, ui_a):
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
            f = font("garamond-i", 27 * size * s, "Italic")
            text_spaced(dr, x * s, y * s, name, f, (200, 222, 230, int(170 * a)), 3 * s, "c",
                        anchor_v="m")

    # ----- komşu devletler
    def draw_rivals(self, dr, cam, t, year, rects, ui_a):
        s = SS
        w = cam[2]
        conq = next((b["t"] for b in self.tl["battles"] if b["id"] == "istanbul"), 1e9)
        for name, lon, lat, ranges, (mn, mxw) in RIVALS:
            ya = 0.0
            for y0, y1 in ranges:
                if name == "BİZANS" and y1 == 1453:
                    y1 = 1460
                ya = max(ya, smooth((year - y0) / 2 + 0.5) * smooth((y1 - year) / 2 + 0.5))
            if name == "BİZANS":
                ya *= 1 - smooth((t - conq) / 0.5)
            a = ya * smooth((w - mn) / (0.25 * mn + 0.5)) * smooth((mxw - w) / (0.25 * mxw)) * ui_a
            if a < 0.02:
                continue
            x, y = self.city_screen(cam, lon, lat)
            a *= self.rect_fade(x, y, rects, 40)
            if a < 0.02:
                continue
            f = font("cinzel", 19 * s, "Bold")
            text_spaced(dr, x * s, y * s, name, f, (88, 58, 38, int(150 * a)), 4 * s, "c",
                        anchor_v="m", stroke=2 * s, stroke_fill=(238, 226, 198, int(70 * a)))

    # ----- şehirler
    def capital_at(self, t):
        cap, tc, prev = None, 0, None
        for c in self.tl["capitals"]:
            if t < c["t"]:
                break
            prev, cap, tc = cap, c["name"], c["t"]
        return cap, tc, prev

    def draw_cities(self, ov, dr, cam, t, year, rects, battle_pos, ui_a):
        s = SS
        w = cam[2]
        cap, tc, prev = self.capital_at(t)
        conq = next((b["t"] for b in self.tl["battles"] if b["id"] == "istanbul"), 1e9)
        for name, lon, lat, ranges, maxw, imp in CITIES:
            ya = 0.0
            for y0, y1 in ranges:
                ya = max(ya, smooth((year - y0) / 1.5 + 0.5) * smooth((y1 - year) / 1.5 + 0.5))
            if name == "Konstantinopolis":
                ya *= 1 - smooth((t - conq) / 0.4)
            elif name == "İstanbul":
                ya *= smooth((t - conq) / 0.4)
            is_cap = (cap == name) or (cap == "İstanbul" and name == "İstanbul")
            mw = maxw * (2.5 if is_cap else 1.0)
            a = ya * smooth((mw - w) / (0.3 * mw)) * ui_a
            if a < 0.02:
                continue
            x, y = self.city_screen(cam, lon, lat)
            a *= self.rect_fade(x, y, rects, 10)
            for bx, by, ba in battle_pos:
                if abs(bx - x) < 120 and abs(by - y) < 40:
                    a *= (1 - ba)
            if a < 0.02:
                continue
            xs, ys = x * s, y * s
            if is_cap:
                ca = smooth((t - tc) / 0.6)
                star = self.w.sprites.get("star", (30 + 10 * (1 - ca)) * s)
                ov.alpha_composite(with_alpha(star, a * ca), (int(xs - star.width / 2), int(ys - star.height / 2)))
                if ca < 1:
                    rr = (14 + 50 * ca) * s
                    dr.ellipse([xs - rr, ys - rr, xs + rr, ys + rr], outline=GOLD + (int(220 * (1 - ca) * a),),
                               width=3 * s)
            else:
                r = (4.2 if imp >= 2 else 3.4) * s
                dr.ellipse([xs - r, ys - r, xs + r, ys + r], fill=(250, 244, 228, int(255 * a)),
                           outline=INK + (int(255 * a),), width=max(2, int(1.3 * s)))
            size = 25 if (imp >= 2 or is_cap) else 21
            f = font("garamond", size * s, "SemiBold" if (imp >= 2 or is_cap) else "Medium")
            dr.text((xs + 11 * s, ys), name, font=f, fill=(42, 28, 18, int(255 * a)), anchor="lm",
                    stroke_width=3 * s, stroke_fill=(240, 230, 204, int(200 * a)))

    # ----- savaşlar
    def draw_battles(self, ov, dr, cam, t, ui_a):
        s = SS
        positions = []
        for b in self.tl["battles"]:
            age = t - b["t"]
            if age < 0:
                continue
            x, y = self.city_screen(cam, b["lon"], b["lat"])
            if not (-60 < x < W + 60 and -60 < y < H + 60):
                continue
            settle = smooth((t - (b["scene_end"] + 0.2)) / 0.7)
            pop = ease_out(age / 0.25)
            bounce = 1 + 0.30 * math.sin(math.pi * clamp01(age / 0.5)) * (age < 0.5)
            small = 26 if cam[2] < 20 else (21 if cam[2] < 45 else 17)
            size = (54 * (1 - settle) + small * settle) * pop * bounce
            kind = "loss" if b["result"] == "loss" else "win"
            ring_col = (200, 40, 50) if kind == "loss" else GOLD
            xs, ys = x * s, y * s
            # nabız halkaları
            for k in (0.0, 0.5):
                ra = age - k
                if 0 < ra < 1.4:
                    rr = (10 + 80 * ease_out(ra / 1.4)) * s
                    al = int(230 * (1 - ra / 1.4))
                    dr.ellipse([xs - rr, ys - rr, xs + rr, ys + rr], outline=ring_col + (al,), width=3 * s)
            # koyu disk
            rd = size * 0.62 * s
            dr.ellipse([xs - rd, ys - rd, xs + rd, ys + rd], fill=(20, 14, 10, int(150 * pop)),
                       outline=ring_col + (int(200 * pop),), width=max(2, int(1.5 * s)))
            spr = self.w.sprites.get(kind, size * s)
            ov.alpha_composite(spr, (int(xs - spr.width / 2), int(ys - spr.height / 2)))
            la = smooth(age / 0.35) * (1 - settle)
            if la > 0.02:
                f = font("garamond", 30 * s, "Bold")
                tx = xs + (size * 0.75 + 8) * s
                anchor = "lm"
                if x > W - 330:
                    tx = xs - (size * 0.75 + 8) * s
                    anchor = "rm"
                dr.text((tx, ys), b["label"], font=f, fill=(255, 246, 226, int(255 * la)), anchor=anchor,
                        stroke_width=4 * s, stroke_fill=(30, 18, 10, int(210 * la)))
                positions.append((x, y, la))
        return positions

    # ----- yıl
    def draw_year(self, dr, year, a):
        s = SS
        y = int(round(year))
        f = font("cinzel", 104 * s, "Bold")
        dr.text((62 * s, 128 * s), str(y), font=f, fill=GOLD + (int(255 * a),), anchor="ls",
                stroke_width=2 * s, stroke_fill=(40, 24, 10, int(180 * a)))
        era = ERAS[0][2]
        for y0, y1, name in ERAS:
            if y0 <= y < y1 or (y == y1 and name == ERAS[-1][2]):
                era = name
        dr.line([(66 * s, 146 * s), (400 * s, 146 * s)], fill=GOLD + (int(160 * a),), width=s)
        text_spaced(dr, 66 * s, 176 * s, era, font("cinzel", 21 * s, "Bold"),
                    CREAM + (int(235 * a),), 4 * s, stroke=2 * s, stroke_fill=(30, 20, 10, int(120 * a)))

    # ----- lejant
    def draw_legend(self, ov, dr, a):
        s = SS
        x0, y0, x1, y1 = 1588, 34, 1886, 192
        dr.rounded_rectangle([x0 * s, y0 * s, x1 * s, y1 * s], radius=8 * s,
                             fill=(16, 12, 9, int(185 * a)), outline=(196, 160, 90, int(200 * a)), width=s)
        f = font("garamond", 23 * s, "Medium")
        rows = [("core", "Osmanlı toprakları"), ("vassal", "Bağlı devletler"),
                ("win", "Zafer / fetih"), ("loss", "Yenilgi")]
        for i, (kind, label) in enumerate(rows):
            cy = (y0 + 30 + i * 36) * s
            sx0, sx1 = (x0 + 18) * s, (x0 + 52) * s
            if kind == "core":
                dr.rectangle([sx0, cy - 9 * s, sx1, cy + 9 * s], fill=(170, 22, 38, int(255 * a)),
                             outline=GOLD + (int(255 * a),), width=s)
            elif kind == "vassal":
                sw = Image.new("RGBA", (sx1 - sx0, 18 * s), (222, 140, 112, int(255 * a)))
                sd = ImageDraw.Draw(sw)
                for k in range(-4, 8):
                    xx = k * 7 * s
                    sd.line([(xx, 18 * s), (xx + 18 * s, 0)], fill=(180, 60, 50, int(230 * a)), width=2 * s)
                ov.alpha_composite(sw, (sx0, cy - 9 * s))
                dr.rectangle([sx0, cy - 9 * s, sx1, cy + 9 * s], outline=(250, 225, 180, int(255 * a)), width=s)
            else:
                spr = self.w.sprites.get(kind, 30 * s)
                ov.alpha_composite(with_alpha(spr, a), (int((sx0 + sx1) / 2 - spr.width / 2), int(cy - spr.height / 2)))
            dr.text(((x0 + 66) * s, cy), label, font=f, fill=CREAM + (int(240 * a),), anchor="lm")

    # ----- zaman çizgisi
    def draw_timeline(self, dr, year, a):
        s = SS
        x0, x1, y = 760, 1860, 1040
        y_a, y_b = 1299, 1683

        def X(yr):
            return x0 + (x1 - x0) * (yr - y_a) / (y_b - y_a)
        ef = font("cinzel", 15 * s, "Bold")
        for e0, e1, name in ERAS:
            xa, xb = X(max(e0, y_a)), X(min(e1, y_b))
            dr.line([(xa * s + 3 * s, (y - 14) * s), (xb * s - 3 * s, (y - 14) * s)],
                    fill=(196, 160, 90, int(110 * a)), width=s)
            text_spaced(dr, (xa + xb) / 2 * s, (y - 22) * s, name.replace(" DÖNEMİ", ""), ef,
                        (226, 210, 170, int(170 * a)), 3 * s, "c")
        dr.line([(x0 * s, y * s), (x1 * s, y * s)], fill=(255, 255, 255, int(70 * a)), width=2 * s)
        xc = X(min(max(year, y_a), y_b))
        dr.line([(x0 * s, y * s), (xc * s, y * s)], fill=GOLD + (int(255 * a),), width=4 * s)
        for b in self.tl["years"]:
            yr = b["year"]
            xx = X(yr) * s
            on = year >= yr - 0.01
            r = 4 * s
            dr.polygon([(xx, y * s - r), (xx + r, y * s), (xx, y * s + r), (xx - r, y * s)],
                       fill=(GOLD if on else (150, 150, 150)) + (int(255 * a),))
        lf = font("garamond", 19 * s, "Medium")
        for yr in (1300, 1400, 1500, 1600):
            dr.text((X(yr) * s, (y + 22) * s), str(yr), font=lf, fill=(220, 210, 190, int(170 * a)), anchor="mm")
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
        x0, y0, x1, y1 = 52, 792 + dy, 700, 1018 + dy
        acc = (120, 150, 190) if c["result"] == "loss" else GOLD
        dr.rounded_rectangle([x0 * s, y0 * s, x1 * s, y1 * s], radius=10 * s,
                             fill=(14, 11, 8, int(212 * a)), outline=(196, 160, 90, int(210 * a)), width=s)
        dr.rectangle([(x0 + 1) * s, (y0 + 14) * s, (x0 + 7) * s, (y1 - 14) * s], fill=acc + (int(255 * a),))
        tx = (x0 + 30) * s
        text_spaced(dr, tx, (y0 + 38) * s, c["tag"], font("cinzel", 19 * s, "Bold"), acc + (int(255 * a),),
                    3 * s)
        dr.text((tx, (y0 + 88) * s), c["title"], font=font("garamond", 46 * s, "SemiBold"),
                fill=CREAM + (int(255 * a),), anchor="ls")
        # alt başlık (⚔ işaretiyle)
        fs = font("garamond-i", 27 * s, "Italic")
        parts = c["sub"].split("⚔")
        x = tx
        ys = (y0 + 126) * s
        for i, part in enumerate(parts):
            part = part.strip()
            if i > 0:
                spr = self.w.sprites.get("win" if c["result"] != "loss" else "loss", 26 * s)
                x += 8 * s
                ov.alpha_composite(with_alpha(spr, a), (int(x), int(ys - 19 * s)))
                x += spr.width + 8 * s
            dr.text((x, ys), part, font=fs, fill=(226, 206, 160, int(255 * a)), anchor="ls")
            x += fs.getlength(part)
        # açıklama (satır kaydırma)
        fd = font("garamond", 25 * s, "Regular")
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
            dr.text((tx, (y0 + 164 + i * 30) * s), ln, font=fd, fill=(214, 204, 186, int(250 * a)), anchor="ls")

    # ----- açılış
    def draw_title(self, dr, a, t):
        s = SS
        cx = W / 2 * s
        ap = a * smooth((t - 0.2) / 1.0)
        f1 = font("cinzel", 92 * s, "Bold")
        text_spaced(dr, cx, 470 * s, "OSMANLI İMPARATORLUĞU", f1, GOLD + (int(255 * ap),), 6 * s, "c",
                    stroke=2 * s, stroke_fill=(30, 18, 8, int(200 * ap)))
        dr.line([(cx - 420 * s, 510 * s), (cx + 420 * s, 510 * s)], fill=GOLD + (int(200 * ap),), width=2 * s)
        f2 = font("garamond-i", 50 * s, "Italic")
        dr.text((cx, 572 * s), "Kuruluştan En Geniş Sınırlara", font=f2, fill=CREAM + (int(255 * ap),),
                anchor="ms", stroke_width=2 * s, stroke_fill=(20, 12, 6, int(160 * ap)))
        f3 = font("cinzel", 40 * s, "Bold")
        text_spaced(dr, cx, 640 * s, "1299 – 1683", f3, (230, 214, 176, int(240 * ap)), 8 * s, "c")

    def draw_outro(self, dr, a):
        s = SS
        cx = W / 2 * s
        f1 = font("cinzel", 58 * s, "Bold")
        text_spaced(dr, cx, 905 * s, "SÖĞÜT'TEN VİYANA KAPILARINA", f1, GOLD + (int(255 * a),), 5 * s, "c",
                    stroke=2 * s, stroke_fill=(20, 12, 6, int(220 * a)))
        f2 = font("garamond-i", 40 * s, "Italic")
        dr.text((cx, 965 * s), "1299 – 1683 · 384 yıllık yükseliş", font=f2, fill=CREAM + (int(255 * a),),
                anchor="ms", stroke_width=2 * s, stroke_fill=(20, 12, 6, int(200 * a)))


# ------------------------------------------------------------------ kare
def render_frame(world, ui, t):
    cam = world.cam.at(t)
    img = render_map(world, t, cam)
    ov, intro_a, out_a = ui.draw(t, cam)
    dim = 0.45 * intro_a + 0.30 * out_a
    if dim > 0:
        img *= (1 - dim)
    dur = world.tl["duration"]
    fade = smooth((dur - t) / 0.9) * smooth(t / 0.6 + 0.0)
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
           "-crf", "17", "-pix_fmt", "yuv420p", "-threads", "2", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(i0, i1):
        fr = render_frame(world, ui, i / FPS)
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    p.wait()
    return path
