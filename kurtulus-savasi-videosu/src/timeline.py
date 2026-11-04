"""Senaryo + seslendirme sürelerinden mutlak zaman çizelgesi üretir."""
from story import SCENES, MARKERS

DEFAULT_LEAD = 0.35
DEFAULT_TAIL = 0.45
DEFAULT_MIN = 3.0
DEFAULT_CAM = 1.8
DEFAULT_TERR = 2.2


def dec_year(d):
    y, m, day = d
    return y + (m - 1) / 12 + ((day or 15) - 1) / 365


def build(narr):
    tl = dict(scenes=[], cam=[], terr=[], dates=[], cards=[], markers=[], capitals=[],
              arrows=[], voice=[], sevr=[], offensive=None, peak=None, outro=None, title=None)
    t = 0.0
    nmap = {n["id"]: n for n in narr}
    prev_terr = "k0"
    tl["capitals"].append(dict(t=0.0, name="İstanbul"))
    for s in SCENES:
        n = nmap[s["id"]]
        start = t
        vs = start + s.get("lead", DEFAULT_LEAD)
        ve = vs + n["dur"]
        end = max(ve + s.get("tail", DEFAULT_TAIL), start + s.get("min_dur", DEFAULT_MIN))
        end += s.get("outro", 0.0)
        tl["voice"].append(dict(id=s["id"], t=vs, dur=n["dur"], npy=n["npy"], sr=n["sr"]))
        if s.get("title"):
            tl["title"] = dict(t0=0.0, t1=end)
        first = s["id"] == SCENES[0]["id"]
        tl["cam"].append(dict(t=0.0 if first else start, dur=0.0 if first else s.get("cam_dur", DEFAULT_CAM),
                              target=list(s["cam"])))
        for e in s["events"]:
            a = e.get("anchor")
            if a == "@end":
                et = ve + 0.35
            else:
                et = vs + n["anchors"].get(a, 0.0) - 0.05
            et = max(et, start)
            if "date" in e:
                tl["dates"].append(dict(t=et, date=list(e["date"]), dec=dec_year(e["date"])))
            if "terr" in e:
                tl["terr"].append(dict(t=et, dur=e.get("terr_dur", DEFAULT_TERR),
                                       src=prev_terr, dst=e["terr"]))
                prev_terr = e["terr"]
            if "card" in e:
                tl["cards"].append(dict(t=et, **e["card"]))
            if "marker" in e:
                m = MARKERS[e["marker"]]
                tl["markers"].append(dict(t=et, id=e["marker"], label=m[0], lon=m[1], lat=m[2],
                                          kind=m[3], scene_end=end))
            for ar in e.get("arrows", []):
                tl["arrows"].append(dict(t=et, scene_end=end, **ar))
            if "capital" in e:
                tl["capitals"].append(dict(t=et, name=e["capital"]))
            if "cam" in e:
                tl["cam"].append(dict(t=et, dur=e.get("cam_dur", DEFAULT_CAM), target=list(e["cam"])))
            if e.get("sevr"):
                tl["sevr"].append(et)
            if e.get("sevr_end"):
                tl["sevr"].append(et)
            if e.get("offensive"):
                tl["offensive"] = et
            if e.get("peak"):
                tl["peak"] = et
            if e.get("outro"):
                tl["outro"] = et
        tl["scenes"].append(dict(id=s["id"], t0=start, t1=end, vs=vs, ve=ve))
        t = end
    tl["duration"] = t
    for i in range(1, len(tl["terr"])):
        p, c = tl["terr"][i - 1], tl["terr"][i]
        if c["t"] < p["t"] + p["dur"]:
            p["dur"] = max(0.6, c["t"] - p["t"])
    tl["cam"].sort(key=lambda c: c["t"])
    tl["dates"].sort(key=lambda d: d["t"])
    return tl
