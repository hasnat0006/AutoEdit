#!/usr/bin/env python3
"""capcut_changes.py: what the creator changed in CapCut since Claude last wrote the project.

Compares the project on disk with the newest snapshot (what capcut_export / capcut_edit wrote) clip by clip and
prints the changes in plain words: moved, trimmed, deleted, added, volume, text, position, size, effects. Writes
<subs>/capcut/changes-<n>.json too. Read this before every round of edits: the creator's changes are the base,
never overwrite them; recurring ones are style notes (pro-shorts "Keep it learning").

Usage: python capcut_changes.py --subs videos/<ep>/mNN/subs
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capcut_lib as L

ap = argparse.ArgumentParser()
ap.add_argument("--subs", required=True)
args = ap.parse_args()
S = os.path.abspath(args.subs)
man = L.load_manifest(S)
if L.capcut_running():
    print("note: CapCut is open; unsaved changes are not on disk yet (save, or close it, then run this again)")
cur = L.Project(man["project"])
base = L.Project.__new__(L.Project); base.folder = cur.folder; base.path = L.last_snapshot(S)
base.d = json.load(open(base.path, encoding="utf-8")); base.M = base.d["materials"]

def info(P, ti, t, s):
    kind, m = P.material(s["material_id"])
    tr, sr = s["target_timerange"], s.get("source_timerange") or {}
    clip = s.get("clip") or {}
    return dict(id=s["id"], track=t.get("name") or "%s %d" % (t["type"], ti + 1), role=P.role(s, man),
                start=L.sec(tr["start"]), dur=L.sec(tr["duration"]), src=L.sec(sr.get("start", 0)),
                vol=s.get("volume", 1.0), speed=s.get("speed", 1.0), visible=s.get("visible", True),
                x=(clip.get("transform") or {}).get("x"), y=(clip.get("transform") or {}).get("y"),
                scale=(clip.get("scale") or {}).get("x"), rot=clip.get("rotation"), alpha=clip.get("alpha"),
                text=L.markup_of(m["content"]) if kind == "texts" else None, path=m["path"] if m and "path" in m else None,
                keyframes=len(s.get("common_keyframes") or []) + len(s.get("keyframe_refs") or []),
                size=json.loads(m["content"])["styles"][0].get("size") if kind == "texts" else None)
a = {s["id"]: info(base, ti, t, s) for ti, t, s in base.segments()}
b = {s["id"]: info(cur, ti, t, s) for ti, t, s in cur.segments()}

# CapCut normally keeps clip ids; when it does not, pair leftovers by what they are and where they sit
gone = [i for i in a if i not in b]; new = [i for i in b if i not in a]
for i in list(gone):
    cands = [j for j in new if b[j]["role"] == a[i]["role"] or (a[i]["path"] and b[j]["path"] == a[i]["path"])]
    if cands:
        j = min(cands, key=lambda j: abs(b[j]["start"] - a[i]["start"]))
        b[i] = b.pop(j); gone.remove(i); new.remove(j)

f2 = lambda v: "%.2f s" % v
changes = []
def note(kind, who, what, **kw): changes.append(dict(kind=kind, clip=who, what=what, **kw))
for i, x in a.items():
    who = "%s (%s, at %.2f s)" % (x["role"], x["track"], x["start"])
    if i in gone:
        note("deleted", who, "deleted"); continue
    y = b[i]
    if abs(y["start"] - x["start"]) > 0.02 and abs(y["dur"] - x["dur"]) <= 0.02:
        note("moved", who, "moved %+.2f s to %s" % (y["start"] - x["start"], f2(y["start"])), by=y["start"] - x["start"])
    elif abs(y["dur"] - x["dur"]) > 0.02 or abs(y["start"] - x["start"]) > 0.02:
        note("trimmed", who, "now %s-%s (was %s-%s)" % (f2(y["start"]), f2(y["start"] + y["dur"]), f2(x["start"]), f2(x["start"] + x["dur"])),
             start=y["start"], end=y["start"] + y["dur"])
    if y["track"] != x["track"]: note("track", who, "moved to track %s" % y["track"])
    if abs(y["vol"] - x["vol"]) > 0.005:
        note("volume", who, "volume %+.1f dB (now %.0f%%, was %.0f%%)" % (L.db(y["vol"]) - L.db(x["vol"]), y["vol"] * 100, x["vol"] * 100), value=y["vol"])
    if y["text"] != x["text"]: note("text", who, "text now \"%s\" (was \"%s\")" % (y["text"], x["text"]), text=y["text"])
    if y["size"] != x["size"] and y["size"] is not None: note("size", who, "font size %s (was %s)" % (y["size"], x["size"]), size=y["size"])
    for k, label in (("x", "x"), ("y", "y")):
        if y[k] is not None and x[k] is not None and abs(y[k] - x[k]) > 0.005:
            px = (y[k] - x[k]) * (540 if k == "x" else -960)
            way = ("right" if px > 0 else "left") if k == "x" else ("down" if px > 0 else "up")
            note("position", who, "moved %s %.0f px" % (way, abs(px)), axis=k, px=px)
    if y["scale"] and x["scale"] and abs(y["scale"] - x["scale"]) > 0.005: note("scale", who, "scale %.0f%% (was %.0f%%)" % (y["scale"] * 100, x["scale"] * 100))
    if y["rot"] != x["rot"]: note("rotation", who, "rotated to %s deg" % y["rot"])
    if y["alpha"] != x["alpha"]: note("opacity", who, "opacity %.0f%%" % ((y["alpha"] or 0) * 100))
    if y["speed"] != x["speed"]: note("speed", who, "speed %.2fx" % y["speed"])
    if y["visible"] != x["visible"]: note("hidden" if not y["visible"] else "shown", who, "hidden" if not y["visible"] else "shown again")
    if y["keyframes"] != x["keyframes"]: note("keyframes", who, "keyframes %d (was %d)" % (y["keyframes"], x["keyframes"]))
for j in new:
    y = b[j]; note("added", "%s (%s)" % (y["role"], y["track"]), "added at %s-%s" % (f2(y["start"]), f2(y["start"] + y["dur"])),
                   path=y["path"], text=y["text"], start=y["start"], end=y["start"] + y["dur"])
for k in sorted(set(cur.M) | set(base.M)):
    na, nb = len(base.M.get(k) or []) if isinstance(base.M.get(k), list) else 0, len(cur.M.get(k) or []) if isinstance(cur.M.get(k), list) else 0
    if k in ("effects", "video_effects", "filters", "transitions", "stickers", "material_animations", "adjusts", "masks") and nb > na:
        anim = k == "material_animations" and any(m.get("animations") for m in cur.M[k])
        if k != "material_animations" or anim:
            note("added", k, "%d new %s" % (nb - na, k.replace("_", " ")))
if abs(L.sec(cur.d["duration"]) - L.sec(base.d["duration"])) > 0.02:
    note("length", "project", "length %.2f s (was %.2f s)" % (L.sec(cur.d["duration"]), L.sec(base.d["duration"])))

print("CapCut project %s, compared with %s" % (man["name"], os.path.basename(base.path)))
if not changes: print("no changes since Claude last wrote it")
for c in changes: print("- %-8s %s: %s" % (c["kind"], c["clip"], c["what"]))
n = len([f for f in os.listdir(os.path.join(S, "capcut")) if f.startswith("changes-")]) + 1
json.dump(changes, open(os.path.join(S, "capcut", "changes-%d.json" % n), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
