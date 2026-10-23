#!/usr/bin/env python3
"""music.py: the music bed for one clip.

  map     the track's loudness every 2 s, and its biggest jumps (the drops) found at 0.1 s
          python music.py map --track videos/_shared/music/<track>.mp3
  bed     cut the section so the drop lands on a chosen line of the clip, then detect its beats
          python music.py bed --track <track> --drop 11.25 --land 8.48 --len 18.07 --out <subs dir>
          -> <subs>/bed.wav and <subs>/beats.json (time + strength; "strong" from strength > 0.5)

Tracks only from Pixabay, never one marked "Content ID Registered" on its page (or with a publisher / IPI block in
the artist bio); credit every one in videos/_shared/music/CREDITS.md. Downloading needs the creator's OK.
"""
import argparse, json, os, shutil, subprocess, sys
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("cmd", choices=["map", "bed"])
ap.add_argument("--track", required=True)
ap.add_argument("--drop", type=float, help="the drop's time in the track (s)")
ap.add_argument("--land", type=float, help="the clip time the drop should land on (s)")
ap.add_argument("--len", type=float, help="the clip length (s)")
ap.add_argument("--out")
args = ap.parse_args()

def pcm(path, sr=16000):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                                        capture_output=True).stdout, np.int16).astype(float), sr
def db(x): return 20 * np.log10(np.sqrt((x ** 2).mean()) / 32768 + 1e-9) if len(x) else -99

if args.cmd == "map":
    a, sr = pcm(args.track); L = len(a) / sr
    print("every 2 s:", " ".join("%d:%.0f" % (s, db(a[s * sr:(s + 2) * sr])) for s in range(0, int(L) - 1, 2)))
    fine = np.array([db(a[int(t * sr):int((t + 0.1) * sr)]) for t in np.arange(0, L - 0.1, 0.1)])
    jump = fine[3:] - np.array([fine[i:i + 3].mean() for i in range(len(fine) - 3)])
    tops = []
    for i in np.argsort(-jump):
        t = (i + 3) * 0.1
        if all(abs(t - p) > 6 for p, _ in tops): tops.append((t, jump[i]))
        if len(tops) >= 5: break
    print("biggest jumps (drop candidates):", ", ".join("%.1f s (+%.0f dB)" % (t, j) for t, j in sorted(tops)))
    sys.exit(0)

if None in (args.drop, args.land, args.len, args.out):
    sys.exit("bed needs --drop --land --len --out")
start = args.drop - args.land
if start < 0:
    sys.exit("the drop at %.2f s cannot land at %.2f s: pick a later drop or an earlier line" % (args.drop, args.land))
bed = os.path.join(args.out, "bed.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "%.3f" % start, "-t", "%.3f" % (args.len + 1.2), "-i", args.track, "-ar", "48000", "-ac", "2", bed], check=True)
proj = os.path.join(args.out, "beatsproj"); os.makedirs(proj, exist_ok=True)
shutil.copy(bed, os.path.join(proj, "bed.wav"))
open(os.path.join(proj, "index.html"), "w").write(
    '<!doctype html><html><body><div id="stage" data-composition-id="b" data-start="0" data-duration="%.3f" data-fps="30" data-width="1080" data-height="1920">'
    '<audio id="music" src="bed.wav" data-start="0" data-duration="%.3f" data-track-index="1" data-volume="1"></audio></div></body></html>' % (args.len, args.len))
r = subprocess.run([shutil.which("npx") or "npx", "hyperframes", "beats", proj, "--json"], capture_output=True, text=True)
src = os.path.join(proj, "beats", "bed.wav.json")
if not os.path.exists(src):
    sys.exit("beat detection failed:\n" + r.stdout[-800:] + r.stderr[-800:])
b = json.load(open(src))["beats"]
json.dump(b, open(os.path.join(args.out, "beats.json"), "w"), indent=0)
print("bed.wav: track %.2f s on, the drop at clip %.2f s; %d beats, %.0f BPM" % (start, args.land, len(b), 60 / np.median(np.diff([x["time"] for x in b]))))
print("beats:", " ".join("%.2f%s" % (x["time"], "*" if x["strength"] > 0.5 else "") for x in b))
