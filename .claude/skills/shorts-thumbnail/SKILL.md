---
name: shorts-thumbnail
description: Makes the thumbnail (cover) for a finished Short, Reel or TikTok in the house look - full 9:16, the key moment as a real image filling the top (with a yellow ring on the exact spot), the key person cut out large at the bottom with a real expression, and a 2-6 word headline with one word in the yellow box; renders 3 versions, checks them at phone size and in each app's crop, and adds the upload frame to the upload-info .txt. Use whenever the user asks for a thumbnail, a cover, a cover frame, "thumb", or "what frame should I use", and at the end of every pro-shorts delivery - even if they don't name the skill.
---

# Shorts thumbnail

A Short's thumbnail is seen small: on the YouTube Shorts shelf (with the title over its bottom), in search, and in
the Instagram and TikTok profile grids (cut to 3:4). It has one job: make someone tap. It tells the story in one
look: **who** (the key person's face, with a feeling), **what** (the key moment, as a real image) and **why it
matters** (a few words).

**Read first:** `youtube-shorts/NOTES.md` (all of it applies: plain text, the font round robin, real photos only,
as few graphics as possible) and `youtube-shorts/THUMBNAIL-NOTES.md` (what the creator picked and rejected).

**Approved worked example:** `videos/clash_02/m01/thumb/thumbs.json` → `E:/AutoEdit/clash_02/thumbnails/clash02-01-kawhi-fifth-bounce-thumb-H3.jpg`
(Rusty cut out, mouth open; Kawhi's shot behind him with the ball on the rim ringed; the sticker hook "WAIT… /
A [5TH] / BOUNCE?!" on a blurred band). Start every thumbnail from it.

## The look (the creator, 2026-10-20: "more professional, key person face, key moment, always full 9:16")

Rejected: a black frame with a square close-up and the headline above it (letterboxed, plain, "I don't like
anyone"). The look now, all layers full bleed on 1080x1920:

- **The key moment, top:** a real image of what the Short is about (a frame of the show's own graphics, B-roll the
  Short uses, or a frame of the clip), sharp, filling the top and fading at its bottom into a dark, blurred copy
  of itself that fills the rest. Never an edge or a black bar: the script scales it up until it covers.
- **A yellow ring on the exact spot** that matters (the ball on the rim, a scoreboard number, a shoe), 14 px, the
  accent colour, nothing else drawn. Only when there is one spot; skip it otherwise.
- **The key person, bottom:** the one the Short is about, cut out (the local u2net person model, edge refined on
  the frame, edge colour cleaned), large (about 1150 px wide, the face ~350 px), bottom-anchored, the body running
  off the bottom. A real expression: mouth open, laughing, shocked, a gesture. Pick from a clean shot (a solo
  interview, a plain backdrop) over a busy one; never through a desk or an answer board (crop above it and set
  `fade`, or use another shot).
- **The hook (headline), top (y 260-720):** 2 to 6 words, 2 or 3 lines, capitals, the Short's subtitle font,
  **exactly one word in the yellow box**. It must be eye-catching (creator, 2026-10-20: plain white text over the
  photo was not enough), so by default it's a **sticker hook**:
  - **solid plates** behind the lines: a white plate with dark text for the set-up line, a plate in the story's
    colour (a team colour: Raptors red `#CE1141`) with white text for the payoff line. A plate is a solid box
    like the yellow one, so it keeps NOTES 7 (no stroke, outline, shadow or glow, ever);
  - **size contrast**: the set-up line small (`scale` 0.5-0.65), the payoff big (1), a giant boxed word (1.3)
    when it's a number;
  - **a slight tilt** (`tilt` -3 to -4 degrees) on the whole block.
  - **a soft blur behind it** (`text_blur`, 10 px by default): the photo under the hook is blurred in a band
    that fades out just below the text, so the plates stand clear of a busy crowd while the ring, the moment and
    the face stay sharp (creator, clash02-01 H3).
  Each line grows to fill the width, and the block shrinks together to fit, so it reads at 150 px.
- **It adds to the title, never repeats it** (`thumbnail.py` flags a headline whose words are mostly in a title).
  Curiosity beats a statement: "WAIT… A [5TH] BOUNCE?!" over "4 BOUNCES OR 5".
- **Safe zones:** headline, ring and face inside y 240-1680 (the 3:4 grid crop); the bottom is only the body,
  where YouTube lays the title.

## 1. Find the person and the moment

Read the transcript: who is the Short about, and what is the one moment (the shot, the play, the answer card)?
```bash
python .claude/skills/shorts-thumbnail/scripts/thumbframes.py --cut videos/<ep>/cuts/<clip>.mp4 --subs videos/<ep>/mNN/subs --out videos/<ep>/mNN/thumb
```
Ranks sharp, still, loud frames per person and writes `contact.jpg`. It can't read an expression or know who
matters, so then **tile close-ups of the key person** across the times they speak (12 to 16 frames, labelled with
the time) and pick the strongest face by eye. For the moment, find the frame where the image is biggest and
sharpest (an answer card, a replay) and note the crop and the focus point in source pixels.

## 2. Write the spec and render 3 versions

`videos/<ep>/mNN/thumb/thumbs.json`:
```json
{
 "slug": "clash02-01-kawhi-fifth-bounce",
 "cut": "videos/clash_02/cuts/clash02-01-kawhi-fifth-bounce.mp4",
 "subs": "videos/clash_02/m01/subs",
 "out": "E:/AutoEdit/clash_02/thumbnails",
 "txt": "E:/AutoEdit/clash_02/edited/clash02-01-kawhi-fifth-bounce-short-v1.txt",
 "pick": "H3",
 "versions": [
  {"id": "H3", "tilt": -3, "size": 230, "bottom": 720,
   "lines": [{"text": "WAIT…", "scale": 0.5, "plate": "#FFFFFF", "color": "#111317"},
             {"text": "A [5TH]", "scale": 1.3},
             {"text": "BOUNCE?!", "scale": 0.8, "plate": "#CE1141"}],
   "person": {"t": 24.2, "crop": [360, 0, 1200, 1080], "width": 1150, "face_x": 700},
   "moment": {"src": "cut", "t": 13.62, "crop": [1024, 320, 820, 554], "focus": [170, 395],
              "focus_at": [230, 900], "scale": 2.3, "ring": 95}}
 ]
}
```
- `lines`: a string (plain white line) or `{"text", "scale", "plate", "color"}`; `[word]` is the boxed word.
  `size` is the biggest a scale-1 line may get (230 for a sticker hook), `bottom` the lowest the block may reach
  (600 by default, up to ~720 when the ring sits at y 900), `tilt` in degrees.
- `person`: the frame time, the crop around them in source pixels (wide enough for the shoulders), the width on
  the thumbnail, where the face goes (`face_x`), and `fade` (px) when the crop stops mid-body. `keep_color`
  `[r, g, b, tol]` keeps a colour the person model drops when it touches the person (Cam Newton's yellow hat brim:
  `[217, 173, 64, 60]`).
- `moment`: `src` is `"cut"` (a frame at `t`) or an image file (in `subs/`, next to the spec, or a path); `focus`
  is the spot in the crop, `focus_at` where it lands on the thumbnail (keep it beside the face, below the
  headline), `ring` the ring radius. `scale` is raised automatically to fill the frame.

Make three real alternatives: other faces of the same person, another moment, another headline angle.
```bash
python .claude/skills/shorts-thumbnail/scripts/thumbnail.py --spec videos/<ep>/mNN/thumb/thumbs.json
```
Writes `<slug>-thumb-<id>.jpg` and `<slug>-thumb-check.jpg` to `E:/AutoEdit/<video>/thumbnails/`, prints the lint
(headline, scaling over 1.6x for the person or 2.6x for the moment, a head running into the headline) and, for
`pick`, writes a THUMBNAIL section into the upload-info .txt (which file, the headline, and the frame time for apps
that only let you pick a frame). Rerunning replaces that section.

## 3. Check, then hand over

Open the check sheet (each version full, in the 3:4 grid crop, on the YouTube shelf, at 150 px) and look at the
full-size pick: the cut-out edge (no halo, no backdrop colour on hair or ears, no half-cut desk or board), the
ring on the spot, the face not covering the moment, the headline readable at 150 px. Fix every FLAG. Show the
creator the check sheet with your pick and one line on why. The moment image is the show's own (or licensed
B-roll): say so when it's someone else's photo. Never send a thumbnail to an outside service without asking.

## Keep it learning

After the creator picks (or rejects) a thumbnail, add one line to `youtube-shorts/THUMBNAIL-NOTES.md`. A
correction that should hold for every thumbnail also goes into "The look" above.
