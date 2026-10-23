#!/usr/bin/env python3
"""edge-levels.py: the audio level around every cut edge, as a 40 ms bar chart, with the transcript's words beside it.

edge-audit.py and sliver.py move edges into quiet, and that is usually right. But a word can have a silence inside it
(the closed "t" in "out|comes"), and Parakeet can place a sentence's last word 0.2 s early: on clip-03 the automatic
fixes ended one segment after "out-" and another before "work". Read this chart after the automatic fixes and before
apply-cut: an edge must sit in a quiet run BETWEEN words, never in a dip inside one.

Usage:
  python3 edge-levels.py --audio W/audio-raw.wav --cut-list W/cut-list.json --transcript W/transcript-raw.json [--pad 0.4]
"""
import argparse, json, wave
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--audio", required=True)
ap.add_argument("--cut-list", required=True)
ap.add_argument("--transcript", required=True)
ap.add_argument("--pad", type=float, default=0.4, help="seconds shown either side of each edge")
args = ap.parse_args()

w = wave.open(args.audio); sr = w.getframerate()
x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float)
if w.getnchannels() > 1:
    x = x.reshape(-1, w.getnchannels()).mean(1)
raw = json.load(open(args.transcript, encoding="utf-8"))
words = [v for v in (raw["words"] if isinstance(raw, dict) and "words" in raw else raw) if str(v.get("text", "")).strip()]
kept = json.load(open(args.cut_list, encoding="utf-8"))["kept"]
STEP = 0.04

def word_at(t):
    for v in words:
        if float(v["start"]) - 0.02 <= t < float(v["end"]):
            return str(v["text"]).strip()
    return ""

def chart(edge, kind):
    print("%s at %.2f s" % (kind, edge))
    t = max(0.0, edge - args.pad)
    while t < edge + args.pad:
        seg = x[int(t * sr):int((t + STEP) * sr)]
        r = float(np.sqrt((seg ** 2).mean())) if len(seg) else 0.0
        mark = " <== cut" if t <= edge < t + STEP else ""
        print("  %6.2f %5d %-30s %s%s" % (t, r, "#" * min(30, int(r / 250)), word_at(t + STEP / 2), mark))
        t += STEP

for i, s in enumerate(kept):
    print("---- segment %d: %.2f - %.2f" % (i, s["start"], s["end"]))
    chart(float(s["start"]), "start")
    chart(float(s["end"]), "end")
