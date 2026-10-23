#!/usr/bin/env python3
"""reframe.py: any flat cut -> the 1080x1920 (9:16) footage a Short is built on, encoded the way the render wants it
(30 fps, CRF 16, a keyframe every 30 frames, BT.709, AAC 48 kHz). Same duration, same audio: cut-map.json and every
flat-cut time stay valid.

  vertical source (phone, 1080x1920 or 2160x3840): scaled to 1080x1920 (a slightly different shape is cropped, centred)
  landscape source (16:9 camera): a 9:16 window of full source height is cut out and scaled to 1080x1920.
      --x 0.5                     where your face is, as a fraction of the source width (0.5 = centre)
      --keys "0:0.5,12.37:0.38"   the window jumps at those flat-cut times (put them on jump cuts from cut-map.json)
  A 4K landscape source gives a 1215x2160 window: sharp. A 1080p landscape source gives 608x1080, upscaled 1.78x: soft.
  The script says so; record vertical or in 4K.

Usage:
  python3 reframe.py --in videos/<p>/flat.mp4 --out videos/<p>/public/input-video.mp4 [--x 0.5 | --keys "t:x,..."] [--crf 16]
"""
import argparse, json, os, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument("--in", dest="src", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--x", type=float, default=0.5, help="landscape only: face centre as a fraction of the source width")
ap.add_argument("--keys", default="", help='landscape only: "t:x,t:x" window positions from flat time t on')
ap.add_argument("--crf", type=int, default=16)
ap.add_argument("--preset", default="fast")
args = ap.parse_args()

OW, OH = 1080, 1920
p = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height:stream_side_data=rotation:format=duration",
                               "-of", "json", args.src], capture_output=True, text=True, check=True).stdout)
v = next(s for s in p["streams"] if s["codec_type"] == "video")
w, h = int(v["width"]), int(v["height"])
rot = next((abs(int(sd.get("rotation", 0))) for sd in v.get("side_data_list", []) if "rotation" in sd), 0)
if rot in (90, 270):          # phones store portrait as landscape + a rotation flag; ffmpeg applies it on decode
    w, h = h, w
has_audio = any(s["codec_type"] == "audio" for s in p["streams"])

def clamp01(x):
    if not 0.0 <= x <= 1.0:
        sys.exit("x position %.3f is outside 0..1 (a fraction of the source width)" % x)
    return x

if h >= w:
    crop_w = min(w, int(round(h * 9 / 16 / 2)) * 2)
    crop_h = min(h, int(round(w * 16 / 9 / 2)) * 2)
    vf = "crop=%d:%d:(iw-ow)/2:(ih-oh)/2," % (crop_w, crop_h)
    mode = "vertical"
else:
    crop_w, crop_h = int(round(h * 9 / 16 / 2)) * 2, h
    keys = [(0.0, clamp01(args.x))]
    if args.keys:
        keys = sorted((float(t), clamp01(float(x))) for t, x in (k.split(":") for k in args.keys.split(",") if k.strip()))
        if keys[0][0] > 0:
            keys.insert(0, (0.0, clamp01(args.x)))
    xs = lambda cx: "max(0,min(iw-ow,%.4f*iw-ow/2))" % cx
    expr = xs(keys[0][1])
    for t, cx in keys[1:]:
        expr = "if(gte(t,%.4f),%s,%s)" % (t, xs(cx), expr)
    vf = "crop=%d:%d:'%s':0," % (crop_w, crop_h, expr)      # quoted: the commas inside stay part of the expression
    mode = "landscape, %d window position(s)" % len(keys)
scale = OH / float(crop_h)
# ffmpeg 9: frame colour properties override the output flags on an encode, so the frames are tagged BT.709 too
vf += ("scale=%d:%d:flags=lanczos,fps=30,format=yuv420p,setsar=1,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv"
       % (OW, OH))

os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
tmp = args.out + ".part.mp4"
cmd = ["ffmpeg", "-y", "-v", "error", "-i", args.src, "-map", "0:v:0"] + (["-map", "0:a:0"] if has_audio else []) + [
       "-vf", vf, "-c:v", "libx264", "-preset", args.preset, "-crf", str(args.crf), "-g", "30", "-keyint_min", "30", "-sc_threshold", "0",
       "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv"]
cmd += (["-c:a", "aac", "-b:a", "256k", "-ar", "48000"] if has_audio else []) + ["-movflags", "+faststart", tmp]
subprocess.run(cmd, check=True)
os.replace(tmp, args.out)

o = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,duration", "-of", "json", args.out],
                              capture_output=True, text=True, check=True).stdout)
ov = next(s for s in o["streams"] if s["codec_type"] == "video")
print("wrote %s: %sx%s from %dx%d (%s), window %dx%d, %.2fx" % (args.out, ov["width"], ov["height"], w, h, mode, crop_w, crop_h, scale))
if scale > 1.05:
    print("WARN the window is upscaled %.2fx: the Short will look soft. Record vertical at 1080x1920 or more, or landscape in 4K." % scale)
if not has_audio:
    print("WARN no audio stream in %s" % args.src)
