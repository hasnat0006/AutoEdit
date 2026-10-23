#!/usr/bin/env python3
"""capcut_lib.py: read, build and safely rewrite CapCut desktop (9.6) projects.

Shared by capcut_export.py (Short -> project), capcut_changes.py (what the creator changed) and capcut_edit.py
(more changes on top of theirs). The format notes behind every choice here are in ../references/capcut-format.md.

Times inside a project are microseconds. Positions are CapCut's: x, y in -1..1 from the canvas centre, +y up.
"""
import copy, html, json, os, re, shutil, subprocess, sys, time, uuid
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LOCAL = os.environ.get("LOCALAPPDATA", "")
ROOT = os.path.join(LOCAL, "CapCut", "User Data", "Projects", "com.lveditor.draft")
FONT = ("155387742", os.path.join(LOCAL, "CapCut", "User Data", "Cache", "effect", "155387742",
                                  "a6c30071ea24cb16a01a3bf1bc6be1fc", "Inter-SemiBold.ttf").replace("\\", "/"))
ACCENT = (1.0, 212 / 255, 0.0)          # #FFD400, the house accent
WHITE = (1.0, 1.0, 1.0)
US = 1_000_000
SUB_Y, SUB_SIZE, HOOK_SIZE = 1380, 11.0, 12.0
T = json.load(open(os.path.join(HERE, "..", "capcut", "template-9.6.json"), encoding="utf-8"))

def uid():
    u = str(uuid.uuid4()).upper().split("-"); u[2] = u[2].lower(); return "-".join(u)
def us(t): return int(round(t * US))
def sec(u): return u / US
def fwd(p): return os.path.abspath(p).replace("\\", "/")
def y_of(px): return (960 - px) / 960.0
def px_of(y): return 960 - y * 960.0
def ff(*a): subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)
def probe_dur(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f],
                                capture_output=True, text=True).stdout.strip())
def pcm(f):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(float)
def rms_db(x): return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
def db(v): return 20 * np.log10(max(v, 1e-6))

def capcut_running():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq CapCut.exe"], capture_output=True, text=True).stdout.lower()
    return "capcut.exe" in out
def require_closed():
    if capcut_running():
        sys.exit("CapCut is open. Save and close it first: it keeps edits in memory and would overwrite the project on exit.")

# ------------------------------------------------------------------------------------------------- layer renders
def render_pass(pub, workdir, out, css, mov=False, drop_video=False):
    """render a copy of the finished page with extra CSS; sounds always removed (CapCut gets them as clips)"""
    shutil.rmtree(workdir, ignore_errors=True)
    shutil.copytree(pub, workdir, ignore=shutil.ignore_patterns(".hyperframes", "renders"))
    page = open(os.path.join(workdir, "index.html"), encoding="utf-8").read()
    page = re.sub(r'<audio id="sfx-\d+"[^>]*>(\s*</audio>)?', "", page)
    if drop_video:
        page = re.sub(r'<video id="clip"[^>]*>\s*</video>', "", page)
    page = page.replace("</style>", css + "\n</style>", 1)
    open(os.path.join(workdir, "index.html"), "w", encoding="utf-8").write(page)
    cmd = [shutil.which("npx") or "npx", "hyperframes", "render", workdir, "--fps", "30", "--workers", "1", "-o", out]
    cmd += ["--format", "mov"] if mov else ["--video-bitrate", "12M"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode or not os.path.exists(out):
        sys.exit("render failed for %s:\n%s%s" % (out, r.stdout[-1500:], r.stderr[-1500:]))
    shutil.rmtree(workdir, ignore_errors=True)

FOOTAGE_CSS = "#fx,#subs,#hook{display:none!important}"
def group_css(ids):
    """only these graphics (and their burst rays, ids '<burst>-N') on a transparent stage"""
    keep_el = "".join(":not(#%s)" % i for i in ids)
    keep_ray = "".join(':not([id^="%s-"])' % i for i in ids)
    return ("html,body,#stage{background:transparent!important}#win,#subs,#hook,#scrim{display:none!important}"
            "#fx > .el%s{opacity:0!important}#fx svg.ov > [id]%s{opacity:0!important}" % (keep_el, keep_ray))

def alpha_spans(mov, gap=0.4, fps=30.0):
    """[(start, end)] where a transparent render has anything on it. ProRes alpha is 12-bit: empty 256, opaque 3774"""
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", mov, "-vf", "alphaextract,scale=108:192,signalstats,"
                          "metadata=print:key=lavfi.signalstats.YMAX:file=-", "-f", "null", "-"], capture_output=True, text=True).stdout
    spans = []
    for i, y in enumerate(float(v) for v in re.findall(r"YMAX=([\d.]+)", out)):
        if y > 320:
            t = i / fps
            if spans and t - spans[-1][1] < gap: spans[-1][1] = t + 1 / fps
            else: spans.append([t, t + 1 / fps])
    return [(a, b) for a, b in spans if b - a > 0.1]

