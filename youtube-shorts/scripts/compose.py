#!/usr/bin/env python3
"""compose.py (youtube-shorts): build public/index.html, a 1080x1920 (9:16) YouTube Short, from storyboard.json.

The storyboard is the review artifact AND the source: retiming a beat is editing one number and rebuilding.
The frame is 1080x1920 and renders 1:1 (npx hyperframes render --resolution portrait). A Short is 60 s at most:
a longer storyboard is refused.

Zones (YouTube draws its own UI over a Short: search and menu at the top; title, channel and music at the bottom;
like / comment / share / remix down the right edge from about y 900):
  top       y 230 to ~700    titles, chips, logos, numbers, lists, image cards     ("pos": "top", the default)
  center    y ~740 to 1100   a beat that matters more than your face for a moment  ("pos": "center")
  captions  y ~1150 to 1420  the word-by-word captions
  keep out  y < 200, y > 1480, and x > 930 below y 900

Usage:
  python3 compose.py --spec videos/<p>/storyboard.json --out videos/<p>/public [--shared videos/_shared]
  --shared: a folder of reusable assets; img/* is copied to <out>/img, sfx/* to <out>/sfx (sfx/pop.mp3 = the logo pop).

storyboard.json:
{
  "id": "short-01", "duration": 42.5, "video": "input-video.mp4", "origin": "50% 0%",
  "captions": {"transcript": "transcript.json", "max_words": 3, "max_chars": 18, "y": 1180, "size": 88,
               "upper": false, "style": "karaoke|plain", "em": ["free"], "off": [[12.0, 15.5]]},
  "progress": false,
  "beats": [
    {"type": "text",  "id": "h1", "text": "I edit every Short with Claude", "em": [5], "color": "cyan|amber", "pos": "top|center", "in": 0.0, "out": 2.8, "anchor": "-"},
    {"type": "chip",  "id": "c1", "text": "it took 4 minutes", "em": [2, 3], "pos": "top|center", "in": 9.1, "out": 11.0, "anchor": "four minutes"},
    {"type": "logo",  "id": "lg", "src": "img/claude.svg", "pos": "top|tl|tr", "pop": 4.32, "in": 4.25, "out": 6.6, "anchor": "Claude"},
    {"type": "list",  "id": "ls", "eyebrow": "YOU NEED", "items": [["A phone", 13.2], ["One script", 14.0, "a script"]],
     "marker": "dot|check", "in": 12.9, "out": 16.5, "anchor": "a phone"},
    {"type": "stat",  "id": "st", "value": 1000, "prefix": "$", "suffix": "", "decimals": 0, "label": "a month", "color": "amber|cyan|white",
     "at": 18.2, "dur": 1.2, "pos": "top|center", "in": 18.0, "out": 21.0, "anchor": "a thousand dollars"},
    {"type": "image", "id": "im", "src": "img/post.png", "frame": "card|full", "push": 1.06, "label": "", "in": 22.0, "out": 25.0, "anchor": "this post"},
    {"type": "clip",  "id": "br", "src": "broll/desk.mp4", "media_start": 0, "label": "", "in": 26.0, "out": 28.6, "anchor": "at my desk"},
    {"type": "split", "id": "sp", "src": "broll/screen.mp4 or img/shot.png", "shift": 560, "in": 30.0, "out": 34.0, "anchor": "on screen"},
    {"type": "cta",   "id": "ct", "text": "Follow for part 2", "button": "Follow", "pos": "top|center", "in": 39.0, "out": 42.0, "anchor": "follow"},
    {"type": "vignette", "id": "vg", "in": 35.0, "out": 36.6, "anchor": "-"}
  ],
  "camera": [["punch", 0.0, 1.08], ["set", 3.10, 1.0], ["creep", 3.1, 8.0, 1.06], ["release", 8.9, 0.4]],
  "sounds": [{"src": "sfx/click.mp3", "at": 13.2, "dur": 0.4, "volume": 0.28}],
  "raw_html": "", "raw_js": ""
}
Every beat: type, id, in, out, anchor (the spoken phrase it lands on; "-" = deliberately unanchored).
"glass_bg" / "chip_bg": the light-glass and chip tints (a bright set takes "chip_bg": "rgba(17,17,17,0.8)").
Any beat can carry "hide_captions": true (the captions step aside while it shows); text beats take "size" (px).
A text beat with "in" at 0 is on screen from the first frame (no entrance): the hook title.
captions.transcript is relative to the storyboard's folder. During a split the captions move up to the seam.
Camera: set t scale | creep t0 t1 scale (power1.inOut) | punch t scale (0.30 s power2.out) | release t dur | reveal t.

The card look (landscape sources): "theme": {} (Rubik Mono One, white + yellow; keys font font_file text accent alert
outline bg) and "frame": {"mode": "card", "y": 590} put the whole 16:9 footage in a rounded card on a drifting background;
captions follow the theme. Motion formats (need the theme):
    {"type": "title", "id": "tt", "text": "It wasn't|bad luck", "em": [1], "size": 92, "y": 296, "pulse": true,
     "strike": {"line": 1, "at": 8.0}, "swap": {"at": 13.7, "text": "It was|overconfidence", "em": [1], "size": 82}, "in": 0, "out": D}
    {"type": "dots", "id": "od", "n": 20, "hit": [13], "at": 8.96, "label": "5% = 1 in 20", "label_em": [0], "label_at": 10.08, "y": 1316, ...}
    {"type": "meter", "id": "mt", "label": "Certainty", "to": 1.35, "over_label": "Too much", "fill_at": 15.6, "x": 110, "y": 1325, "w": 640, ...}
    {"type": "emoji", "id": "e1", "char": "\U0001F632", "x": 975, "y": 612, "size": 130, "spin": false, ...}   (SVGs in assets/emoji)
    {"type": "credit", "id": "src", "text": "Show name · episode", "y": 200, ...}
Hand-made elements (need the theme; strokes are hand-wobbled, seeded by the beat id, drawn on by stroke-dashoffset):
    {"type": "draw", "id": "sh", "shapes": [{"shape": "burst", "cx": 530, "cy": 545, "n": 4, "from": -100, "to": -10, "r0": 30, "r1": 98, "at": 0.98},
       {"shape": "circle|underline|arrow|path", ...}], "color": "accent", "width": 8, "in": .., "out": .., "anchor": ".."}
    {"type": "dice", "id": "die", "x": 540, "y": 1268, "size": 104, "face": 1, "land": 8.05, "in": .., "out": .., "anchor": ".."}
    {"type": "chart", "id": "ch", "x": 200, "y": 1175, "w": 570, "h": 165, "lines": [{"label": "Reality", "color": "text",
       "points": [[0, .3], [1, .36]], "at": .., "dur": .45}, {"label": "Expected", "points": [[0, .3], [1, 1.05]], "arrow": true, ...}], ...}
    dots + "ring": true, "ring_at": t (a marker ring around the hits); title "swap" + "underline": line, "underline_at": t
Worked example: examples/clip-03/storyboard-v3.json.
"""
import argparse, glob, json, math, os, random, shutil, sys
from html import escape as _esc

hesc = lambda s: _esc(str(s), quote=False)
qesc = lambda s: _esc(str(s), quote=True)

FW, FH = 1080, 1920
MAX_LEN = 60.0
POS_Y = {"top": 250, "center": 760}

