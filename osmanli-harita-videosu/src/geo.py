"""Coğrafi yardımcılar: Mercator projeksiyonu ve Natural Earth katmanları."""
import json
import math
import os
import pickle

import numpy as np
import shapely
from shapely.geometry import box, shape, Point
from shapely.strtree import STRtree

from config import DATA_DIR, CACHE_DIR

# Görüntülenebilir bölge (boylam/enlem)
REGION = (-30.0, -2.0, 90.0, 64.0)


def merc_y(lat):
    lat = np.clip(np.asarray(lat, dtype=np.float64), -85, 85)
    return np.degrees(np.log(np.tan(np.pi / 4 + np.radians(lat) / 2)))


def inv_merc_y(y):
    return np.degrees(2 * np.arctan(np.exp(np.radians(np.asarray(y, dtype=np.float64)))) - np.pi / 2)


def project_coords(coords):
    """Nx2 (lon, lat) -> Nx2 (X, Y) Mercator 'derece' birimi."""
    c = np.asarray(coords, dtype=np.float64)
    return np.column_stack([c[:, 0], merc_y(c[:, 1])])


def project_geom(geom):
    return shapely.transform(geom, project_coords)


def _load(name):
    with open(os.path.join(DATA_DIR, name + ".geojson")) as f:
        return json.load(f)


def _polys(geom):
    if geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        return [geom]
    if hasattr(geom, "geoms"):
        out = []
        for g in geom.geoms:
            out += _polys(g)
        return out
    return []


def _lines(geom):
    if geom.is_empty:
        return []
    if geom.geom_type == "LineString":
        return [geom]
    if hasattr(geom, "geoms"):
        out = []
        for g in geom.geoms:
            out += _lines(g)
        return out
    return []


class Basemap:
    """Kara, göl ve nehir katmanları (lon/lat + Mercator kopyaları)."""

    def __init__(self):
        cache = os.path.join(CACHE_DIR, "basemap.pkl")
        if os.path.exists(cache):
            with open(cache, "rb") as f:
                self.__dict__.update(pickle.load(f))
        else:
            self._build()
            with open(cache, "wb") as f:
                pickle.dump(self.__dict__, f)
        self._tree = STRtree(self.land_ll)

    def _build(self):
        B = box(*REGION)
        land = []
        for f in _load("ne_10m_land")["features"]:
            g = shape(f["geometry"])
            if not g.intersects(B):
                continue
            land += _polys(g.intersection(B))
        self.land_ll = land
        lakes = []
        for f in _load("ne_10m_lakes")["features"]:
            p = f["properties"]
            sr = p.get("scalerank") or 10
            if sr > 9:
                continue
            g = shape(f["geometry"])
            if not g.intersects(B):
                continue
            lakes += [(sr, q) for q in _polys(g.intersection(B))]
        self.lakes_ll = lakes
        rivers = []
        for f in _load("ne_10m_rivers_lake_centerlines")["features"]:
            p = f["properties"]
            sr = p.get("scalerank") or 10
            if sr > 7:
                continue
            g = shape(f["geometry"])
            if not g.intersects(B):
                continue
            for ln in _lines(g.intersection(B)):
                rivers.append((sr, ln))
        self.rivers_ll = rivers

        # Mercator dizileri: iki ayrıntı düzeyi (yakın / uzak)
        def rings(polys, tol):
            out = []
            for p in polys:
                ps = p.simplify(tol, preserve_topology=True) if tol else p
                for q in _polys(ps):
                    ext = project_coords(np.asarray(q.exterior.coords))
                    holes = [project_coords(np.asarray(h.coords)) for h in q.interiors]
                    bb = (ext[:, 0].min(), ext[:, 1].min(), ext[:, 0].max(), ext[:, 1].max())
                    out.append((bb, ext.astype(np.float32), [h.astype(np.float32) for h in holes]))
            return out

        self.land_fine = rings(land, 0.004)
        self.land_coarse = rings(land, 0.03)
        self.lakes_fine = rings([q for sr, q in lakes], 0.002)
        self.lakes_coarse = rings([q for sr, q in lakes if sr <= 6], 0.03)
        rv = []
        for sr, ln in rivers:
            xy = project_coords(np.asarray(ln.simplify(0.01).coords)).astype(np.float32)
            bb = (xy[:, 0].min(), xy[:, 1].min(), xy[:, 0].max(), xy[:, 1].max())
            rv.append((sr, bb, xy))
        self.rivers = rv

    def island_lookup(self, lon, lat):
        pt = Point(lon, lat)
        idx = self._tree.query(pt, predicate="intersects")
        if len(idx) == 0:
            # en yakın kara parçası (küçük adalarda nokta biraz denizde kalabilir)
            j = self._tree.nearest(pt)
            g = self.land_ll[j]
            if g.distance(pt) > 0.12:
                return None
            idx = [j]
        g = self.land_ll[idx[0]]
        if g.area > 40:  # kıta parçası; ada değil
            return None
        return g
