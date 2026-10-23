#!/usr/bin/env python3
"""voice-pitch.py: which words were said by someone else? A podcast clip carries the host's "Yeah." and "Right." inside
the guest's answer, and the transcript does not say who spoke. Each word's median pitch (autocorrelation on 40 ms
frames) is compared with the clip's main voice; a word far from it is flagged as another speaker.

On clip-03 the guest spoke at 180-250 Hz and the host's "Yeah." / "Right." measured 94 / 90 Hz.

Usage:
  python3 voice-pitch.py --audio W/audio-raw.wav --transcript W/transcript-raw.json [--ratio 0.7] [--all]
Prints the main voice's median pitch, then every flagged word (--all prints every word). Exit 0 either way.
"""
import argparse, json, sys, wave
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--audio", required=True, help="16 kHz mono WAV (the Cut stage's audio-raw.wav)")
ap.add_argument("--transcript", required=True)
ap.add_argument("--ratio", type=float, default=0.7, help="flag a word below ratio x or above x / ratio the main pitch")
ap.add_argument("--all", action="store_true")
args = ap.parse_args()

w = wave.open(args.audio)
if w.getnchannels() != 1 or w.getsampwidth() != 2:
    sys.exit("needs a 16-bit mono WAV: ffmpeg -i in -vn -acodec pcm_s16le -ar 16000 -ac 1 out.wav")
sr = w.getframerate()
x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float)
raw = json.load(open(args.transcript, encoding="utf-8"))
words = [v for v in (raw["words"] if isinstance(raw, dict) and "words" in raw else raw) if str(v.get("text", "")).strip()]

def pitch(a, b):
    """Median voiced pitch in [a, b] seconds; 0 when nothing is voiced."""
    seg, out, n = x[int(a * sr):int(b * sr)], [], int(0.04 * sr)
    for i in range(0, max(0, len(seg) - n), n // 4):
        f = seg[i:i + n] * np.hanning(n)
        if np.sqrt((f ** 2).mean()) < 300:          # too quiet to be voiced
            continue
        ac = np.correlate(f, f, "full")[n - 1:]
        lo, hi = sr // 400, sr // 70                   # 70 to 400 Hz
        lag = lo + int(np.argmax(ac[lo:hi]))
        if ac[lag] > 0.3 * ac[0]:
            out.append(sr / float(lag))
    return float(np.median(out)) if out else 0.0

rows = [(v, pitch(float(v["start"]), float(v["end"]))) for v in words]
voiced = [p for _, p in rows if p > 0]
if not voiced:
    sys.exit("no voiced words found")
main = float(np.median(voiced))
print("main voice: %.0f Hz (median of %d voiced words)" % (main, len(voiced)))
flagged = 0
for v, p in rows:
    other = p > 0 and (p < main * args.ratio or p > main / args.ratio)
    flagged += other
    if other or args.all:
        print("  %7.2f - %7.2f  %-16s %4.0f Hz%s" % (float(v["start"]), float(v["end"]), str(v["text"]).strip(), p,
                                                   "  <-- another voice?" if other else ""))
print("%d word(s) flagged; listen to each before cutting (a laugh or a whisper can read low too)" % flagged)
