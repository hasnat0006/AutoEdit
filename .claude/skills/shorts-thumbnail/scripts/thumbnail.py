#!/usr/bin/env python3
"""thumbnail.py: render a Short's thumbnail versions from thumbs.json, check them, and hand them over.

The look (full 9:16, nothing letterboxed, creator 2026-10-20): the key moment as a real image filling the top
(a frame of the show's own graphics or B-roll, sharp, faded into a dark blurred copy of itself that fills the
rest), an optional yellow ring on the exact spot that matters (the ball on the rim), the key person cut out
large at the bottom (the local u2net person model, edges refined on the frame), and the headline at the top in
the Short's subtitle font (plain text, one word in the yellow box: NOTES 7). Rendered with `hyperframes snapshot`.
Everything that matters sits inside y 240-1680, the 3:4 middle the Instagram and TikTok grids keep; the bottom is
left to the person's body, where YouTube lays its title on the Shorts shelf.

Writes to "out": <slug>-thumb-<id>.jpg (1080x1920) per version and <slug>-thumb-check.jpg (each version full, as
the 3:4 grid crop, on the YouTube shelf, and at phone size, 150 px wide). Lints each headline (length, one boxed
word, not a repeat of a title) and the scaling, and, with "txt", writes a THUMBNAIL section into the upload .txt.

Usage: python thumbnail.py --spec <mNN/thumb/thumbs.json> [--only A,B]
"""
import argparse, base64, glob, html, io, json, os, re, shutil, subprocess, sys
from collections import deque
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ap = argparse.ArgumentParser()
ap.add_argument("--spec", required=True)
ap.add_argument("--only")
args = ap.parse_args()
S = json.load(open(args.spec, encoding="utf-8"))
base = os.path.dirname(os.path.abspath(args.spec))
rel = lambda p: p if os.path.isabs(p) else os.path.join(os.getcwd(), p)
slug, cut, subs, out = S["slug"], rel(S["cut"]), rel(S["subs"]), S["out"]
work = os.path.join(base, "render")
os.makedirs(out, exist_ok=True); os.makedirs(work, exist_ok=True)
cap = json.load(open(os.path.join(subs, "captions.json"), encoding="utf-8"))
font = os.path.join(subs, "public", "fonts", cap["font_file"])
gsap = os.path.join(subs, "public", "vendor", "gsap.min.js")
accent = cap.get("accent", "#FFD400")
SAFE = (240, 1680)          # the 3:4 middle of 1920
MODEL = os.path.expanduser("~/.cache/hyperframes/background-removal/models/u2net_human_seg.onnx")

def titles():
    if not S.get("txt") or not os.path.exists(S["txt"]): return []
    t = open(S["txt"], encoding="utf-8").read().split("DESCRIPTION")[0]
    return [re.sub(r"^\d+\.\s*", "", l).strip() for l in t.splitlines() if re.match(r"^\d+\.", l.strip())]

def words(s):
    return [w for w in re.findall(r"[a-z0-9']+", s.lower()) if w not in {"the", "a", "an", "to", "of", "and", "is", "it", "his", "he"}]

def ltext(l):
    """A headline line is a string or {"text", "scale", "plate", "color"} (see SKILL.md, "The hook")."""
    return l if isinstance(l, str) else l["text"]

def lint(v):
    msgs, lines = [], [ltext(l) for l in v["lines"]]
    text = " ".join(lines).replace("[", "").replace("]", "")
    n = len(text.split())
    if not 2 <= n <= 6: msgs.append("FLAG %d words: keep the headline to 2-6" % n)
    if len(lines) > 3: msgs.append("FLAG %d lines: 3 at most" % len(lines))
    for l in lines:
        if len(l.replace("[", "").replace("]", "")) > 18: msgs.append("FLAG line '%s' over 18 characters" % l)
    boxes = sum(l.count("[") for l in lines)
    if boxes != 1: msgs.append("FLAG %d boxed words: box exactly one (the word the thumbnail is about)" % boxes)
    hw = set(words(text))
    for t in titles():
        tw = set(words(t))
        if hw and len(hw & tw) / len(hw) > 0.6:
            msgs.append("FLAG repeats the title '%s': the headline should add to it, not say it again" % t)
    return msgs

def b64(p):
    mime = "image/png" if p.endswith(".png") else "image/jpeg"
    return "data:%s;base64,%s" % (mime, base64.b64encode(open(p, "rb").read()).decode())

