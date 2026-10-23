# The footage takes part: camera moves and transitions

All of these are `"camera"` ops in captions.json, run by `youtube-shorts/scripts/subtitles.py`. The picture of a
letterboxed clip lives in its own window (`"window": {"y", "h"}`), so a move zooms or shakes the picture inside the
window and never the black bands. The cut-out people and the "behind" layer live in the same moving box, so they
stay locked to the footage through every move.

## Ops (frame px for origins; the face from shots.png)

| Op | What | When |
|---|---|---|
| `["set", t, s]` | jump to a scale | 1.0 on every shot change (a zoom never carries across a cut) |
| `["punch", t, s, ox, oy]` | 0.26 s `expo.out` zoom toward a face | every hit: 1.04 on the drop, 1.06 on a slam, 1.12 to 1.13 on the big one |
| `["creep", t0, t1, s, ox, oy]` | slow `sine.inOut` push | long shots (1.04 to 1.08), toward whoever speaks |
| `["release", t, dur]` | back to 1.0 | after a punch, before a transition |
| `["shake", t, amp, dur]` | a decaying shake (each kick smaller) | impacts: 9 to 13 px, 0.22 to 0.3 s; while scaled >= 1.04, or the window edges show |
| `["flash", t, op]` | white over the picture, 0.2 s | with a shake or a punch: 0.16 to 0.28 |
| `["whip", cut, dir]` | outgoing slides off under a horizontal-only blur (`feGaussianBlur 46 0`), incoming slides in, scaled 1.24 | a cut into a turn, on a beat (cut-08.2 into the rant) |
| `["zoomblur", cut, ox, oy]` | zoom + blur + overexpose into the cut, land zoomed, settle, flash | a cut to a reaction (14.53 into Jeff's laugh) |
| `["leak", cut]` | a soft warm band sweeps across (`mix-blend-mode: screen`), the picture brightens | a quiet cut on a beat (5.30) |

The picture can also breathe on the beats (`tl.to('#win', scale 1.012)`) in a quiet stretch.

## Rules learned

- **Treat 2 to 3 of a clip's cuts, never all of them.** Prefer cuts that land on a beat (`window.json` shots vs
  `beats.json`) and the cuts into a turn or a reaction. The rest stay hard cuts: too many transitions look cheap.
- **Two tweens on one property fight.** Remove any `set` at a transition's cut (v4's `set 8.199` would have broken
  the whip) and start a push after a zoom-blur settles (+0.3 s), not during it.
- **Never change the zoom origin while zoomed in:** the picture jumps. Release to 1.0 before a move with a new origin.
- **A light leak is a soft band, no hard shapes.** A round highlight read as a fake disc; it also hung as an orange
  haze for too long until it was cut to ~0.45 s and peak opacity 0.75.
- **Every transition gets a sound**: a whoosh for a whip (0.3) and a zoom (0.26), a soft one for a leak (0.12).
- **Black flashes in the source edit stay** (verify-render flags them; check the source with blackdetect first).
