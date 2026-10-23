#!/usr/bin/env python3
"""capcut_edit.py: Claude's changes, applied on top of the creator's latest CapCut project.

Takes a list of operations (JSON file or inline), works on the project exactly as the creator last saved it, and
saves only when every operation applied (CapCut closed, the replaced file snapshotted, so any round can be undone).

Selectors ("what"):
  footage@12.3   the footage clip playing at 12.3 s       shot:3      the 3rd footage clip
  graphic:joe-card                                         music       the music bed
  sfx@8.24       the sound starting nearest 8.24 s       sfx:thud@8.24   only thud sounds
  sub@12.3       the subtitle on screen at 12.3 s         sub~monsale   the subtitle containing that text
  hook           the hook text                            id:<clip id>  one clip (ids from capcut_changes.py)
  all-sfx / all-subs / all-graphics                       every clip of that kind

Operations (times in seconds on the timeline, as the creator sees it now):
  {"op":"text", "what":"sub~monsale", "text":"Joe was in bed at *10*"}       *word* = accent yellow, / = line break
  {"op":"style", "what":"all-subs", "size":12, "y":1400}                       font size, centre height in px
  {"op":"volume", "what":"music", "db":-3}   relative;  "set_db":-20  or  "value":0.1  absolute
  {"op":"delete", "what":"graphic:checklist"}
  {"op":"move", "what":"sfx@8.24", "by":0.1}   or  "to":8.4
  {"op":"trim", "what":"graphic:ten-beers", "start":7.0, "end":9.0}           either end
  {"op":"remove_range", "start":20.1, "end":21.4}     cut a stretch out of every track and close the gap
  {"op":"add_sfx", "file":"videos/_shared/sfx/pop.wav", "at":12.3, "volume":0.25}
  {"op":"add_text", "text":"*LSU* 2019", "start":12, "end":14, "y":500, "size":14}
  {"op":"regraphic", "group":"joe-card"}     re-render one graphic from the rebuilt page and swap it in place

Usage: python capcut_edit.py --subs videos/<ep>/mNN/subs --ops ops.json   (or --op '{"op":...}' repeated)
"""
import argparse, copy, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capcut_lib as L

ap = argparse.ArgumentParser()
ap.add_argument("--subs", required=True)
ap.add_argument("--ops", help="JSON file with a list of operations")
ap.add_argument("--op", action="append", default=[], help="one operation as inline JSON (repeatable)")
ap.add_argument("--label", default="edit")
args = ap.parse_args()
S = os.path.abspath(args.subs)
man = L.load_manifest(S)
L.require_closed()
ops = (json.load(open(args.ops, encoding="utf-8")) if args.ops else []) + [json.loads(o) for o in args.op]
if not ops: sys.exit("no operations")
P = L.Project(man["project"])

KIND = {"video": "video", "audio": "audio", "text": "text"}
def tr(s): return s["target_timerange"]
def s_start(s): return L.sec(tr(s)["start"])
def s_end(s): return L.sec(tr(s)["start"] + tr(s)["duration"])
def all_with(pred):
    return [(t, s) for _, t, s in P.segments() if pred(t, s, P.role(s, man))]

