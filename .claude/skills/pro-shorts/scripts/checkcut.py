#!/usr/bin/env python3
"""checkcut.py: prove every cut kept its words. Transcribes each finished cut and compares it with the plan:
the share of planned words heard, and whether each piece's first and last word are heard (the edges).
A few unheard words in a clip is ASR noise (fast or overlapping speech); a missing edge word is a real clip: look at it.

Usage: python checkcut.py --episode videos/<episode> 01 02 ...
"""
import argparse, difflib, json, os, re, shutil, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("--episode", required=True)
ap.add_argument("clips", nargs="*")
args = ap.parse_args()
E = args.episode
plan = json.load(open(os.path.join(E, "cut-plan.json"), encoding="utf-8"))
N = lambda s: re.sub(r"[^a-z0-9']", "", s.lower())
npx = shutil.which("npx") or "npx"
for c in args.clips or sorted(plan):
    f = [x for x in os.listdir(os.path.join(E, "cuts")) if x.endswith(".mp4") and re.search(r"-(\d+)-", x) and re.search(r"-(\d+)-", x).group(1) == c][0]
    d = os.path.join(E, "check", "v" + c); os.makedirs(d, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(E, "cuts", f), "-vn", "-ac", "1", "-ar", "16000", d + "/a.wav"], check=True)
    subprocess.run([npx, "hyperframes", "transcribe", d + "/a.wav", "-d", d, "--engine", "parakeet", "--json"], capture_output=True)
    got = [N(x["text"]) for x in json.load(open(d + "/transcript.json", encoding="utf-8"))]
    want = [N(t) for s in plan[c]["segments"] for t in s["text"].split()]
    hit = sum(b.size for b in difflib.SequenceMatcher(a=want, b=got, autojunk=False).get_matching_blocks())
    edges = []
    for s in plan[c]["segments"]:
        ws = [N(t) for t in s["text"].split()]
        edges.append(("ok" if ws[0] in got else "START?") + "/" + ("ok" if ws[-1] in got else "END?"))
    p = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate:format=duration", "-of", "json",
                                   os.path.join(E, "cuts", f)], capture_output=True, text=True).stdout)
    v = next(s for s in p["streams"] if s["codec_type"] == "video")
    print("%s %-36s %dx%d %s %.2fs  words %d/%d  edges %s" % (c, f, v["width"], v["height"], v["r_frame_rate"], float(p["format"]["duration"]), hit, len(want), " ".join(edges)), flush=True)
