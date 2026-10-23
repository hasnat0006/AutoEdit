#!/usr/bin/env python3
"""capcut_export.py: a finished pro-shorts Short -> an editable CapCut project the creator and Claude both work on.

Layers (bottom to top):
  V1  footage with the camera moves, flashes and transitions baked in, cut at every shot change, voice on the clips
  V2+ one transparent clip per graphic idea (groups from <subs>/capcut-groups.json), each its own file
  T   hook text and subtitles as real CapCut text, one clip per caption line, accent words in yellow
  A   the music bed at the measured level, every sound effect its own clip at its volume

Writes <subs>/capcut/manifest.json (what each file is) and snapshot 001, the baseline that capcut_changes.py
compares the creator's edits against. CapCut must be closed.

Usage: python capcut_export.py --subs videos/<ep>/mNN/subs --name <ep>-NN-<slug>-vN [--rerender]
"""
import argparse, json, os, re, shutil, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capcut_lib as L

ap = argparse.ArgumentParser()
ap.add_argument("--subs", required=True)
ap.add_argument("--name", required=True)
ap.add_argument("--root", default=L.ROOT, help="CapCut drafts folder")
ap.add_argument("--bed-under", type=float, default=18.0, help="dB the music sits under the voice")
ap.add_argument("--sub-size", type=float, default=L.SUB_SIZE)
ap.add_argument("--hook-size", type=float, default=L.HOOK_SIZE)
ap.add_argument("--rerender", action="store_true", help="render the layers again even if they are newer than the page")
args = ap.parse_args()

S = os.path.abspath(args.subs); C = os.path.join(S, "capcut"); PUB = os.path.join(S, "public")
proj_dir = os.path.join(args.root, args.name)
if os.path.exists(proj_dir): sys.exit("a CapCut project named %s already exists: pick another --name" % args.name)
L.require_closed()
os.makedirs(C, exist_ok=True)
win = json.load(open(os.path.join(S, "window.json")))
DUR = L.us(win["duration"])
page_time = os.path.getmtime(os.path.join(PUB, "index.html"))
fresh = lambda f: os.path.exists(f) and os.path.getmtime(f) > page_time and not args.rerender

# ---------------------------------------------------------------- groups: one CapCut clip per graphic idea
els, bursts = L.graphic_ids(PUB)
gp = os.path.join(S, "capcut-groups.json")
if os.path.exists(gp):
    groups = json.load(open(gp, encoding="utf-8"))
else:
    groups = {e: [e] for e in els}
    print("no capcut-groups.json: one clip per element (%d). Write the file to group them by idea." % len(els))
for b in bursts:                                   # a burst belongs to the element it fires from (bTb -> Tb)
    if not any(b in ids for ids in groups.values()):
        owner = next((g for g, ids in groups.items() if b[1:] in ids), None) or \
                next((g for g, ids in groups.items() if any(re.fullmatch(re.escape(b[1:]) + r"\d+", i) for i in ids)), None)   # bTm -> Tm0, Tm1 (type_beat)
        if owner: groups[owner].append(b)
        else: print("burst %s belongs to no group: add it to capcut-groups.json" % b)
missing = [e for e in els if not any(e in ids for ids in groups.values())]
if missing: sys.exit("graphics not in any group: %s" % ", ".join(missing))

# ---------------------------------------------------------------- layer renders
raw = os.path.join(C, "footage-raw.mp4")
if fresh(raw): print("reusing footage-raw.mp4")
else:
    print("rendering the footage layer (~2 min per 18 s)")
    L.render_pass(PUB, os.path.join(C, "_pass-footage"), raw, L.FOOTAGE_CSS)
footage = os.path.join(C, "footage.mp4")       # the voice levelled to -14 LUFS, muxed so every cut carries its words
L.ff("-i", raw, "-i", os.path.join(S, "edit.mp4"), "-map", "0:v", "-map", "1:a", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
     "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest", footage)
gfx = {}
old = {}
if os.path.exists(os.path.join(C, "manifest.json")):
    old = json.load(open(os.path.join(C, "manifest.json"), encoding="utf-8")).get("groups", {})
for g, ids in groups.items():
    o = old.get(g)
    if o and o.get("ids") == ids and fresh(o.get("file", "")):
        print("reusing graphic", g); gfx[g] = o; continue
    print("rendering graphic %s (%s)" % (g, ", ".join(ids)))
    r = L.render_group(S, g, ids)
    if r: gfx[g] = dict(ids=ids, file=r[0], start=r[1], dur=r[2])