def select(what):
    w = what.strip()
    if w.startswith("id:"): return all_with(lambda t, s, r: s["id"] == w[3:])
    if w == "music": return all_with(lambda t, s, r: r == "music")
    if w == "hook": return all_with(lambda t, s, r: r.startswith("hook"))
    if w == "all-sfx": return all_with(lambda t, s, r: r.startswith("sfx"))
    if w == "all-subs": return all_with(lambda t, s, r: r.startswith("text") and t.get("name") == "Subtitles")
    if w == "all-graphics": return all_with(lambda t, s, r: r.startswith("graphic"))
    if w.startswith("graphic:"): return all_with(lambda t, s, r: r == "graphic " + w[8:])
    if w.startswith("shot:"):
        shots = sorted(all_with(lambda t, s, r: r == "footage"), key=lambda ts: tr(ts[1])["start"])
        n = int(w[5:]); return [shots[n - 1]] if 0 < n <= len(shots) else []
    m = re.match(r"(footage|sub|text)@([\d.]+)$", w)
    if m:
        t0 = float(m.group(2)); want = {"footage": "footage", "sub": "text", "text": "text"}[m.group(1)]
        hits = all_with(lambda t, s, r: r.startswith(want) and s_start(s) <= t0 < s_end(s)
                        and (m.group(1) != "sub" or t.get("name") == "Subtitles"))
        return hits[:1]
    if w.startswith("sub~"):
        q = w[4:].lower(); return all_with(lambda t, s, r: r.startswith("text") and q in r.lower())
    m = re.match(r"sfx(?::([^@]+))?@([\d.]+)$", w)
    if m:
        name, t0 = m.group(1), float(m.group(2))
        hits = all_with(lambda t, s, r: r.startswith("sfx") and (not name or name in r) and abs(s_start(s) - t0) < 0.35)
        return sorted(hits, key=lambda ts: abs(s_start(ts[1]) - t0))[:1]
    sys.exit("unknown selector: " + what)
def need(what):
    hits = select(what)
    if not hits: sys.exit("nothing matches %r (run capcut_changes.py to see what is in the project)" % what)
    return hits

def text_mat(s): return P.material(s["material_id"])[1]
def set_text(s, markup, size=None):
    m = text_mat(s); c = json.loads(m["content"])
    size = size or c["styles"][0].get("size", L.SUB_SIZE)
    new_id = P.text_material(L.words_markup(markup), size)
    new = P.M["texts"].pop(); new["id"] = m["id"]           # keep the creator's material (its other settings) in place
    for k in ("content", "font_size"): m[k] = new[k]
def trim(t, s, start=None, end=None):
    a, b = s_start(s), s_end(s)
    start = a if start is None else start; end = b if end is None else end
    if end - start < 0.04: return False
    if t["type"] != "text" and s.get("source_timerange"):
        sp = s.get("speed", 1.0) or 1.0
        s["source_timerange"]["start"] += L.us((start - a) * sp)
        s["source_timerange"]["duration"] = L.us((end - start) * sp)
    tr(s)["start"] = L.us(start); tr(s)["duration"] = L.us(end - start)
    return True
def free_track(ttype, a, b, prefer=None):
    """a track of this type with nothing between a and b (the named one first), or a new one"""
    tracks = [t for t in P.d["tracks"] if t["type"] == ttype]
    tracks.sort(key=lambda t: t.get("name") != prefer)
    for t in tracks:
        if prefer and t.get("name", "").split(" ")[0] != prefer.split(" ")[0]: continue
        if all(s_end(s) <= a or s_start(s) >= b for s in t["segments"]): return t
    return P.add_track(ttype, [], name=prefer or "")

