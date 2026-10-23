#!/usr/bin/env python3
"""strips.py: review motion, not stills. Tiles every frame (or a fixed rate) of each moment of a render, so a move's
ease, overshoot, blur and settle are visible; stills hide all of it.

Usage: python strips.py --render <subs>/render-raw.mp4 --out <subs>/strips --crop band|picture|full [--fps 12]
                        name:start:end [name:start:end ...]
  band     the black band above the picture (where most elements live), picture: the window, full: the whole frame
"""
import argparse, json, os, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("--render", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--crop", default="full", choices=["band", "picture", "full"])
ap.add_argument("--fps", type=int, default=12)
ap.add_argument("moments", nargs="+")
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)
win = os.path.join(os.path.dirname(os.path.abspath(args.render)), "window.json")
y, h = (json.load(open(win))["y"], json.load(open(win))["h"]) if os.path.exists(win) else (0, 1920)
crop = {"band": "crop=1080:%d:0:%d" % (y + h - 200, 200), "picture": "crop=1080:%d:0:%d" % (h, y), "full": "null"}[args.crop]
for m in args.moments:
    n, a, b = m.split(":"); a, b = float(a), float(b)
    frames = max(1, int((b - a) * args.fps)); cols = min(8, frames); rows = (frames + cols - 1) // cols
    out = os.path.join(args.out, n + ".png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "%.3f" % a, "-to", "%.3f" % b, "-i", args.render, "-vf",
                    "fps=%d,%s,scale=%d:-1,tile=%dx%d" % (args.fps, crop, 1728 // cols, cols, rows), "-frames:v", "1", out], check=True)
    print(out)
