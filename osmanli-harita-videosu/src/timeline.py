"""Senaryo + seslendirme sürelerinden mutlak zaman çizelgesi üretir."""
from story import SCENES, BATTLES

DEFAULT_LEAD = 0.35
DEFAULT_TAIL = 0.40
DEFAULT_MIN = 3.0
DEFAULT_CAM = 1.8
DEFAULT_TERR = 2.2


def build(narr):
    tl = dict(scenes=[], cam=[], terr=[], years=[], cards=[], battles=[], capitals=[],
              voice=[], peak=None, outro=None, title=None)
    t = 0.0
    nmap = {n["id"]: n for n in narr}
    prev_terr = "seed"
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
        tl["cam"].append(dict(t=start if s["id"] != "intro" else 0.0,
                              dur=s.get("cam_dur", DEFAULT_CAM) if s["id"] != "intro" else 0.0,
                              target=list(s["cam"])))
        for e in s["events"]:
            a = e.get("anchor")
            if a == "@end":
                et = ve + 0.35
            else:
                et = vs + n["anchors"].get(a, 0.0) - 0.05
            et = max(et, start)
            if "year" in e:
                tl["years"].append(dict(t=et, year=e["year"]))
            if "terr" in e:
                tl["terr"].append(dict(t=et, dur=e.get("terr_dur", DEFAULT_TERR),
                                       src=prev_terr, dst=e["terr"]))
                prev_terr = e["terr"]
            if "card" in e:
                tl["cards"].append(dict(t=et, **e["card"]))
            if "battle" in e:
                b = BATTLES[e["battle"]]
                tl["battles"].append(dict(t=et, id=e["battle"], label=b[0], lon=b[1], lat=b[2],
                                          result=b[3], scene_end=end))
            if "capital" in e:
                tl["capitals"].append(dict(t=et, name=e["capital"]))
            if "cam" in e:
                tl["cam"].append(dict(t=et, dur=e.get("cam_dur", DEFAULT_CAM),
                                      target=list(e["cam"])))
            if e.get("peak"):
                tl["peak"] = et
            if e.get("outro"):
                tl["outro"] = et
        tl["scenes"].append(dict(id=s["id"], t0=start, t1=end, vs=vs, ve=ve))
        t = end
    tl["duration"] = t
    # Ardışık toprak geçişleri çakışmasın
    for i in range(1, len(tl["terr"])):
        p, c = tl["terr"][i - 1], tl["terr"][i]
        if c["t"] < p["t"] + p["dur"]:
            p["dur"] = max(0.6, c["t"] - p["t"])
    tl["cam"].sort(key=lambda c: c["t"])
    return tl