# ---------------------------------------------------------------- the project
lines, hook, sounds = L.read_page(PUB, win["duration"])
os.makedirs(os.path.join(proj_dir, "Timelines"))
tl_id = L.uid(); draft_id = L.uid()
P = L.Project.__new__(L.Project)
P.folder = proj_dir; P.path = os.path.join(proj_dir, "draft_content.json")
P.d = json.loads(json.dumps(L.T["draft"])); P.M = P.d["materials"]
P.d.update(id=tl_id, duration=DUR, fps=30.0, name="")
P.d["canvas_config"] = {"ratio": "9:16", "width": 1080, "height": 1920, "background": None}
P.d["config"]["subtitle_taskinfo"] = []

ti = 0
fid = P.video_material(footage, has_audio=True)
cuts = [0.0] + [t for t in win["shots"] if 0 < t < win["duration"]] + [win["duration"]]
P.add_track("video", [P.segment("video", fid, L.us(a), L.us(b) - L.us(a), src_start=L.us(a), track_index=ti)
                      for a, b in zip(cuts, cuts[1:])], name="Footage"); ti += 1
# graphics: as few overlay tracks as never overlap, in the order they appear
lanes = []
for g, info in sorted(gfx.items(), key=lambda kv: kv[1]["start"]):
    a, d = L.us(info["start"]), L.us(info["dur"])
    lane = next((l for l in lanes if l[-1][0] + l[-1][1] <= a), None)
    if lane is None: lane = []; lanes.append(lane)
    lane.append((a, d, g))
for li, lane in enumerate(lanes):
    segs = [P.segment("video", P.video_material(gfx[g]["file"]), a, d, volume=0.0, render_index=1 + li, track_index=ti) for a, d, g in lane]
    P.add_track("video", segs, flag=2, name="Graphics %d" % (li + 1)); ti += 1
hook_text = None
if hook:
    words = []
    for ri, row in enumerate(hook["rows"]):
        if ri: words.append(("\n", False))
        words += row
    mid = P.text_material(words, args.hook_size)
    hook_text = json.loads(P.M["texts"][-1]["content"])["text"].replace("\n", " / ")
    P.add_track("text", [P.segment("text", mid, 0, L.us(hook["end"]), xy=(0.0, L.y_of(hook["y"])), render_index=14000, track_index=ti)], name="Hook"); ti += 1
P.add_track("text", [P.segment("text", P.text_material(l["words"], args.sub_size * (1.2 if l["punch"] else 1.0)), L.us(l["start"]),
                               L.us(l["end"]) - L.us(l["start"]), xy=(0.0, L.y_of(L.SUB_Y)), render_index=14001, track_index=ti)
                     for l in lines if l["end"] > l["start"]], name="Subtitles"); ti += 1
bed = os.path.join(S, "bed.wav"); bed_vol = None
if os.path.exists(bed):
    bed_vol = 10 ** ((L.rms_db(L.pcm(footage)) - args.bed_under - L.rms_db(L.pcm(bed))) / 20)
    bid = P.audio_material(bed, "music bed")
    P.add_track("audio", [P.segment("audio", bid, 0, min(DUR, L.us(L.probe_dur(bed))), volume=bed_vol, track_index=ti)], name="Music"); ti += 1
    print("music bed volume %.3f (%+.1f dB): %.0f dB under the voice" % (bed_vol, L.db(bed_vol), args.bed_under))
lanes = []
for s in sorted(sounds, key=lambda s: s["at"]):
    a = L.us(s["at"]); d = min(L.us(s["dur"]), L.us(L.probe_dur(s["src"])))
    lane = next((l for l in lanes if l[-1]["target_timerange"]["start"] + l[-1]["target_timerange"]["duration"] <= a), None)
    if lane is None: lane = []; lanes.append(lane)
    lane.append(P.segment("audio", P.audio_material(s["src"]), a, d, volume=s["vol"]))
for li, lane in enumerate(lanes):
    for s in lane: s["track_render_index"] = ti
    P.add_track("audio", lane, name="SFX %d" % (li + 1)); ti += 1

# ---------------------------------------------------------------- folder, media panel, registration
os.makedirs(os.path.join(proj_dir, "Timelines", tl_id))
body = json.dumps(P.d, ensure_ascii=False)
for p in (P.path, os.path.join(proj_dir, "Timelines", tl_id, "draft_content.json")):
    open(p, "w", encoding="utf-8").write(body)
