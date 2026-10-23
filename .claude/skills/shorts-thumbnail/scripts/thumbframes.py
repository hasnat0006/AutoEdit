#!/usr/bin/env python3
"""thumbframes.py: find the best thumbnail frames in a fresh cut, so nobody types timestamps and crop numbers.

Samples the cut 4 times a second and scores each frame on the main person (the local u2net_human_seg cut-out
model that hyperframes remove-background already downloaded, no new download): how sharp the head is, how still
(no motion blur), how big the person is, how loud the moment is (laughing, shouting, a big reaction), and how far
from a shot change. Keeps the top N frames at least 1.5 s apart (at most 2 per shot) and writes:
  candidates.json  each pick: t, score, the square crop (x, y, side in source pixels), the head point
  contact.jpg      the picks as they will look in the thumbnail (square crop), numbered, with the time
Open contact.jpg and choose by eye: the score finds sharp, expressive frames, it can't judge the expression.

Usage: python thumbframes.py --cut <cuts/clip.mp4> --out <dir> [--subs <mNN/subs>] [--n 6]
  --subs  reads window.json for the shot changes (otherwise found from the frame differences)
"""
import argparse, json, os, subprocess
from collections import deque
import numpy as np
from PIL import Image, ImageDraw, ImageFont

MODEL = os.path.expanduser("~/.cache/hyperframes/background-removal/models/u2net_human_seg.onnx")
AW = 960            # analysis width
FPS = 4

ap = argparse.ArgumentParser()
ap.add_argument("--cut", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--subs")
ap.add_argument("--n", type=int, default=6)
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)
if not os.path.exists(MODEL):
    raise SystemExit("no person model at %s: run prep.py --depth once (asks before the ~170 MB download)" % MODEL)
import onnxruntime as ort
sess = ort.InferenceSession(MODEL, providers=["CPUExecutionProvider"])
inp = sess.get_inputs()[0].name

probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-show_entries", "format=duration", "-of", "json", args.cut], capture_output=True, text=True, check=True)
pj = json.loads(probe.stdout)
W, H = pj["streams"][0]["width"], pj["streams"][0]["height"]
dur = float(pj["format"]["duration"])
AH = int(round(AW * H / W / 2)) * 2
sc = W / AW

