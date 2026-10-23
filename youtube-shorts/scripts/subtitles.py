#!/usr/bin/env python3
"""subtitles.py: animated subtitles over a clip that is already edited. The picture and the cut stay exactly as they
are; this only adds the captions (motion-graphic, word-exact) and the few sounds they earn.

The look (NOTES.md): one font (round robin Inter / Montserrat), plain text (no stroke, outline, shadow or glow),
simple, professional. What makes it feel premium is the motion, not decoration:
  word      each word lands as it is spoken: rises a third of an em out of a light blur (0.26 s power3.out); the
            words still to come hold their place, so a line never re-centres while it fills
  em        an emphasis word is in the accent colour and lands a touch bigger (1.14 -> 1, expo.out)
  punch     a punchline word gets a line of its own, 1.45x ("punch_scale"), letters rising in a quick stagger
            (no underline or bar under any word, in any style)
  exit      a line lifts and blurs out in 0.12 s, ending exactly when the next line starts (never two on screen)
  scrim     a soft dark band behind the caption zone (the footage darkens, the text stays plain); 0 turns it off
Sounds ("sfx": "auto"): a short whoosh 0.08 s before each punch word, a soft click on an emphasis word when nothing
has sounded for 2 s; never two inside 0.3 s. Extra sounds go in "sounds" by hand.

captions.json (next to the transcript; every key is optional except transcript):
{"transcript": "transcript.json", "preset": "clean", "font": "Inter", "font_file": "Inter-700.woff2", "size": 78, "y": 1250,
 "max_words": 3, "max_chars": 16, "text": "#FFFFFF", "accent": "#FFD400", "punch_scale": 1.45,
 "em": ["sandals", 41], "punch": [57, "18-19"], "breaks": [12, 30], "off": [[20.5, 23.0]], "upper": false,
 "scrim": 0.28, "sfx": "auto", "sfx_gain": 1.0, "sounds": [{"src": "sfx/pop.wav", "at": 3.2, "dur": 0.6, "volume": 0.2}],
 "hook": {"text": "Stop playing college|football at 26", "em": ["26"], "y": 470, "size": 76, "out": 19.8},
 "raw_html": "<svg ...>", "raw_js": "tl.fromTo(...);"}
  subject / behind_html: depth. subject = the people cut out of the window crop (remove-background, .webm);
  behind_html = elements between the footage and the people (frame coordinates), animated from raw_js.
  raw_html / raw_js: hand-made motion elements (drawn marker strokes, pops) placed between the footage and the
  captions; raw_js runs on the same paused timeline `tl`. Keep them out of the caption zone and plain (NOTES 7).
  preset: a named animation look from templates/subtitle-presets.json (clean, box, bounce, karaoke, wipe, calm); it
  fills style / size / max_words / max_chars / upper / punch_scale / rows only where the spec leaves them out.
  rows: 2 lets a caption run to two rows (max_words and max_chars are per row), split where the rows come out most
  even, so it stays up longer and is easier to read; a caption that fits one row stays on one, a punch stays on one.
  hook: the on-screen hook, plain text from the first frame (no entrance: the feed autoplays), "|" breaks a line, em
  words in the accent; held to "out" (default: the whole clip). Keep it out of the top 200 px (YouTube's icons).
  em / punch / breaks: a word index in the transcript (exact) or, for em, a word (every occurrence, case and
  punctuation ignored); a punch can be a short phrase "a-b" (word indices, inclusive), kept on one big line. breaks: a line starts at that word index. y: the centre of the caption line in px.

Usage:
  python3 subtitles.py --video W/edit.mp4 --spec W/captions.json --out W/public [--shared videos/_shared] [--snap]
--snap also snapshots the key moments into W/snaps/ and tiles W/snaps/sheet.png. The script prints the render
command (the clip's own size and frame rate).
"""
import argparse, fractions, glob, html, json, math, os, shutil, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument("--video", required=True)
ap.add_argument("--spec", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--shared", default="")
ap.add_argument("--snap", action="store_true")
ap.add_argument("--at", action="append", default=[], help="extra snapshot moments (with --snap)")
args = ap.parse_args()

SKILL = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SPEC_DIR = os.path.dirname(os.path.abspath(args.spec))
S = json.load(open(args.spec, encoding="utf-8"))
# "preset": a named look from templates/subtitle-presets.json (style, size, line length, case); it only fills the keys
# the spec leaves out, so a spec value still wins
if S.get("preset"):
    PRESETS = json.load(open(os.path.join(SKILL, "templates", "subtitle-presets.json"), encoding="utf-8"))
    if S["preset"] not in PRESETS or S["preset"].startswith("_"):
        sys.exit("no subtitle preset %r (have: %s)" % (S["preset"], ", ".join(k for k in PRESETS if not k.startswith("_"))))
    S = dict({k: v for k, v in PRESETS[S["preset"]].items() if not k.startswith("_")}, **S)
OUT = args.out
os.makedirs(OUT, exist_ok=True)

# ---- the clip -----------------------------------------------------------------------------------------
pj = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate:format=duration",
                                "-of", "json", args.video], capture_output=True, text=True, check=True).stdout)
vs = next((s for s in pj["streams"] if s["codec_type"] == "video"), None)
if vs is None:
    sys.exit("%s has no video stream" % args.video)
