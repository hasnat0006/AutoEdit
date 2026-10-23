#!/usr/bin/env python3
"""finish.py: the rendered Short -> the file you upload. The picture is copied, never re-encoded.

  loudness  the voice levelled (two-pass loudnorm; a render keeps the camera level, ~-25 LUFS), then the whole mix
            measured and set to -14 LUFS with one gain and a -1 dB limiter, so a bed never pushes it over
  music     optional: a bed looped under the whole Short, faded in and out, ducked under the voice (sidechain).
            Silence is the default; a bed has to earn its place like any sound.
  tags      BT.709 in the H.264 stream and the MP4 container (the render leaves them "unknown" and players show faces
            darker and redder)
  checks    1080x1920, 60 s at most; prints the measured loudness and the md5

Usage:
  python3 finish.py --in videos/<p>/render-raw.mp4 --out "<Renders>/<p>/<p>-short.mp4"
                    [--music bed.mp3 --music-db -20 [--no-duck]] [--lufs -14]
Exit 1 when the file is not a Short (over 60 s, or not 1080x1920).
"""
import argparse, hashlib, json, os, re, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument("--in", dest="src", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--lufs", type=float, default=-14.0)
ap.add_argument("--music")
ap.add_argument("--music-db", type=float, default=-20.0, help="bed gain before ducking (dB)")
ap.add_argument("--no-duck", action="store_true", help="a flat bed, no sidechain")
args = ap.parse_args()

def probe(path):
    j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height:format=duration",
                                   "-of", "json", path], capture_output=True, text=True, check=True).stdout)
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    return v, a, float(j["format"]["duration"])

v, a, dur = probe(args.src)
if v is None or a is None:
    sys.exit("%s needs a video and an audio stream" % args.src)

out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", args.src, "-vn", "-af",
                      "loudnorm=I=%s:TP=-1.5:LRA=11:print_format=json" % args.lufs, "-f", "null", "-"], capture_output=True, text=True).stderr
m = json.loads(out[out.rfind("{"):out.rfind("}") + 1])
voice = ("loudnorm=I=%s:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
         "aresample=48000,aformat=channel_layouts=stereo" % (args.lufs, m["input_i"], m["input_tp"], m["input_lra"], m["input_thresh"], m["target_offset"]))

def integrated(path):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    i, pk = re.findall(r"I:\s+(-?[\d.]+) LUFS", err), re.findall(r"Peak:\s+(-?[\d.]+) dBFS", err)
    return (float(i[-1]) if i else None), (pk[-1] if pk else "?")

# 1. the mix, lossless: the voice levelled, the bed (if any) looped, faded and ducked under it
os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
mix = args.out + ".mix.wav"
cmd = ["ffmpeg", "-y", "-v", "error", "-i", args.src]
if args.music:
    if not os.path.exists(args.music):
        sys.exit("no music file at %s" % args.music)
    cmd += ["-stream_loop", "-1", "-i", args.music]
    fade = min(1.5, dur / 4)
    bed = ("[1:a]atrim=0:%.3f,asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,volume=%sdB,"
           "afade=t=in:d=%.2f,afade=t=out:st=%.3f:d=%.2f[bed]" % (dur, args.music_db, fade, max(0.0, dur - fade), fade))
    if args.no_duck:
        fc = "[0:a]%s[voice];%s;[voice][bed]amix=inputs=2:duration=first:normalize=0[a]" % (voice, bed)
    else:
        fc = ("[0:a]%s,asplit=2[voice][sc];%s;[bed][sc]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=350[duck];"
              "[voice][duck]amix=inputs=2:duration=first:normalize=0[a]" % (voice, bed))
    cmd += ["-filter_complex", fc, "-map", "[a]"]
else:
    cmd += ["-map", "0:a:0", "-af", voice]
subprocess.run(cmd + ["-vn", "-c:a", "pcm_s24le", "-t", "%.3f" % dur, mix], check=True)

# 2. one gain so the whole mix (voice + bed) lands on the target, a -1 dB limiter (no auto-level), then AAC once
mix_i, _ = integrated(mix)
gain = (args.lufs - mix_i) if mix_i is not None else 0.0
cmd = ["ffmpeg", "-y", "-v", "error", "-i", args.src, "-i", mix, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy"]
if v.get("codec_name") == "h264":
    cmd += ["-bsf:v", "h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1"]
cmd += ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
        "-af", "volume=%.2fdB,alimiter=limit=0.89:level=disabled" % gain,
        "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2", "-t", "%.3f" % dur, "-movflags", "+write_colr+faststart"]
subprocess.run(cmd + [args.out], check=True)
os.remove(mix)

ov, oa, odur = probe(args.out)
lufs, peak = integrated(args.out)
md5 = hashlib.md5(open(args.out, "rb").read()).hexdigest()
print("wrote %s: %sx%s, %.2f s, %s LUFS (from %s), true peak %s dBFS, music %s, md5 %s"
      % (args.out, ov["width"], ov["height"], odur, "%.1f" % lufs if lufs is not None else "?", m["input_i"], peak,
         ("%s at %s dB%s" % (os.path.basename(args.music), args.music_db, "" if args.no_duck else ", ducked")) if args.music else "none", md5))
bad = []
if odur > 60.0 + 1.0 / 30:
    bad.append("%.2f s is over the 60 s a Short may run" % odur)
if (int(ov["width"]), int(ov["height"])) != (1080, 1920):
    bad.append("%sx%s is not 1080x1920" % (ov["width"], ov["height"]))
for b in bad:
    print("FAIL", b)
sys.exit(1 if bad else 0)
