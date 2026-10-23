#!/usr/bin/env python3
"""hookcheck.py: the first-3-seconds rule (NOTES 13, from real retention graphs). Flags a Short whose opening
loses the scroll: speech that starts late, a claim that lands after ~3 s, no hook text at frame 0, a shot change
(a cutaway, B-roll, a stock photo in the source) or a graphic before the claim. Writes hook-strip.png (frames 0 to
the claim, plus one per shot before it) so you can see the speaker is on screen from frame 0: a script cannot.

Usage: python hookcheck.py --subs videos/<episode>/mNN/subs --claim "super wrong"
  --claim  the words of the bold claim / question / first story line, as said (copied from the transcript).
FLAG = breaks the rule (exit 1). LOOK = a shot change before the claim: an angle change on the speaker is fine,
a cutaway is not; the strip decides.
"""
import argparse, json, os, re, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("--subs", required=True)
ap.add_argument("--claim", help="the claim's words as said; without it the first seconds are printed to judge")
ap.add_argument("--by", type=float, default=3.5, help="the claim must end by this (s); the rule is ~3 s")
args = ap.parse_args()
S = args.subs
cap = json.load(open(os.path.join(S, "captions.json"), encoding="utf-8"))
words = json.load(open(os.path.join(S, cap.get("transcript", "transcript.json")), encoding="utf-8"))
win = json.load(open(os.path.join(S, "window.json"))) if os.path.exists(os.path.join(S, "window.json")) else {}
N = lambda s: re.sub(r"[^a-z0-9']", "", s.lower())
flags, notes = [], []

# 1. Speech from the first frame
t0 = words[0]["start"] if words else 99
(flags if t0 > 0.5 else notes).append("first word at %.2fs%s" % (t0, " (dead air before the hook)" if t0 > 0.5 else ""))

# 2. The claim inside ~3 s
claim_end = None
if args.claim:
    want = [N(w) for w in args.claim.split()]
    got = [N(w["text"]) for w in words]
    for i in range(len(got) - len(want) + 1):
        if got[i:i + len(want)] == want:
            claim_end = words[i + len(want) - 1]["end"]; break
    if claim_end is None:
        flags.append('claim "%s" not found in the transcript (copy it as said)' % args.claim)
    else:
        (flags if claim_end > args.by else notes).append('claim "%s" ends at %.2fs (rule: by %.1fs)' % (args.claim, claim_end, args.by))
else:
    notes.append("no --claim given: is the claim in here? " + " ".join(w["text"] for w in words if w["start"] < args.by))
upto = claim_end if claim_end else 3.0

# 3. Hook text on screen from frame 0
hook = cap.get("hook")
if not hook:
    flags.append("no hook text (NOTES 11: the hook in the black above the footage from frame 0)")
elif hook.get("at", 0) > 0.1:
    flags.append("hook text comes in at %.2fs, not frame 0" % hook["at"])
else:
    notes.append('hook "%s" from frame 0' % hook["text"].replace("|", " "))

# 4. Nothing but the speaker before the claim: source shot changes and graphics
shots = [t for t in win.get("shots", []) if t < upto]
looks = ["shot change at %.2fs, before the claim: still the speaker, or a cutaway / B-roll / photo? (hook-strip.png)" % t for t in shots]
shown = sorted({float(m) for m in re.findall(r"tl\.set\('#[\w-]+',\s*\{\s*opacity:\s*1\s*\},\s*([\d.]+)\)", cap.get("raw_js", ""))})
for t in [t for t in shown if t < upto]:
    flags.append("graphic on screen at %.2fs, before the claim: it must not cover the speaker" % t)

# The strip: what a viewer sees before the claim
video = next((os.path.join(S, f) for f in ("render-raw.mp4", "edit.mp4") if os.path.exists(os.path.join(S, f))), None)
if video:
    ts = sorted({round(x * 0.5, 2) for x in range(int(upto / 0.5) + 1)} | {round(t + 0.2, 2) for t in shots})
    sel = "+".join("between(t,%s,%s)" % (t, t + 0.034) for t in ts)
    out = os.path.join(S, "hook-strip.png")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", "select='%s',scale=216:-1,tile=%dx1" % (sel, len(ts)),
                        "-frames:v", "1", "-fps_mode", "vfr", out], capture_output=True, text=True)
    notes.append("hook-strip.png: %s at %s" % (os.path.basename(video), " ".join("%.1f" % t for t in ts)) if r.returncode == 0 else "strip failed: " + r.stderr[-200:])

for n in notes: print("  ok   ", n)
for l in looks: print("  LOOK ", l)
for f in flags: print("  FLAG ", f)
print("hookcheck %s: %s" % (S, "%d flagged" % len(flags) if flags else "pass"))
raise SystemExit(1 if flags else 0)
