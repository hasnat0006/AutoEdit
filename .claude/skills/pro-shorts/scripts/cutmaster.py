#!/usr/bin/env python3
"""cutmaster.py: cut the planned clips from the master, native size and frame rate, no grading, 15 ms audio fades
at every edge (no clicks). Writes <episode>/cuts/<prefix>-<id>-<slug>.mp4.

A 4K master encodes at ~4 min per minute of clip: cut one or two clips per call in the foreground (a background job
dies with the session and leaves a broken file).

Usage: python cutmaster.py --episode videos/<episode> --master "E:/path/episode.mp4" --prefix codpod12 [01 02 ...]
"""
import argparse, json, os, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("--episode", required=True)
ap.add_argument("--master", required=True)
ap.add_argument("--prefix", required=True)
ap.add_argument("clips", nargs="*")
args = ap.parse_args()
plan = json.load(open(os.path.join(args.episode, "cut-plan.json"), encoding="utf-8"))
os.makedirs(os.path.join(args.episode, "cuts"), exist_ok=True)
for c in args.clips or sorted(plan):
    segs = plan[c]["segments"]; t0 = segs[0]["start"] - 2.0; t1 = segs[-1]["end"] + 1.0
    v, a = [], []
    for k, s in enumerate(segs):
        st, en = s["start"] - t0, s["end"] - t0
        v.append("[0:v]trim=%.3f:%.3f,setpts=PTS-STARTPTS[v%d]" % (st, en, k))
        a.append("[0:a]atrim=%.3f:%.3f,asetpts=PTS-STARTPTS,afade=t=in:d=0.015,afade=t=out:st=%.3f:d=0.015[a%d]" % (st, en, en - st - 0.015, k))
    fc = ";".join(v + a) + ";" + "".join("[v%d][a%d]" % (k, k) for k in range(len(segs))) + "concat=n=%d:v=1:a=1[v][a]" % len(segs)
    out = os.path.join(args.episode, "cuts", "%s-%s-%s.mp4" % (args.prefix, c, plan[c]["slug"]))
    if os.path.exists(out): os.remove(out)
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "%.3f" % max(0, t0), "-to", "%.3f" % t1, "-i", args.master, "-filter_complex", fc,
                        "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "fast", "-crf", "16", "-pix_fmt", "yuv420p",
                        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                        "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-movflags", "+faststart", out], capture_output=True, text=True)
    print(c, out, "OK" if r.returncode == 0 else "FAIL " + r.stderr[-400:], flush=True)
