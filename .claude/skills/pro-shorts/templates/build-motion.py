#!/usr/bin/env python3
# NOTE (NOTES 19): this is the old, heavy v5 example. A new Short uses FAR fewer elements (often 0 to 2),
# no text-only graphics, no shakes/flashes/whips, and quiet sounds (0.05 to 0.15). Delete most of MOMENTS.
"""build-motion.py: one clip's motion design. Copy it into <clip>/subs/, then rewrite the MOMENTS section for the clip.

As shipped it rebuilds the approved codpod12-03 "No spoilers" v5 (the reference for the style), so every move here
is a working example: a word behind the people with a no-sign, a trophy out from behind a shoulder that gets an X,
comment cards flying out of a mouth and getting deleted, a like count running down to 0, a padlock landing and
snapping shut, the beat-snapped timing, the camera (punches, shakes, flashes, pushes) and three transitions.

Usage (from the project root): python <clip>/subs/build-motion.py  -> writes <clip>/subs/captions.json
then: python youtube-shorts/scripts/subtitles.py --video <subs>/edit.mp4 --spec <subs>/captions.json --out <subs>/public --shared videos/_shared
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.getcwd(), ".claude", "skills", "pro-shorts", "scripts"))   # run from the project root
from motionkit import Kit, HEART

k = Kit(seed="codpod12-03", window=json.load(open(os.path.join(HERE, "window.json"))), beats=os.path.join(HERE, "beats.json"))
WY, D = k.WY, k.D
# faces in the picture (frame px), from shots.png: punch-ins and fly-outs aim here
BARRY, JEFF, CENTRE = (300, WY + 120), (540, WY + 190), (540, WY + 285)
DROP = 8.54                                   # the music's drop (music.py bed --land), on "You're not gonna get an award"

# ================================ MOMENTS: one block per idea, each on its word ================================
# 1. "No SPOILERS" (0.16-0.40): a big word BEHIND the guests, slammed on the word, ring and slash on the beats
k.big_word("A", "SPOILERS", cy=WY + 210, layer="behind", no_sign=True)
k.show("#A", 0.10); k.slam("#A-word", land=0.38)
k.burst("bA", 540, WY + 210, 0.38, n=12, r0=420, r1=540, width=7, layer="behind")
k.draw("A-ring", k.beat(0.50) - 0.02, 0.24); slash = k.beat(0.90); k.draw("A-slash", slash - 0.08, 0.08, "power4.in")
k.J("tl.to('#A-word', { opacity: 0.55, duration: 0.15 }, %.3f);" % slash)
k.pulse_on_beats("#A", slash + 0.2, k.beat(2.80) - 0.1, scale=1.025, strong=False)
k.exit_fall("#A", k.beat(2.80))
k.sound("thud.wav", 0.36, 0.12)                    # no scribble sound, ever (NOTES 12)

# 2. "get an AWARD" (9.36): a trophy out from behind Barry's shoulder (lands on the drop), sparkles, X on the word
k.icon("B", "trophy", 540, WY + 172, 230, layer="behind", x_mark=True)
k.slide_in("#B", land=DROP)
for sid, x, y, s, t in (("s1", 420, WY + 40, 40, 8.89), ("s3", 700, WY + 250, 42, 8.89), ("s2", 690, WY + 70, 32, 9.28), ("s4", 430, WY + 230, 28, 9.28)):
    k.star(sid, x, y, s, layer="behind"); k.twinkle("#" + sid, t)
k.x_slam("B", 9.36); k.burst("bB", 540, WY + 172, 9.40, n=10, r0=150, r1=230, color="#FF3B30", width=7, layer="behind")
sink = k.beat(10.37); k.slide_out("#B", sink - 0.10)
k.sound("ping.wav", 8.86, 0.05); k.sound("whoosh-short.wav", sink - 0.10, 0.08, 0.5)

# 3. "this happened" x3 (12.24 / 12.72 / 13.12): comment cards fly out of Barry's mouth; deleted on "No one's"
CARDS = [("C1", 120, 520, -3, 12.24, "#6C5CE7", "jay_cod"), ("C2", 520, 400, 2.5, 12.72, "#00866A", "mw4_leaks"), ("C3", 180, 278, -1.5, 13.12, "#E17055", "k1ller_kev")]
for i, (cid, x, y, rot, t, col, nm) in enumerate(CARDS):
    k.card(cid, x, y, nm, "this happened", col)
    k.fly_from("#" + cid, BARRY, (x + 220, y + 50), t - 0.06, rot)
    for prev in CARDS[:i]:
        k.J("tl.to('#%s', { y: '-=16', scale: '-=0.03', duration: 0.3, ease: 'power3.out' }, %.3f);" % (prev[0], t))
    k.sound("pop.wav", t, 0.08)
dele = k.beat(13.70); k.delete(["#C3", "#C2", "#C1"], dele); k.sound("whoosh-short.wav", dele, 0.08, 0.5)

# 4. "No one's IMPRESSED" (14.08): a heart pops on the beat and beats; the like count runs down to 0 on the next beat
heart, zero = k.beat(14.00), k.beat(14.70)
k.el("D", 300, 345, 180, 170, HEART % {"w": 180, "h": 170})
k.number("D-n", 500, 372, "12,481")
k.show("#D", heart - 0.04); k.pop("#D", heart); k.pulse_on_beats("#D", heart + 0.25, zero - 0.1, scale=1.18)
k.J("tl.fromTo('#D-n', { opacity: 0, x: 30 }, { opacity: 1, x: 0, duration: 0.2, ease: 'power3.out' }, %.3f);" % (heart + 0.04))
k.count("#D-n", 12481, 0, heart + 0.06, zero - heart - 0.06); k.squash("#D-n", zero)
k.burst("bD", 390, 430, zero, n=8, r0=110, r1=170, color="#FFD400")
k.J("tl.to('#D svg', { filter: 'grayscale(1) brightness(.6)', duration: 0.25 }, %.3f);" % (zero + 0.04))
k.J("tl.to('#D, #D-n', { opacity: 0, scale: 0.6, duration: 0.2, ease: 'power3.in' }, 15.04);")
k.sound("pop.wav", heart + 0.02, 0.09); k.sound("ping.wav", zero, 0.10)

# 5. "nobody's BOTHERED" (15.28): no element, the footage takes the hit (camera shake + flash below)
k.sound("thud.wav", 15.28, 0.17); k.sound("riser.wav", 15.62, 0.06, 1.25)

# 6. "keep it to YOURSELF" (16.48): a padlock drops in on the beat, its shackle snaps shut on the word, pulses to the end
land, snap = k.beat(16.10), 16.52
k.icon("E", "padlock", 540, 430, 220)
k.J("tl.set('#E .shackle', { y: -46 }, 0);")
k.drop_in("#E", land); k.burst("bE", 540, 545, land, n=7, r0=60, r1=140, width=5, a0=150, a1=390)
k.J("tl.to('#E .shackle', { y: 4, duration: 0.09, ease: 'power4.in' }, %.3f);" % (snap - 0.08))
k.J("tl.to('#E .shackle', { y: 0, duration: 0.12, ease: 'power2.out' }, %.3f);" % (snap + 0.01))
k.J("tl.to('#E', { keyframes: [{ rotation: -5, duration: 0.05 }, { rotation: 4, duration: 0.06 }, { rotation: 0, duration: 0.18, ease: 'elastic.out(1, 0.4)' }] }, %.3f);" % snap)
k.burst("bE2", 540, 400, snap + 0.03, n=10, r0=140, r1=210, color="#FFD400")
k.pulse_on_beats("#E", snap + 0.3, D - 0.1, scale=1.06)
k.sound("click-soft.wav", land, 0.08, 0.32); k.sound("click-soft.wav", snap, 0.14, 0.32); k.sound("whoosh-short.wav", 16.84, 0.10, 0.5)

# ================================ CAMERA: the footage takes part ================================================
# reset ("set") on every shot change; never a push or set across a transition (two tweens on one scale fight)
CAMERA = [
    ["set", 0.0, 1.0],
    ["punch", 0.36, 1.06, CENTRE[0], CENTRE[1]], ["shake", 0.38, 12, 0.26], ["flash", 0.38, 0.28], ["release", 0.85, 0.3],
    ["set", 1.199, 1.0], ["creep", 1.25, 3.6, 1.06, 540, WY + 220],
    ["set", 3.666, 1.0],
    ["leak", 5.30],                                                  # transition: on a beat in the quiet stretch
    ["whip", 8.20, 1],                                               # transition: on the beat, into the rant, before the drop
    ["punch", DROP, 1.04, BARRY[0], BARRY[1]], ["flash", DROP, 0.16],
    ["creep", DROP + 0.3, 9.31, 1.06, BARRY[0], BARRY[1]],
    ["punch", 9.36, 1.13, BARRY[0], BARRY[1]], ["shake", 9.40, 9, 0.22], ["flash", 9.38, 0.22], ["release", 10.4, 0.3],
    ["creep", 11.9, 14.05, 1.06, BARRY[0], BARRY[1]], ["release", 14.05, 0.3],
    ["zoomblur", 14.533, 540, WY + 250],                             # transition: punch through into the reaction
    ["creep", 14.82, 16.7, 1.08, JEFF[0], JEFF[1]],
    ["shake", 15.28, 13, 0.3], ["flash", 15.28, 0.2],
    ["set", 16.799, 1.0], ["creep", 16.84, D, 1.07, BARRY[0], BARRY[1]],
]
for b in k.beats_between(10.7, 11.9):                                # the picture breathes in the quiet stretch
    k.J("tl.to('#win', { keyframes: [{ scale: 1.012, duration: 0.05 }, { scale: 1, duration: 0.24, ease: 'power2.out' }] }, %.3f);" % b)
k.sound("whoosh.wav", 5.12, 0.05, 0.5); k.sound("whoosh.wav", 8.07, 0.13, 0.5); k.sound("whoosh-short.wav", 14.40, 0.10, 0.5)

k.write(os.path.join(HERE, "captions.json"), CAMERA)
