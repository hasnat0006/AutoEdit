# Example: clip-03 ("It wasn't bad luck")

The first real Short made with this skill: an 18.3 s clip from a two-person podcast (Solved., episode 04 "Human Luck"),
1080p landscape source, edited three times on the creator's notes. Start a new Short from `storyboard-v3.json`.

| File | What it is |
|---|---|
| `cut-list.json` | the final cut of the 28.5 s raw clip: 5 kept segments, edges set by the audio level |
| `cut-map.json` | where each jump cut landed in the 18.25 s flat cut (written by `apply-cut.py`) |
| `PAPER-CUT.md` | what was kept and removed, and why (the host's lines, the broken first and last sentences) |
| `storyboard-v1.json` | v1: full-frame 9:16 crop, DM Sans + cyan captions, karaoke, wide shot over a blurred fill |
| `storyboard-v2.json` | v2: the card look, Rubik Mono One white + yellow, title strike and swap, emoji, dots, meter |
| `storyboard-v3.json` | v3 (approved): smaller type, no credit chip, hand-made elements (marker strokes, 3D die, chart), 8 SFX, plain captions |
| `STORYBOARD.md` | the delivery note for v3 |

The notes that shaped each version:

- **v1 → v2:** "I don't like the font, font colour and placement"; "add motion graphics and elements that attract
  viewers"; "zooming to fill looks low quality, leave blank space and animate in it".
- **v2 → v3:** "the font is too big"; "no 'Solved podcast' chip"; "don't use stock emoji, animate elements yourself";
  "add SFX"; "it shouldn't feel edited by an AI".

To reuse a storyboard on a new clip: change `id`, `duration`, every beat's `in` / `out` / `at` and `anchor` to the new
words (`phrase-times.py` finds them), the title text, and the camera `set` times to the new `cut-map.json` jump frames.