# loudness per 0.1 s (mono 16 kHz)
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", args.cut, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                     capture_output=True, check=True).stdout
a = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
win = 1600
rms = np.sqrt(np.mean(a[:len(a) // win * win].reshape(-1, win) ** 2, axis=1)) if len(a) >= win else np.zeros(1)
rms = rms / (np.percentile(rms, 95) + 1e-6)

def loud(t):
    i = int(t * 10)
    return float(np.mean(rms[max(0, i - 2):i + 3])) if len(rms) else 0.0

def erode(g):
    e = g.copy()
    e[1:] &= g[:-1]; e[:-1] &= g[1:]; e[:, 1:] &= g[:, :-1]; e[:, :-1] &= g[:, 1:]
    return e

def people(rgb):
    """Every person blob on a 96-wide grid (eroded twice, so people side by side or in a grid of panels come apart):
    a list of (x0, y0, x1, y1 in analysis px, area fraction, xs, ys, cell size)."""
    x = np.asarray(Image.fromarray(rgb).resize((320, 320), Image.BILINEAR), np.float32) / 255
    x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    m = sess.run(None, {inp: x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0, 0]
    m = (m - m.min()) / (m.max() - m.min() + 1e-6)
    gw, gh = 96, max(2, int(96 * AH / AW))
    g = erode(erode(np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((gw, gh), Image.BILINEAR)) > 128))
    lab = np.zeros(g.shape, np.int32); n = 0; out = []
    k = AW / gw
    for sy, sx in zip(*np.nonzero(g)):
        if lab[sy, sx]: continue
        n += 1; q = deque([(sy, sx)]); lab[sy, sx] = n; c = 0
        while q:
            y, x0 = q.popleft(); c += 1
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x0 + dx
                if 0 <= yy < gh and 0 <= xx < gw and g[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = n; q.append((yy, xx))
        if c < 0.012 * gw * gh: continue
        ys, xs = np.nonzero(lab == n)
        out.append(((xs.min() - 2) * k, max(0, ys.min() - 2) * k, (xs.max() + 3) * k, min(gh, ys.max() + 3) * k,
                    c / (gw * gh), xs, ys, k))
    return out

def head_box(p):
    x0, y0, x1, y1, area, xs, ys, k = p
    top = ys <= ys.min() + max(2, (ys.max() - ys.min()) * 0.25)
    cx = float(np.mean(xs[top]) + 0.5) * k
    hw = max(40.0, (xs[top].max() - xs[top].min() + 1) * k)
    hh = min(y1 - y0, hw * 1.3)
    return cx, y0, hw, hh

def lap_var(g):
    if g.shape[0] < 5 or g.shape[1] < 5: return 0.0
    l = -4 * g[1:-1, 1:-1] + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:]
    return float(l.var())

proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", args.cut, "-vf", "fps=%d,scale=%d:%d" % (FPS, AW, AH),
                         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
rows, grays = [], []
fsz = AW * AH * 3
i = 0
while True:
    buf = proc.stdout.read(fsz)
    if len(buf) < fsz: break
    rgb = np.frombuffer(buf, np.uint8).reshape(AH, AW, 3)
    t = (i + 0.5) / FPS; i += 1
    gray = rgb.astype(np.float32).mean(axis=2)
    grays.append(gray[::4, ::4])
    # one row per person (the best one per frame is kept later): a grid of webcams gives each face its own chance
    found = False
    for p in people(rgb):
        cx, hy, hw, hh = head_box(p)
        hx0, hx1 = int(max(0, cx - hw / 2)), int(min(AW, cx + hw / 2))
        hy0, hy1 = int(max(0, hy)), int(min(AH, hy + hh))
        if hx1 - hx0 < 8 or hy1 - hy0 < 8: continue
        rows.append(dict(t=t, j=i - 1, ok=True, sharp=lap_var(gray[hy0:hy1, hx0:hx1]), size=(p[3] - p[1]) / AH,
                         area=p[4], cx=cx, hy=hy, hh=hh, ph=(p[3] - p[1]) * sc, box=(hx0, hy0, hx1, hy1), loud=loud(t)))
        found = True
    if not found: rows.append(dict(t=t, j=i - 1, ok=False))
proc.wait()

# stillness: frame difference with the neighbours, inside the head box (on the quarter-size grays)
diffs = [0.0] + [float(np.abs(grays[j] - grays[j - 1]).mean()) for j in range(1, len(grays))]
shots = []
if args.subs and os.path.exists(os.path.join(args.subs, "window.json")):
    shots = json.load(open(os.path.join(args.subs, "window.json"))).get("shots", [])
else:
    med = np.median(diffs) + 1e-6
    shots = [j / FPS for j in range(1, len(diffs)) if diffs[j] > 6 * med and diffs[j] > 12]
for r in rows:
    if not r["ok"]: continue
    j = r["j"]
    x0, y0, x1, y1 = [v // 4 for v in r["box"]]
    m = []
    for k in (j - 1, j + 1):
        if 0 <= k < len(grays) and x1 > x0 and y1 > y0:
            m.append(float(np.abs(grays[j][y0:y1, x0:x1] - grays[k][y0:y1, x0:x1]).mean()))
    r["motion"] = max(m) if m else 0.0
    r["gap"] = min([abs(r["t"] - s) for s in shots] + [9.0])
    r["shot"] = sum(1 for s in shots if s <= r["t"])

ok = [r for r in rows if r["ok"] and 0.3 < r["t"] < dur - 0.3]
if not ok: raise SystemExit("no person found in any frame")

def z(key):
    v = np.array([r[key] for r in ok], np.float64)
    return (v - v.mean()) / (v.std() + 1e-6)

zs, zm, zl = z("sharp"), z("motion"), z("loud")
# the square crop in source pixels: framed on this person (head to chest), as big as the frame allows, never
# smaller than half the frame height (a 1080 square from fewer pixels than that looks soft: NOTES 2)
big = int(min(H * 0.9, W * 0.95))
for r, a1, a2, a3 in zip(ok, zs, zm, zl):
    r["side"] = int(min(big, max(H * 0.5, r["ph"] * 1.2))) // 2 * 2
    up = 1080 / r["side"]                               # how much the crop is scaled up for the thumbnail
    small = r["ph"] < H * 0.3                           # a person in a wide shot: too small for a thumbnail
    r["score"] = round(float(1.0 * a1 - 1.0 * a2 + 0.6 * a3 + 1.5 * min(r["size"], 0.85) / 0.85
                             - 1.2 * max(0.0, up - 1.25) - (2.0 if small else 0) - (2.0 if r["gap"] < 0.3 else 0)), 3)

picks, per_shot = [], {}
for r in sorted(ok, key=lambda r: -r["score"]):
    if any(abs(r["t"] - q["t"]) < 1.5 for q in picks) or per_shot.get(r["shot"], 0) >= 2: continue
    picks.append(r); per_shot[r["shot"]] = per_shot.get(r["shot"], 0) + 1
    if len(picks) >= args.n: break

out = []
for n, r in enumerate(picks, 1):
    side = r["side"]
    hx, hy = r["cx"] * sc, (r["hy"] + r["hh"] * 0.45) * sc
    x = int(min(max(0, hx - side / 2), W - side)) // 2 * 2
    y = int(min(max(0, hy - side * 0.32), H - side)) // 2 * 2
    out.append(dict(n=n, t=round(r["t"], 2), score=r["score"], crop=dict(x=x, y=y, side=side),
                    head=[int(hx), int(hy)], sharp=round(r["sharp"], 1), motion=round(r["motion"], 2),
                    loud=round(r["loud"], 2), size=round(r["size"], 2)))
json.dump(dict(cut=os.path.abspath(args.cut), width=W, height=H, duration=dur, candidates=out),
          open(os.path.join(args.out, "candidates.json"), "w"), indent=1)

tiles = []
for c in out:
    cr = c["crop"]
    jpg = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(c["t"]), "-i", args.cut, "-frames:v", "1", "-vf",
                          "crop=%d:%d:%d:%d,scale=480:480" % (cr["side"], cr["side"], cr["x"], cr["y"]),
                          "-f", "image2pipe", "-vcodec", "mjpeg", "-"], capture_output=True, check=True).stdout
    import io
    im = Image.open(io.BytesIO(jpg)).convert("RGB")
    d = ImageDraw.Draw(im)
    try: f = ImageFont.truetype("arialbd.ttf", 30)
    except OSError: f = ImageFont.load_default()
    d.rectangle([0, 0, 230, 44], fill=(0, 0, 0))
    d.text((10, 6), "#%d  %.2f s" % (c["n"], c["t"]), fill=(255, 212, 0), font=f)
    tiles.append(im)
cols = 3; rws = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (cols * 490 + 10, rws * 490 + 10), (30, 30, 30))
for k, im in enumerate(tiles):
    sheet.paste(im, (10 + (k % cols) * 490, 10 + (k // cols) * 490))
sheet.save(os.path.join(args.out, "contact.jpg"), quality=90)
for c in out:
    print("#%d  t=%5.2f  score %6.2f  sharp %7.1f  motion %5.2f  loud %4.2f  size %.2f  crop x=%d y=%d side=%d"
          % (c["n"], c["t"], c["score"], c["sharp"], c["motion"], c["loud"], c["size"], c["crop"]["x"], c["crop"]["y"], c["crop"]["side"]))
print("wrote", os.path.join(args.out, "contact.jpg"))
