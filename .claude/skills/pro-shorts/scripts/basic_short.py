#!/usr/bin/env python3
"""basic_short.py: the simplest Short, one moment, no extras.

Takes one moment from moments.json, puts its fresh cut on a 1080x1920 black frame (the whole 16:9 picture, not cropped),
burns the transcript's own words underneath as plain subtitles, keeps the original voice and writes the upload .txt.
No music, no B-roll, no motion graphics, no sound effects. Words come from the transcript; nothing is added or changed.

Usage: python basic_short.py --moments E:/AutoEdit/Buttigieg-DOAC/moments.json --id m03 --prefix pete \
                             --transcript videos/buttigieg-doac/transcript.json
Writes <folder>/edited/<prefix>-NN-<slug>-short-v1.mp4 and .txt, and marks the moment as edited in moments.json.
"""
import argparse, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", "youtube-shorts", "assets", "fonts", "RubikMonoOne-Regular.ttf"))
MAX_CHARS, MAX_GAP = 18, 0.6

ap = argparse.ArgumentParser()
ap.add_argument("--moments", required=True)
ap.add_argument("--id", required=True, help="moment id, e.g. m03")
ap.add_argument("--prefix", required=True, help="file prefix, e.g. pete (gives pete-03-...)")
ap.add_argument("--transcript", required=True, help="transcript.json of the master (word start/end in master seconds)")
ap.add_argument("--work", help="scratch folder (default: videos/basic/<prefix>-<id>)")
args = ap.parse_args()

folder = os.path.dirname(os.path.abspath(args.moments))
data = json.load(open(args.moments, encoding="utf-8"))
m = next((x for x in data["moments"] if x["id"] == args.id), None)
if m is None: sys.exit("no moment " + args.id)
if len(m["segments"]) != 1: sys.exit("basic_short handles one segment per moment; this one has %d" % len(m["segments"]))
seg_in, seg_out = m["segments"][0]["in"], m["segments"][0]["out"]
cut = m["fresh_cut"]
if not os.path.exists(cut): sys.exit("fresh cut not found: " + cut)
stem = "%s-%s-%s" % (args.prefix, args.id[1:].zfill(2), m["slug"])
out_dir = os.path.join(folder, "edited"); os.makedirs(out_dir, exist_ok=True)
out_mp4 = os.path.join(out_dir, stem + "-short-v1.mp4"); out_txt = os.path.join(out_dir, stem + "-short-v1.txt")
if os.path.exists(out_mp4): sys.exit("already exists, not overwriting: " + out_mp4)
work = args.work or os.path.join("videos", "basic", "%s-%s" % (args.prefix, args.id)); os.makedirs(os.path.join(work, "fonts"), exist_ok=True)
shutil.copy(FONT, os.path.join(work, "fonts"))

# 1. the transcript's words inside the cut, as clip-relative seconds, grouped into short lines
words = [w for w in json.load(open(args.transcript, encoding="utf-8")) if seg_in - 0.05 <= w["start"] < seg_out]
lines, cur = [], []
for w in words:
    if cur and (w["start"] - cur[-1]["end"] > MAX_GAP or len(" ".join(x["text"] for x in cur + [w])) > MAX_CHARS):
        lines.append(cur); cur = []
    cur.append(w)
    if w["text"].endswith((".", "?", "!")):
        lines.append(cur); cur = []
if cur: lines.append(cur)

def ts(t):
    h, rem = divmod(max(t, 0), 3600); mi, s = divmod(rem, 60)
    return "%d:%02d:%05.2f" % (h, mi, s)

# 2. ASS subtitles: plain white Rubik Mono One with a black outline, in the band under the picture
ass = os.path.join(work, "subs.ass")
with open(ass, "w", encoding="utf-8") as f:
    f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\n\n")
    f.write("[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
            "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
            "MarginL, MarginR, MarginV, Encoding\n")
    f.write("Style: Default,Rubik Mono One,56,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,5,0,2,60,60,540,1\n\n")
    f.write("[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    for i, line in enumerate(lines):
        start = line[0]["start"] - seg_in
        end = (lines[i + 1][0]["start"] - seg_in) if i + 1 < len(lines) and lines[i + 1][0]["start"] - line[-1]["end"] < MAX_GAP else line[-1]["end"] - seg_in + 0.25
        text = " ".join(w["text"] for w in line)
        f.write("Dialogue: 0,%s,%s,Default,,0,0,0,,%s\n" % (ts(start), ts(end), text))

# 3. render: full 16:9 picture centred on black, subtitles on top, original audio, H.264 for upload
vf = "scale=1080:-2,pad=1080:1920:0:(oh-ih)/2:black,subtitles=subs.ass:fontsdir=fonts"
# the fresh cut already starts at the moment's in point, so no seek here; subtitle times above are relative to it
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.abspath(cut), "-t", "%.3f" % (seg_out - seg_in),
       "-vf", vf, "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "out.mp4"]
r = subprocess.run(cmd, cwd=work, capture_output=True, text=True)
if r.returncode: sys.exit(r.stderr[-1500:])
shutil.copy(os.path.join(work, "out.mp4"), out_mp4)

# 4. the upload text, the same shape as the others in this folder
text = " ".join(w["text"] for w in words)
txt = "\n".join([
    "TITLE IDEAS (under 60 characters)",
    "1. " + m["summary"],
    "2. " + m["claim_words"][:1].upper() + m["claim_words"][1:],
    "3. " + m["who"].split(",")[0].replace(" (guest)", "") + ": " + m["summary"].lower(),
    "",
    "CAPTION / DESCRIPTION (#Ad on its own line, first hashtag)",
    m.get("caption") or m["summary"] + ".",
    "#Ad",
    "#Shorts #PeteButtigieg",
    "",
    "SOURCE",
    "%s, %s-%s s of the master" % (data.get("source", ""), round(seg_in), round(seg_out)),
    "Campaign: " + data.get("campaign", ""),
    "",
    "TRANSCRIPT (for checking)",
    text,
    "",
])
open(out_txt, "w", encoding="utf-8").write(txt)

# 5. record it in moments.json
m["status"] = "edited"
m["edited"] = {"v1": out_mp4.replace("\\", "/"), "txt": out_txt.replace("\\", "/"), "thumbnail": None, "builder": "basic_short.py"}
json.dump(data, open(args.moments, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(out_mp4)
print(out_txt)
