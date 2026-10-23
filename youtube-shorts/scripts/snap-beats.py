#!/usr/bin/env python3
"""snap-beats.py: snapshot every card moment of a composed project and tile them into one contact sheet.
Reads the storyboard.json next to public/ (compose.py format): the first frame (0.1 s, the hook gate), every beat
in + 0.9, a list again 0.6 s after its last item, a stat once its count lands, captions at a few spoken words, plus
any --at extras. A snapshot is seconds; a render is minutes.

Usage: python3 snap-beats.py --project videos/<p> [--at 12.3 --at 20.0]
Writes videos/<p>/snaps/at-<t>.png and videos/<p>/snaps/sheet.png (tiled 5 across, 270x480 each).
"""
import argparse, json, os, subprocess, shutil, glob, math

ap = argparse.ArgumentParser()
ap.add_argument("--project", required=True)
ap.add_argument("--at", action="append", default=[])
args = ap.parse_args()
P = args.project
S = json.load(open(os.path.join(P, "storyboard.json"), encoding="utf-8"))
moments = [0.1]
for b in S.get("beats", []):
    moments.append(float(b["in"]) + 0.9)
    if b["type"] == "list" and b.get("items"):
        moments.append(float(b["items"][-1][1]) + 0.6)
    elif b["type"] == "stat":
        moments.append(float(b.get("at", float(b["in"]) + 0.15)) + float(b.get("dur", 1.2)) + 0.2)
    elif b["type"] == "split":
        moments.append(float(b["out"]) - 0.8)
cap = S.get("captions")
tp = cap and os.path.join(P, cap.get("transcript", "transcript.json"))
if tp and os.path.exists(tp):     # a few caption moments where no beat is on screen: the captions alone must read
    raw = json.load(open(tp, encoding="utf-8")); ws = raw["words"] if isinstance(raw, dict) else raw
    busy = [(float(b["in"]), float(b["out"])) for b in S.get("beats", [])]
    free = [float(w["start"]) + 0.05 for w in ws if not any(a <= float(w["start"]) <= z for a, z in busy)]
    moments += free[::max(1, len(free) // 3)][:3]
moments += [float(x) for x in args.at]
moments = sorted(set(round(min(m, float(S["duration"]) - 0.05), 2) for m in moments))
snapdir = os.path.join(P, "snaps"); os.makedirs(snapdir, exist_ok=True)
pub = os.path.join(P, "public")
raw = os.path.join(snapdir, "raw")
shutil.rmtree(raw, ignore_errors=True)
# one browser for every moment; npx is npx.cmd on Windows, so resolve it (a bare "npx" only runs on Mac and Linux)
r = subprocess.run([shutil.which("npx") or "npx", "hyperframes", "snapshot", pub, "--at", ",".join("%.2f" % t for t in moments),
                    "-o", raw, "--no-end"], capture_output=True, text=True)
frames = sorted(glob.glob(os.path.join(raw, "frame-*-at-*.png")))    # frame-NN-at-<t>s.png, in --at order
if len(frames) != len(moments):
    print(r.stdout[-2000:] + r.stderr[-2000:])
    raise SystemExit("asked for %d snapshots, got %d" % (len(moments), len(frames)))
outs = []
for t, f in zip(moments, frames):
    dst = os.path.join(snapdir, "at-%05.2f.png" % t)
    shutil.copy(f, dst); outs.append(dst)
    print("snap", t)
if outs:
    cols = 5; rows = math.ceil(len(outs) / cols)
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for o in outs: cmd += ["-i", o]
    n = len(outs)
    # pad to a full grid with copies of the last frame so tile does not drop a row
    while n % cols: cmd += ["-i", outs[-1]]; n += 1
    cmd += ["-filter_complex", "".join("[%d]" % i for i in range(n)) + "concat=n=%d:v=1:a=0,scale=270:480,tile=%dx%d" % (n, cols, rows), "-frames:v", "1", os.path.join(snapdir, "sheet.png")]
    subprocess.run(cmd, check=True)
    print("sheet:", os.path.join(snapdir, "sheet.png"), "(%d frames, %dx%d)" % (len(outs), cols, rows))
