#!/usr/bin/env python3
"""prep.py: a fresh cut -> everything the edit needs, in <clip>/subs/.

  edit.mp4         1080x1920 at 30 fps. A landscape clip is letterboxed: the whole picture, sharp (downscaled to 1080
                   wide, never cropped or upscaled), centred on black; a vertical clip is scaled to 1080x1920.
  audio.wav        16 kHz mono; transcript.json (Parakeet words): fix misheard words before building, same timings
  window.json      where the picture sits ({"y", "h"}) and the shot changes inside it (for camera resets, transitions)
  depth/picture.mp4, depth/subject.webm  with --depth: the people cut out of the picture (remove-background, CPU,
                   ~10 min for 18 s; the first run downloads the model, ~170 MB: ask the creator first)
  shots.png        one frame per shot, the picture only (to find faces for punch-in origins)

Usage: python prep.py --clip videos/<episode>/cuts/<file>.mp4 --out videos/<episode>/mNN/subs [--depth]
"""
import argparse, json, os, shutil, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument("--clip", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--depth", action="store_true")
ap.add_argument("--scene", type=float, default=0.08, help="shot-change threshold inside the picture (dark sets need it low)")
args = ap.parse_args()
O = args.out; os.makedirs(O, exist_ok=True)
npx = shutil.which("npx") or "npx"
p = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height", "-of", "json", args.clip],
                              capture_output=True, text=True, check=True).stdout)
v = next(s for s in p["streams"] if s["codec_type"] == "video"); W0, H0 = int(v["width"]), int(v["height"])
if W0 > H0:
    h = int(round(1080 * H0 / W0 / 2) * 2); y = (1920 - h) // 2
    vf = "scale=1080:%d:flags=lanczos,pad=1080:1920:0:%d:black,setsar=1,fps=30" % (h, y)
else:
    h, y = 1920, 0; vf = "scale=1080:1920:flags=lanczos,setsar=1,fps=30"
edit = os.path.join(O, "edit.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", args.clip, "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p",
                "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", edit], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", edit, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", os.path.join(O, "audio.wav")], check=True)
r = subprocess.run([npx, "hyperframes", "transcribe", os.path.join(O, "audio.wav"), "-d", O, "--engine", "parakeet", "--json"], capture_output=True, text=True)
if r.returncode != 0:
    sys.exit("transcription failed:\n" + r.stderr[-1500:])
out = subprocess.run(["ffmpeg", "-hide_banner", "-i", edit, "-an", "-vf", "crop=1080:%d:0:%d,scale=270:-1,select='gt(scene,%s)',showinfo" % (h, y, args.scene),
                      "-f", "null", "-"], capture_output=True, text=True).stderr
shots = [round(float(t.split(":")[1]), 3) for t in out.split() if t.startswith("pts_time:")]
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", edit], capture_output=True, text=True).stdout)
shots = [t for t in shots if 0.3 < t < dur - 0.3]          # a "change" in the first or last frames is a fade, not a shot
json.dump({"y": y, "h": h, "duration": round(dur, 3), "shots": shots}, open(os.path.join(O, "window.json"), "w"), indent=1)
mids = [(a + b) / 2 for a, b in zip([0] + shots, shots + [dur])]
cmd = ["ffmpeg", "-v", "error", "-y"]
for t in mids: cmd += ["-ss", "%.2f" % t, "-i", edit]
cmd += ["-filter_complex", "".join("[%d]crop=1080:%d:0:%d,scale=360:-1[s%d];" % (i, h, y, i) for i in range(len(mids))) +
        "".join("[s%d]" % i for i in range(len(mids))) + "vstack=%d" % len(mids) if len(mids) > 1 else "[0]crop=1080:%d:0:%d,scale=360:-1" % (h, y),
        "-frames:v", "1", os.path.join(O, "shots.png")]
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print("shots.png failed:", r.stderr[-300:])
if args.depth:
    os.makedirs(os.path.join(O, "depth"), exist_ok=True)
    pic = os.path.join(O, "depth", "picture.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", edit, "-vf", "crop=1080:%d:0:%d" % (h, y), "-an", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", pic], check=True)
    r = subprocess.run([npx, "hyperframes", "remove-background", pic, "-o", os.path.join(O, "depth", "subject.webm"), "--quality", "best"], capture_output=True, text=True)
    print("cut-out:", "OK" if r.returncode == 0 else "FAILED " + r.stderr[-600:])
words = json.load(open(os.path.join(O, "transcript.json"), encoding="utf-8"))
print("edit.mp4 1080x1920, %.2f s; picture y %d, h %d; %d shots at %s" % (dur, y, h, len(shots) + 1, " ".join("%.2f" % s for s in shots)))
print("words:", " ".join("%d:%s@%.2f" % (i, x["text"], x["start"]) for i, x in enumerate(words)))
