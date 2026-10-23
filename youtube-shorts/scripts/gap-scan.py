#!/usr/bin/env python3
"""gap-scan.py: pacing scan of a Short.

Lists every timed overlay (card-host, cutaway) and every camera move in public/index.html by start time and
reports the stretches where nothing changes: no overlay on screen and no camera move. A camera move is a GSAP
tl.to / tl.fromTo on '#video-zoom' or '#video-wrap' with a literal time; a tl.set (the snap back at a jump cut)
is not a move. The captions run the whole time and do not count: the question is whether the PICTURE goes static.
A Short is swiped away in a second, so the defaults are: the hook (first 5 s) flags > 2.5 s, the body flags > 4 s,
hard ceiling 6 s. Also prints the density: overlays and camera moves per 10 s against a target of about 1.5 + 1.

Usage:
  python3 gap-scan.py --index videos/<p>/public/index.html [--hook 5 --early 2.5 --body 4 --max 6]
"""
import argparse, re, sys

ap = argparse.ArgumentParser()
ap.add_argument("--index", required=True)
ap.add_argument("--hook", type=float, default=5.0, help="seconds counted as the hook")
ap.add_argument("--early", type=float, default=2.5)
ap.add_argument("--body", type=float, default=4.0)
ap.add_argument("--max", type=float, default=6.0)
args = ap.parse_args()

html = open(args.index, encoding="utf-8").read()
root = re.search(r'<div[^>]*data-composition-id="([^"]+)"[^>]*data-duration="([\d.]+)"', html)
if not root:
    sys.exit("no root composition found")
total = float(root.group(2))

items = []
for m in re.finditer(r"<(div|video|audio)\b([^>]*)>", html):
    attrs = m.group(2)
    if "data-start" not in attrs or "data-duration" not in attrs:
        continue
    if "data-composition-id" in attrs:      # the root stage is not an overlay
        continue
    gid = re.search(r'\bid="([^"]+)"', attrs)
    gid = gid.group(1) if gid else "?"
    if gid in ("bg-video", "fg-matte"):
        continue
    if m.group(1) == "audio":
        continue
    start = float(re.search(r'data-start="([\d.]+)"', attrs).group(1))
    dur = float(re.search(r'data-duration="([\d.]+)"', attrs).group(1))
    anchor = re.search(r'data-anchor="([^"]*)"', attrs)
    items.append((start, start + dur, gid, "[%s]" % anchor.group(1) if anchor else ""))
items.sort()

# camera moves: tl.to / tl.fromTo('#video-zoom' | '#video-wrap', {...}[, {...}], <time>); a set is not a move
moves = []
for m in re.finditer(r"tl\.(to|fromTo|set)\(\s*(['\"])#(video-zoom|video-wrap)\2\s*,([^;]*?),\s*([\d.]+)\s*\)\s*;", html):
    if m.group(1) == "set":
        continue
    t = float(m.group(5))
    d = re.findall(r"duration\s*:\s*([\d.]+)", m.group(4))
    moves.append((t, t + (float(d[-1]) if d else 0.0), "cam " + m.group(3), m.group(1)))
moves.sort()

print("composition %s  %.1fs  %d overlay(s), %d camera move(s)" % (root.group(1), total, len(items), len(moves)))
for s, e, gid, note in sorted(items + moves):
    print("  %7.2f - %7.2f  %-24s %s" % (s, e, gid, note))

gaps, cursor = [], 0.0
for s, e, gid, _ in sorted(items + moves):
    if s > cursor:
        gaps.append((cursor, s))
    cursor = max(cursor, e)
if cursor < total:
    gaps.append((cursor, total))

print("\ngaps (talking head only, camera still):")
flagged = 0
for a, b in gaps:
    g = b - a
    limit = args.early if a < args.hook else args.body
    tag = ""
    if g > args.max:
        tag = "  <-- over the %gs ceiling" % args.max; flagged += 1
    elif g > limit:
        tag = "  <-- over %gs, consider a beat or a camera move" % limit; flagged += 1
    if g >= 2:
        print("  %7.2f - %7.2f  %5.1fs%s" % (a, b, g, tag))
covered, cur_s, cur_e = 0.0, None, None        # union of overlay spans, not their sum
for s, e, _, _ in items:
    if cur_e is None or s > cur_e:
        if cur_e is not None:
            covered += cur_e - cur_s
        cur_s, cur_e = s, e
    else:
        cur_e = max(cur_e, e)
if cur_e is not None:
    covered += cur_e - cur_s
per10 = lambda n: 10.0 * n / total if total else 0.0
print("\noverlay coverage %.0f%% of runtime, %d gap(s) flagged" % (100 * min(covered, total) / total, flagged))
print("density: %.1f overlays + %.1f camera moves per 10 s (target about 1.5 + 1)" % (per10(len(items)), per10(len(moves))))
sys.exit(1 if flagged else 0)
