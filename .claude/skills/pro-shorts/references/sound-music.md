# Sound and music

## Sound effects

The kit is `videos/_shared/sfx/` (Pixabay, no attribution; `thud.wav` was made here: a falling 62 Hz sine with a
noise click, peak -3 dBFS). Every effect is peak-normalised and trimmed so its transient lands on its frame.

**Volumes were halved on NOTES 19 (the old levels were too loud).** Fewer sounds: only on the few graphics or
transitions left, about 3 to 6 in a Short. `Kit.sound` refuses a volume above 0.18.

| Moment | Sound | Volume |
|---|---|---|
| A word slams in / a heavy line ("nobody's bothered") | `thud` | 0.12 / 0.15 |
| A marker stroke: a slash, an X | silent (**never `scribble`**: NOTES 12) | - |
| A pop-in (a card, a photo) | `pop` | 0.08 to 0.10 |
| A number landing | `ping` | 0.10 |
| A zoom-blur transition, a slide back | `whoosh-short` | 0.08 to 0.12 |
| A lock landing / snapping shut | `click-soft` | 0.10 |
| Into the last line | `riser` (1.25 s, ending on the line) | 0.06 to 0.08 |
| An opening "no" | `error` (a buzzer) | 0.08 |

- One sound per animated thing, never two inside 0.3 s (`Kit.write` warns): when two land together, keep the one that
  explains the picture. A B-roll cut-in can be silent.
- The voice always wins: if a sound is noticed over a word, it is too loud.
- Set `"sfx": false` in captions.json when placing them by hand (always, with motion elements).

## Music

- **Source: original tracks generated with vidIQ AI music** (`vidiq_generate_music`, instrumental, ~60 s, a drop
  asked for at a set time; 25 credits each), downloaded into `videos/_shared/music/` (they arrive as MP3) and credited
  in CREDITS.md. The creator downloads nothing themselves (2026-10-22). **Pixabay tracks got a YouTube music copyright notice on the Jacob &
  Co. Shorts (2026-10-22) even after the checks below, so Pixabay is no longer used.** Old Pixabay rule, kept for the
  record: on the track page reject anything marked **"Content ID Registered"** and any artist whose
  bio carries a publisher / IPI / DDEX block (both mean YouTube may claim it). Scan many at once from the browser:
  fetch each track page and test the HTML for those strings (as done on 2026-10-18). Ask the creator before downloading.
  Credit every track in `videos/_shared/music/CREDITS.md` (title, artist, URL, the date it was checked).
- **In the library:** `prettyjohn1-hip-hop-groove-526148` (playful, drop ~62.25 s), `bombinsound-trap-warriors-571369`
  (trap, drops ~11.25 s and ~58 s), `kulakovka-inspiring-piano-cinematic-614895` (emotional, lifts ~42 s).
- **Mood:** playful groove for comedy, trap for a rant or a flex, cinematic piano for something heartfelt.
- **The drop lands on the turn:** `music.py map` finds the drops; `music.py bed --drop D --land L` starts the bed at
  D - L so the drop hits the line (codpod12-03: "You're not gonna get an award" at 8.48 s). The quiet intro before it is
  a feature: the Short builds.
- **Level, always measured** (`mix.py`): the bed alone (music version minus the no-music twin) 16 to 20 dB under the
  voice. The gain that does it has been +8, -11 and -6 on three clips. `finish.py` ducks it under speech.
- Always deliver the no-music twin too (the creator may add a sound in the app).
