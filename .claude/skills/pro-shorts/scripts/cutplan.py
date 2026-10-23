#!/usr/bin/env python3
"""cutplan.py: turn the chosen moments into exact cut points, every edge in a quiet gap between words.

keeps.txt, one kept piece per line (a clip can have several pieces: 04a, 04b, 04c... they play in time order):
    <clip id><piece letter> | <slug> | <first words of the piece> | <last words of the piece> | <search after, seconds>
    01a | price-voice | What's the most demanding | Tell me it's the voice. | 1970
    01b | price-voice | as you can hear my | I'm fucking crazy as well. | 2060
Phrases are matched word for word against the episode transcript (case and punctuation ignored), so copy them from
transcript.txt. A start edge goes to the quietest 10 ms in the gap before the first word (up to 0.25 s), an end edge
to the quietest point after the last word (up to 0.30 s, stopping before the next word). Prints each clip's pieces and
length, flags a clip over 60 s, and writes cut-plan.json.

Usage: python cutplan.py --episode videos/<episode> [--keeps keeps.txt] [--first-word-back 01a]
  --first-word-back ID  start that piece one word earlier (the transcript split "I | have heard" across lines)
"""
import argparse, json, os, re, sys, wave
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--episode", required=True)
ap.add_argument("--keeps", default="keeps.txt")
ap.add_argument("--first-word-back", action="append", default=[])
args = ap.parse_args()
E = args.episode
w = json.load(open(os.path.join(E, "transcript.json"), encoding="utf-8")); w = w["words"] if isinstance(w, dict) else w
N = lambda s: re.sub(r"[^a-z0-9']", "", s.lower())
toks = [N(x["text"]) for x in w]
f = wave.open(os.path.join(E, "audio-full.wav")); SR = f.getframerate()
A = np.frombuffer(f.readframes(f.getnframes()), np.int16).astype(float)

def find(phrase, after):
    p = [N(t) for t in phrase.split()]
    for i in range(len(w)):
        if w[i]["start"] >= after and toks[i:i + len(p)] == p:
            return i
    sys.exit("not found after %.1f s: %r (copy it from transcript.txt)" % (after, phrase))
def rms(t, d=0.02):
    s = A[int(t * SR):int((t + d) * SR)]; return float(np.sqrt((s ** 2).mean())) if len(s) else 0.0
def quietest(a, b):
    ts = np.arange(a, max(a + 0.021, b), 0.01); return float(min(ts, key=rms))
def start_edge(i):
    t0 = w[i]["start"]; prev = w[i - 1]["end"] if i else 0
    return quietest(max(prev, t0 - 0.25), t0 + 0.01) if t0 - prev > 0.04 else quietest(t0 - 0.08, t0 + 0.02)
def end_edge(j):
    t1 = w[j]["end"]; nxt = w[j + 1]["start"] if j + 1 < len(w) else t1 + 1
    return quietest(t1 - 0.02, min(nxt, t1 + 0.30)) if nxt - t1 > 0.04 else quietest(t1 - 0.03, t1 + 0.06)

clips = {}
for line in open(os.path.join(E, args.keeps), encoding="utf-8"):
    if not line.strip() or line.lstrip().startswith("#"): continue
    pid, slug, a, b, after = [s.strip() for s in line.split("|")]
    i = find(a, float(after)); j = find(b, w[i]["start"]) + len(b.split()) - 1
    if pid in args.first_word_back: i -= 1
    c = re.match(r"\d+", pid).group(0)
    clips.setdefault(c, {"slug": slug, "pieces": []})["pieces"].append((i, j))
plan = {}
for c, v in sorted(clips.items()):
    segs = []
    for i, j in sorted(v["pieces"]):
        segs.append({"start": round(start_edge(i), 3), "end": round(end_edge(j), 3), "text": " ".join(x["text"] for x in w[i:j + 1])})
    L = sum(s["end"] - s["start"] for s in segs)
    plan[c] = {"slug": v["slug"], "segments": segs, "length": round(L, 2)}
    print("%s %-22s %s = %.1f s%s" % (c, v["slug"], " + ".join("%.2f-%.2f" % (s["start"], s["end"]) for s in segs), L,
                                       "   OVER 60 s: drop an aside" if L > 60 else ""))
json.dump(plan, open(os.path.join(E, "cut-plan.json"), "w", encoding="utf-8"), indent=1)
