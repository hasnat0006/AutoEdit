#!/usr/bin/env python3
"""moments.py: get a long episode ready for choosing its best moments.

Writes into the episode folder: audio-full.wav (16 kHz mono), transcript.json (Parakeet, word timings),
transcript.txt (lines broken at pauses, with mm:ss stamps: the thing you read to pick moments), energy.txt
(the loudest spots against a 60 s local baseline: laughter and reactions on a raw mix; flat on a compressed one)
and frames/overview.jpg (one frame every 90 s, to see the set, the people and the cutaways).

Usage: python moments.py --master "E:/path/episode.mp4" --out videos/<episode>
The transcription of a 40-minute episode takes ~15 minutes on CPU: run it in the background.
"""
import argparse, json, os, shutil, subprocess, sys
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--master", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--skip-transcribe", action="store_true", help="only rebuild transcript.txt / energy.txt")
args = ap.parse_args()
W = args.out; os.makedirs(os.path.join(W, "frames"), exist_ok=True)
wav = os.path.join(W, "audio-full.wav")
if not os.path.exists(wav):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", args.master, "-vn", "-ac", "1", "-ar", "16000", wav], check=True)
if not args.skip_transcribe:
    npx = shutil.which("npx") or "npx"
    r = subprocess.run([npx, "hyperframes", "transcribe", wav, "-d", W, "--engine", "parakeet", "--json"], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("transcription failed:\n" + r.stderr[-2000:])
words = json.load(open(os.path.join(W, "transcript.json"), encoding="utf-8"))
words = words["words"] if isinstance(words, dict) else words

# readable transcript: a new line on a pause over 0.9 s or every ~30 words
out, cur, st, prev = [], [], None, None
for x in words:
    if prev is not None and (x["start"] - prev > 0.9 or len(cur) > 30):
        out.append((st, " ".join(cur))); cur, st = [], None
    if st is None: st = x["start"]
    cur.append(x["text"]); prev = x["end"]
if cur: out.append((st, " ".join(cur)))
with open(os.path.join(W, "transcript.txt"), "w", encoding="utf-8") as f:
    for s, t in out:
        f.write("%02d:%05.2f %s\n" % (s // 60, s % 60, t))

# loudness peaks against a local baseline
import wave
wf = wave.open(wav); sr = wf.getframerate()
a = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768
win = sr // 2; n = len(a) // win
db = 20 * np.log10(np.sqrt((a[:n * win].reshape(n, win) ** 2).mean(1) + 1e-12))
base = np.array([np.median(db[max(0, i - 60):i + 60]) for i in range(n)])
ex = db - base; picked = []
for i in np.argsort(-ex):
    t = i * 0.5
    if all(abs(t - p) > 20 for p, _ in picked): picked.append((t, ex[i]))
    if len(picked) >= 30: break
with open(os.path.join(W, "energy.txt"), "w") as f:
    for t, e in sorted(picked):
        f.write("%02d:%04.1f  +%.1f dB\n" % (t // 60, t % 60, e))

ov = os.path.join(W, "frames", "overview.jpg")
if not os.path.exists(ov):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", args.master, "-vf", "fps=1/90,scale=384:-1,tile=6x5", "-frames:v", "1", ov])
print("%d words, %d lines -> %s/transcript.txt; peaks -> energy.txt; frames -> frames/overview.jpg" % (len(words), len(out), W))