ap = argparse.ArgumentParser()
ap.add_argument("--spec", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--shared", default="")
args = ap.parse_args()
S = json.load(open(args.spec, encoding="utf-8"))
SPEC_DIR = os.path.dirname(os.path.abspath(args.spec))
OUT = args.out
D = float(S["duration"])
if D > MAX_LEN + 1e-6:
    sys.exit("FAIL duration %.2f s: a Short is %.0f s at most. Cut it down before composing." % (D, MAX_LEN))
os.makedirs(OUT, exist_ok=True)

# ---- stage shared assets (fonts, gsap, logos, sfx) ---------------------------------------------------
SKILL = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
def stage(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(src) and not os.path.exists(dst):
        shutil.copy(src, dst)
# The three 7 KB DMSans-400/500/700 subsets: Chrome draws the system face at these metrics, the approved look.
fonts = sorted(f for ext in ("*.woff2", "*.ttf", "*.otf") for f in glob.glob(os.path.join(SKILL, "assets", "fonts", ext)))
if not fonts:
    print("WARN no .woff2 fonts in %s: the text falls back to the system sans" % os.path.join(SKILL, "assets", "fonts"))
for f in fonts:
    stage(f, os.path.join(OUT, "fonts", os.path.basename(f)))
GSAP_CDN = "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"
stage(os.path.join(SKILL, "assets", "vendor", "gsap.min.js"), os.path.join(OUT, "vendor", "gsap.min.js"))
GSAP_SRC = "vendor/gsap.min.js" if os.path.exists(os.path.join(OUT, "vendor", "gsap.min.js")) else GSAP_CDN
if GSAP_SRC == GSAP_CDN:
    print("note: no local gsap.min.js, the page loads GSAP from %s (the first render needs internet)" % GSAP_CDN)
if args.shared:
    for sub in ("img", "sfx"):
        for f in glob.glob(os.path.join(args.shared, sub, "*")):
            if os.path.isfile(f):
                stage(f, os.path.join(OUT, sub, os.path.basename(f)))

origin = S.get("origin", "50% 0%")
GLASS_BG = S.get("glass_bg", "rgba(255,255,255,0.18)")
CHIP_BG = S.get("chip_bg", "rgba(17,17,17,0.5)")    # a bright set (white wall) needs it darker: rgba(17,17,17,0.8)
# "theme": a display font + colours for captions and the motion-graphic formats; without it, the house look (DM Sans, cyan)
THEME = S.get("theme")
if THEME is not None:
    THEME = dict({"font": "Rubik Mono One", "font_file": "RubikMonoOne-Regular.ttf", "text": "#FFFFFF", "accent": "#FFD400",
                  "alert": "#FF3B30", "outline": "#000000", "bg": "#0C0C10"}, **THEME)
ACCENT = THEME["accent"] if THEME else "#0AF0F0"
TEXT = THEME["text"] if THEME else "#FFFFFF"
ALERT = THEME["alert"] if THEME else "#FF3B30"
def rgb(hexcol):
    h = hexcol.lstrip("#"); return "%d,%d,%d" % (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
# "frame": {"mode": "card"} shows the whole 16:9 footage in a rounded card (never upscaled) on an animated background,
# leaving the space above and below for the headline, captions and graphics
FRAME = S.get("frame") or {}
CARD = FRAME.get("mode") == "card"
if CARD:
    CX, CY, CW = int(FRAME.get("x", 40)), int(FRAME.get("y", 600)), int(FRAME.get("w", FW - 80))
    CH, CR = int(FRAME.get("h", round(CW * 9 / 16.0))), int(FRAME.get("radius", 32))

CSS = """
  @font-face { font-family: "DM Sans"; src: url("fonts/DMSans-400.woff2") format("woff2"); font-weight: 400; font-display: block; }
  @font-face { font-family: "DM Sans"; src: url("fonts/DMSans-500.woff2") format("woff2"); font-weight: 500; font-display: block; }
  @font-face { font-family: "DM Sans"; src: url("fonts/DMSans-700.woff2") format("woff2"); font-weight: 700; font-display: block; }
  * { box-sizing: border-box; }
  html, body { margin:0; padding:0; width:100%; height:100%; overflow:hidden; background:#000;
    font-family: "DM Sans", ui-sans-serif, system-ui, sans-serif; }
  #stage { position:relative; width:100%; height:100%; overflow:hidden; background:#000; }
  :root { --cyan:#0AF0F0; --blue:#0005EE; --magenta:#CD00EE; --amber:#FFB904; --white:#FFFFFF; --red:#FF0000; }
  .video-wrapper { position:absolute; left:0; top:0; width:1080px; height:1920px; overflow:hidden; transform-origin:50% 0%; will-change:transform; }
  #video-zoom { position:absolute; inset:0; transform-origin:ORIGIN; will-change:transform; }
  #video-zoom video { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; display:block; }
  #bg-video { z-index:1; }
  .card-host { position:absolute; pointer-events:none; overflow:hidden; z-index:25; }
  .card-host .card { position:relative; width:100%; height:100%; overflow:hidden; }
  .shadow { text-shadow: 0 0 3px rgba(0,0,0,.9), 0 3px 6px rgba(0,0,0,.85), 0 10px 34px rgba(0,0,0,.6); }
  .glass { position:absolute; border-radius:28px; background: rgba(255,255,255,0);
    backdrop-filter: blur(30px) saturate(1.25); -webkit-backdrop-filter: blur(30px) saturate(1.25);
    border: 3px solid rgba(255,255,255,0); box-shadow: 0 24px 80px rgba(0,0,0,0); }
  .centered { left:0; right:0; margin:0 auto; width:max-content; }
  /* text: a headline, words rise in, wraps inside the safe width */
  .tx { position:absolute; left:60px; right:60px; text-align:center; font-weight:700; font-size:96px; line-height:1.08;
    letter-spacing:-.015em; color:var(--white); }
  .tx .w { display:inline-block; }
  .tx .w.em { color:var(--cyan); } .tx.amber .w.em { color:var(--amber); }
  /* chip: the punchline, dark glass, emphasis magenta */
  .chip { position:absolute; max-width:960px; padding:22px 38px; border-radius:18px; text-align:center;
    background: rgba(17,17,17,0); backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px); }
  .chip .inner { opacity:0; font-weight:700; font-size:72px; line-height:1.1; color:var(--white); letter-spacing:-.012em; }
  .chip .inner .em { color:var(--magenta); }
  /* logo plate: logo only, you say the name */
  .logo-plate { width:360px; height:360px; }
  .logo-plate .inner { opacity:0; width:100%; height:100%; display:flex; align-items:center; justify-content:center; }
  .logo-plate .inner img { max-height:250px; max-width:270px; width:auto; height:auto; display:block; filter: drop-shadow(0 4px 14px rgba(0,0,0,.45)); }
  /* list: a glass card that grows with its items */
  .list { width:820px; padding:32px 40px 14px; }
  .list .inner { opacity:0; }
  .list .eyebrow { font-weight:700; font-size:36px; color:rgba(255,255,255,.92); line-height:1; margin-bottom:26px; letter-spacing:.04em; }
  .list .item { display:none; align-items:center; gap:24px; margin-bottom:24px; }
  .list .item .d { width:22px; height:22px; border-radius:50%; background:var(--white); flex:none; box-shadow: 0 2px 8px rgba(0,0,0,.6); }
  .list .item .t { font-weight:700; font-size:62px; line-height:1.06; color:var(--white); letter-spacing:-.012em; }
  .mk { width:48px; height:48px; flex:none; }
  .mk svg { width:48px; height:48px; overflow:visible; }
  .mk .ring { fill:rgba(10,240,240,0); stroke:rgba(255,255,255,.85); stroke-width:3; }
  .mk .tick { fill:none; stroke:#06121a; stroke-width:4.5; stroke-linecap:round; stroke-linejoin:round; }
  /* stat: one number, every digit, counting up */
  .stat { position:absolute; left:40px; right:40px; text-align:center; opacity:0; }
  .stat .num { font-weight:700; line-height:1; letter-spacing:-.02em; color:var(--white); font-variant-numeric: tabular-nums; }
  .stat.amber .num { color:var(--amber); } .stat.cyan .num { color:var(--cyan); }
  .stat .lab { margin-top:14px; font-weight:700; font-size:56px; line-height:1.1; color:var(--white); }
  /* image card: a screenshot or photo in a glass frame */
  .imgcard { width:920px; padding:14px; }
  .imgcard .inner { opacity:0; border-radius:16px; overflow:hidden; }
  .imgcard img { display:block; width:100%; height:auto; max-height:860px; object-fit:contain; transform-origin:50% 50%; }
  .imgfull { position:absolute; inset:0; overflow:hidden; background:#05060c; }
  .imgfull img { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; transform-origin:50% 40%; }
  .slabel { position:absolute; left:60px; right:60px; top:250px; text-align:center; font-weight:700; font-size:84px; line-height:1.08;
    color:var(--white); letter-spacing:-.015em; opacity:0; }
  .slabel .em { color:var(--cyan); }
  .cutaway-video { position:absolute; left:0; top:0; width:1080px; height:1920px; object-fit:cover; z-index:20; }
  .split-video { position:absolute; left:0; top:0; width:1080px; height:960px; object-fit:cover; z-index:20; }
  .split-img { position:absolute; left:0; top:0; width:1080px; height:960px; overflow:hidden; background:#05060c; }
  .split-img img { width:100%; height:100%; object-fit:cover; display:block; }
  .seam { position:absolute; left:0; top:956px; width:1080px; height:8px; background:var(--cyan); box-shadow: 0 0 22px rgba(10,240,240,.8); }
  /* cta: follow / subscribe pill */
  .cta { padding:22px 26px 22px 40px; border-radius:999px; }
  .cta .inner { opacity:0; display:flex; align-items:center; gap:30px; }
  .cta .txt { font-weight:700; font-size:54px; line-height:1.1; color:var(--white); white-space:nowrap; }
  .cta .btn { font-weight:700; font-size:40px; line-height:1; color:#fff; background:var(--red); padding:22px 34px; border-radius:999px; white-space:nowrap; }
  /* vignette + grain: a beat, not a look */
  .vig { position:absolute; inset:0; opacity:0; background: radial-gradient(ellipse at 50% 40%, rgba(0,0,0,0) 36%, rgba(0,0,0,.8) 100%); }
  .grain { position:absolute; inset:0; opacity:0; mix-blend-mode: overlay;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' seed='7' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E"); }
  /* captions: word-exact, a few words at a time, above everything but the progress bar */
  #captions { position:absolute; left:0; top:0; width:1080px; height:1920px; pointer-events:none; z-index:40; }
  .cap { position:absolute; left:110px; right:110px; text-align:center; font-weight:700; line-height:1.08;
    letter-spacing:-.01em; color:var(--white); visibility:hidden; transform-origin:50% 50%; }
  .cap .cw { display:inline-block; }
  .cap .cw.em { color:var(--amber); }
  .cap.upper { text-transform:uppercase; }
  #progress { position:absolute; left:0; top:0; width:1080px; height:8px; background:var(--cyan); transform-origin:0 50%;
    box-shadow: 0 0 14px rgba(10,240,240,.8); z-index:50; }
""".replace("ORIGIN", origin)

if THEME:
    CSS += ("""
  @font-face { font-family: "%(font)s"; src: url("fonts/%(font_file)s"); font-display: block; }
  .disp { font-family: "%(font)s", "DM Sans", sans-serif; font-weight: 400; text-transform: uppercase; letter-spacing: -.02em; }
  /* the outline sits behind the fill (paint-order), a drop under it keeps it legible on any footage */
  .outl { color: %(text)s; -webkit-text-stroke: .17em %(outline)s; paint-order: stroke fill;
    text-shadow: 0 .08em 0 %(outline)s, 0 .18em .45em rgba(0,0,0,.45); }
  .acc { color: %(accent)s !important; } .alr { color: %(alert)s !important; }
  /* title: the persistent headline; a strike can cross a line, a swap replaces every line */
  .ttl { position:absolute; left:40px; right:40px; text-align:center; line-height:1.12; }
  .ttl .tl-line { display:block; }
  .ttl .tl-txt { display:inline-block; position:relative; transform-origin:50%% 60%%; }
  .ttl .strike, .ttl .uline { position:absolute; left:-4%%; width:108%%; overflow:visible; }
  .ttl .strike { top:26%%; height:46%%; rotate:-2deg; }
  .ttl .uline { top:88%%; height:34%%; }
  .ttl .strike path, .ttl .uline path { fill:none; stroke-width:.12em; stroke-linecap:round; stroke-linejoin:round; }
  /* hand-drawn strokes (draw, chart, the ring around a dot): pathLength 100, drawn by stroke-dashoffset */
  .drw { position:absolute; left:0; top:0; overflow:visible; filter: drop-shadow(0 4px 0 rgba(0,0,0,.5)); }
  .drw path, .ring path { fill:none; stroke-linecap:round; stroke-linejoin:round; }
  .dots .ring { position:absolute; left:-80%%; top:-80%%; width:260%%; height:260%%; overflow:visible; }
  .chl { position:absolute; font-size:28px; opacity:0; white-space:nowrap; }
  /* dice: a CSS cube, tumbling in to land on one face */
  .dice-wrap { position:absolute; translate:-50%% -50%%; perspective:900px; }
  .dice-cube { position:absolute; inset:0; transform-style:preserve-3d; }
  .dice-face { position:absolute; inset:0; border-radius:18%%; background:linear-gradient(145deg,#ffffff,#e4e0d8); display:grid;
    grid-template-columns:repeat(3,1fr); grid-template-rows:repeat(3,1fr); padding:13%%; box-shadow: inset 0 0 0 3px rgba(0,0,0,.10), inset 0 -8px 16px rgba(0,0,0,.10); }
  .dice-face .pip { width:72%%; height:72%%; margin:auto; border-radius:50%%; background:#151515; box-shadow: inset 0 3px 4px rgba(0,0,0,.6); }
  .dice-face .pip.red { background:#d3201a; width:86%%; height:86%%; }
  .dice-shadow { position:absolute; left:8%%; width:84%%; top:104%%; height:16%%; border-radius:50%%;
    background: radial-gradient(ellipse at center, rgba(0,0,0,.6) 0%%, rgba(0,0,0,0) 70%%); }
  /* dots: n of them, the hits light up (k in n) */
  .dots { position:absolute; left:40px; right:40px; text-align:center; }
  .dots .lab { font-size:40px; margin-bottom:16px; opacity:0; }
  .dots .row { display:flex; justify-content:center; flex-wrap:wrap; }
  .dots .dt { position:relative; border-radius:50%%; background:rgba(255,255,255,.88); box-shadow: 0 3px 0 rgba(0,0,0,.55); }
  /* meter: a bar that can fill past 100%% and turn to the alert colour */
  .meter { position:absolute; }
  .meter .lab { font-size:34px; margin-bottom:14px; opacity:0; }
  .meter .trk { position:relative; height:34px; border-radius:17px; background:rgba(255,255,255,.12); border:3px solid rgba(255,255,255,.7); opacity:0; }
  .meter .fil { position:absolute; left:-3px; top:-3px; height:34px; border-radius:17px; background:%(accent)s; transform-origin:0 50%%;
    box-shadow: 0 0 26px rgba(%(accent_rgb)s,.55); }
  .meter .tick { position:absolute; top:-12px; width:5px; height:52px; border-radius:3px; background:#fff; box-shadow: 0 0 0 2px rgba(0,0,0,.6); }
  .meter .tickl { position:absolute; top:48px; font: 700 22px "DM Sans", sans-serif; color:rgba(255,255,255,.85); translate:-50%% 0; }
  .meter .over { position:absolute; top:-52px; font-size:34px; opacity:0; white-space:nowrap; translate:-100%% 0; }
  /* emoji: pops in, floats, pops out */
  .emo { position:absolute; display:block; translate:-50%% -50%%; filter: drop-shadow(0 10px 18px rgba(0,0,0,.5)); }
  /* credit: who and where the clip is from */
  .credit { position:absolute; display:flex; align-items:center; gap:12px; padding:12px 26px 12px 20px; border-radius:999px;
    background:rgba(255,255,255,.08); border:2px solid rgba(255,255,255,.18); font: 700 26px "DM Sans", sans-serif;
    color:rgba(255,255,255,.9); letter-spacing:.07em; text-transform:uppercase; white-space:nowrap; }
""" % dict(THEME, accent_rgb=rgb(THEME["accent"])))
if CARD:
    bg = THEME["bg"] if THEME else "#0C0C10"
    CSS += """
  #bg { position:absolute; inset:0; overflow:hidden; background:%s; z-index:0; }
  #bg .blob { position:absolute; width:1000px; height:1000px; border-radius:50%%; }
  #bg .b1 { left:-380px; top:-260px; background: radial-gradient(circle, rgba(%s,.20) 0%%, rgba(%s,0) 62%%); }
  #bg .b2 { left:380px; top:1150px; background: radial-gradient(circle, rgba(%s,.16) 0%%, rgba(%s,0) 62%%); }
  #bg .b3 { left:420px; top:-200px; background: radial-gradient(circle, rgba(90,120,255,.13) 0%%, rgba(90,120,255,0) 62%%); }
  #bg .dotgrid { position:absolute; inset:0; opacity:.14; background-image: radial-gradient(rgba(255,255,255,.8) 1.4px, transparent 1.7px); background-size:40px 40px; }
  #card { position:absolute; left:%dpx; top:%dpx; width:%dpx; height:%dpx; border-radius:%dpx; overflow:hidden; z-index:2; background:#000;
    box-shadow: 0 0 0 4px rgba(255,255,255,.12), 0 30px 80px rgba(0,0,0,.65), 0 0 70px rgba(%s,.16); }
  #card .video-wrapper { width:100%%; height:100%%; }
  #card #progress { top:auto; bottom:0; width:100%%; height:8px; z-index:5; }
""" % (bg, rgb(ACCENT), rgb(ACCENT), rgb(ALERT), rgb(ALERT), CX, CY, CW, CH, CR, rgb(ACCENT))
if THEME:
    CSS += "  #progress { background:%s; box-shadow: 0 0 14px rgba(%s,.8); }\n" % (ACCENT, rgb(ACCENT))


html_parts, js_parts, audio_parts, warns = [], [], [], []
track, audio_track = 3, 60
def js(s): js_parts.append(s)

def attr_anchor(anchor):
    if anchor == "-":
        return ' data-unanchored="1"'
    return ' data-anchor="%s"' % qesc(anchor) if anchor else ""

def host(bid, t_in, t_out, inner, anchor="", z=None, track_i=None):
    zs = "z-index:%d;" % z if z is not None else ""
    return ('    <div class="card-host clip" id="host-%s" data-card-id="%s" data-start="%.3f" data-duration="%.3f" data-track-index="%d"%s\n'
            '      style="left:0;top:0;width:%dpx;height:%dpx;visibility:hidden;opacity:1;%s">\n      <div class="card">%s</div>\n    </div>\n'
            % (bid, bid, t_in, t_out - t_in, track if track_i is None else track_i, attr_anchor(anchor), FW, FH, zs, inner))

def item_attrs(it):
    anchor = it[2] if len(it) > 2 else it[0]
    return ' data-at="%.3f"%s' % (float(it[1]), attr_anchor(anchor))

def spans(text, em, cls):
    em = set(em or [])
    return " ".join('<span class="%s%s">%s</span>' % (cls, " em" if i in em else "", hesc(w)) for i, w in enumerate(text.split()))

def pos_y(b, default="top"):
    p = b.get("pos", default)
    if p not in POS_Y:
        sys.exit("beat %s: pos %r is not one of %s (the bottom of a Short belongs to the captions and YouTube's own UI)"
                 % (b["id"], p, ", ".join(POS_Y)))
    return POS_Y[p]

def fmt_value(v, prefix="", suffix="", decimals=0):
    return "%s%s%s" % (prefix, ("{:,.%df}" % int(decimals)).format(v), suffix)

def fade_card(bid, t_in, t_out, glass_from):
    """Glass enters by its look (never an ancestor's opacity: Chrome drops backdrop-filter during the fade), copy fades."""
    js("glassIn('#%s-glass', %.3f, %s);" % (bid, t_in, glass_from))
    js("tl.fromTo('#%s-inner', { opacity: 0 }, { opacity: 1, duration: 0.36 }, %.3f);" % (bid, t_in + 0.04))
    if t_out >= D - 0.05:     # held to the last frame: no exit (a half-faded pill on the final frame reads as a glitch)
        return
    js("tl.to('#%s-inner', { opacity: 0, duration: 0.28, ease: 'power2.in' }, %.3f);" % (bid, t_out - 0.38))
    js("glassOut('#%s-glass', %.3f, 0.33);" % (bid, t_out - 0.34))
    js("tl.set('#%s-inner', { opacity: 0 }, %.3f);" % (bid, t_out - 0.10))

def check_in(sel, t):
    js("tl.to('%s .ring', { fill: 'rgba(10,240,240,1)', stroke: 'rgba(10,240,240,1)', duration: 0.26, ease: 'power2.out' }, %.3f);" % (sel, t + 0.22))
    js("tl.to('%s .tick', { strokeDashoffset: 0, duration: 0.30, ease: 'power2.out' }, %.3f);" % (sel, t + 0.32))

CHECK_SVG = ('<div class="mk"><svg viewBox="0 0 44 44"><circle class="ring" cx="22" cy="22" r="19"/>'
             '<path class="tick" d="M13 22.5 L19.5 29 L31 16" style="stroke-dasharray:30;stroke-dashoffset:30"/></svg></div>')

def label_html(bid, b, t_out):
    if not b.get("label"):
        return ""
    t = float(b.get("label_at", b["in"]))
    js("tl.fromTo('#%s-label', { opacity: 0, y: 26 }, { opacity: 1, y: 0, duration: 0.4, ease: 'power2.out' }, %.3f);" % (bid, t))
    js("tl.to('#%s-label', { opacity: 0, duration: 0.3, ease: 'power2.in' }, %.3f);" % (bid, t_out - 0.34))
    return '<div class="slabel shadow" id="%s-label">%s</div>' % (bid, spans(b["label"], b.get("label_em"), "lw"))

def smooth(pts):
    """Catmull-Rom through the points as cubic Beziers."""
    d = "M%.1f %.1f" % pts[0]
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i else pts[i]; p1, p2 = pts[i], pts[i + 1]; p3 = pts[i + 2] if i + 2 < len(pts) else p2
        d += " C%.1f %.1f %.1f %.1f %.1f %.1f" % (p1[0] + (p2[0] - p0[0]) / 6.0, p1[1] + (p2[1] - p0[1]) / 6.0,
                                                    p2[0] - (p3[0] - p1[0]) / 6.0, p2[1] - (p3[1] - p1[1]) / 6.0, p2[0], p2[1])
    return d

def rough_line(x1, y1, x2, y2, r, j=3.0, n=5, bow=0.0):
    L = math.hypot(x2 - x1, y2 - y1) or 1.0; nx, ny = -(y2 - y1) / L, (x2 - x1) / L
    pts = []
    for k in range(n + 1):
        t = k / float(n); off = bow * math.sin(math.pi * t) + (r.uniform(-j, j) if 0 < k < n else 0)
        pts.append((x1 + (x2 - x1) * t + nx * off, y1 + (y2 - y1) * t + ny * off))
    return smooth(pts)

def rough_ellipse(cx, cy, rx, ry, r, turns=1.12):
    a0 = r.uniform(0, 2 * math.pi); steps = 28; pts = []
    for k in range(steps + 1):
        a = a0 + 2 * math.pi * turns * k / steps; f = 1 + r.uniform(-0.045, 0.045) + 0.07 * k / steps
        pts.append((cx + rx * f * math.cos(a), cy + ry * f * math.sin(a)))
    return smooth(pts)

def shape_paths(sh, r):
    """A shape spec -> [path d, ...] in drawing order."""
    k = sh["shape"]
    if k == "burst":        # short strokes radiating from a point: shock, surprise, emphasis
        n, a0, a1 = int(sh.get("n", 4)), math.radians(float(sh.get("from", -80))), math.radians(float(sh.get("to", 10)))
        out = []
        for i in range(n):
            a = a0 + (a1 - a0) * i / max(1, n - 1) + r.uniform(-0.12, 0.12)
            r0, r1 = float(sh.get("r0", 30)) * r.uniform(0.9, 1.1), float(sh.get("r1", 80)) * r.uniform(0.85, 1.1)
            out.append(rough_line(sh["cx"] + r0 * math.cos(a), sh["cy"] + r0 * math.sin(a), sh["cx"] + r1 * math.cos(a), sh["cy"] + r1 * math.sin(a), r, j=2, n=3))
        return out
    if k == "circle":
        return [rough_ellipse(sh["cx"], sh["cy"], sh["rx"], sh.get("ry", sh["rx"]), r)]
    if k == "underline":    # out and back, the way a marker underlines
        x1, x2, y = float(sh["x1"]), float(sh["x2"]), float(sh["y"])
        return [smooth([(x1, y), ((x1 + x2) / 2, y + r.uniform(-4, 4)), (x2, y - 3), (x2 - 30, y + 12), (x1 + 40, y + 16)])]
    if k == "arrow":
        x1, y1, x2, y2 = [float(sh[c]) for c in ("x1", "y1", "x2", "y2")]
        a = math.atan2(y2 - y1, x2 - x1); hl = float(sh.get("head", 34))
        return [rough_line(x1, y1, x2, y2, r, j=3, n=5, bow=float(sh.get("bow", 18))),
                rough_line(x2, y2, x2 - hl * math.cos(a - 0.5), y2 - hl * math.sin(a - 0.5), r, j=1, n=2),
                rough_line(x2, y2, x2 - hl * math.cos(a + 0.5), y2 - hl * math.sin(a + 0.5), r, j=1, n=2)]
    if k == "path":
        return [sh["d"]]
    sys.exit("draw: unknown shape %r (burst circle underline arrow path)" % k)

COLORS = lambda c: {"accent": ACCENT, "alert": ALERT, "text": TEXT}.get(c, c)
DASH = "stroke-dasharray:100;stroke-dashoffset:100"

def wipe_in(sel, t, dur, ease="power2.out", from_right=False):
    start = "inset(0% 0% 0% 100%)" if from_right else "inset(0% 100% 0% 0%)"
    js("tl.fromTo('%s', { clipPath: '%s' }, { clipPath: 'inset(0%% 0%% 0%% 0%%)', duration: %.2f, ease: '%s' }, %.3f);" % (sel, start, dur, ease, t))

def draw_in(sel, t, dur, ease="power2.out"):
    js("tl.fromTo('%s', { strokeDashoffset: 100 }, { strokeDashoffset: 0, duration: %.2f, ease: '%s' }, %.3f);" % (sel, dur, ease, t))

hidden, seams = [], []   # caption-free windows; split windows (captions move to the seam)
first_visual = None

# ---- beats ------------------------------------------------------------------------------------------
for b in S.get("beats", []):
    t, bid, t_in, t_out = b["type"], b["id"], float(b["in"]), float(b["out"])
    anchor = b.get("anchor", "")
    if t_out > D + 1e-6:
        sys.exit("beat %s ends at %.2f, past the %.2f s duration" % (bid, t_out, D))
    if t_out <= t_in:
        sys.exit("beat %s: out %.2f is not after in %.2f" % (bid, t_out, t_in))
    if b.get("hide_captions"):
        hidden.append((t_in, t_out))
    if t != "vignette":
        first_visual = t_in if first_visual is None else min(first_visual, t_in)

    if t == "text":
        y = pos_y(b)
        cls = "tx shadow" + (" amber" if b.get("color") == "amber" else "")
        size = ' font-size:%dpx;' % int(b["size"]) if b.get("size") else ""
        inner = '<div class="%s" id="%s" style="top:%dpx;%s">%s</div>' % (cls, bid, y, size, spans(b["text"], b.get("em"), "w"))
        html_parts.append(host(bid, t_in, t_out, inner, anchor))
        if t_in > 0.05:      # at 0 the hook title is simply there on the first frame
            js("tl.fromTo('#%s .w', { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.4, ease: 'power2.out', stagger: 0.055 }, %.3f);" % (bid, t_in))
        if t_out < D - 0.05:
            js("tl.to('#%s', { opacity: 0, duration: 0.3, ease: 'power2.in' }, %.3f);" % (bid, t_out - 0.32))
            js("tl.set('#%s', { opacity: 0 }, %.3f);" % (bid, t_out - 0.01))
    elif t == "chip":
        y = pos_y(b)
        inner = ('<div class="chip centered" id="%s-chip" style="top:%dpx"><div class="inner shadow" id="%s-inner">%s</div></div>'
                 % (bid, y, bid, spans(b["text"], b.get("em"), "cw")))
        html_parts.append(host(bid, t_in, t_out, inner, anchor))
        js("tl.fromTo('#%s-chip', { backgroundColor: 'rgba(17,17,17,0)', y: 18 }, { backgroundColor: '%s', y: 0, duration: 0.40, ease: 'power2.out' }, %.3f);" % (bid, CHIP_BG, t_in))
        js("tl.fromTo('#%s-inner', { opacity: 0 }, { opacity: 1, duration: 0.32 }, %.3f);" % (bid, t_in + 0.06))
        if t_out < D - 0.05:
            js("tl.to('#%s-inner', { opacity: 0, duration: 0.26, ease: 'power2.in' }, %.3f);" % (bid, t_out - 0.36))
            js("tl.to('#%s-chip', { backgroundColor: 'rgba(17,17,17,0)', duration: 0.30, ease: 'power2.in' }, %.3f);" % (bid, t_out - 0.32))
            js("tl.set('#%s-inner', { opacity: 0 }, %.3f);" % (bid, t_out - 0.10))
    elif t == "logo":
        p = b.get("pos", "top")
        place = {"top": "top:250px;", "tl": "left:60px; top:240px;", "tr": "right:60px; top:240px;"}.get(p)
        if place is None:
            sys.exit("beat %s: logo pos %r is not top, tl or tr" % (bid, p))
        inner = ('<div class="glass logo-plate%s" id="%s-glass" style="%s"><div class="inner" id="%s-inner"><img src="%s" alt="" /></div></div>'
                 % (" centered" if p == "top" else "", bid, place, bid, qesc(b["src"])))
        html_parts.append(host(bid, t_in, t_out, inner, anchor))
        fade_card(bid, t_in, t_out, "{ y: -30 }" if p == "top" else "{ x: %d }" % (-40 if p == "tl" else 40))
        if b.get("pop") is not None:
            audio_parts.append('    <audio id="sfx-pop-%s" src="sfx/pop.mp3" data-start="%.3f" data-duration="0.72" data-track-index="%d" data-volume="0.34"></audio>\n'
                               % (bid, float(b["pop"]), audio_track))
            audio_track += 1
    elif t == "list":
        y = pos_y(b)
        mark = CHECK_SVG if b.get("marker") == "check" else '<div class="d"></div>'
        sz = ' style="font-size:%dpx"' % int(b["size"]) if b.get("size") else ""
        items = "".join('<div class="item" id="%s-i%d"%s>%s<div class="t shadow"%s>%s</div></div>' % (bid, i, item_attrs(it), mark, sz, hesc(it[0]))
                        for i, it in enumerate(b["items"]))
        eyebrow = '<div class="eyebrow shadow">%s</div>' % hesc(b["eyebrow"]) if b.get("eyebrow") else ""
        width = "width:%dpx;" % int(b["width"]) if b.get("width") else ""
        inner = ('<div class="glass list centered" id="%s-glass" style="top:%dpx;%s"><div class="inner" id="%s-inner">%s%s</div></div>'
                 % (bid, y, width, bid, eyebrow, items))
        html_parts.append(host(bid, t_in, t_out, inner, anchor))
        fade_card(bid, t_in, t_out, "{ y: -30 }")
        for i, it in enumerate(b["items"]):
            js("tl.set('#%s-i%d', { display: 'flex' }, %.3f);" % (bid, i, float(it[1])))
            js("tl.fromTo('#%s-i%d', { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.40, ease: 'power2.out' }, %.3f);" % (bid, i, float(it[1])))
            if b.get("marker") == "check":
                check_in("#%s-i%d" % (bid, i), float(it[1]))
    elif t == "stat":
        y = pos_y(b)
        final = fmt_value(b["value"], b.get("prefix", ""), b.get("suffix", ""), b.get("decimals", 0))
        size = int(b.get("size") or min(170, int(1000 / (0.6 * max(1, len(final))))))
        color = b.get("color", "white")
        label = '<div class="lab shadow">%s</div>' % spans(b["label"], b.get("label_em"), "lw") if b.get("label") else ""
        inner = ('<div class="stat %s" id="%s" style="top:%dpx"><div class="num shadow" id="%s-n" style="font-size:%dpx">%s</div>%s</div>'
                 % (color, bid, y, bid, size, hesc(fmt_value(0, b.get("prefix", ""), b.get("suffix", ""), b.get("decimals", 0))), label))
        html_parts.append(host(bid, t_in, t_out, inner, anchor))
        ta = float(b.get("at", t_in + 0.15))
        js("tl.fromTo('#%s', { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.4, ease: 'power2.out' }, %.3f);" % (bid, t_in))
        js("countUp('#%s-n', %s, %.3f, %.2f, %s, %s, %d);" % (bid, json.dumps(b["value"]), ta, float(b.get("dur", 1.2)),
           json.dumps(b.get("prefix", "")), json.dumps(b.get("suffix", "")), int(b.get("decimals", 0))))
        if t_out < D - 0.05:
            js("tl.to('#%s', { opacity: 0, duration: 0.3, ease: 'power2.in' }, %.3f);" % (bid, t_out - 0.32))
            js("tl.set('#%s', { opacity: 0 }, %.3f);" % (bid, t_out - 0.01))
    elif t == "image":
        push = float(b.get("push", 1.06))
        if b.get("frame", "card") == "full":
            inner = '<div class="imgfull"><img id="%s-img" src="%s" alt="" /></div>%s' % (bid, qesc(b["src"]), label_html(bid, b, t_out))
            html_parts.append(host(bid, t_in, t_out, inner, anchor, z=20))
            js("tl.fromTo('#%s-img', { scale: 1.0 }, { scale: %.3f, duration: %.3f, ease: 'none' }, %.3f);" % (bid, push, t_out - t_in, t_in))
        else:
            y = pos_y(b)
            inner = ('<div class="glass imgcard centered" id="%s-glass" style="top:%dpx"><div class="inner" id="%s-inner"><img id="%s-img" src="%s" alt="" /></div></div>'
                     % (bid, y - 10, bid, bid, qesc(b["src"])))
            html_parts.append(host(bid, t_in, t_out, inner, anchor))
            fade_card(bid, t_in, t_out, "{ y: 40 }")
            js("tl.fromTo('#%s-img', { scale: 1.0 }, { scale: %.3f, duration: %.3f, ease: 'none' }, %.3f);" % (bid, push, t_out - t_in, t_in))
    elif t == "clip":
        # a full-frame cutaway: a direct child of the root, muted, z 20 (inside a timed wrapper it fails lint), a slow drift
        html_parts.append('    <video class="cutaway-video clip" id="%s" src="%s" muted playsinline data-start="%.3f" data-duration="%.3f" data-media-start="%.3f" data-track-index="%d"%s></video>\n'
                          % (bid, qesc(b["src"]), t_in, t_out - t_in, float(b.get("media_start", 0)), track, attr_anchor(anchor)))
        if b.get("drift", True):
            js("tl.fromTo('#%s', { scale: 1.0 }, { scale: 1.04, duration: %.3f, ease: 'none' }, %.3f);" % (bid, t_out - t_in, t_in))
        if b.get("label"):
            track += 1
            html_parts.append(host(bid + "-over", t_in, t_out, label_html(bid, b, t_out), "-", z=26))
    elif t == "split":
        # the media fills the top half; the footage slides down so your face sits in the bottom half
        shift = int(b.get("shift", 560))
        src = b["src"]
        if os.path.splitext(src)[1].lower() in (".mp4", ".mov", ".webm", ".m4v"):
            html_parts.append('    <video class="split-video clip" id="%s" src="%s" muted playsinline data-start="%.3f" data-duration="%.3f" data-media-start="%.3f" data-track-index="%d"%s></video>\n'
                              % (bid, qesc(src), t_in, t_out - t_in, float(b.get("media_start", 0)), track, attr_anchor(anchor)))
            track += 1
            html_parts.append(host(bid + "-seam", t_in, t_out, '<div class="seam"></div>', "-", z=21))
        else:
            inner = '<div class="split-img"><img src="%s" alt="" /></div><div class="seam"></div>' % qesc(src)
            html_parts.append(host(bid, t_in, t_out, inner, anchor, z=20))
        js("tl.to('#video-wrap', { y: %d, duration: 0.45, ease: 'power2.inOut' }, %.3f);" % (shift, max(0.0, t_in - 0.1)))
        js("tl.to('#video-wrap', { y: 0, duration: 0.45, ease: 'power2.inOut' }, %.3f);" % (t_out - 0.45))
        seams.append((t_in, t_out))
    elif t == "cta":
        y = pos_y(b)
        inner = ('<div class="glass cta centered" id="%s-glass" style="top:%dpx"><div class="inner" id="%s-inner"><div class="txt shadow">%s</div>'
                 '<div class="btn" id="%s-btn">%s</div></div></div>' % (bid, y, bid, hesc(b.get("text", "Follow for more")), bid, hesc(b.get("button", "Follow"))))
        html_parts.append(host(bid, t_in, t_out, inner, anchor))
        fade_card(bid, t_in, t_out, "{ y: -30 }")
        js("tl.fromTo('#%s-btn', { scale: 1.0 }, { scale: 1.08, duration: 0.28, ease: 'power1.inOut', yoyo: true, repeat: 5 }, %.3f);" % (bid, t_in + 0.6))
    elif t == "vignette":
        inner = '<div class="vig" id="%s-vig"></div><div class="grain" id="%s-grain"></div>' % (bid, bid)
        html_parts.append(host(bid, t_in, t_out, inner, anchor, z=22))
        js("tl.fromTo('#%s-vig', { opacity: 0 }, { opacity: 1, duration: 0.45, ease: 'power2.out' }, %.3f);" % (bid, t_in))
        js("tl.fromTo('#%s-grain', { opacity: 0 }, { opacity: 0.35, duration: 0.45, ease: 'power2.out' }, %.3f);" % (bid, t_in))
        js("tl.to('#%s-vig, #%s-grain', { opacity: 0, duration: 0.35, ease: 'power2.in' }, %.3f);" % (bid, bid, t_out - 0.35))
        js("tl.set('#%s-vig, #%s-grain', { opacity: 0 }, %.3f);" % (bid, bid, t_out - 0.01))
    elif t in ("title", "dots", "meter", "credit", "draw", "dice", "chart") and not THEME:
        sys.exit("beat %s: the %s format needs a \"theme\" in the storyboard (its font and colours)" % (bid, t))
    elif t == "title":
        # the persistent headline: on screen from its first frame when in = 0; "strike" crosses one line out on a word,
        # "swap" replaces every line on a word ("It wasn't bad luck" -> "It was overconfidence")
        size, y = int(b.get("size", 70)), int(b.get("y", 250))
        def tlines(text, em, pre, strike_line=None, uline=None):
            out = ""
            for i, line in enumerate(text.split("|")):
                st = ""
                # these strokes stretch with the text (non-scaling stroke), where a dash reveal is measured in screen px:
                # they are revealed by a wipe instead, one svg per marker pass
                if i == strike_line:     # two marker passes, out and back
                    st = ('<svg class="strike" id="%s-s%d" viewBox="0 0 100 20" preserveAspectRatio="none" style="clip-path:inset(0%% 100%% 0%% 0%%)">'
                          '<path vector-effect="non-scaling-stroke" style="stroke:%s" d="M1 12 C22 8 46 15 71 9 S94 9 99 8"/></svg>'
                          '<svg class="strike" id="%s-s%db" viewBox="0 0 100 20" preserveAspectRatio="none" style="clip-path:inset(0%% 0%% 0%% 100%%)">'
                          '<path vector-effect="non-scaling-stroke" style="stroke:%s" d="M97 13 C72 16 42 10 3 15"/></svg>'
                          % (pre, i, ALERT, pre, i, ALERT))
                if i == uline:
                    st = ('<svg class="uline" id="%s-u%d" viewBox="0 0 100 20" preserveAspectRatio="none" style="clip-path:inset(0%% 100%% 0%% 0%%)">'
                          '<path vector-effect="non-scaling-stroke" style="stroke:%s" d="M2 8 C30 5 62 11 98 6 C80 12 45 14 12 15"/></svg>'
                          % (pre, i, COLORS(swap.get("underline_color", "text")) if swap else TEXT))
                out += '<div class="tl-line"><span class="tl-txt%s" id="%s-l%d">%s%s</span></div>' % (" acc" if i in set(em or []) else "", pre, i, hesc(line), st)
            return out
        strike, swap = b.get("strike"), b.get("swap")
        inner = '<div class="ttl disp outl" id="%s-a" style="top:%dpx;font-size:%dpx">%s</div>' % (bid, y, size, tlines(b["text"], b.get("em"), bid + "-a", strike["line"] if strike else None))
        if swap:
            inner += '<div class="ttl disp outl" id="%s-b" style="top:%dpx;font-size:%dpx">%s</div>' % (bid, int(swap.get("y", y)), int(swap.get("size", size)), tlines(swap["text"], swap.get("em"), bid + "-b", uline=swap.get("underline")))
        html_parts.append(host(bid, t_in, t_out, inner, anchor))
        if t_in > 0.05:
            js("tl.fromTo('#%s-a .tl-txt', { scale: 0.6, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.45, ease: 'back.out(1.8)', stagger: 0.12 }, %.3f);" % (bid, t_in))
        first_change = min([float(x["at"]) for x in (strike, swap) if x] + [t_out])
        if b.get("pulse") and first_change - t_in > 2.0:      # the emphasised line breathes until the first change
            reps = max(1, int((first_change - t_in - 1.0) / 0.7))
            reps = reps if reps % 2 else reps - 1                # an odd repeat count ends back at scale 1
            js("tl.fromTo('#%s-a .tl-txt.acc', { scale: 1 }, { scale: 1.06, duration: 0.7, ease: 'sine.inOut', yoyo: true, repeat: %d, immediateRender: false }, %.3f);" % (bid, max(1, reps), t_in + 0.6))
        if strike:
            sa = float(strike["at"])
            wipe_in("#%s-a-s%d" % (bid, int(strike["line"])), sa, 0.2, "power1.in")
            wipe_in("#%s-a-s%db" % (bid, int(strike["line"])), sa + 0.19, 0.18, "power1.out", from_right=True)
            js("tl.fromTo('#%s-a-l%d', { rotation: 0 }, { rotation: -2, duration: 0.12, yoyo: true, repeat: 1, ease: 'power1.inOut', immediateRender: false }, %.3f);" % (bid, int(strike["line"]), sa + 0.3))
        if swap:
            wa = float(swap["at"])
            js("tl.to('#%s-a .tl-txt', { y: -36, opacity: 0, duration: 0.28, ease: 'power2.in', stagger: 0.05 }, %.3f);" % (bid, wa - 0.1))
            js("tl.fromTo('#%s-b .tl-txt', { scale: 0.4, opacity: 0, y: 20 }, { scale: 1, opacity: 1, y: 0, duration: 0.5, ease: 'back.out(1.9)', stagger: 0.12 }, %.3f);" % (bid, wa + 0.12))
            if swap.get("underline") is not None:
                wipe_in("#%s-b-u%d" % (bid, int(swap["underline"])), float(swap.get("underline_at", wa + 0.75)), 0.4, "power1.inOut")
        if t_out < D - 0.05:
            js("tl.to('#host-%s .ttl', { opacity: 0, duration: 0.3, ease: 'power2.in' }, %.3f);" % (bid, t_out - 0.32))
    elif t == "dots":
        # k in n: n dots pop in, the hits light up on their word and pulse, the rest dim; a label can land on a later word
        n = int(b.get("n", 20))
        hits = set(int(h) for h in b.get("hit", [n // 2]))
        y, ta = int(b.get("y", 1320)), float(b.get("at", t_in + 0.4))
        lab = ('<div class="lab disp outl" id="%s-lab">%s</div>' % (bid, spans(b["label"], b.get("label_em"), "lw").replace('class="lw em"', 'class="lw acc"'))) if b.get("label") else ""
        ds, gap = int(b.get("size", 34)), int(b.get("gap", 8))
        ring = lambda i: ('<svg class="ring" viewBox="0 0 100 100"><path pathLength="100" style="stroke:%s;stroke-width:5px;%s" d="%s"/></svg>'
                          % (COLORS(b.get("ring_color", "text")), DASH, rough_ellipse(50, 50, 40, 36, random.Random(bid + str(i))))) if b.get("ring") else ""
        dots = "".join('<div class="dt%s" style="width:%dpx;height:%dpx">%s</div>' % (" hit" if i in hits else "", ds, ds, ring(i) if i in hits else "") for i in range(n))
        inner = '<div class="dots" id="%s" style="top:%dpx">%s<div class="row" style="gap:%dpx">%s</div></div>' % (bid, y, lab, gap, dots)
        html_parts.append(host(bid, t_in, t_out, inner, anchor))
        js("tl.fromTo('#%s .dt', { scale: 0 }, { scale: 1, duration: 0.3, ease: 'back.out(2.2)', stagger: %.3f }, %.3f);" % (bid, min(0.03, 0.6 / n), t_in))
        js("tl.to('#%s .dt:not(.hit)', { opacity: 0.28, duration: 0.3 }, %.3f);" % (bid, ta))
        js("tl.to('#%s .dt.hit', { backgroundColor: '%s', boxShadow: '0 0 26px rgba(%s,0.9)', scale: 1.45, duration: 0.3, ease: 'back.out(2.4)' }, %.3f);" % (bid, ACCENT, rgb(ACCENT), ta))
        js("tl.to('#%s .dt.hit', { scale: 1.2, duration: 0.32, ease: 'sine.inOut', yoyo: true, repeat: 3 }, %.3f);" % (bid, ta + 0.35))
        if b.get("ring"):
            draw_in("#%s .ring path" % bid, float(b.get("ring_at", ta + 0.3)), 0.4, "power1.inOut")
        if b.get("label"):
            js("tl.fromTo('#%s-lab', { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.4, ease: 'back.out(1.8)' }, %.3f);" % (bid, float(b.get("label_at", ta))))
        if t_out < D - 0.05:
            js("tl.to('#%s', { opacity: 0, y: 20, duration: 0.28, ease: 'power2.in' }, %.3f);" % (bid, t_out - 0.3))
    elif t == "meter":
        # a bar fills on its word; past 100% it keeps going and turns to the alert colour, shakes, and the "over" label lands
        x, y, w = int(b.get("x", 110)), int(b.get("y", 1320)), int(b.get("w", 660))
        to, ta, dur = float(b.get("to", 1.0)), float(b.get("fill_at", t_in + 0.4)), float(b.get("dur", 1.1))
        if x + w * to > FW - 20:
            warns.append("meter %s overflows the frame (x + w * to = %d): lower w or to" % (bid, x + w * to))
        over = ('<div class="over disp outl alr" id="%s-over" style="left:%dpx">%s</div>' % (bid, int(w * to), hesc(b["over_label"]))) if b.get("over_label") else ""
        tick = ('<div class="tick" style="left:%dpx"></div><div class="tickl" style="left:%dpx">100%%</div>' % (w - 2, w)) if to > 1.0 else ""
        inner = ('<div class="meter" id="%s" style="left:%dpx;top:%dpx;width:%dpx"><div class="lab disp outl" id="%s-lab">%s</div>'
                 '<div class="trk" id="%s-trk"><div class="fil" id="%s-fil" style="width:%dpx"></div>%s%s</div></div>'
                 % (bid, x, y, w, bid, hesc(b.get("label", "")), bid, bid, int(round(w * to)), tick, over))
        html_parts.append(host(bid, t_in, t_out, inner, anchor))
        js("tl.fromTo('#%s-lab, #%s-trk', { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 0.4, ease: 'power2.out', stagger: 0.08 }, %.3f);" % (bid, bid, t_in))
        js("tl.fromTo('#%s-fil', { scaleX: 0 }, { scaleX: 1, duration: %.2f, ease: 'power2.inOut' }, %.3f);" % (bid, dur, ta))
        if to > 1.0:
            js("tl.to('#%s-fil', { backgroundColor: '%s', boxShadow: '0 0 30px rgba(%s,0.8)', duration: 0.25 }, %.3f);" % (bid, ALERT, rgb(ALERT), ta + dur * 0.5))
            js("tl.fromTo('#%s', { x: -7 }, { x: 7, duration: 0.05, yoyo: true, repeat: 5, ease: 'none', immediateRender: false }, %.3f);" % (bid, ta + dur))
            js("tl.set('#%s', { x: 0 }, %.3f);" % (bid, ta + dur + 0.31))
        if b.get("over_label"):
            js("tl.fromTo('#%s-over', { opacity: 0, scale: 0.5 }, { opacity: 1, scale: 1, duration: 0.4, ease: 'back.out(2)' }, %.3f);" % (bid, ta + dur + 0.05))
        if t_out < D - 0.05:
            js("tl.to('#%s', { opacity: 0, duration: 0.3, ease: 'power2.in' }, %.3f);" % (bid, t_out - 0.32))
    elif t == "emoji":
        # an emoji pops in on its word (a die tumbles in with "spin"), floats, pops out
        # drawn from the Noto emoji SVGs in assets/emoji (a font emoji depends on what the render machine has installed)
        x, y, size = int(b.get("x", 540)), int(b.get("y", 600)), int(b.get("size", 130))
        src = b.get("src")
        if not src:
            name = "emoji_u%s.svg" % "_".join("%x" % ord(ch) for ch in b["char"] if ord(ch) != 0xFE0F)
            path = os.path.join(SKILL, "assets", "emoji", name)
            if not os.path.exists(path):
                sys.exit("beat %s: no %s in assets/emoji (get it from github.com/googlefonts/noto-emoji, folder 2D/svg)" % (bid, name))
            src = "emoji/" + name
            stage(path, os.path.join(OUT, "emoji", name))
        inner = '<img class="emo" id="%s" src="%s" alt="" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx" />' % (bid, qesc(src), x, y, size, size)
        html_parts.append(host(bid, t_in, t_out, inner, anchor, z=30))
        if b.get("spin"):
            js("tl.fromTo('#%s', { scale: 0, rotation: -540, y: -120 }, { scale: 1, rotation: 0, y: 0, duration: 0.75, ease: 'back.out(1.5)' }, %.3f);" % (bid, t_in))
        else:
            js("tl.fromTo('#%s', { scale: 0, rotation: -25 }, { scale: 1, rotation: 0, duration: 0.45, ease: 'back.out(2.4)' }, %.3f);" % (bid, t_in))
        hold = t_out - t_in - 1.1
        if hold > 0.6:
            reps = max(1, int(hold / 0.5))
            reps = reps if reps % 2 else reps - 1
            js("tl.to('#%s', { y: -16, duration: 0.5, ease: 'sine.inOut', yoyo: true, repeat: %d }, %.3f);" % (bid, max(1, reps), t_in + 0.8))
        if t_out < D - 0.05:
            js("tl.to('#%s', { scale: 0, duration: 0.22, ease: 'power2.in' }, %.3f);" % (bid, t_out - 0.24))
    elif t == "draw":
        # hand-drawn marker strokes on words: bursts, circles, underlines, arrows; each shape draws on its own time
        col, wid = COLORS(b.get("color", "accent")), int(b.get("width", 8))
        paths, js_draw = [], []
        for k, sh in enumerate(b["shapes"]):
            r = random.Random("%s-%d" % (bid, k)); at, dur = float(sh.get("at", t_in)), float(sh.get("dur", 0.28))
            for j, d in enumerate(shape_paths(sh, r)):
                pid = "%s-p%d" % (bid, len(paths))
                paths.append('<path id="%s" pathLength="100" d="%s" style="stroke:%s;stroke-width:%dpx;%s"/>'
                             % (pid, d, COLORS(sh.get("color", col)), int(sh.get("width", wid)), DASH))
                js_draw.append(("#" + pid, at + j * float(sh.get("stagger", 0.06 if sh["shape"] == "burst" else dur * 0.9)), dur))
        inner = '<svg class="drw" id="%s" viewBox="0 0 %d %d" width="%d" height="%d">%s</svg>' % (bid, FW, FH, FW, FH, "".join(paths))
        html_parts.append(host(bid, t_in, t_out, inner, anchor, z=30))
        for sel, at, dur in js_draw:
            draw_in(sel, at, dur)
        if t_out < D - 0.05:
            js("tl.to('#%s', { opacity: 0, duration: 0.22, ease: 'power2.in' }, %.3f);" % (bid, t_out - 0.24))
    elif t == "dice":
        # a die tumbles in from the side, bounces and lands showing "face" (1 = the red pip: snake eyes, bad luck)
        x, y, dsz, face = int(b.get("x", 540)), int(b.get("y", 1330)), int(b.get("size", 120)), int(b.get("face", 1))
        land = float(b.get("land", t_in + 0.8))
        PIPS = {1: [(1, 1)], 2: [(0, 0), (2, 2)], 3: [(0, 0), (1, 1), (2, 2)], 4: [(0, 0), (0, 2), (2, 0), (2, 2)],
                5: [(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)], 6: [(0, 0), (1, 0), (2, 0), (0, 2), (1, 2), (2, 2)]}
        rest = [v for v in (2, 3, 1, 4, 5, 6) if v not in (face, 7 - face)]
        layout = [(face, "translateZ(%dpx)"), (7 - face, "rotateY(180deg) translateZ(%dpx)"), (rest[0], "rotateY(90deg) translateZ(%dpx)"),
                  (7 - rest[0], "rotateY(-90deg) translateZ(%dpx)"), (rest[1], "rotateX(90deg) translateZ(%dpx)"), (7 - rest[1], "rotateX(-90deg) translateZ(%dpx)")]
        faces = ""
        for v, tf in layout:
            pips = "".join('<div class="pip%s" style="grid-row:%d;grid-column:%d"></div>' % (" red" if v == 1 else "", rr + 1, cc + 1) for rr, cc in PIPS[v])
            faces += '<div class="dice-face" style="transform:%s">%s</div>' % (tf % (dsz // 2), pips)
        inner = ('<div class="dice-wrap" id="%s" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx"><div class="dice-shadow" id="%s-sh"></div>'
                 '<div class="dice-cube" id="%s-c">%s</div></div>' % (bid, x, y, dsz, dsz, bid, bid, faces))
        html_parts.append(host(bid, t_in, t_out, inner, anchor, z=30))
        span = land - t_in
        js("tl.fromTo('#%s-c', { rotationX: -755, rotationY: 610, rotationZ: 50 }, { rotationX: -16, rotationY: 22, rotationZ: 0, duration: %.2f, ease: 'power3.out' }, %.3f);" % (bid, span, t_in))
        js("tl.fromTo('#%s', { x: %d, opacity: 0 }, { x: 0, opacity: 1, duration: %.2f, ease: 'power2.out' }, %.3f);" % (bid, int(b.get("from_x", -380)), span * 0.85, t_in))
        js("tl.fromTo('#%s', { y: -230 }, { y: 0, duration: %.2f, ease: 'bounce.out' }, %.3f);" % (bid, span, t_in))
        js("tl.fromTo('#%s-sh', { opacity: 0, scale: 0.4 }, { opacity: 1, scale: 1, duration: %.2f, ease: 'power2.out' }, %.3f);" % (bid, span, t_in))
        if t_out < D - 0.05:
            js("tl.to('#%s', { scale: 0, rotation: -25, duration: 0.24, ease: 'power2.in' }, %.3f);" % (bid, t_out - 0.26))
    elif t == "chart":
        # a hand-drawn mini chart: the axes draw in, then each line draws on its word with its label at its end
        x, y, w, h = int(b.get("x", 200)), int(b.get("y", 1240)), int(b.get("w", 560)), int(b.get("h", 160))
        r = random.Random(bid)
        paths = ['<path id="%s-ax" pathLength="100" d="%s" style="stroke:rgba(255,255,255,.75);stroke-width:5px;%s"/>'
                 % (bid, smooth([(x, y - 6), (x + r.uniform(-2, 2), y + h * 0.5), (x, y + h), (x + w * 0.5, y + h + r.uniform(-2, 2)), (x + w + 10, y + h)]), DASH)]
        labels, later = "", []
        for i, ln in enumerate(b["lines"]):
            pts = [(x + px * w, y + h - py * h) for px, py in ln["points"]]
            pts = [pts[0]] + [(px + r.uniform(-3, 3), py + r.uniform(-3, 3)) for px, py in pts[1:-1]] + [pts[-1]]
            col = COLORS(ln.get("color", "accent")); lid = "%s-l%d" % (bid, i)
            paths.append('<path id="%s" pathLength="100" d="%s" style="stroke:%s;stroke-width:%dpx;%s"/>' % (lid, smooth(pts), col, int(ln.get("width", 8)), DASH))
            at, dur = float(ln.get("at", t_in + 0.4 + 0.5 * i)), float(ln.get("dur", 0.6))
            later.append(("#" + lid, at, dur))
            if ln.get("arrow"):
                (ax, ay), (bx, by) = pts[-2], pts[-1]; a = math.atan2(by - ay, bx - ax)
                for sgn, nm in ((-1, "a"), (1, "b")):
                    hid = "%s-h%s" % (lid, nm)
                    paths.append('<path id="%s" pathLength="100" d="M%.1f %.1f L%.1f %.1f" style="stroke:%s;stroke-width:%dpx;%s"/>'
                                 % (hid, bx, by, bx - 26 * math.cos(a + sgn * 0.55), by - 26 * math.sin(a + sgn * 0.55), col, int(ln.get("width", 8)), DASH))
                    later.append(("#" + hid, at + dur - 0.02, 0.12))
            if ln.get("label"):
                lx, ly = pts[-1]
                labels += ('<div class="chl disp outl" id="%s-t" style="left:%dpx;top:%dpx;color:%s">%s</div>'
                           % (lid, int(lx + float(ln.get("label_dx", 14))), int(ly + float(ln.get("label_dy", -16))), col, hesc(ln["label"])))
                js("tl.fromTo('#%s-t', { opacity: 0, x: -10 }, { opacity: 1, x: 0, duration: 0.3, ease: 'power2.out' }, %.3f);" % (lid, at + dur - 0.1))
        inner = '<svg class="drw" viewBox="0 0 %d %d" width="%d" height="%d">%s</svg>%s' % (FW, FH, FW, FH, "".join(paths), labels)
        html_parts.append(host(bid, t_in, t_out, inner, anchor, z=30))
        draw_in("#%s-ax" % bid, t_in, 0.35, "power1.inOut")
        for sel, at, dur in later:
            draw_in(sel, at, dur, "power1.inOut")
        if t_out < D - 0.05:
            js("tl.to('#host-%s .card', { opacity: 0, duration: 0.25, ease: 'power2.in' }, %.3f);" % (bid, t_out - 0.27))
    elif t == "credit":
        # who and where the clip comes from: a small pill, from the first frame when in = 0
        mic = ('<svg viewBox="0 0 24 24" width="30" height="30"><path fill="%s" d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3zm5-3a5 5 0 0 1-10 0H5'
               'a7 7 0 0 0 6 6.92V21h2v-3.08A7 7 0 0 0 19 11h-2z"/></svg>' % ACCENT)
        inner = '<div class="credit centered" id="%s" style="top:%dpx">%s<span>%s</span></div>' % (bid, int(b.get("y", 210)), mic, hesc(b["text"]))
        html_parts.append(host(bid, t_in, t_out, inner, anchor))
        if t_in > 0.05:
            js("tl.fromTo('#%s', { opacity: 0, y: -16 }, { opacity: 1, y: 0, duration: 0.4, ease: 'power2.out' }, %.3f);" % (bid, t_in))
    else:
        sys.exit("unknown beat type %r (text chip logo list stat image clip split cta vignette title dots meter emoji credit draw dice chart)" % t)
    track += 1

# ---- captions ---------------------------------------------------------------------------------------
cap_html, n_groups = "", 0
C = S.get("captions")
if C:
    tpath = C.get("transcript", "transcript.json")
    tpath = tpath if os.path.isabs(tpath) else os.path.join(SPEC_DIR, tpath)
    if not os.path.exists(tpath):
        sys.exit("captions: no transcript at %s (transcribe the flat cut first)" % tpath)
    raw = json.load(open(tpath, encoding="utf-8"))
    words = [w for w in (raw["words"] if isinstance(raw, dict) and "words" in raw else raw) if str(w.get("text", "")).strip()]
    # themed captions use the display font (wide caps), so a group holds fewer characters
    max_w, max_c = int(C.get("max_words", 3)), int(C.get("max_chars", 14 if THEME else 18))
    groups, cur = [], []
    for w in words:
        txt = str(w["text"]).strip()
        if cur:
            gap = float(w["start"]) - float(cur[-1]["end"])
            chars = len(" ".join(str(x["text"]).strip() for x in cur + [w]))
            if len(cur) >= max_w or chars > max_c or gap > 0.45 or str(cur[-1]["text"]).strip()[-1:] in ".?!":
                groups.append(cur); cur = []
        cur.append(w)
    if cur:
        groups.append(cur)
    off = sorted([tuple(map(float, r)) for r in C.get("off", [])] + hidden)
    em_words = {e.lower() for e in C.get("em", [])}
    norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum() or ch in "$'%")
    y = int(C.get("y", (CY + CH + 46) if CARD else 1180))
    size = int(C.get("size", 56 if THEME else 88))
    karaoke = C.get("style", "karaoke") == "karaoke"
    upper = " upper" if C.get("upper") else ""
    look = "disp outl" if THEME else "shadow"
    lit = ("{ color: '%s', scale: 1.12 }" % ACCENT, "{ color: '%s', scale: 1 }" % TEXT) if THEME else ("{ color: '#0AF0F0' }", "{ color: '#FFFFFF' }")
    for gi, g in enumerate(groups):
        s = max(0.0, float(g[0]["start"]) - 0.04)
        e = float(g[-1]["end"]) + 0.6
        if gi + 1 < len(groups):
            e = min(e, float(groups[gi + 1][0]["start"]) - 0.04)
        e = min(max(e, s + 0.12), D)
        # subtract the caption-free windows
        wins = [(s, e)]
        for a, b2 in off:
            wins = [piece for (x, y2) in wins for piece in ((x, min(y2, a)), (max(x, b2), y2)) if piece[1] - piece[0] > 0.05]
        if not wins or s >= D:
            continue
        gid = "cap%d" % gi
        ws = []
        for wi, w in enumerate(g):
            txt = str(w["text"]).strip()
            ws.append('<span class="cw%s" id="%s-w%d">%s</span>' % ((" em acc" if THEME else " em") if norm(txt) in em_words else "", gid, wi, hesc(txt)))
        cap_html += '      <div class="cap %s%s" id="%s" style="top:%dpx;font-size:%dpx">%s</div>\n' % (look, upper, gid, y, size, " ".join(ws))
        n_groups += 1
        for a, b2 in wins:
            js("tl.set('#%s', { visibility: 'visible' }, %.3f);" % (gid, a))
            js("tl.fromTo('#%s', { opacity: 0, scale: 0.94 }, { opacity: 1, scale: 1, duration: 0.08, ease: 'power2.out', immediateRender: false }, %.3f);" % (gid, a))
            js("tl.set('#%s', { visibility: 'hidden' }, %.3f);" % (gid, b2))
        if karaoke:
            for wi, w in enumerate(g):
                if norm(str(w["text"])) in em_words:
                    continue
                ws_t = max(s, float(w["start"]))
                we_t = float(g[wi + 1]["start"]) if wi + 1 < len(g) else e
                js("tl.set('#%s-w%d', %s, %.3f);" % (gid, wi, lit[0], ws_t))
                js("tl.set('#%s-w%d', %s, %.3f);" % (gid, wi, lit[1], max(ws_t + 0.02, we_t)))
    for a, b2 in seams:      # during a split the captions ride on the seam between the media and your face
        js("tl.to('#captions', { y: %d, duration: 0.45, ease: 'power2.inOut' }, %.3f);" % (900 - y, max(0.0, a - 0.1)))
        js("tl.to('#captions', { y: 0, duration: 0.45, ease: 'power2.inOut' }, %.3f);" % (b2 - 0.45))
    if words:
        first_visual = float(words[0]["start"]) if first_visual is None else min(first_visual, float(words[0]["start"]))

prog_html = ""
if S.get("progress"):
    prog_html = '    <div id="progress"></div>\n'      # in card mode it sits along the card's bottom edge instead
    js("tl.fromTo('#progress', { scaleX: 0 }, { scaleX: 1, duration: %.3f, ease: 'none' }, 0);" % D)

# the footage: full frame, or (card mode) inside a rounded card over a slowly drifting background
video_html = ('    <div class="video-wrapper" id="video-wrap">\n      <div id="video-zoom">\n'
              '        <video id="bg-video" src="%s" playsinline data-has-audio="true" data-start="0" data-duration="%.3f" data-track-index="1"></video>\n'
              '      </div>\n    </div>\n' % (S.get("video", "input-video.mp4"), D))
if CARD:
    video_html = ('    <div id="bg"><div class="blob b1"></div><div class="blob b2"></div><div class="blob b3"></div><div class="dotgrid"></div></div>\n'
                  '    <div id="card">\n%s%s    </div>\n' % (video_html, prog_html))
    prog_html = ""
    for sel, dx, dy in (("b1", 260, 220), ("b2", -240, -260), ("b3", -180, 200)):
        js("tl.fromTo('#bg .%s', { x: 0, y: 0 }, { x: %d, y: %d, duration: %.3f, ease: 'sine.inOut' }, 0);" % (sel, dx, dy, D))
    js("tl.fromTo('#bg .dotgrid', { y: 0 }, { y: -80, duration: %.3f, ease: 'none' }, 0);" % D)

for snd in S.get("sounds", []):
    audio_parts.append('    <audio id="sfx-%d" src="%s" data-start="%.3f" data-duration="%.2f" data-track-index="%d" data-volume="%.2f"></audio>\n'
                       % (audio_track, qesc(snd["src"]), float(snd["at"]), float(snd.get("dur", 0.6)), audio_track, float(snd.get("volume", 0.3))))
    audio_track += 1

# ---- camera -----------------------------------------------------------------------------------------
cam = ["tl.set('#video-zoom', { scale: 1.0 }, 0);", "tl.set('#video-wrap', { scale: 1.0, x: 0, y: 0 }, 0);"]
for op in S.get("camera", []):
    if op[0] == "set":
        cam.append("tl.set('#video-zoom', { scale: %.3f }, %.3f);" % (float(op[2]), float(op[1])))
    elif op[0] == "creep":
        t0, t1, sc = float(op[1]), float(op[2]), float(op[3])
        cam.append("tl.to('#video-zoom', { scale: %.3f, duration: %.3f, ease: 'power1.inOut' }, %.3f);" % (sc, t1 - t0, t0))
    elif op[0] == "punch":
        cam.append("tl.to('#video-zoom', { scale: %.3f, duration: 0.30, ease: 'power2.out' }, %.3f);" % (float(op[2]), float(op[1])))
    elif op[0] == "reveal":
        cam.append("tl.fromTo('#video-zoom', { scale: 1.10 }, { scale: 1.00, duration: 0.5, ease: 'power2.inOut', immediateRender: false }, %.3f);" % float(op[1]))
    elif op[0] == "release":
        cam.append("tl.to('#video-zoom', { scale: 1.00, duration: %.3f, ease: 'power2.inOut' }, %.3f);" % (float(op[2]), float(op[1])))
    else:
        sys.exit("unknown camera op %r" % (op,))
    sc = float(op[3]) if op[0] == "creep" else (float(op[2]) if op[0] in ("set", "punch") else 1.0)
    soft = float(FRAME.get("max_zoom", 1.6)) if CARD else 1.15     # a card shows 1080p footage downscaled: room to push in
    if sc > soft + 1e-9:
        warns.append("camera %s at %.2f goes to %.2f: the footage turns soft past ~%.2f" % (op[0], float(op[1]), sc, soft))

HELPERS = """
        const glassIn = function (sel, t, from, dur) {
          tl.fromTo(sel, Object.assign({ backgroundColor: 'rgba(255,255,255,0)', borderColor: 'rgba(255,255,255,0)', boxShadow: '0 24px 80px rgba(0,0,0,0)' }, from || {}),
            { backgroundColor: 'GLASS_BG', borderColor: 'rgba(255,255,255,0.58)', boxShadow: '0 24px 80px rgba(0,0,0,0.38)', x: 0, y: 0, duration: dur || 0.42, ease: 'power2.out' }, t);
        };
        const glassOut = function (sel, t, dur) {
          tl.to(sel, { backgroundColor: 'rgba(255,255,255,0)', borderColor: 'rgba(255,255,255,0)', boxShadow: '0 24px 80px rgba(0,0,0,0)', duration: dur || 0.35, ease: 'power2.in' }, t);
        };
        // count-up in full digits ("1,000", never "1K"); the proxy lives on the one paused timeline
        const countUp = function (sel, to, t, dur, prefix, suffix, dec) {
          const el = document.querySelector(sel); const o = { v: 0 };
          const fmt = function (v) { return prefix + v.toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec }) + suffix; };
          el.textContent = fmt(0);
          tl.fromTo(o, { v: 0 }, { v: to, duration: dur, ease: 'power2.out', immediateRender: false,
            onUpdate: function () { el.textContent = fmt(dec ? o.v : Math.round(o.v)); } }, t);
        };
""".replace("GLASS_BG", GLASS_BG)

page = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<style>%s</style>
</head>
<body>
  <div id="stage" data-composition-id="%s" data-start="0" data-duration="%.3f" data-fps="30" data-width="%d" data-height="%d">

%s
%s%s    <div id="captions">
%s    </div>
%s%s
    <script src="%s"></script>
    <script>
      (function () {
        const tl = window.gsap.timeline({ paused: true });
%s
        // camera
        %s

        // beats, captions
        %s
%s
        tl.to({}, { duration: %.3f }, 0);
        window.__timelines = window.__timelines || {};
        window.__timelines["%s"] = tl;
      })();
    </script>
  </div>
</body>
</html>
""" % (CSS, S["id"], D, FW, FH, video_html, "".join(html_parts), S.get("raw_html", ""), cap_html,
       prog_html, "".join(audio_parts), GSAP_SRC, HELPERS, "\n        ".join(cam), "\n        ".join(js_parts), S.get("raw_js", ""), D, S["id"])
with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
    f.write(page)
with open(os.path.join(OUT, "hyperframes.json"), "w", encoding="utf-8") as f:
    f.write(json.dumps({"$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
                        "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
                        "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
                        "media": {"autoProxy": True}}, indent=2))

# ---- report -------------------------------------------------------------------------------------------
beats = S.get("beats", [])
print("wrote %s/index.html: 1080x1920, %.1f s, %d beats, %d caption groups, %d camera ops, %d sounds"
      % (OUT, D, len(beats), n_groups, len(S.get("camera", [])), len(audio_parts)))
print("snapshot moments:", " ".join("%.2f" % m for m in sorted({0.1} | {min(float(b["in"]) + 0.9, D - 0.05) for b in beats})))
seq = sorted((float(b["in"]), b["type"]) for b in beats)
counts = {}
for _, ty in seq:
    counts[ty] = counts.get(ty, 0) + 1
print("format usage:", ", ".join("%s %d" % kv for kv in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))) or "none")
for (t1, a), (t2, b2) in zip(seq, seq[1:]):
    if a == b2 and a not in ("text", "vignette", "emoji", "credit", "title", "draw"):     # accents, not devices
        warns.append("same device twice in a row: %s at %.2f and %.2f" % (a, t1, t2))
if first_visual is None or first_visual > 0.5:
    warns.append("hook gate: nothing on screen before 0.5 s (first at %s); a Short earns the swipe in its first frame"
                 % ("never" if first_visual is None else "%.2f s" % first_visual))
for w in warns:
    print("WARN", w)