cover = os.path.join(proj_dir, "draft_cover.jpg")
L.ff("-ss", "1", "-i", raw, "-frames:v", "1", "-vf", "scale=360:-2", cover)
shutil.copy(cover, os.path.join(proj_dir, "Timelines", tl_id, "draft_cover.jpg"))
now = int(time.time() * L.US)
project = json.loads(json.dumps(L.T["project"])); project.update(id=L.uid(), main_timeline_id=tl_id, create_time=now, update_time=now)
project["timelines"] = [{"create_time": now, "id": tl_id, "is_marked_delete": False, "name": "Timeline 01", "update_time": now}]
json.dump(project, open(os.path.join(proj_dir, "Timelines", "project.json"), "w", encoding="utf-8"))
layout = json.loads(json.dumps(L.T["layout"])); layout["dockItems"][0]["timelineIds"] = [tl_id]
json.dump(layout, open(os.path.join(proj_dir, "timeline_layout.json"), "w", encoding="utf-8"))
panel = []
for k, kind in (("videos", "video"), ("audios", "music")):
    for m in P.M[k]:
        if any(x["file_Path"] == m["path"] for x in panel): continue
        panel.append({"ai_group_type": "", "create_time": now // L.US, "duration": m["duration"], "enter_from": 0,
                      "extra_info": os.path.basename(m["path"]), "file_Path": m["path"], "height": m.get("height", 0), "id": L.uid().lower(),
                      "import_time": now // L.US, "import_time_ms": now, "item_source": 1, "material_color_tag": "", "md5": "",
                      "metetype": kind, "roughcut_time_range": {"duration": m["duration"], "start": 0},
                      "sub_time_range": {"duration": -1, "start": -1}, "type": 0, "width": m.get("width", 0)})
root_fwd = L.fwd(args.root)
meta = json.loads(json.dumps(L.T["meta"]))
meta.update(draft_id=draft_id, draft_name=args.name, draft_fold_path=root_fwd + "/" + args.name, draft_root_path=root_fwd,
            draft_cover="draft_cover.jpg", tm_draft_create=now, tm_draft_modified=now, tm_duration=DUR,
            draft_timeline_materials_size_=0, draft_materials_copied_info=[], draft_segment_extra_info=[])
meta["draft_materials"] = [{"type": g["type"], "value": panel if g["type"] == 0 else []} for g in L.T["meta"]["draft_materials"]]
json.dump(meta, open(os.path.join(proj_dir, "draft_meta_info.json"), "w", encoding="utf-8"), ensure_ascii=False)
rm = os.path.join(args.root, "root_meta_info.json")
root = json.load(open(rm, encoding="utf-8"))
shutil.copy(rm, os.path.join(C, "root_meta_info.before-%s.json" % args.name))
e = json.loads(json.dumps(L.T["root_entry"]))
e.update(draft_id=draft_id, draft_name=args.name, draft_fold_path=root_fwd + "/" + args.name, draft_root_path=root_fwd,
         draft_cover=root_fwd + "/" + args.name + "\\draft_cover.jpg", draft_json_file=root_fwd + "/" + args.name + "\\draft_content.json",
         tm_draft_create=now, tm_draft_modified=now, tm_duration=DUR, draft_timeline_materials_size=0)
root["all_draft_store"].insert(0, e); root["draft_ids"] = root.get("draft_ids", 0) + 1
json.dump(root, open(rm, "w", encoding="utf-8"), ensure_ascii=False)

snaps = os.path.join(C, "snapshots"); shutil.rmtree(snaps, ignore_errors=True); os.makedirs(snaps)
open(os.path.join(snaps, "001-export.json"), "w", encoding="utf-8").write(body)
L.save_manifest(S, dict(project=proj_dir, name=args.name, footage=L.fwd(footage), bed=L.fwd(bed) if bed_vol else None,
                        hook_text=hook_text, groups={g: dict(v, file=L.fwd(v["file"])) for g, v in gfx.items()},
                        exported=time.strftime("%Y-%m-%d %H:%M")))
print("CapCut project:", proj_dir)
print("tracks:", ", ".join("%s(%d)" % (t["name"] or t["type"], len(t["segments"])) for t in P.d["tracks"]))
for g, v in sorted(gfx.items(), key=lambda kv: kv[1]["start"]):
    print("  graphic %-16s %5.2f-%5.2f s" % (g, v["start"], v["start"] + v["dur"]))