done = []
for op in ops:
    o = op["op"]
    if o == "text":
        for t, s in need(op["what"]): set_text(s, op["text"])
    elif o == "style":
        for t, s in need(op["what"]):
            if "size" in op:
                m = text_mat(s); c = json.loads(m["content"])
                for st in c["styles"]: st["size"] = op["size"]
                m["content"] = json.dumps(c, ensure_ascii=False); m["font_size"] = op["size"]
            if "y" in op: s["clip"]["transform"]["y"] = L.y_of(op["y"])
            if "x" in op: s["clip"]["transform"]["x"] = (op["x"] - 540) / 540.0
    elif o == "volume":
        for t, s in need(op["what"]):
            v = s.get("volume", 1.0)
            if "value" in op: v = op["value"]
            elif "set_db" in op: v = 10 ** (op["set_db"] / 20)
            else: v = v * 10 ** (op["db"] / 20)
            s["volume"] = v; s["last_nonzero_volume"] = v if v > 0 else s.get("last_nonzero_volume", 1.0)
    elif o == "delete":
        for t, s in need(op["what"]): t["segments"].remove(s)
    elif o == "move":
        for t, s in need(op["what"]):
            to = op["to"] if "to" in op else s_start(s) + op["by"]
            tr(s)["start"] = L.us(max(0.0, to))
            if any(x is not s and s_start(x) < s_end(s) and s_end(x) > s_start(s) for x in t["segments"]):
                t["segments"].remove(s); free_track(t["type"], s_start(s), s_end(s), t.get("name")).setdefault("segments", []).append(s)
    elif o == "trim":
        for t, s in need(op["what"]):
            if not trim(t, s, op.get("start"), op.get("end")): sys.exit("trim would leave %s empty" % op["what"])
    elif o == "remove_range":
        a, b = float(op["start"]), float(op["end"]); gap = b - a
        for t in P.d["tracks"]:
            keep = []
            for s in t["segments"]:
                x, y = s_start(s), s_end(s)
                if y <= a: keep.append(s)
                elif x >= b: tr(s)["start"] -= L.us(gap); keep.append(s)
                elif x >= a and y <= b: continue
                elif x < a and y <= b: trim(t, s, x, a); keep.append(s)
                elif x >= a and y > b: trim(t, s, b, y); tr(s)["start"] = L.us(a); keep.append(s)
                else:                                            # spans the whole cut
                    if t["type"] == "text":
                        tr(s)["duration"] -= L.us(gap); keep.append(s); continue
                    tail = copy.deepcopy(s); tail["id"] = L.uid(); tail["extra_material_refs"] = P.extras(KIND[t["type"]])
                    trim(t, s, x, a); trim(t, tail, b, y); tr(tail)["start"] = L.us(a); keep += [s, tail]
            t["segments"] = sorted(keep, key=lambda s: tr(s)["start"])
    elif o == "add_sfx":
        path = os.path.abspath(op["file"]); a = float(op["at"])
        d = min(op.get("dur", 99), L.probe_dur(path))
        seg = P.segment("audio", P.audio_material(path), L.us(a), L.us(d), volume=op.get("volume", 0.25))
        free_track("audio", a, a + d, "SFX 1")["segments"].append(seg)
    elif o == "add_text":
        a, b = float(op["start"]), float(op["end"])
        seg = P.segment("text", P.text_material(L.words_markup(op["text"]), op.get("size", L.SUB_SIZE)), L.us(a), L.us(b - a),
                        xy=(0.0, L.y_of(op.get("y", L.SUB_Y))), render_index=14002)
        free_track("text", a, b, "Text" if op.get("y", L.SUB_Y) != L.SUB_Y else "Subtitles")["segments"].append(seg)
    elif o == "regraphic":
        g = op["group"]; old = man["groups"].get(g)
        ids = op.get("ids") or (old or {}).get("ids") or sys.exit("unknown graphic group " + g)
        print("re-rendering graphic", g)
        r = L.render_group(S, g, ids)
        if not r: sys.exit("graphic %s renders empty" % g)
        path, start, dur = r
        hits = select("graphic:" + g)
        delta = (s_start(hits[0][1]) - old["start"]) if hits and old else 0.0     # keep where the creator moved it
        mid = P.video_material(path)
        if hits:
            for t, s in hits: t["segments"].remove(s)
        seg = P.segment("video", mid, L.us(start + delta), L.us(dur), volume=0.0, render_index=1)
        gt = free_track("video", start + delta, start + delta + dur, "Graphics 1"); gt["flag"] = 2; gt["segments"].append(seg)
        man["groups"][g] = dict(ids=ids, file=L.fwd(path), start=start, dur=dur)
    else:
        sys.exit("unknown op " + o)
    done.append(o)

for t in P.d["tracks"]: t["segments"].sort(key=lambda s: tr(s)["start"])
P.save(os.path.join(S, "capcut", "snapshots"), args.label)
L.save_manifest(S, man)
print("applied %d change(s): %s. Project saved; open it in CapCut." % (len(done), ", ".join(done)))