def line_html(l):
    s = ltext(l)
    o = {} if isinstance(l, str) else l
    i, h = 0, ""
    while i < len(s):
        if s[i] == "[":
            j = s.index("]", i); h += '<span class="box">%s</span>' % html.escape(s[i + 1:j]); i = j + 1
        else:
            h += html.escape(s[i]); i += 1
    style = "".join("%s:%s;" % kv for kv in (("background", o.get("plate")), ("color", o.get("color"))) if kv[1])
    return '<div class="ln%s" data-scale="%s" style="%s">%s</div>' % (" plate" if o.get("plate") else "", o.get("scale", 1), style, h)

def grab(t, crop, src=None):
    """A source frame (or a still image) cropped to [x, y, w, h], as a PIL image at native resolution."""
    x, y, w, h = crop
    if src and not src.lower().endswith((".mp4", ".mov", ".mkv")):
        return Image.open(src).convert("RGB").crop((x, y, x + w, y + h))
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", src or cut, "-frames:v", "1", "-vf",
                        "crop=%d:%d:%d:%d" % (w, h, x, y), "-f", "image2pipe", "-vcodec", "png", "-"],
                       capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(b)).convert("RGB")

def boxf(a, r):
    c = np.cumsum(np.cumsum(np.pad(a, ((r + 1, r), (r + 1, r)), mode="edge"), 0), 1)
    return (c[2 * r + 1:, 2 * r + 1:] - c[:-2 * r - 1, 2 * r + 1:] - c[2 * r + 1:, :-2 * r - 1] + c[:-2 * r - 1, :-2 * r - 1]) / (2 * r + 1) ** 2

def guided(I, p, r=10, eps=1e-3):
    """He et al. guided filter: snaps the coarse model mask to the frame's real edges (hair, shoulders)."""
    mI, mp = boxf(I, r), boxf(p, r)
    a = (boxf(I * p, r) - mI * mp) / (boxf(I * I, r) - mI * mI + eps)
    b = mp - a * mI
    return boxf(a, r) * I + boxf(b, r)

