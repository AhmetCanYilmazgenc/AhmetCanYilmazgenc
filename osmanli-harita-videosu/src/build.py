"""Tüm üretim hattı: seslendirme → zaman çizelgesi → kareler → müzik → video."""
import argparse
import json
import math
import multiprocessing as mp
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import CACHE_DIR, OUT_DIR, FPS  # noqa: E402
from story import SCENES  # noqa: E402


def load_world():
    import tts
    import timeline
    import sdf
    import render
    from geo import Basemap
    from territories import KEY_ORDER, keyframe_geoms
    narr = tts.synthesize_all(SCENES)
    tl = timeline.build(narr)
    with open(os.path.join(CACHE_DIR, "timeline.json"), "w") as f:
        json.dump(tl, f, ensure_ascii=False, indent=1)
    bm = Basemap()
    sdfs = sdf.build_all(bm, KEY_ORDER, keyframe_geoms)
    return render.World(bm, sdfs, tl), tl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", type=str, default="", help="virgülle ayrılmış saniyeler → PNG")
    ap.add_argument("--workers", type=int, default=max(1, os.cpu_count() or 1))
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=-1)
    ap.add_argument("--out", type=str, default=os.path.join(OUT_DIR, "osmanli_1299_1683.mp4"))
    args = ap.parse_args()

    import render
    world, tl = load_world()
    print(f"Süre: {tl['duration']:.2f} sn")

    if args.preview:
        ui = render.UI(world)
        for ts in args.preview.split(","):
            t = float(ts)
            t0 = time.time()
            im = render.render_frame(world, ui, t)
            path = os.path.join(CACHE_DIR, f"preview_{t:06.2f}.png")
            im.save(path)
            print(f"  {path}  ({time.time() - t0:.2f} sn)")
        return

    import audio
    wav = audio.build(tl, os.path.join(CACHE_DIR, "soundtrack.wav"))

    n = int(math.ceil(tl["duration"] * FPS))
    i0 = int(args.start * FPS)
    i1 = n if args.end < 0 else min(n, int(args.end * FPS))
    k = args.workers
    bounds = [i0 + (i1 - i0) * j // k for j in range(k + 1)]
    jobs = [(bounds[j], bounds[j + 1], os.path.join(CACHE_DIR, f"seg_{j:02d}.mp4")) for j in range(k)]
    t0 = time.time()
    ctx = mp.get_context("fork")
    render._init_world(world)
    with ctx.Pool(k) as pool:
        segs = pool.map(render.render_segment, jobs)
    print(f"Kareler: {i1 - i0} kare, {time.time() - t0:.1f} sn")
    lst = os.path.join(CACHE_DIR, "segments.txt")
    with open(lst, "w") as f:
        for p in segs:
            f.write(f"file '{p}'\n")
    video = os.path.join(CACHE_DIR, "video_noaudio.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", video], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", wav,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-af", f"atrim=0:{(i1 - i0) / FPS:.3f}" if i0 == 0 else "anull",
                    "-shortest", "-movflags", "+faststart", args.out], check=True)
    print("Çıktı:", args.out)


if __name__ == "__main__":
    main()
