#!/usr/bin/env python3
"""mix.py: the render -> the files you upload.

finish.py twice (the no-music twin, then the music version), with the bed's gain searched until it sits 16 to 20 dB
under the voice (measured: music version minus the twin = the bed alone, RMS against the voice). Pixabay tracks are
mastered differently: the right --music-db has been +8, -6 and -11 on three clips, so it is always measured.
Then verify-render (with the clipped-words check) and a copy to ~/Videos/YouTube Shorts/<folder>/.

Usage: python mix.py --subs <subs dir> --name <file stem> --deliver codpod-12 [--start-db -6]
"""
import argparse, os, shutil, subprocess, sys
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--subs", required=True)
ap.add_argument("--name", required=True)
ap.add_argument("--deliver", required=True, help="folder name under ~/Videos/YouTube Shorts")
ap.add_argument("--start-db", type=float, default=-6.0)
ap.add_argument("--target", type=float, default=18.0, help="dB the bed sits under the voice")
args = ap.parse_args()
S = args.subs
YS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "youtube-shorts", "scripts"))
PY = sys.executable
raw = os.path.join(S, "render-raw.mp4"); bed = os.path.join(S, "bed.wav")
twin = os.path.join(S, args.name + "-nomusic.mp4"); final = os.path.join(S, args.name + ".mp4")

def run(*a):
    r = subprocess.run([PY, os.path.join(YS, a[0])] + list(a[1:]), capture_output=True, text=True)
    if r.returncode not in (0, 1): sys.exit(r.stdout[-800:] + r.stderr[-800:])
    return r.stdout
def pcm(f): return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout, np.int16).astype(float)
R = lambda x: 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)

print(run("finish.py", "--in", raw, "--out", twin).strip().splitlines()[-1][:120])
voice = pcm(twin)
if os.path.exists(bed):
    g = args.start_db
    for _ in range(4):
        run("finish.py", "--in", raw, "--out", final, "--music", bed, "--music-db", "%.1f" % g)
        m = pcm(final); n = min(len(m), len(voice)); under = R(voice[:n]) - R(m[:n] - voice[:n])
        print("music-db %+.1f: bed %.1f dB under the voice" % (g, under))
        if abs(under - args.target) <= 2: break
        g += under - args.target
else:
    shutil.copy(twin, final); print("no bed.wav: delivered without music")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", final, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", os.path.join(S, "audio-final.wav")], check=True)
subprocess.run([shutil.which("npx") or "npx", "hyperframes", "transcribe", os.path.join(S, "audio-final.wav"), "-d", os.path.join(S, "final-tx"), "--engine", "parakeet", "--json"], capture_output=True)
v = run("verify-render.py", "--render", final, "--index", os.path.join(S, "public", "index.html"),
        "--words", os.path.join(S, "final-tx", "transcript.json"), "--kept", os.path.join(S, "transcript.json"))
print("\n".join(l for l in v.splitlines() if "PASS" in l or "FAIL" in l))
dst = os.path.join(os.path.expanduser("~"), "Videos", "YouTube Shorts", args.deliver); os.makedirs(dst, exist_ok=True)
shutil.copy(final, dst)   # music version only (NOTES 16); the no-music twin stays in the work folder
print("delivered:", dst)