def render_group(subs, name, ids):
    """one graphic idea -> <subs>/capcut/gfx/<name>.mov, trimmed to when it is on screen. Returns (path, start, dur)"""
    C = os.path.join(subs, "capcut"); os.makedirs(os.path.join(C, "gfx"), exist_ok=True)
    full = os.path.join(C, "gfx", "_full-%s.mov" % name)
    render_pass(os.path.join(subs, "public"), os.path.join(C, "_pass-" + name), full, group_css(ids), mov=True, drop_video=True)
    spans = alpha_spans(full)
    if not spans:
        os.remove(full); print("  %s: nothing visible, skipped" % name); return None
    a, b = max(0.0, spans[0][0] - 0.05), spans[-1][1] + 0.05
    stamp = time.strftime("%H%M%S")
    out = os.path.join(C, "gfx", "%s-%s.mov" % (name, stamp))       # a new file name each time: CapCut caches by path
    ff("-ss", "%.3f" % a, "-i", full, "-t", "%.3f" % (b - a), "-an", "-c:v", "copy", out)
    os.remove(full)
    return out, a, probe_dur(out)

# ------------------------------------------------------------------------------------------------- the page
def plain(s): return html.unescape(re.sub(r"<[^>]+>", "", s))
def read_page(pub, duration):
    """subtitle lines, hook and sounds as the render shows them"""
    page = open(os.path.join(pub, "index.html"), encoding="utf-8").read()
    lines = []
    for m in re.finditer(r'<div class="line( punch)?" id="(l\d+)"[^>]*>(.*?)</div>', page, re.S):
        lid, body = m.group(2), m.group(3)
        words = [(plain(w.group(2)), "em" in w.group(1)) for w in
                 re.finditer(r'<span class="(w[^"]*)" id="%s-w\d+">(.*?)</span>(?=\s|<span class="bar"|</span>)' % lid, body, re.S)]
        on = re.search(r"tl\.set\('#%s', \{ visibility: 'visible'[^}]*\}, ([\d.]+)\)" % lid, page)
        off = re.search(r"tl\.set\('#%s', \{ visibility: 'hidden' \}, ([\d.]+)\)" % lid, page)
        if words and on:
            lines.append(dict(words=words, punch=bool(m.group(1)), start=float(on.group(1)),
                              end=float(off.group(1)) if off else duration))
    hook = None
    hm = re.search(r'<div id="hook" style="top:(\d+)px[^"]*">(.*?)</div>\s*</div>', page, re.S)
    if hm:
        out = re.search(r"tl\.to\('#hook', \{ opacity: 0[^)]*\}, ([\d.]+)\)", page)
        rows = [[(plain(w.group(2)), "em" in w.group(1)) for w in re.finditer(r'<span class="(hk-w[^"]*)">(.*?)</span>', r)]
                for r in re.findall(r'<div class="hk-row">(.*?)(?:</div>|$)', hm.group(2), re.S)]
        hook = dict(y=int(hm.group(1)), rows=rows, end=float(out.group(1)) + 0.3 if out else 5.5)
    sounds = [dict(src=os.path.join(pub, a.group(1)), at=float(a.group(2)), dur=float(a.group(3)), vol=float(a.group(4)))
              for a in re.finditer(r'<audio id="sfx-\d+" src="([^"]+)" data-start="([\d.]+)" data-duration="([\d.]+)"[^>]*data-volume="([\d.]+)"', page)]
    return lines, hook, sounds

def graphic_ids(pub):
    page = open(os.path.join(pub, "index.html"), encoding="utf-8").read()
    els = re.findall(r'<div class="el" id="([^"]+)"', page)
    bursts = sorted(set(re.findall(r'<path id="([^"]+)-\d+" class="ray"', page)))
    return els, bursts