_sess = None
def cutout(im, keep_color=None):
    """RGBA cut-out of the biggest person in the image, plus the head's x (px from the left).
    keep_color [r, g, b, tol]: also keep pixels of that colour that touch the person (a wide hat brim the person
    model drops: Cam Newton's yellow hat on clashcam)."""
    global _sess
    import onnxruntime as ort
    if _sess is None: _sess = ort.InferenceSession(MODEL, providers=["CPUExecutionProvider"])
    x = np.asarray(im.resize((320, 320), Image.BILINEAR), np.float32) / 255
    x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    m = _sess.run(None, {_sess.get_inputs()[0].name: x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0, 0]
    m = (m - m.min()) / (m.max() - m.min() + 1e-6)
    g = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((160, 160))) > 128
    lab = np.zeros(g.shape, np.int32); n = 0; best, bi = 0, 0
    for sy, sx in zip(*np.nonzero(g)):
        if lab[sy, sx]: continue
        n += 1; q = deque([(sy, sx)]); lab[sy, sx] = n; c = 0
        while q:
            yy, xx = q.popleft(); c += 1
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                a, b = yy + dy, xx + dx
                if 0 <= a < 160 and 0 <= b < 160 and g[a, b] and not lab[a, b]:
                    lab[a, b] = n; q.append((a, b))
        if c > best: best, bi = c, n
    keep = Image.fromarray(((lab == bi) * 255).astype(np.uint8)).resize(im.size, Image.BILINEAR).filter(ImageFilter.MaxFilter(9))
    coarse = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize(im.size, Image.BICUBIC), np.float32) / 255
    coarse *= np.asarray(keep, np.float32) / 255
    if keep_color:
        r, g_, b, tol = keep_color
        px = np.asarray(im, np.float32)
        hit = np.sqrt(((px - [r, g_, b]) ** 2).sum(-1)) < tol
        hit = np.asarray(Image.fromarray((hit * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(9)), np.float32) / 255 > 0.5
        sm = np.asarray(Image.fromarray(hit.astype(np.uint8) * 255).resize((160, 160), Image.NEAREST)) > 0
        body = np.asarray(Image.fromarray((lab == bi).astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(5))) > 0
        hl = np.zeros(sm.shape, np.int32); n = 0; keepc = np.zeros(sm.shape, bool)
        for sy, sx in zip(*np.nonzero(sm)):           # colour blobs that touch the person
            if hl[sy, sx]: continue
            n += 1; q = deque([(sy, sx)]); hl[sy, sx] = n; cells = []
            while q:
                yy, xx = q.popleft(); cells.append((yy, xx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    a, b2 = yy + dy, xx + dx
                    if 0 <= a < 160 and 0 <= b2 < 160 and sm[a, b2] and not hl[a, b2]:
                        hl[a, b2] = n; q.append((a, b2))
            if any(body[yy, xx] for yy, xx in cells):
                for yy, xx in cells: keepc[yy, xx] = True
        region = np.asarray(Image.fromarray(keepc.astype(np.uint8) * 255).resize(im.size, Image.NEAREST).filter(ImageFilter.MaxFilter(15))) > 0
        coarse = np.maximum(coarse, (hit & region).astype(np.float32))
    I = np.asarray(im.convert("L"), np.float32) / 255
    alpha = np.clip(guided(I, coarse), 0, 1)
    alpha = np.clip((alpha - 0.15) / 0.7, 0, 1)            # firm the edge: no halo of the old background
    a8 = Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(1.2))
    alpha = np.asarray(a8, np.float32) / 255               # pull the edge 2 px inside the model's line
    ys, xs = np.nonzero(alpha > 0.5)
    top = ys.min() if len(ys) else 0
    hx = float(xs[ys < top + (ys.max() - top) * 0.2].mean()) if len(ys) else im.width / 2
    # clean the edge colour: where the alpha is partial, the pixel still holds the old backdrop (a purple fringe on
    # hair); take the person's own colour from just inside the edge instead
    rgb = np.asarray(im, np.float32)
    inner = (alpha > 0.97).astype(np.float32)
    w = boxf(inner, 8)[..., None] + 1e-4
    fg = np.stack([boxf(rgb[..., c] * inner, 8) for c in range(3)], -1) / w
    edge = ((alpha < 0.97) & (w[..., 0] > 0.02))[..., None]
    rgb = np.where(edge, fg, rgb)
    rgba = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)); rgba.putalpha(Image.fromarray((alpha * 255).astype(np.uint8)))
    return rgba, hx, top

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
@font-face { font-family: "F"; src: url("fonts/f.woff2"); font-display: block; }
html, body { margin:0; background:#000; }
#stage { position:relative; width:1080px; height:1920px; overflow:hidden; background:#0B0C10; }
#bg { position:absolute; inset:-60px; width:1200px; height:2040px; object-fit:cover; filter:blur(36px) brightness(.42) saturate(1.15); }
#moment { position:absolute; -webkit-mask-image:linear-gradient(#000 70%%, transparent 100%%); mask-image:linear-gradient(#000 70%%, transparent 100%%); }
#ring { position:absolute; border:14px solid %s; border-radius:50%%; box-sizing:border-box; }
#shade { position:absolute; left:0; top:0; width:1080px; height:700px; background:linear-gradient(rgba(0,0,0,.82) 0%%, rgba(0,0,0,.6) 45%%, rgba(0,0,0,0) 100%%); }
#tblur { position:absolute; left:0; top:0; width:1080px; backdrop-filter:blur(%dpx); -webkit-backdrop-filter:blur(%dpx);
  -webkit-mask-image:linear-gradient(#000 75%%, transparent 100%%); mask-image:linear-gradient(#000 75%%, transparent 100%%); }
#low { position:absolute; left:0; bottom:0; width:1080px; height:900px; background:linear-gradient(rgba(0,0,0,0), rgba(0,0,0,.75)); }
#person { position:absolute; bottom:0; }
#head { position:absolute; left:40px; right:40px; top:260px; text-align:center; font-family:"F", sans-serif; font-weight:700;
  font-size:%dpx; line-height:1.08; letter-spacing:-.03em; color:#FFFFFF; text-transform:uppercase; transform:rotate(%sdeg); }
#head .ln { display:table; margin:.06em auto; white-space:nowrap; line-height:1.12; }
#head .plate { padding:.02em .2em .04em; border-radius:.1em; margin:.08em auto; }
#head .box { background:%s; color:#111317; border-radius:.12em; padding:0 .12em; }
</style></head><body>
<div id="stage" data-composition-id="%s" data-start="0" data-duration="1" data-fps="30" data-width="1080" data-height="1920">
<img id="bg" src="%s">%s<div id="shade"></div><div id="tblur" style="height:%dpx"></div><div id="low"></div>%s<div id="head">%s</div>
<script src="vendor/gsap.min.js"></script>
<script>(function(){ const tl = window.gsap.timeline({ paused: true }); tl.to({}, { duration: 1 }, 0);
window.__timelines = window.__timelines || {}; window.__timelines["%s"] = tl;
// fit the headline: each line as big as its scale and the width allow (it has to read at 150 px wide), then the
// whole block shrunk together until it fits y 260-%d (the ring and the face start below)
const h = document.getElementById("head"), ls = [...h.querySelectorAll(".ln")], MAX = %d, ROOM = %d;
function fit() {
  ls.forEach(l => { let s = Math.round(MAX * +l.dataset.scale); l.style.fontSize = s + "px";
    while (s > 40 && l.offsetWidth > 980) { s -= 2; l.style.fontSize = s + "px"; } });
  if (h.offsetHeight > ROOM) { const k = ROOM / h.offsetHeight;
    ls.forEach(l => { l.style.fontSize = Math.floor(parseFloat(l.style.fontSize) * k) + "px"; }); } }
fit(); document.fonts.ready.then(fit); })();</script>
</div></body></html>"""

made, report = [], []
for v in S["versions"]:
    if args.only and v["id"] not in args.only.split(","): continue
    tid = "%s-thumb-%s" % (slug, v["id"])
    msgs = lint(v)
    d = os.path.join(work, tid); shutil.rmtree(d, ignore_errors=True); os.makedirs(d + "/vendor"); os.makedirs(d + "/fonts")
    shutil.copy(gsap, d + "/vendor/gsap.min.js"); shutil.copy(font, d + "/fonts/f.woff2")

    # the key person, cut out, bottom-anchored, the face at face_x
    P = v["person"]
    pim = grab(P["t"], P["crop"])
    rgba, hx, ptop = cutout(pim, P.get("keep_color"))
    ps = P.get("width", 1150) / pim.width
    if ps > 1.6: msgs.append("FLAG the person is scaled %.1fx: crop wider or pick a closer shot" % ps)
    rgba = rgba.resize((round(pim.width * ps), round(pim.height * ps)), Image.LANCZOS)
    rgba.save(d + "/person.png")
    left = P.get("face_x", 540) - hx * ps
    face_y = 1920 - rgba.height + ptop * ps
    if face_y < 760: msgs.append("FLAG the head starts at y %d: it runs into the headline" % face_y)
    # "fade": when the crop stops mid-body (above a desk, an answer board), the body fades out into the bottom
    fade = P.get("fade", 0)
    fcss = ("-webkit-mask-image:linear-gradient(#000 calc(100%% - %dpx), transparent); mask-image:linear-gradient(#000 calc(100%% - %dpx), transparent);"
            % (fade, fade)) if fade else ""
    person = '<img id="person" src="%s" style="left:%dpx; width:%dpx; %s">' % (b64(d + "/person.png"), left, rgba.width, fcss)

    # the key moment: a real image in the top, sharp, the focus point placed at focus_at, an optional ring on it
    moment, bgsrc = "", d + "/bg.jpg"
    M = v.get("moment")
    if M:
        src = M.get("src", "cut")
        src = None if src == "cut" else next((q for q in (os.path.join(subs, src), os.path.join(base, src), src) if os.path.exists(q)), src)
        mim = grab(M.get("t", 0), M["crop"], src)
        sc = M.get("scale", 2.0)
        fx, fy = M["focus"]; ax, ay = M["focus_at"]
        sc = max(sc, ay / max(fy, 1), ax / max(fx, 1), (1080 - ax) / max(mim.width - fx, 1))   # always full bleed: no edge shows
        if sc > 2.6: msgs.append("FLAG the moment image is scaled %.1fx: it will look soft" % sc)
        mw, mh = round(mim.width * sc), round(mim.height * sc)
        big = mim.resize((mw, mh), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
        big.save(d + "/moment.jpg", quality=92); mim.save(bgsrc, quality=90)
        mx, my = ax - fx * sc, ay - fy * sc
        moment = '<img id="moment" src="%s" style="left:%dpx; top:%dpx; width:%dpx; height:%dpx">' % (b64(d + "/moment.jpg"), mx, my, mw, mh)
        if M.get("ring"):
            r = M["ring"]
            moment += '<div id="ring" style="left:%dpx; top:%dpx; width:%dpx; height:%dpx"></div>' % (ax - r, ay - r, 2 * r, 2 * r)
    else:
        grab(P["t"], [0, 0] + list(map(int, subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
             "stream=width,height", "-of", "csv=p=0", cut], capture_output=True, text=True).stdout.strip().split(",")))).save(bgsrc, quality=90)

    lines_bottom = v.get("bottom", 600)               # keep it above the ring and the face
    size = v.get("size", 150)                          # the biggest a scale-1 line may get
    # blur the photo behind the hook (creator, clash02-01 H3): a soft band down to just under the text, fading out
    # before the ring, so the moment itself stays sharp
    tb = v.get("text_blur", 10)
    page = PAGE % (accent, tb, tb, size, v.get("tilt", 0), accent, tid, b64(bgsrc), moment, lines_bottom + 90, person,
                   "".join(line_html(l) for l in v["lines"]), tid, lines_bottom, size, lines_bottom - 260)
    open(d + "/index.html", "w", encoding="utf-8").write(page)
    raw = d + "/snap"
    r = subprocess.run([shutil.which("npx") or "npx", "hyperframes", "snapshot", d, "--at", "0.5", "-o", raw, "--no-end"],
                       capture_output=True, text=True)
    shots = glob.glob(raw + "/*.png")
    if not shots: sys.exit(r.stdout[-1500:] + r.stderr[-1500:])
    jpg = os.path.join(out, tid + ".jpg")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", shots[0], "-q:v", "2", jpg], check=True)
    made.append((v, jpg, P["t"]))
    report.append("%s  person %.2f s (x%.2f)  %s" % (v["id"], P["t"], ps, " | ".join(msgs) or "ok"))

# the check sheet: per version, full / 3:4 grid crop / YouTube shelf (title over the bottom) / phone size 150 px
try:
    F = ImageFont.truetype("arialbd.ttf", 22); Fs = ImageFont.truetype("arial.ttf", 18)
except OSError:
    F = Fs = ImageFont.load_default()
cols = [("full 9:16", 270, 480), ("IG / TikTok grid 3:4", 270, 360), ("YouTube shelf", 270, 480), ("phone 150 px", 150, 267)]
cw = sum(c[1] for c in cols) + 40 * (len(cols) + 1)
sheet = Image.new("RGB", (cw, 60 + len(made) * 540), (28, 28, 30))
dr = ImageDraw.Draw(sheet)
x = 40
for name, w, h in cols:
    dr.text((x, 18), name, fill=(220, 220, 220), font=F); x += w + 40
for k, (v, jpg, t) in enumerate(made):
    im = Image.open(jpg).convert("RGB"); y = 60 + k * 540
    dr.text((10, y + 4), v["id"], fill=(255, 212, 0), font=F)
    x = 40
    full = im.resize((270, 480), Image.LANCZOS)
    grid = im.crop((0, SAFE[0], 1080, SAFE[1])).resize((270, 360), Image.LANCZOS)
    shelf = full.copy(); sd = ImageDraw.Draw(shelf, "RGBA")
    for i in range(140):
        sd.line([(0, 480 - i), (270, 480 - i)], fill=(0, 0, 0, int(200 * (1 - i / 140))))
    sd.text((12, 410), "Title of the Short goes", fill=(255, 255, 255), font=Fs)
    sd.text((12, 432), "here, two lines  ·  1.2M views", fill=(255, 255, 255), font=Fs)
    phone = im.resize((150, 267), Image.LANCZOS)
    for tile in (full, grid, shelf, phone):
        sheet.paste(tile, (x, y + 30)); x += tile.width + 40
sheet_p = os.path.join(out, slug + "-thumb-check.jpg")
sheet.save(sheet_p, quality=90)

pick = S.get("pick")
if S.get("txt") and os.path.exists(S["txt"]) and pick:
    pv = next((m for m in made if m[0]["id"] == pick), None)
    if pv:
        txt = open(S["txt"], encoding="utf-8").read().split("\nTHUMBNAIL\n")[0].rstrip() + "\n"
        txt += ("\nTHUMBNAIL\nUpload: %s\nHeadline: %s\nIf the app only lets you pick a frame from the video, pick %d:%04.1f.\n"
                % (os.path.basename(pv[1]), " / ".join(ltext(l) for l in pv[0]["lines"]).replace("[", "").replace("]", ""),
                   int(pv[2] // 60), pv[2] % 60))
        open(S["txt"], "w", encoding="utf-8").write(txt)
        report.append("wrote the THUMBNAIL section into %s" % S["txt"])

for l in report: print(l)
for v, jpg, t in made: print("wrote", jpg)
print("wrote", sheet_p)
