# YouTube Shorts with Claude Code: what we built and how it works

A learning guide to everything done in this folder: the setup, the `youtube-shorts` skill, and the first real Short
(clip-03) through its three versions. Read it top to bottom once; afterwards, jump to "Making your next Short".

---

## 1. Where everything is

| Path | What it is |
|---|---|
| `youtube-shorts/` | **The Shorts skill we built.** Always 9:16, 1080x1920, 60 s at most. |
| `youtube-shorts/SKILL.md` | The rulebook Claude follows. Every lesson below is written into it. |
| `youtube-shorts/scripts/` | The tools (Python). `compose.py` builds the animated page; the rest cut, check and finish. |
| `youtube-shorts/scripts/tests/` | 46 automatic tests. Run them after changing any script. |
| `youtube-shorts/assets/` | Fonts (DM Sans, Rubik Mono One), GSAP (the animation library), 30 emoji SVGs, the sound-effect kit. |
| `youtube-shorts/examples/clip-03/` | The finished example: cut list and the v1, v2 and v3 storyboards. |
| `LICENSES/` | Licences for the fonts, the emoji and the sound effects. |
| `..\videos\clip-03\` | The working folder for clip-03 (raw clip, transcripts, renders, snapshots). |
| `..\videos\_shared\sfx\` | The sound effects the composer copies into each Short. |
| `C:\Users\Hasnat0006\Videos\YouTube Shorts\clip-03\` | The delivered files: v1, v2, v3, each with a no-music twin, plus notes. |

---

## 2. Your setup, and why each piece is there

| Tool | What it does in the pipeline |
|---|---|
| **Node.js** | Runs HyperFrames. |
| **HyperFrames** (`npx hyperframes`) | Turns an HTML page with a GSAP timeline into a video: it opens the page in Chrome, steps the timeline frame by frame, screenshots each frame and encodes them with the audio. It also transcribes (`transcribe`), checks a page (`check`) and takes stills (`snapshot`). |
| **Parakeet** | The speech-to-text model HyperFrames uses. Gives every word with its start and end time, which is what lets captions and animations land on words. |
| **FFmpeg / ffprobe** | Cuts, encodes, measures loudness, finds scene changes, reads file info. Almost every script calls it. |
| **auto-editor** | Finds where speech is, by audio level. The paper cut uses it to tell talking from silence. |
| **Python + numpy** | Runs the scripts; numpy does the audio maths (levels, pitch). |
| **Google Chrome** | HyperFrames renders in it. |

**Windows fixes made during setup** (the kit was written on a Mac):
- `python3` opened the Microsoft Store, so a copy of `python.exe` named `python3.exe` was added next to it.
- `PYTHONUTF8=1` was set for your user, because the scripts write text with characters like `→` that Windows' default
  encoding cannot write.
- `teardown.py` and `snap-beats.py` were fixed for Windows paths and for `npx` being `npx.cmd`.

**This PC:** 7.7 GB of RAM, so renders always use `--workers 1` (one Chrome at a time). An 18 s Short renders in
about 2 to 3 minutes.

---

## 3. How a Short gets made (the pipeline)

```
raw clip ──► CUT ──► flat cut ──► LAYOUT ──► storyboard.json ──► compose.py ──► index.html (animated page)
                                                                                    │
           upload ◄── finish.py ◄── render-raw.mp4 ◄── hyperframes render ◄── snapshots (checkpoint)