# ------------------------------------------------------------------------------------------------- the project
def words_markup(s):
    """'Joe *Burrow* over' -> [('Joe', False), ('Burrow', True), ('over', False)]; '/' makes a line break"""
    out = []
    for tok in s.replace("/", " / ").split():
        m = re.match(r"^\*(.+?)\*(\W*)$", tok)             # *Manziel*. -> accent, punctuation kept
        out.append(("\n", False) if tok == "/" else (m.group(1) + m.group(2), True) if m else (tok, False))
    return out
def markup_of(content):
    """CapCut rich text back to the '*accent*' markup"""
    c = json.loads(content); text = c["text"]; u16 = text.encode("utf-16-le")
    acc = [s["range"] for s in c["styles"] if tuple(round(v, 2) for v in s["fill"]["content"]["solid"]["color"][:3]) != (1.0, 1.0, 1.0)]
    out, pos = [], 0
    for part in re.split(r"( |\n)", text):
        n = len(part.encode("utf-16-le")) // 2
        if part == "\n": out.append("/")
        elif part.strip():
            out.append("*%s*" % part if any(a <= pos < b for a, b in acc) else part)
        pos += n
    return " ".join(out).replace(" / ", " / ")

class Project:
    """a CapCut project folder. Every save: CapCut must be closed, the file being replaced is snapshotted first."""
    def __init__(self, folder):
        self.folder = folder
        self.path = os.path.join(folder, "draft_content.json")
        self.d = json.load(open(self.path, encoding="utf-8"))
        self.M = self.d["materials"]

    # ---- building blocks (also used by the export)
    def extras(self, kind):
        ids = []
        for k in T["extra_refs"][kind]:
            o = copy.deepcopy(T["materials"][k]); o["id"] = uid(); self.M.setdefault(k, []).append(o); ids.append(o["id"])
        return ids
    def segment(self, kind, mat_id, start, dur, src_start=0, volume=1.0, xy=(0.0, 0.0), render_index=0, track_index=0):
        s = copy.deepcopy(T["segments"][kind]); s["id"] = uid(); s["material_id"] = mat_id
        s["target_timerange"] = {"start": start, "duration": dur}
        s["source_timerange"] = None if kind == "text" else {"start": src_start, "duration": dur}
        s["volume"] = volume; s["last_nonzero_volume"] = volume if volume > 0 else 1.0
        s["extra_material_refs"] = self.extras(kind); s["render_index"] = render_index; s["track_render_index"] = track_index
        s["keyframe_refs"] = []; s["common_keyframes"] = []
        if s.get("clip"):
            s["clip"]["scale"] = {"x": 1.0, "y": 1.0}; s["clip"]["transform"] = {"x": xy[0], "y": xy[1]}
        return s
    def add_track(self, kind, segs, flag=0, name=""):
        t = copy.deepcopy(T["tracks"][kind]); t["id"] = uid(); t["flag"] = flag; t["segments"] = segs
        t["name"] = name; t["is_default_name"] = not name
        self.d["tracks"].append(t); return t
    def video_material(self, path, w=1080, h=1920, has_audio=False):
        v = copy.deepcopy(T["materials"]["videos"]); v.update(id=uid(), path=fwd(path), material_name=os.path.basename(path),
            duration=us(probe_dur(path)), width=w, height=h, has_audio=has_audio, local_material_id=str(uuid.uuid4()))
        self.M["videos"].append(v); return v["id"]
    def audio_material(self, path, name=None):
        a = copy.deepcopy(T["materials"]["audios"]); a.update(id=uid(), path=fwd(path), name=name or os.path.basename(path),
            duration=us(probe_dur(path)), type="extract_music", music_id=str(uuid.uuid4()), local_material_id=str(uuid.uuid4()))
        self.M["audios"].append(a); return a["id"]
    def text_material(self, words, size):
        """words: [(word, accent)] with ('\\n', False) for a line break; accent words in the house yellow"""
        text, styles, pos = "", [], 0
        for i, (w, em) in enumerate(words):
            if w == "\n":
                text += "\n"; styles.append((pos, pos + 1, False)); pos += 1; continue
            if i and text and not text.endswith("\n"):
                text += " "; styles.append((pos, pos + 1, False)); pos += 1
            n = len(w.encode("utf-16-le")) // 2
            styles.append((pos, pos + n, em)); text += w; pos += n
        merged = []
        for a, b, em in styles:
            if merged and merged[-1][2] == em: merged[-1][1] = b
            else: merged.append([a, b, em])
        content = {"text": text, "styles": [{"fill": {"content": {"render_type": "solid", "solid": {"color": list(ACCENT if em else WHITE)}}},
                   "font": {"path": FONT[1], "id": FONT[0]}, "size": size, "bold": True, "useLetterColor": True, "range": [a, b]}
                   for a, b, em in merged]}
        t = copy.deepcopy(T["materials"]["texts"]); t.update(id=uid(), content=json.dumps(content, ensure_ascii=False),
            font_size=size, font_path=FONT[1], font_resource_id=FONT[0], text_color="#ffffff", alignment=1, has_shadow=False, border_color="")
        for f in t.get("fonts", []): f.update(id=uid(), resource_id=FONT[0], path=FONT[1])
        self.M["texts"].append(t); return t["id"]

    # ---- lookups
    def material(self, mid):
        for k in ("videos", "audios", "texts"):
            for m in self.M.get(k, []):
                if m["id"] == mid: return k, m
        return None, None
    def segments(self):
        for ti, t in enumerate(self.d["tracks"]):
            for s in t["segments"]:
                yield ti, t, s
    def role(self, s, manifest=None):
        """what a clip is, in the creator's words: 'shot 3', 'graphic joe-card', 'subtitle "I knew Joe"', 'sfx thud.wav', 'music'"""
        kind, m = self.material(s["material_id"])
        man = manifest or {}
        if kind == "texts":
            txt = json.loads(m["content"])["text"].replace("\n", " / ")
            return ("hook" if man.get("hook_text") and txt == man["hook_text"] else "text") + ' "%s"' % txt
        if kind == "videos":
            p = m["path"]
            for g, info in man.get("groups", {}).items():
                if os.path.basename(p).startswith(g + "-"): return "graphic " + g
            if p == man.get("footage"): return "footage"
            return "video " + os.path.basename(p)
        if kind == "audios":
            return "music" if m["path"] == man.get("bed") else "sfx " + os.path.basename(m["path"])
        return "clip"
    def end(self):
        return max([s["target_timerange"]["start"] + s["target_timerange"]["duration"] for _, _, s in self.segments()] or [0])

    # ---- save
    def save(self, snapshot_dir, label):
        require_closed()
        self.d["duration"] = self.end()
        os.makedirs(snapshot_dir, exist_ok=True)
        n = len([f for f in os.listdir(snapshot_dir) if f.endswith(".json")])
        shutil.copy(self.path, os.path.join(snapshot_dir, "%03d-before-%s.json" % (n, label)))
        body = json.dumps(self.d, ensure_ascii=False)
        targets = [self.path]
        pj = os.path.join(self.folder, "Timelines", "project.json")
        if os.path.exists(pj):
            tl = json.load(open(pj, encoding="utf-8"))["main_timeline_id"]
            targets.append(os.path.join(self.folder, "Timelines", tl, "draft_content.json"))
        for p in targets:
            tmp = p + ".tmp"; open(tmp, "w", encoding="utf-8").write(body); os.replace(tmp, p)
        open(os.path.join(snapshot_dir, "%03d-%s.json" % (n + 1, label)), "w", encoding="utf-8").write(body)
        self._touch_meta()
    def _touch_meta(self):
        now = int(time.time() * US); dur = self.d["duration"]
        mp = os.path.join(self.folder, "draft_meta_info.json")
        if os.path.exists(mp):
            m = json.load(open(mp, encoding="utf-8")); m.update(tm_draft_modified=now, tm_duration=dur)
            json.dump(m, open(mp, "w", encoding="utf-8"), ensure_ascii=False)
        rm = os.path.join(os.path.dirname(self.folder), "root_meta_info.json")
        if os.path.exists(rm):
            r = json.load(open(rm, encoding="utf-8"))
            for e in r.get("all_draft_store", []):
                if os.path.normcase(os.path.normpath(e.get("draft_fold_path", ""))) == os.path.normcase(os.path.normpath(self.folder)):
                    e.update(tm_draft_modified=now, tm_duration=dur)
            json.dump(r, open(rm, "w", encoding="utf-8"), ensure_ascii=False)

def load_manifest(subs):
    p = os.path.join(subs, "capcut", "manifest.json")
    if not os.path.exists(p): sys.exit("no CapCut export for %s yet: run capcut_export.py first" % subs)
    return json.load(open(p, encoding="utf-8"))
def save_manifest(subs, man):
    json.dump(man, open(os.path.join(subs, "capcut", "manifest.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
def last_snapshot(subs):
    d = os.path.join(subs, "capcut", "snapshots")
    snaps = sorted(f for f in os.listdir(d) if f.endswith(".json") and "-before-" not in f)
    return os.path.join(d, snaps[-1])
