"""Dönem sınırlarını işaretli mesafe alanlarına (SDF) dönüştürür.

Izgara Mercator koordinatlarındadır (X = boylam, Y = Mercator enlem, ikisi de
'derece' birimi). SDF değeri < 0 ise nokta bölgenin içindedir. Değerler
int16 olarak 0.001 birim hassasiyetle saklanır.
"""
import os

import numpy as np
import shapely
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

from config import CACHE_DIR
from geo import merc_y, project_geom, _polys

GX0, GX1 = 18.0, 51.0
GY0, GY1 = float(merc_y(30.0)), float(merc_y(46.5))
RES = 0.016
NX = int(round((GX1 - GX0) / RES))
NY = int(np.ceil((GY1 - GY0) / RES))
SCALE = 1000.0
CLAMP = 32.0


def cell_centers(rows, cols):
    return GX0 + (cols + 0.5) * RES, GY1 - (rows + 0.5) * RES


def _rasterize(geom_p):
    img = Image.new("L", (NX, NY), 0)
    dr = ImageDraw.Draw(img)
    for p in _polys(geom_p):
        ext = np.asarray(p.exterior.coords)
        pts = np.column_stack([(ext[:, 0] - GX0) / RES - 0.5, (GY1 - ext[:, 1]) / RES - 0.5])
        dr.polygon([tuple(v) for v in pts], fill=1)
        for h in p.interiors:
            hc = np.asarray(h.coords)
            pts = np.column_stack([(hc[:, 0] - GX0) / RES - 0.5, (GY1 - hc[:, 1]) / RES - 0.5])
            dr.polygon([tuple(v) for v in pts], fill=0)
    return np.asarray(img, dtype=bool)


def geom_sdf(geom_ll):
    """lon/lat geometrisinden int16 SDF ızgarası."""
    if geom_ll.is_empty:
        return np.full((NY, NX), int(CLAMP * SCALE), dtype=np.int16)
    gp = project_geom(geom_ll)
    mask = _rasterize(gp)
    d_out = distance_transform_edt(~mask) * RES
    d_in = distance_transform_edt(mask) * RES
    sdf = np.where(mask, -(d_in - 0.5 * RES), d_out - 0.5 * RES).astype(np.float32)

    # sınıra yakın hücrelerde kesin mesafe (kenarların pürüzsüz görünmesi için)
    band = np.abs(sdf) < 3.5 * RES
    rr, cc = np.nonzero(band)
    if len(rr):
        xs, ys = cell_centers(rr, cc)
        bnd = shapely.segmentize(gp.boundary, RES / 6)
        pts = shapely.get_coordinates(bnd)
        tree = cKDTree(pts)
        dist, _ = tree.query(np.column_stack([xs, ys]), workers=-1)
        inside = shapely.contains_xy(gp, xs, ys)
        sdf[rr, cc] = np.where(inside, -dist, dist)
    sdf = np.clip(sdf, -CLAMP, CLAMP)
    return np.round(sdf * SCALE).astype(np.int16)


def point_sdf(lon, lat):
    X, Y = lon, float(merc_y(lat))
    cols = GX0 + (np.arange(NX) + 0.5) * RES
    rows = GY1 - (np.arange(NY) + 0.5) * RES
    d = np.sqrt((cols[None, :] - X) ** 2 + (rows[:, None] - Y) ** 2)
    return np.round(np.clip(d, -CLAMP, CLAMP) * SCALE).astype(np.int16)


def build_all(layer_geoms, force=False):
    """Katman geometrilerini SDF'ye çevirir (aynı geometriler bir kez hesaplanır).

    layer_geoms: {anahtar: {katman: shapely}} → {anahtar: {katman: int16 dizi | None}}
    """
    import hashlib
    uniq = {}
    out = {}
    for key, layers in layer_geoms.items():
        out[key] = {}
        for lname, g in layers.items():
            if g is None or g.is_empty:
                out[key][lname] = None
                continue
            h = hashlib.sha1(g.wkb).hexdigest()[:16]
            if h not in uniq:
                path = os.path.join(CACHE_DIR, f"sdf_{h}.npy")
                if os.path.exists(path) and not force:
                    uniq[h] = np.load(path)
                else:
                    uniq[h] = geom_sdf(g)
                    np.save(path, uniq[h])
                    print(f"  [sdf] {key}/{lname} hazır")
            out[key][lname] = uniq[h]
    return out