```

### Step 1: the cut (raw clip → "flat cut")

A **flat cut** is your clip with every mistake, pause and unwanted line removed, no effects yet.

1. **Extract the audio and transcribe it** with Parakeet, so every word has a time.
2. **`paper-cut.py`** proposes what to remove: restarts, retakes (it keeps the last take), false starts, long pauses.
   It writes `PAPER-CUT.md` for you to read. This is **checkpoint A**: you approve the cut in plain words.
3. **`hand-cut.py`** rebuilds the cut from the lines you choose to keep, when the paper cut misread something.
4. **`tighten-cut.py`, `sliver.py`, `edge-audit.py`** trim each edge by the sound so no breath or half-word leaks in.
5. **`edge-levels.py`** (new) prints the level around every edge, so you can see each cut sits in silence *between* words.
6. **`apply-cut.py`** makes the flat cut in one frame-accurate encode and writes `cut-map.json` (where every jump cut is).
7. **`dead-air.py`** finds any pause over 0.4 s that survived; remove them and repeat until it says 0.

### Step 2: the layout

- **Vertical source** (a phone): scale it to 1080x1920 with `reframe.py`.
- **Landscape source** (a podcast, a camera): **the card look**. The whole 16:9 video sits in a rounded card in the
  middle; above and below it go the headline, captions and animations. Nothing is enlarged, so it stays sharp.

### Step 3: the storyboard and the composer

`storyboard.json` lists everything that happens and when: the headline, each animated element (a "beat") with the
spoken words it belongs to (its "anchor"), the captions, the camera moves and the sounds. `compose.py` turns it into
`public/index.html`, a web page whose GSAP timeline is the whole edit. Retiming anything is editing one number and
rebuilding.

Checks before rendering:
- `npx hyperframes check` catches layout and contrast problems.
- `beat-check.py` proves every element enters within 0.6 s before to 0.1 s after its word.
- `gap-scan.py` finds stretches where the picture does not change.
- `snap-beats.py` takes a still of every moment. This is **checkpoint B**: a snapshot takes seconds, a render takes
  minutes, so every visual problem is caught here.

### Step 4: render, finish, verify, deliver

- `npx hyperframes render ... --resolution portrait --workers 1` makes `render-raw.mp4`.
- `finish.py` sets the loudness to -14 LUFS (YouTube's level), mixes the music under the voice, and adds the colour tags.
  It copies the picture without re-encoding it, so no quality is lost.
- `verify-render.py` checks the finished file: size, colour tags, bitrate, length (60 s max), sync, black frames, and
  that no word was clipped (it transcribes the finished file and compares).

---

## 4. The clip-03 story

**The source:** `D:\Projects\automation\transcripts\output\Mark3\clips_video\clip_03.mp4`, 28.5 s of a two-person
podcast ("Solved.", episode 04 "Human Luck"), 1920x1080 at 24 fps. The guest explains why people call bad outcomes
"bad luck" when they were really overconfident.

### The cut (28.5 s → 18.3 s), and the mistakes caught along the way

- The clip **started and ended mid-sentence** ("...out well that they're almost" / "...turn away from the uncertainty
  and"). The Short starts at "They're constantly surprised..." and ends on "...the way the world was gonna work." That
  ending leads back into the opening, so the Short loops when YouTube replays it.
- **The host's "Yeah." and "Right."** sat inside her answer. The transcript doesn't say who speaks, so I measured each
  word's pitch: she speaks at about 200 Hz, his two words measured 94 and 90 Hz. Both cut. This is now `voice-pitch.py`.
- **The paper cut misread a deliberate repeat** ("five percent is going to happen five percent of the time") as a
  restart and dropped the first "five percent", which would have broken her point. Fixed by hand.
- **Three edges would have damaged words**, all from the automatic steps:
  - "outcomes" would have played as "out-": the edge fix had moved the cut into the tiny silence of the "t".
  - "work" would have been cut off: Parakeet had placed it 0.2 s early.
  - The host's "Right." had crept back in: Parakeet stretched "overestimated." to 1.5 s, so the kept line ran on through his word.

  The fix was reading the audio level around each edge. This is now `edge-levels.py`, and the final check confirmed
  0 of 65 words missing.

### v1: full-frame vertical

What it had:
- The landscape video cropped to 9:16 on her face.
- DM Sans in white with cyan word-by-word captions.
- A hook title, a "5%" count-up, a punchline chip and a closing headline.
- The wide two-shot shown whole over a blurred fill.
- Music: *Icelandic Arpeggios* (DivKid, YouTube Audio Library).

**Your notes:** you didn't like the font, its colour or its placement; you wanted motion graphics; and the zoomed crop
looked low quality.

**Why it looked soft:** a 9:16 window of a 1080p frame is only 608 px wide, so it must be enlarged 1.78x to fill
1080 px. No setting fixes that; only 4K or vertical footage would.

### v2: the card look

What changed:
- The whole video in a card, downscaled instead of enlarged, so it's sharp.
- A dark animated background.
- Rubik Mono One (you asked for "BlockRub", which doesn't exist anywhere I could find; you chose this instead), white
  with a black outline, yellow highlights.
- A headline that strikes through "BAD LUCK" when she says "not really", then flips to "IT WAS OVERCONFIDENCE".
- 20 dots with one lit for "5% = 1 in 20".
- A certainty meter that overfills into red.
- Emoji pops.

**Your notes:** the type was too big; you didn't want the source chip or stock emoji, and wanted elements animated
here instead; you wanted sound effects; and it shouldn't feel AI-edited.

### v3: hand-made and with sound (approved)

What changed:
- **Smaller type:** title 70 px, captions 56 px.
- **No chip:** credit the podcast in the description instead.
- **Elements drawn and animated here, not stock:**
  - marker shock lines by her head on "surprised"
  - a 3D die that tumbles and lands on a red 1 on "unlucky"
  - a marker strike through "BAD LUCK"
  - a marker circle around the lit dot
  - an "expected vs reality" chart that draws itself
  - an underline under "OVERCONFIDENCE"
- **Plain captions:** only six meaning words in yellow, instead of highlighting every word as it's spoken (that's the
  most recognisable sign of auto-generated captions).
- **Eight sound effects,** each on the exact frame of its visual: whoosh, dice rattle, marker scribble, ping, whoosh,
  pop, riser, error buzz. Each one measured 9–14 dB under her voice.

**One bug caught in v3's snapshots:** the red strike showed from the first frame. Strokes that stretch with text can't
use the usual "draw-on" trick in Chrome, so they're now revealed with a wipe.

---

## 5. The lessons, and the reasons behind them

**Cutting**
- Trust the transcript for where words *start*, the audio for where they *end*: Parakeet stretches the last word of a
  sentence into the pause after it.
- Every automatic edge fix needs a human-style look at the level chart. An edge belongs in silence between two words,
  never in a dip inside a word.
- In a conversation, check for a second voice before cutting. Pitch tells voices apart well (about 90 Hz vs 200 Hz here).

**Design**
- Never enlarge a 1080p landscape video to fill 9:16. Use the card look, or record vertical or in 4K.
- Text on a Short is smaller than it feels when designing: 70 px headlines and 56 px captions read fine on a phone.
- Keep everything out of the bottom quarter (YouTube's title and music bar) and the lower right edge (the like and share
  buttons).
- One graphic at a time in the space under the captions.

**Making it feel human-edited**
- Highlight the few words that carry the meaning, not every word as it's spoken.
- Draw elements here rather than using stock stickers. Hand-wobbled strokes in a marker's rhythm look made by a person.
- Vary the motion: different speeds and eases, a bounce where something physical would bounce.
- Give every animated element its sound, quietly and exactly on its frame.

**Sound and music**
- Measure levels; don't guess. Music under nonstop talking needed +8 dB here, because the ducking holds it down most of
  the time. At -12 dB it was 37 dB under the voice and inaudible; +8 put it 18 dB under, which is right.
- Use music and sounds you have the rights to. Commercial songs get Content ID claims on Shorts. The safe files from
  your music folder were *Icelandic Arpeggios* (YouTube Audio Library) and the Pixabay tracks.

**Checking**
- Snapshot before rendering, every time. Every visual bug in this project was found in a snapshot, not a render.
- Verify the finished file, not the render: colour tags and loudness are only right after `finish.py`.

---

## 6. Making your next Short

**The prompt:**

> Use my youtube-shorts skill to make a Short from `D:\Projects\automation\transcripts\output\Mark3\clips_video\clip_04.mp4`.
> Use the card look like clip-03 (`examples/clip-03/storyboard-v3.json`), music from `E:\Download\Music`, and add sound effects.

**What to expect:**
1. Claude transcribes and cuts it, checks for the host's voice, and shows you `PAPER-CUT.md` with the length.
2. It plans the headline and 3 to 5 animated elements tied to what's said, and shows you a snapshot sheet.
3. You give notes in plain words ("the chart is too small", "no sound on the die"), then it renders, finishes and checks.
4. Files arrive in `Videos\YouTube Shorts\<name>\`, with and without music.

**Checklist before you upload:**
- [ ] Watched it once on a phone with the sound **off**: the headline and captions carry it.
- [ ] Watched it once with sound: every effect is on its moment, none covers a word.
- [ ] `VERIFY.md` says PASS.
- [ ] Description credits the podcast (and the music, if its licence asks for it).
- [ ] You have the right to post the clip (your own show, permission, or the show's clipping programme).

**To make a rule permanent,** say "save this to the skill" after a note. Claude adds it to `youtube-shorts/SKILL.md`,
and the next Short starts from it.

---

## 7. Glossary

| Term | Meaning |
|---|---|
| **Flat cut** | The clip with mistakes and pauses removed, before any effects. |
| **Jump cut** | A cut inside one continuous shot, where the speaker jumps slightly. |
| **Paper cut** | The written list of what to keep and remove, before touching the video. |
| **Anchor** | The spoken words an element belongs to; the checks prove it appears on them. |
| **Storyboard** | `storyboard.json`: every element, word timing, camera move and sound of the Short. |
| **Composition** | The HTML page (`index.html`) HyperFrames renders into video. |
| **GSAP / timeline** | The animation library; every animation is placed on one timeline at an exact time. |
| **Snapshot** | A still frame of the page at a given time, taken before rendering. |
| **LUFS** | Loudness unit. YouTube plays everything at about -14 LUFS, so we deliver at -14. |
| **dBFS / "dB under"** | Level in decibels. 10 dB quieter sounds about half as loud. |
| **Ducking (sidechain)** | Music automatically turned down while someone speaks. |
| **BT.709** | The colour standard for HD video; files must be tagged with it or players show skin redder. |
| **CRF / bitrate** | How much quality the encoder keeps. We render at about 12 Mb/s for 1080x1920. |
| **Card look** | The layout with the whole landscape video in a card and graphics around it. |
| **Content ID** | YouTube's copyright matcher; a claimed song can mute or demonetise a Short. |

---

## 8. Licences and rights

- **Fonts:** DM Sans and Rubik Mono One, under the SIL Open Font License (free, including commercial use).
- **Emoji SVGs:** Noto Emoji, under an open licence (no credit needed). We stopped using them in v3, but they ship with the skill.
- **Sound effects:** Pixabay, via the HyperFrames library, under the Pixabay Content License (commercial use allowed, no
  credit required). `dice-roll.wav` is remixed from Pixabay clicks; `scribble.wav` was generated here.
- **Music:** *Icelandic Arpeggios* by DivKid (YouTube Audio Library). Check the track's own terms in the Audio Library
  in case it asks for credit in the description.
- **Footage:** the podcast belongs to its owners. Posting clips of it needs their permission (or their clipping
  programme), and a credit in the description.
