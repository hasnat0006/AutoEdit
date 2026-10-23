#!/usr/bin/env python3
"""catalog.py: the HyperFrames block catalog (~450 render-tested motion pieces) for pro-shorts.

Before hand-drawing an element, look for a catalog block that already does the move, read its source, and port its
look and motion into the clip's build-motion.py (one shared timeline `tl`, 9:16, the house rules). The blocks are
standalone 1920x1080 pages with their own timeline, so they are references to port, never dropped in as-is.

  search  python catalog.py search "lower third name"        name | size | seconds | what it is (top 15)
  fetch   python catalog.py fetch lt-kicker-name --out <subs>/blocks
          -> <out>/<name>.html (the raw block file from the registry on GitHub; `hyperframes add` timed out here), then an audit
  audit   python catalog.py audit <subs>/blocks/<name>.html   flags what breaks NOTES.md before you port it

The audit flags: text-shadow / glow / -webkit-text-stroke / outlines on text (NOTES 7), fonts other than Inter and
Montserrat (NOTES 3), a progress bar (NOTES 6), emoji (NOTES 15), remote URLs other than GSAP (freeze assets locally),
Math.random / Date.now (non-deterministic). Already ported into motionkit: lt-kicker-name -> Kit.lower_third,
x-post -> Kit.post_card. Fetching downloads code from GitHub: ask the creator the first time in a session.
"""
import argparse, json, os, re, shutil, subprocess, sys, urllib.request

RAW = "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry/blocks/%s/%s.html"
npx = shutil.which("npx") or "npx"

def search(q):
    r = subprocess.run([npx, "hyperframes", "catalog", "--query", q, "--json"], capture_output=True, text=True, encoding="utf-8")
    try:
        data = json.loads(r.stdout[r.stdout.index("{"):])
    except ValueError:
        sys.exit("catalog search failed:\n" + (r.stderr or r.stdout)[-800:])
    print("%d of %d items match %r" % (data.get("shown", 0), data.get("total", 0), q))
    for it in data.get("results", [])[:15]:
        d = it.get("dimensions") or {}
        print("  %-28s %4sx%-4s %5ss  %s" % (it["name"], d.get("width", "?"), d.get("height", "?"), it.get("duration", "?"), (it.get("description") or it.get("title", ""))[:90]))

def fetch(name, out):
    os.makedirs(out, exist_ok=True)
    dst = os.path.join(out, name + ".html")
    try:
        with urllib.request.urlopen(RAW % (name, name), timeout=60) as r:
            open(dst, "wb").write(r.read())
    except Exception as e:
        sys.exit("could not fetch %s: %s" % (name, e))
    if os.path.getsize(dst) < 200:
        os.remove(dst); sys.exit("%s: not a single-file block (no %s.html in the registry); browse it with `npx hyperframes catalog %s`" % (name, name, name))
    print("fetched -> %s (%d bytes)" % (dst, os.path.getsize(dst)))
    audit(dst)

RULES = [
    (r"text-shadow", "text-shadow (NOTES 7: text is plain)"),
    (r"-webkit-text-stroke|text-stroke", "text stroke/outline (NOTES 7)"),
    (r"drop-shadow\(|box-shadow", "shadow (fine on a card or photo, never on text)"),
    (r"\bglow\b|neon", "glow / neon look (NOTES 7)"),
    (r"font-family\s*:\s*[\"']?(?!Inter|Montserrat|SubFont|var\()([A-Za-z][^;\"',]*)", "font other than Inter/Montserrat (NOTES 3): use SubFont"),
    (r"progress", "progress bar? (NOTES 6)"),
    (r"[\U0001F300-\U0001FAFF☀-➿]", "emoji (NOTES 15)"),
    (r"Math\.random|Date\.now|setInterval|setTimeout", "non-deterministic timing (render must be seek-safe)"),
    (r"https?://(?!cdn\.jsdelivr\.net/npm/gsap)[^\s\"')]+", "remote asset (freeze it locally)"),
]

def audit(path):
    src = open(path, encoding="utf-8", errors="replace").read()
    hits = 0
    for pat, why in RULES:
        found = sorted(set(m.group(0)[:60] for m in re.finditer(pat, src)))
        if found:
            hits += 1
            print("  FIX   %s: %s" % (why, ", ".join(found[:4])))
    canvas = re.search(r'data-width="(\d+)"\s+data-height="(\d+)"', src)
    if canvas:
        print("  NOTE  built for %sx%s: rescale for the 1080x1920 page (band y 200-640 above a letterboxed picture)" % canvas.groups())
    print("  ok    nothing against the house rules" if not hits else "  -> port the look and motion, drop the flagged parts")

ap = argparse.ArgumentParser()
sub = ap.add_subparsers(dest="cmd", required=True)
s = sub.add_parser("search"); s.add_argument("query", nargs="+")
f = sub.add_parser("fetch"); f.add_argument("name"); f.add_argument("--out", required=True)
a = sub.add_parser("audit"); a.add_argument("path")
args = ap.parse_args()
if args.cmd == "search": search(" ".join(args.query))
elif args.cmd == "fetch": fetch(args.name, args.out)
else: audit(args.path)