if not any(s["codec_type"] == "audio" for s in pj["streams"]):
    sys.exit("%s has no audio stream: subtitles follow the voice" % args.video)
FW, FH = int(vs["width"]), int(vs["height"])
FPS = fractions.Fraction(vs["r_frame_rate"])
D = float(pj["format"]["duration"])
VIDEO = "input-video" + os.path.splitext(args.video)[1].lower()
dst = os.path.join(OUT, VIDEO)
if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(args.video) or os.path.getsize(dst) != os.path.getsize(args.video):
    shutil.copy2(args.video, dst)

# ---- assets -------------------------------------------------------------------------------------------
def stage(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(src) and not os.path.exists(dst):
        shutil.copy(src, dst)
FONT, FONT_FILE = S.get("font", "Inter"), S.get("font_file", "Inter-700.woff2")
if not os.path.exists(os.path.join(SKILL, "assets", "fonts", FONT_FILE)):
    sys.exit("no font %s in assets/fonts" % FONT_FILE)
stage(os.path.join(SKILL, "assets", "fonts", FONT_FILE), os.path.join(OUT, "fonts", FONT_FILE))
stage(os.path.join(SKILL, "assets", "vendor", "gsap.min.js"), os.path.join(OUT, "vendor", "gsap.min.js"))
GSAP_SRC = "vendor/gsap.min.js" if os.path.exists(os.path.join(OUT, "vendor", "gsap.min.js")) else "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"
sfx_dirs = [os.path.join(args.shared, "sfx")] if args.shared else []
sfx_dirs.append(os.path.join(SKILL, "assets", "sfx"))
def stage_sfx(rel):
    name = os.path.basename(rel)
    for d in sfx_dirs:
        if os.path.exists(os.path.join(d, name)):
            stage(os.path.join(d, name), os.path.join(OUT, "sfx", name)); return True
    return False

# ---- words and lines ----------------------------------------------------------------------------------
tpath = S.get("transcript", "transcript.json")
tpath = tpath if os.path.isabs(tpath) else os.path.join(SPEC_DIR, tpath)
raw = json.load(open(tpath, encoding="utf-8"))
words = [w for w in (raw["words"] if isinstance(raw, dict) and "words" in raw else raw) if str(w.get("text", "")).strip()]
if not words:
    sys.exit("no words in %s" % tpath)
norm = lambda s: "".join(ch for ch in str(s).lower() if ch.isalnum() or ch in "$'%")
em_idx = {int(e) for e in S.get("em", []) if isinstance(e, int)}
em_txt = {norm(e) for e in S.get("em", []) if isinstance(e, str)}
ranges = []                      # a punch is a word index, or "a-b" for a short phrase ("hate 'em.")
for p in S.get("punch", []):
    a, _, b = str(p).partition("-")
    ranges.append((int(a), int(b or a)))
punch = {i for a, b in ranges for i in range(a, b + 1)}
p_start = {a for a, b in ranges}
p_inner = punch - p_start
breaks = {int(b) for b in S.get("breaks", [])} | p_start | {b + 1 for a, b in ranges}
is_em = lambda i: i in em_idx or norm(words[i]["text"]) in em_txt
max_w, max_c = int(S.get("max_words", 3)), int(S.get("max_chars", 16))
ROWS = max(1, int(S.get("rows", 1)))
row_w, row_c = max_w, max_c       # per row; a caption may hold ROWS of them
max_w, max_c = max_w * ROWS, max_c * ROWS + ROWS - 1

lines, cur = [], []
for i, w in enumerate(words):
    if cur and i in p_inner:      # a punch phrase stays on one line
        cur.append(i); continue
    if cur:
        prev = words[cur[-1]]
        chars = len(" ".join(str(words[k]["text"]).strip() for k in cur + [i]))
        if (i in breaks or len(cur) >= max_w or chars > max_c or float(w["start"]) - float(prev["end"]) > 0.45
                or str(prev["text"]).strip()[-1:] in ".?!"):
            lines.append(cur); cur = []
    cur.append(i)
if cur:
    lines.append(cur)

off = [tuple(map(float, r)) for r in S.get("off", [])]
SIZE = int(S.get("size", 78 if FH >= FW else 64))
Y = int(S.get("y", 1250 if (FW, FH) == (1080, 1920) else round(FH * 0.80)))
TEXT, ACCENT = S.get("text", "#FFFFFF"), S.get("accent", "#FFD400")
UPPER = bool(S.get("upper", False))
PSCALE = float(S.get("punch_scale", 1.45))   # a long punch phrase ("nobody's bothered.") runs smaller to stay on one line
# "style": "rise" (default: words rise in one by one, punch lines cascade by letter) or "highlight" (after captions.ai's
# Bellatrix, clashcam-06): the whole line pops in at once and a box in the accent colour jumps to each word as it is
# said, that word turning dark on it. Punch lines run bigger in the same way.
# "pop" (clashcam-03 v3): each word bounces in on its word (back.out), yellow while it is said, then white; best with
# max_words 2. "karaoke" (clashcam-07 v2): the whole line slides up dim, each word lights up as it is said. Both plain
# text (NOTES 7).
# "wipe": each word is revealed left to right as it is said, sliding a little into place.
# "calm": the whole line fades in at once and nothing else moves, only an emphasis word turns accent when it is said.
STYLE = S.get("style", "rise")
if STYLE not in ("rise", "highlight", "pop", "karaoke", "wipe", "calm"):
    sys.exit("unknown subtitle style %r" % STYLE)
HL_TEXT = S.get("hl_text", "#111317")

def esc(s): return html.escape(str(s), quote=True)

def join_rows(spans, ln, big):
    """The word spans of one caption; with rows 2, a caption longer than a row breaks where the rows are most even."""
    lens = [len(str(words[i]["text"]).strip()) for i in ln]
    if ROWS < 2 or big or len(ln) < 2 or (len(ln) <= row_w and sum(lens) + len(ln) - 1 <= row_c):
        return " ".join(spans)
    k = min(range(1, len(ln)), key=lambda k: max(sum(lens[:k]) + k - 1, sum(lens[k:]) + len(ln) - k - 1))
    return " ".join(spans[:k]) + "<br>" + " ".join(spans[k:])

html_lines, js, moments = [], [], [0.1]
HOOK = S.get("hook")
hook_html = ""
if HOOK:
    hem = {norm(e) for e in HOOK.get("em", [])}
    rows = "".join('<div class="hk-row">%s</div>' % " ".join('<span class="hk-w%s">%s</span>' % (" em" if norm(w) in hem else "", esc(w)) for w in ln.split())
                   for ln in str(HOOK["text"]).split("|"))
    hook_html = '    <div id="hook" style="top:%dpx;font-size:%dpx">%s</div>\n' % (int(HOOK.get("y", 470)), int(HOOK.get("size", 76)), rows)
    h_out = float(HOOK.get("out", D))
    if h_out < D - 0.02:
        js.append("tl.to('#hook', { opacity: 0, y: -12, duration: 0.3, ease: 'power2.in' }, %.3f);" % (h_out - 0.3))
    if int(HOOK.get("y", 470)) - int(HOOK.get("size", 76)) < 200:
        print("WARN hook reaches into the top 200 px (YouTube's search and menu icons)")
for li, ln in enumerate(lines):
    s = max(0.0, float(words[ln[0]]["start"]) - 0.04)
    nxt = float(words[lines[li + 1][0]]["start"]) - 0.04 if li + 1 < len(lines) else D
    e = min(float(words[ln[-1]]["end"]) + 0.7, nxt, D)
    if any(a <= s < b for a, b in off) or e - s < 0.08:
        continue
    for a, b in off:              # a caption-free window cuts a line short
        if s < a < e:
            e = a
    lid = "l%d" % li
    big = ln[0] in p_start
    if STYLE == "highlight":
        spans = ['<span class="w hw%s" id="%s-w%d"><span class="hb"></span><span class="ht">%s</span></span>'
                 % (" em" if is_em(i) else "", lid, k, esc(str(words[i]["text"]).strip())) for k, i in enumerate(ln)]
        html_lines.append('      <div class="line hl%s" id="%s" style="top:%dpx;font-size:%dpx"><span class="row">%s</span></div>\n'
                          % (" punch" if big else "", lid, Y, round(SIZE * (PSCALE if big else 1)), join_rows(spans, ln, big)))
        js.append("tl.set('#%s', { visibility: 'visible', opacity: 1, y: 0, filter: 'blur(0px)' }, %.3f);" % (lid, s))
        js.append("tl.fromTo('#%s .row', { scale: 0.86, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.2, ease: 'back.out(2)' }, %.3f);" % (lid, s))
        for k, i in enumerate(ln):
            t = max(s, float(words[i]["start"]) - 0.03)
            sel = "#%s-w%d" % (lid, k)
            if k:                     # the box leaves the last word
                js.append("tl.to('#%s-w%d .hb', { opacity: 0, duration: 0.06 }, %.3f);" % (lid, k - 1, t))
                js.append("tl.set('#%s-w%d .ht', { color: '%s' }, %.3f);" % (lid, k - 1, ACCENT if is_em(ln[k - 1]) else TEXT, t))
            js.append("tl.fromTo('%s .hb', { opacity: 1, scaleX: 0.55, scaleY: 0.8 }, { scaleX: 1, scaleY: 1, duration: 0.14, ease: 'back.out(2.2)', immediateRender: false }, %.3f);" % (sel, t))
            js.append("tl.set('%s .ht', { color: '%s' }, %.3f);" % (sel, HL_TEXT, t))
            if big or is_em(i):
                js.append("tl.fromTo('%s', { scale: 1.12 }, { scale: 1, duration: 0.3, ease: 'expo.out', immediateRender: false }, %.3f);" % (sel, t))
                moments.append(round(t + 0.35, 2))
        if e < D - 0.02:
            js.append("tl.to('#%s', { opacity: 0, scale: 0.94, duration: 0.1, ease: 'power2.in' }, %.3f);" % (lid, max(s + 0.05, e - 0.1)))
            js.append("tl.set('#%s', { visibility: 'hidden' }, %.3f);" % (lid, e))
        continue
    if STYLE in ("wipe", "calm"):
        spans = ['<span class="w%s" id="%s-w%d">%s</span>' % (" em" if is_em(i) else "", lid, k, esc(str(words[i]["text"]).strip()))
                 for k, i in enumerate(ln)]
        html_lines.append('      <div class="line %s%s" id="%s" style="top:%dpx;font-size:%dpx"><span class="row">%s</span></div>\n'
                          % (STYLE, " punch" if big else "", lid, Y, round(SIZE * (PSCALE if big else 1)), join_rows(spans, ln, big)))
        js.append("tl.set('#%s', { visibility: 'visible', opacity: 1, y: 0, filter: 'blur(0px)' }, %.3f);" % (lid, s))
        if STYLE == "calm":       # the whole line at once; nothing else moves
            js.append("tl.fromTo('#%s .row', { opacity: 0, y: '0.12em' }, { opacity: 1, y: 0, duration: 0.18, ease: 'power2.out' }, %.3f);" % (lid, s))
        for k, i in enumerate(ln):
            t = max(s, float(words[i]["start"]) - 0.03)
            sel = "#%s-w%d" % (lid, k)
            if STYLE == "wipe":   # revealed left to right as it is said, sliding a little into place
                js.append("tl.fromTo('%s', { clipPath: 'inset(-25%% 100%% -25%% 0%%)', x: '-0.14em' }, { clipPath: 'inset(-25%% -6%% -25%% 0%%)', x: 0, duration: 0.24, ease: 'power3.out', immediateRender: false }, %.3f);" % (sel, t))
            if is_em(i):
                if STYLE == "calm":
                    js.append("tl.set('%s', { color: '%s' }, %.3f);" % (sel, ACCENT, t))
                js.append("tl.fromTo('%s', { scale: 1.08 }, { scale: 1, duration: 0.3, ease: 'expo.out', immediateRender: false }, %.3f);" % (sel, t))
            if big or is_em(i):
                moments.append(round(t + 0.35, 2))
        if e < D - 0.02:
            js.append("tl.to('#%s', { opacity: 0, duration: 0.1, ease: 'power2.in' }, %.3f);" % (lid, max(s + 0.05, e - 0.1)))
            js.append("tl.set('#%s', { visibility: 'hidden' }, %.3f);" % (lid, e))
        continue
    if STYLE in ("pop", "karaoke"):
        spans = ['<span class="w kw%s" id="%s-w%d"><span class="ht">%s</span></span>'
                 % (" em" if is_em(i) else "", lid, k, esc(str(words[i]["text"]).strip())) for k, i in enumerate(ln)]
        html_lines.append('      <div class="line %s%s" id="%s" style="top:%dpx;font-size:%dpx"><span class="row">%s</span></div>\n'
                          % (STYLE, " punch" if big else "", lid, Y, round(SIZE * (PSCALE if big else 1)), join_rows(spans, ln, big)))
        js.append("tl.set('#%s', { visibility: 'visible', opacity: 1, y: 0, filter: 'blur(0px)' }, %.3f);" % (lid, s))
        if STYLE == "karaoke":    # the whole line slides up dim, then each word lights up as it is said
            js.append("tl.fromTo('#%s .row', { y: '0.5em', opacity: 0 }, { y: 0, opacity: 1, duration: 0.22, ease: 'power3.out' }, %.3f);" % (lid, s))
        for k, i in enumerate(ln):
            t = max(s, float(words[i]["start"]) - 0.03)
            sel = "#%s-w%d" % (lid, k)
            rest = ACCENT if is_em(i) else TEXT
            if STYLE == "pop":    # each word bounces in on its word, yellow while it is being said
                js.append("tl.fromTo('%s', { opacity: 0, scale: 0.45, y: '0.25em' }, { opacity: 1, scale: 1, y: 0, duration: 0.3, ease: 'back.out(3)', immediateRender: false }, %.3f);" % (sel, t))
                js.append("tl.set('%s .ht', { color: '%s' }, %.3f);" % (sel, ACCENT, t))
                if k:
                    js.append("tl.set('#%s-w%d .ht', { color: '%s' }, %.3f);" % (lid, k - 1, ACCENT if is_em(ln[k - 1]) else TEXT, t))
                if big or is_em(i):
                    js.append("tl.fromTo('%s', { rotation: -4 }, { rotation: 0, duration: 0.35, ease: 'elastic.out(1.2, 0.5)', immediateRender: false }, %.3f);" % (sel, t))
            else:
                js.append("tl.fromTo('%s', { opacity: 0.38 }, { opacity: 1, duration: 0.08, immediateRender: false }, %.3f);" % (sel, t))
                js.append("tl.set('%s .ht', { color: '%s' }, %.3f);" % (sel, rest, t))
                if big or is_em(i):
                    js.append("tl.fromTo('%s', { scale: 1.12 }, { scale: 1, duration: 0.3, ease: 'expo.out', immediateRender: false }, %.3f);" % (sel, t))
            if big or is_em(i):
                moments.append(round(t + 0.35, 2))
        if e < D - 0.02:
            js.append("tl.to('#%s', { opacity: 0, scale: 0.92, duration: 0.1, ease: 'power2.in' }, %.3f);" % (lid, max(s + 0.05, e - 0.1)))
            js.append("tl.set('#%s', { visibility: 'hidden' }, %.3f);" % (lid, e))
        continue
    spans = []
    for k, i in enumerate(ln):
        txt = str(words[i]["text"]).strip()
        cls = "w" + (" em" if is_em(i) or big else "")
        inner = "".join('<span class="ch">%s</span>' % esc(c) for c in txt) if big else esc(txt)
        spans.append('<span class="%s" id="%s-w%d">%s</span>' % (cls, lid, k, inner))
    html_lines.append('      <div class="line%s" id="%s" style="top:%dpx;font-size:%dpx"><span class="row">%s</span></div>\n'
                      % (" punch" if big else "", lid, Y, round(SIZE * (PSCALE if big else 1)), join_rows(spans, ln, big)))
    js.append("tl.set('#%s', { visibility: 'visible', opacity: 1, y: 0, filter: 'blur(0px)' }, %.3f);" % (lid, s))
    for k, i in enumerate(ln):
        t = max(s, float(words[i]["start"]) - 0.03)
        sel = "#%s-w%d" % (lid, k)
        if big:
            js.append("tl.fromTo('%s .ch', { opacity: 0, y: '0.42em', scale: 1.25 }, { opacity: 1, y: 0, scale: 1, duration: 0.42, ease: 'expo.out', stagger: 0.028 }, %.3f);" % (sel, t))
            if k == 0:
                moments += [round(t + 0.16, 2), round(t + 0.7, 2)]
        else:
            js.append("tl.fromTo('%s', { opacity: 0, y: '0.32em', filter: 'blur(8px)' }, { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.26, ease: 'power3.out' }, %.3f);" % (sel, t))
            if is_em(i):
                js.append("tl.fromTo('%s', { scale: 1.14 }, { scale: 1, duration: 0.45, ease: 'expo.out', immediateRender: false }, %.3f);" % (sel, t))
                moments.append(round(t + 0.5, 2))
    if e < D - 0.02:
        js.append("tl.to('#%s', { opacity: 0, y: '-0.18em', filter: 'blur(6px)', duration: 0.12, ease: 'power2.in' }, %.3f);" % (lid, max(s + 0.05, e - 0.12)))
        js.append("tl.set('#%s', { visibility: 'hidden' }, %.3f);" % (lid, e))

# ---- sound --------------------------------------------------------------------------------------------
sounds = []
gain = float(S.get("sfx_gain", 1.0))
if S.get("sfx", "auto") == "auto":
    cand = []
    for ln in lines:
        for i in ln:
            t = float(words[i]["start"])
            if i in p_start:
                cand.append((t - 0.08, "sfx/whoosh-short.wav", 0.50, 0.26, 0))
            elif is_em(i):
                cand.append((t, "sfx/click-soft.wav", 0.32, 0.14, 1))
    last = -9.0
    for t, src, dur, vol, kind in sorted(cand):
        if any(a <= t < b for a, b in off) or t < 0:
            continue
        if t - last < 0.3 or (kind == 1 and t - last < 2.0):
            continue
        sounds.append({"src": src, "at": round(t, 3), "dur": dur, "volume": round(vol * gain, 3)}); last = t
sounds += S.get("sounds", [])
audio_html = []
for k, snd in enumerate(sorted(sounds, key=lambda x: float(x["at"]))):
    if not stage_sfx(snd["src"]):
        sys.exit("sound %s not found in %s" % (snd["src"], " or ".join(sfx_dirs)))
    audio_html.append('    <audio id="sfx-%d" src="sfx/%s" data-start="%.3f" data-duration="%.2f" data-track-index="%d" data-volume="%.2f"></audio>\n'
                      % (k, esc(os.path.basename(snd["src"])), float(snd["at"]), float(snd.get("dur", 0.6)), 60 + k, float(snd.get("volume", 0.2))))

# ---- the footage window and the camera (optional) ------------------------------------------------------
# "window": {"y": 675, "h": 570} puts the picture of a letterboxed clip in its own box, so a punch-in, a push or a
# shake moves the picture inside it and never the black bands. "camera" ops (frame px for origins):
#   ["set", t, scale] ["punch", t, scale, ox, oy] ["creep", t0, t1, scale, ox, oy] ["release", t, dur]
#   ["shake", t, amp_px, dur] ["flash", t, opacity]
#   transitions over a source cut at t: ["whip", t, dir] ["zoomblur", t, ox, oy] ["leak", t]
WIN = S.get("window")
CAM = S.get("camera", [])
if CAM and not WIN:
    WIN = {"y": 0, "h": FH}
cam_js = []
used = set()          # transitions in use: their filter defs and overlays get added to the page
if WIN:
    WY, WH = int(WIN["y"]), int(WIN["h"])
    def origin(t, ox, oy):
        cam_js.append("tl.set('#cam', { transformOrigin: '%dpx %dpx' }, %.3f);" % (int(ox), int(oy) - WY, t))
    cam_js.append("tl.set('#cam', { scale: 1, x: 0, y: 0, transformOrigin: '50%% 50%%' }, 0);")
    for op in CAM:
        k = op[0]
        if k == "set":
            cam_js.append("tl.set('#cam', { scale: %.3f }, %.3f);" % (float(op[2]), float(op[1])))
        elif k == "punch":
            if len(op) > 3: origin(float(op[1]) - 0.001, op[3], op[4])
            cam_js.append("tl.to('#cam', { scale: %.3f, duration: 0.26, ease: 'expo.out' }, %.3f);" % (float(op[2]), float(op[1])))
        elif k == "creep":
            if len(op) > 4: origin(float(op[1]) - 0.001, op[4], op[5])
            cam_js.append("tl.to('#cam', { scale: %.3f, duration: %.3f, ease: 'sine.inOut' }, %.3f);" % (float(op[3]), float(op[2]) - float(op[1]), float(op[1])))
        elif k == "release":
            cam_js.append("tl.to('#cam', { scale: 1, duration: %.3f, ease: 'power2.inOut' }, %.3f);" % (float(op[2]), float(op[1])))
        elif k == "shake":
            t, amp, dur = float(op[1]), float(op[2]), float(op[3]); n = max(2, int(dur / 0.035))
            for i in range(n):          # a decaying shake: each kick smaller than the last
                a = amp * (1 - i / float(n)); sx = (1 if i % 2 else -1) * a; sy = (-0.6 if i % 3 else 0.5) * a
                cam_js.append("tl.to('#cam', { x: %.1f, y: %.1f, rotation: %.2f, duration: 0.035, ease: 'none' }, %.3f);" % (sx, sy, sx * 0.03, t + i * 0.035))
            cam_js.append("tl.to('#cam', { x: 0, y: 0, rotation: 0, duration: 0.05, ease: 'power1.out' }, %.3f);" % (t + n * 0.035))
        elif k == "whip":
            # a whip pan across a cut: the outgoing shot slides off with horizontal motion blur, the incoming one slides
            # in from the other side; scaled up so the window's edges never show. ["whip", cut, dir (+1 = to the left)]
            t, d = float(op[1]), (1 if len(op) < 3 else int(op[2])); used.add("hblur")
            cam_js.append("tl.set('#cam', { filter: 'url(#hblur)' }, %.3f);" % (t - 0.13))
            cam_js.append("tl.fromTo('#cam', { x: 0, scale: 1 }, { x: %d, scale: 1.24, duration: 0.13, ease: 'power3.in', immediateRender: false }, %.3f);" % (-120 * d, t - 0.13))
            cam_js.append("tl.fromTo('#hblurdev', { attr: { stdDeviation: '0 0' } }, { attr: { stdDeviation: '46 0' }, duration: 0.13, ease: 'power3.in', immediateRender: false }, %.3f);" % (t - 0.13))
            cam_js.append("tl.fromTo('#cam', { x: %d, scale: 1.24 }, { x: 0, scale: 1, duration: 0.2, ease: 'power3.out', immediateRender: false }, %.3f);" % (120 * d, t))
            cam_js.append("tl.fromTo('#hblurdev', { attr: { stdDeviation: '46 0' } }, { attr: { stdDeviation: '0 0' }, duration: 0.2, ease: 'power3.out', immediateRender: false }, %.3f);" % t)
            cam_js.append("tl.set('#cam', { filter: 'none' }, %.3f);" % (t + 0.21))
        elif k == "zoomblur":
            # punch through a cut: zoom in hard on the outgoing shot, land zoomed on the incoming one and settle, a flash at the cut
            t = float(op[1]); used.add("zoom")
            if len(op) > 3: origin(t - 0.16, op[2], op[3])
            cam_js.append("tl.fromTo('#cam', { scale: 1, filter: 'blur(0px) brightness(1)' }, { scale: 1.22, filter: 'blur(7px) brightness(1.35)', duration: 0.14, ease: 'power3.in', immediateRender: false }, %.3f);" % (t - 0.14))
            cam_js.append("tl.fromTo('#cam', { scale: 1.2, filter: 'blur(7px) brightness(1.35)' }, { scale: 1, filter: 'blur(0px) brightness(1)', duration: 0.26, ease: 'expo.out', immediateRender: false }, %.3f);" % t)
            cam_js.append("tl.fromTo('#flash', { opacity: 0.32 }, { opacity: 0, duration: 0.18, ease: 'power2.out', immediateRender: false }, %.3f);" % t)
            cam_js.append("tl.set('#cam', { filter: 'none' }, %.3f);" % (t + 0.27))
        elif k == "leak":
            # a warm light leak sweeping across the window over a cut, the picture briefly overexposed
            t = float(op[1]); used.add("leak")
            cam_js.append("tl.fromTo('#leak', { opacity: 0, xPercent: -60 }, { keyframes: [{ opacity: 0.75, xPercent: -8, duration: 0.18, ease: 'power2.out' }, { opacity: 0, xPercent: 45, duration: 0.26, ease: 'power2.in' }], immediateRender: false }, %.3f);" % (t - 0.16))
            cam_js.append("tl.fromTo('#cam', { filter: 'brightness(1)' }, { keyframes: [{ filter: 'brightness(1.22)', duration: 0.16 }, { filter: 'brightness(1)', duration: 0.26 }], immediateRender: false }, %.3f);" % (t - 0.14))
            cam_js.append("tl.set('#cam', { filter: 'none' }, %.3f);" % (t + 0.3))
        elif k == "flash":
            cam_js.append("tl.fromTo('#flash', { opacity: %.2f }, { opacity: 0, duration: 0.2, ease: 'power2.out', immediateRender: false }, %.3f);" % (float(op[2]), float(op[1])))
        else:
            sys.exit("unknown camera op %r" % (op,))

# ---- the page -----------------------------------------------------------------------------------------
scrim = float(S.get("scrim", 0.28))
first = float(words[lines[0][0]]["start"]) - 0.04
if scrim > 0:
    js.insert(0, "tl.fromTo('#scrim', { opacity: 0 }, { opacity: 1, duration: 0.4, ease: 'power1.out' }, %.3f);" % max(0.0, first - 0.3))
side = 110 if FW >= 1000 else round(FW * 0.08)
CSS = """
  @font-face { font-family: "SubFont"; src: url("fonts/%(ff)s"); font-display: block; }
  * { box-sizing: border-box; }
  html, body { margin:0; padding:0; width:100%%; height:100%%; overflow:hidden; background:#000; }
  #stage { position:relative; width:%(w)dpx; height:%(h)dpx; overflow:hidden; background:#000; }
  #clip { position:absolute; inset:0; width:100%%; height:100%%; object-fit:cover; display:block; }
  #win { position:absolute; left:0; width:100%%; overflow:hidden; }
  #cam { position:absolute; left:0; top:0; width:100%%; height:100%%; will-change:transform; }
  #win #clip { inset:auto; left:0; width:%(w)dpx; height:%(h)dpx; }
  #flash { position:absolute; inset:0; background:#fff; opacity:0; pointer-events:none; }
  #leak { position:absolute; top:-20%%; left:-30%%; width:160%%; height:140%%; opacity:0; pointer-events:none; mix-blend-mode:screen;
    background: linear-gradient(100deg, rgba(255,120,30,0) 18%%, rgba(255,150,60,.55) 36%%, rgba(255,214,150,.85) 46%%, rgba(255,150,60,.5) 56%%, rgba(255,120,30,0) 76%%);
    filter: blur(28px); }
  #behind { position:absolute; left:0; width:%(w)dpx; height:%(h)dpx; pointer-events:none; }
  #subject { position:absolute; left:0; top:0; width:100%%; height:100%%; object-fit:fill; display:block; }
  #scrim { position:absolute; left:0; width:100%%; top:%(st)dpx; height:%(sh)dpx; opacity:0; pointer-events:none;
    background: linear-gradient(to bottom, rgba(0,0,0,0) 0%%, rgba(0,0,0,%(sa).3f) 38%%, rgba(0,0,0,%(sa).3f) 62%%, rgba(0,0,0,0) 100%%); }
  #subs { position:absolute; inset:0; pointer-events:none; }
  .line { position:absolute; left:%(side)dpx; right:%(side)dpx; text-align:center; visibility:hidden; translate:0 -50%%;
    font-family:"SubFont", sans-serif; font-weight:700; line-height:1.1; letter-spacing:-.02em; color:%(text)s; %(upper)s }
  .line .row { position:relative; display:inline-block; }
  .line .w { display:inline-block; opacity:0; transform-origin:50%% 80%%; }
  .line .w.em { color:%(acc)s; }
  .line.punch .w { opacity:1; letter-spacing:-.03em; }
  .line.punch .ch { display:inline-block; opacity:0; transform-origin:50%% 90%%; }
  #hook { position:absolute; left:70px; right:70px; text-align:center; translate:0 -50%%; font-family:"SubFont", sans-serif;
    font-weight:700; line-height:1.12; letter-spacing:-.02em; color:%(text)s; }
  #hook .em { color:%(acc)s; }
  .line.hl .row { transform-origin:50%% 60%%; }
  .line.hl .w { opacity:1; position:relative; margin:0 .1em; }
  .line.hl .hb { position:absolute; left:-.12em; right:-.12em; top:-.02em; bottom:-.06em; border-radius:.16em;
    background:%(acc)s; opacity:0; z-index:0; }
  .line.hl .ht { position:relative; z-index:1; }
  .line.pop .w, .line.karaoke .w { position:relative; margin:0 .08em; transform-origin:50%% 85%%; }
  .line.karaoke .w { opacity:.38; }
  .line.hl .w.em .ht { color:%(acc)s; }
  .line.wipe .w { opacity:1; clip-path:inset(-25%% 100%% -25%% 0%%); }
  .line.calm .w { opacity:1; }
  .line.calm .w.em { color:%(text)s; }
""" % dict(ff=FONT_FILE, w=FW, h=FH, st=Y - SIZE * 3, sh=SIZE * 6, sa=scrim, side=side, text=TEXT, acc=ACCENT, hlt=HL_TEXT,
           upper="text-transform:uppercase;" if UPPER else "")

video_tag = '<video id="clip" src="%s" playsinline data-has-audio="true" data-start="0" data-duration="%.3f" data-track-index="1"%s></video>' % (VIDEO, D, ' style="top:-%dpx"' % WY if WIN else "")
# depth: "subject" is the cut-out of the people (hyperframes remove-background on the window crop: a transparent
# WebM the size of the window); "behind_html" goes between the footage and the subject, in frame coordinates, so an
# element sits behind the speakers. Both live inside #cam: they move with every punch, push and shake.
depth = ""
if S.get("subject"):
    if not WIN:
        sys.exit("a subject cut-out needs a \"window\" (the crop it was made from)")
    sp = S["subject"] if os.path.isabs(S["subject"]) else os.path.join(SPEC_DIR, S["subject"])
    if not os.path.exists(sp):
        sys.exit("no subject cut-out at %s" % sp)
    sdst = os.path.join(OUT, "subject" + os.path.splitext(sp)[1].lower())
    if not os.path.exists(sdst) or os.path.getmtime(sdst) < os.path.getmtime(sp):
        shutil.copy2(sp, sdst)
    depth = ('<div id="behind" style="top:-%dpx">%s</div><video id="subject" src="%s" muted playsinline data-start="0" data-duration="%.3f" data-track-index="2"></video>'
             % (WY, S.get("behind_html", ""), os.path.basename(sdst), D))
extras = ""
if "hblur" in used:
    extras += ('<svg width="0" height="0" style="position:absolute"><filter id="hblur" x="-10%" y="0" width="120%" height="100%">'
               '<feGaussianBlur id="hblurdev" stdDeviation="0 0" edgeMode="duplicate"/></filter></svg>')
if "leak" in used:
    extras += '<div id="leak"></div>'
video_html = ('    <div id="win" style="top:%dpx;height:%dpx"><div id="cam">%s%s</div><div id="flash"></div>%s</div>' % (WY, WH, video_tag, depth, extras)) if WIN else "    " + video_tag
page = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<style>%s</style>
</head>
<body>
  <div id="stage" data-composition-id="%s" data-start="0" data-duration="%.3f" data-fps="%d" data-width="%d" data-height="%d">
%s
    <div id="scrim"></div>
%s%s    <div id="subs">
%s    </div>
%s
    <script src="%s"></script>
    <script>
      (function () {
        const tl = window.gsap.timeline({ paused: true });
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
""" % (CSS, S.get("id", "subs"), D, round(float(FPS)), FW, FH, video_html, hook_html, S.get("raw_html", ""), "".join(html_lines), "".join(audio_html), GSAP_SRC,
       "\n        ".join(cam_js + js), S.get("raw_js", ""), D, S.get("id", "subs"))
with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
    f.write(page)
with open(os.path.join(OUT, "hyperframes.json"), "w", encoding="utf-8") as f:
    json.dump({"$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
               "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
               "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
               "media": {"autoProxy": True}}, f, indent=2)

fps_arg = "%d/%d" % (FPS.numerator, FPS.denominator) if FPS.denominator != 1 else str(FPS.numerator)
n_em = sum(1 for ln in lines for i in ln if is_em(i))
print("wrote %s/index.html: %dx%d @ %s fps, %.2f s, %d lines (%d punch, %d emphasis words), %d sounds"
      % (OUT, FW, FH, fps_arg, D, len(html_lines), sum(1 for ln in lines if ln[0] in p_start), n_em, len(audio_html)))
for i in sorted(p_start | {b for a, b in ranges}):
    if i >= len(words):
        print("WARN punch index %d is past the last word (%d)" % (i, len(words) - 1))
if Y + SIZE > FH - (440 if (FW, FH) == (1080, 1920) else 0):
    print("WARN captions at y %d sit in YouTube's bottom UI (keep the line above y 1480)" % Y)
print("render: npx hyperframes render %s --fps %s --video-bitrate 12M --workers 1 -o <render-raw.mp4>" % (OUT, fps_arg))

# ---- snapshots ----------------------------------------------------------------------------------------
if args.snap:
    plain = [round(float(words[ln[-1]]["start"]) + 0.3, 2) for ln in lines if ln[0] not in p_start]
    moments += plain[::max(1, len(plain) // 6)][:6] + [float(a) for a in args.at]
    moments = sorted(set(round(min(m, D - 0.05), 2) for m in moments))[:25]
    P = os.path.dirname(os.path.abspath(OUT))
    snapdir = os.path.join(P, "snaps"); rawd = os.path.join(snapdir, "raw")
    shutil.rmtree(rawd, ignore_errors=True); os.makedirs(snapdir, exist_ok=True)
    for old in glob.glob(os.path.join(snapdir, "at-*.png")):
        os.remove(old)
    r = subprocess.run([shutil.which("npx") or "npx", "hyperframes", "snapshot", OUT, "--at", ",".join("%.2f" % t for t in moments),
                        "-o", rawd, "--no-end"], capture_output=True, text=True)
    frames = sorted(glob.glob(os.path.join(rawd, "frame-*-at-*.png")))
    if len(frames) != len(moments):
        print(r.stdout[-2000:] + r.stderr[-2000:])
        sys.exit("asked for %d snapshots, got %d" % (len(moments), len(frames)))
    outs = []
    for t, fr in zip(moments, frames):
        o = os.path.join(snapdir, "at-%05.2f.png" % t); shutil.copy(fr, o); outs.append(o)
    cols = 5; n = len(outs); rows = math.ceil(n / cols)
    tw = 270 if FH >= FW else 384; th = round(tw * FH / FW / 2) * 2
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for o in outs: cmd += ["-i", o]
    while n % cols: cmd += ["-i", outs[-1]]; n += 1
    cmd += ["-filter_complex", "".join("[%d]" % i for i in range(n)) + "concat=n=%d:v=1:a=0,scale=%d:%d,tile=%dx%d" % (n, tw, th, cols, rows),
            "-frames:v", "1", os.path.join(snapdir, "sheet.png")]
    subprocess.run(cmd, check=True)
    print("snapshots:", " ".join("%.2f" % m for m in moments))
    print("sheet:", os.path.join(snapdir, "sheet.png"))
