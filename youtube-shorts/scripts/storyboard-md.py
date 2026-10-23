#!/usr/bin/env python3
"""storyboard-md.py: render the delivery STORYBOARD.md (time / beat / what is on screen) from one or more
storyboard.json files, so the review document is generated from the same source the composition is built from.

Usage: python3 storyboard-md.py --title "Hook v2" --note "what changed" --project videos/<p>/C0001:01-hook:"Part 1" ... --out videos/<p>/STORYBOARD.md
"""
import argparse, json, os

ap = argparse.ArgumentParser()
ap.add_argument("--title", required=True)
ap.add_argument("--note", action="append", default=[])
ap.add_argument("--concern", action="append", default=[])
ap.add_argument("--project", action="append", required=True, help="<dir>:<slug>:<title>")
ap.add_argument("--out", required=True)
args = ap.parse_args()

WHAT = {"text": lambda b: "headline (%s%s)" % (b.get("pos", "top"), ", first frame" if float(b["in"]) <= 0.05 else ""),
        "chip": lambda b: "punchline chip", "logo": lambda b: "logo card%s" % (" + pop" if b.get("pop") is not None else ""),
        "list": lambda b: "glass list card", "stat": lambda b: "count-up number",
        "image": lambda b: "image %s" % ("full frame" if b.get("frame") == "full" else "card"), "clip": lambda b: "full-frame cutaway",
        "split": lambda b: "split screen (media top, you below)", "cta": lambda b: "follow pill", "vignette": lambda b: "vignette + grain (deadpan)"}
def text_of(b):
    if b.get("text"): return b["text"]
    if b.get("value") is not None: return "%s%s%s %s" % (b.get("prefix", ""), "{:,}".format(b["value"]), b.get("suffix", ""), b.get("label", ""))
    if b.get("label"): return b["label"]
    if b.get("items"): return ((b.get("eyebrow") + ": ") if b.get("eyebrow") else "") + ", ".join(i[0] for i in b["items"])
    if b.get("src"): return os.path.basename(b["src"])
    return ""

out = ["# " + args.title, ""]
if args.note:
    out += ["## What changed", ""] + ["- " + n for n in args.note] + [""]
if args.concern:
    out += ["## Concerns to check", ""] + ["- " + c for c in args.concern] + [""]
for spec in args.project:
    d, slug, title = spec.split(":", 2)
    s = json.load(open(os.path.join(d, "storyboard.json"), encoding="utf-8"))
    out += ["## %s: %s (%s, %.1f s)" % (slug, title, s["id"], float(s["duration"])), "", "| Time | Beat | On screen |", "|---|---|---|"]
    if s.get("captions"):
        c = s["captions"]; out.append("| 0.0 - %.1f | captions | up to %s words at a time, %s%s |" % (float(s["duration"]), c.get("max_words", 3),
                                      c.get("style", "karaoke"), ", off %s" % c["off"] if c.get("off") else ""))
    for b in s.get("beats", []):
        out.append("| %.1f - %.1f | %s | %s |" % (b["in"], b["out"], WHAT.get(b["type"], lambda b: b["type"])(b), text_of(b)))
    moves = [op for op in s.get("camera", []) if op[0] != "set"]
    out.append("| camera | %d moves | %s |" % (len(moves), ", ".join("%s %.1f" % (op[0], float(op[1])) for op in moves)))
    out.append("")
open(args.out, "w", encoding="utf-8").write("\n".join(out))
print("wrote", args.out, len(out), "lines")
