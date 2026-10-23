---
name: pro-shorts
description: The creator's house editing style for YouTube Shorts, Reels and TikToks cut from long videos (podcasts, interviews, shows, streams). Takes a long episode or a raw clip all the way to an upload-ready 9:16 Short - finding the best moments, fresh cuts from the master, letterboxing, animated word-by-word subtitles, hand-made motion graphics tied to the footage (punch-ins, shakes, flashes, elements behind the cut-out speakers), transitions on the cuts, sound effects, a Content-ID-safe music bed timed to the beat, and a measured mix. Use this skill whenever the user gives a video or clip path and says "edit this clip", "make a Short", "find the best/funny moments", "clip this episode", "fresh cut", "add subtitles / motion / sfx / music", "edit it like before", or asks for any next version of a Short - even if they don't name the skill.
---

# Pro Shorts: the house editing style

This is the edit the creator approved on CODPOD EP12 #3 "No spoilers" (v5) after five rounds of notes. Every rule
here came from a note on a real Short; follow them and the output starts at that level instead of at v1.
Worked example (all files): `videos/codpod-12/m03/subs/` (`build-motion-v5.py`, `captions.json`) and the Short
`~/Videos/YouTube Shorts/codpod-12/codpod12-03-no-spoilers-short-v5.mp4`.

**Read first, every time:** `youtube-shorts/NOTES.md` (the creator's standing corrections: the font round robin,
plain text, no progress bar, captions simple, letterbox landscape). A note there beats anything here.

**Tools this skill uses:** the scripts in `scripts/` (below) plus `youtube-shorts/scripts/` (`subtitles.py`
builds the page, `finish.py` levels and tags, `verify-render.py` checks). Python, FFmpeg and `npx hyperframes`
(render, transcribe, snapshot, beats, remove-background). On Windows set `PYTHONUTF8=1`. Run from the project root.

## What the creator wants (and has rejected)

- **Wants (NOTES 19 overrides the older v5 look):** a simple, clean Short, not an over-produced one: the speaker,
  clean subtitles, B-roll where it helps, plain transitions, **as few motion graphics as possible** (often 0 to 2),
  very few and quiet sounds, a music bed you feel but never fight.
- **Rejected:** too many motion graphics and loud graphic sounds (NOTES 19); text-only graphics (a big word, a
  kinetic headline); the "card look" (footage in a rounded card with headlines, meters and charts around it) as a
  default; thin single-colour line icons ("very simple, not professional"); outlined or shadowed text; a progress
  bar; anything judged from still frames only.
- **The default order of work, checkpoints in bold:** moments → **the cut** → prep → **snapshot sheet** → render →
  mix → deliver (with the thumbnail). Ask before every download (models, music, sound packs). One step per round when they say "step by step".

## 1. Find the moments (a long episode)

```bash
python .claude/skills/pro-shorts/scripts/moments.py --master "E:/path/episode.mp4" --out videos/<episode>   # background: ~15 min / 40 min
```
Read `transcript.txt` (and `frames/overview.jpg` for who is who and the cutaways). Pick 10 moments of 15 to 60 s
that stand alone: a hook line in the first seconds, one idea, a payoff at the end (ideally one that loops back).
`references/moments.md` has what makes a moment and the write-up format; save the shortlist to `MOMENTS.md`.

## 2. Fresh cuts from the master (checkpoint: the cut)

Write `videos/<episode>/keeps.txt` (one kept piece per line, phrases copied from `transcript.txt`), then:
```bash
python .claude/skills/pro-shorts/scripts/cutplan.py  --episode videos/<episode>              # edges snapped to quiet gaps, lengths, >60 s flagged
python .claude/skills/pro-shorts/scripts/cutmaster.py --episode videos/<episode> --master "<master>" --prefix <ep> 01 02   # 1-2 per call, foreground
python .claude/skills/pro-shorts/scripts/checkcut.py  --episode videos/<episode> 01 02         # every edge word heard
```
Native size, frame rate and level, no editing. Drop asides (a job title, "what's the code") to stay under 60 s;
start on a full sentence; never invent or reorder what was said. **The first 3 seconds** (NOTES 13, from real
retention): the speaker on screen from frame 0, the claim said by ~3 s, no B-roll, stock photo, title card or
graphic over the speaker before it; cut away to who is named only after the claim. A fresh cut is a deliverable on its own: when the
creator asks for "just the cuts", stop here.

## 3. Prep one clip

```bash
python .claude/skills/pro-shorts/scripts/prep.py --clip videos/<episode>/cuts/<file>.mp4 --out videos/<episode>/mNN/subs --depth
```
Letterboxes a landscape clip sharp on black (1080 wide, centred; the picture y and h land in `window.json` with the
shot changes), transcribes it, cuts the people out (`--depth`, ~10 min CPU per 18 s; the model download needs a yes
the first time) and writes `shots.png` (one frame per shot: find each face for punch-in origins). Then **fix the
transcript** (misheard names and slang, "twenty six" → "26", never add a word nobody said; flag guesses to the creator).

## 4. Music (Content-ID safe, timed to the line)

```bash
python .claude/skills/pro-shorts/scripts/music.py map --track videos/_shared/music/<track>.mp3       # energy + drop candidates
python .claude/skills/pro-shorts/scripts/music.py bed --track <track> --drop <s in track> --land <s in clip> --len <clip s> --out <subs>
```
Pick the mood (playful groove for funny, cinematic piano for emotional, trap for a rant or a flex). Land the drop on
the turn or the payoff line. Tracks: Pixabay only, never "Content ID Registered", credited in
`videos/_shared/music/CREDITS.md`. `bed` also writes `beats.json`. Details: `references/sound-music.md`.

## 5. Design the motion (keep it minimal: NOTES 19)

**Approved minimal example: `videos/clash-cam/m05/subs/build-motion.py`** (clashcam-05 v1, "I love this edit"):
Cam from frame 0 with the hook in the band, two B-roll moments as photo cards in the black band above the picture
(plain fade-up in and out, < 3 s, never over the speaker), gentle creeps, one zoom-blur, 3 pops at 0.09. Start from it.
The kit has it as two calls: `k.band_broll(id, img, name, sub, t_in, t_out)` (the card, its fades and the pop) and
`Kit.shot_camera([(shot_start, (x, y), zoom), ...], end, zoomblur=(t,))` (a reset and a creep per shot); see
`videos/clash-cam/m07/subs/build-motion.py`.

**Default is no graphic.** Add one only when the viewer would not understand the line without it, and never a
graphic that is only text: if a word or number really must be shown, put it on a real element (a photo card, a UI
card, an object from the clip). B-roll of what is named comes before any drawn graphic. The rules below are *how*
to make the few graphics that pass that test.

Copy `templates/build-motion.py` into the clip's `subs/` and rewrite its MOMENTS block for this clip. It uses
`scripts/motionkit.py`, so each idea is a few lines: `big_word`, `icon` (shaded trophy / heart / padlock),
`card`, `number`, `star`, `burst`, and the moves `slam`, `pop`, `fly_from`, `slide_in/out`, `drop_in`, `x_slam`,
`delete`, `exit_fall`, `pulse_on_beats`, `count`, plus `beat()` to snap a time to the music.

- **One element per idea, on its word, and only the ideas that need it** (usually 0 to 2 per Short); leave the
  rest to the subtitles. No `big_word` / kinetic text on its own.
- **Designed, not drawn:** filled shapes with a gradient and a highlight, real-looking UI (comment cards, a like
  count), bold sizes (a big word spans the frame; an icon ~230 px). Never a bare outline icon.
- **Motion principles on every move:** anticipation → move with motion blur → overshoot → settle; squash on impact;
  a secondary detail on each hit (a burst of rays, sparkles). Why and how: `references/motion.md`.
- **Tied to the footage:** behind the people (`layer="behind"`, needs the cut-out) for words and objects that live
  *in* the scene; in front for things that fly *at* the camera; out of a mouth or from behind a shoulder.
- **On the beat:** snap every move the speech does not pin (`k.beat(t)`); keep word-locked hits on the word; land
  the biggest entrance on the drop; let held elements pulse on beats.
- **The camera block, simple:** a gentle punch-in or slow push now and then, a reset on every shot change, and at
  most **1 to 2 simple transitions** (a short `zoomblur` or a plain crossfade) on the source's cuts into a turn.
  No shakes, white flashes or whips by default. `references/camera-transitions.md`.
- **Catalog first** (`references/catalog.md`): before hand-drawing an element, `scripts/catalog.py search "<the move>"`
  the HyperFrames catalog (~450 render-tested blocks), fetch the closest, and port its look and motion onto `tl`.
  Ported already: `lower_third`, `post_card`; from approved Shorts: `photo_card` (B-roll of who is talked about,
  NOTES 14), `type_beat`, `checklist`. Never emoji-style icons (NOTES 15).
- **B-roll, generously** (NOTES 13 to 15, 18, 20): read the transcript for what is named but not on screen (a
  person, a place, a team, a product, an event) *and* the concrete things a line paints (an action, a play, a
  stat made visual: "crushing it 400 feet" = a home run photo). Aim for ~1 B-roll per 8 to 10 s of talk (3 to 5 in
  a 30 to 40 s Short); a Short with none looks bare (clashcam-01 v2). It is the main visual, not decoration.
  **On topic only** (NOTES 21): every photo must be about what the clip is discussing, not a literal match for one
  word (a boxing photo on "knock you out" in a baseball-vs-football debate was rejected). Find it by searching the browser for the thing named (real photos or
  footage; prefer freely licensed sources such as Wikimedia Commons; ask before each download), save it to
  `<subs>/broll/`, resize to ~600 px, and show it in the picture window or as a `photo_card` in the band, on the
  word that names it. **Each B-roll is visible 3 s at most**, then back to the speaker. Never before the claim.
- **Sounds by hand** (`k.sound`): only on the few things that move, **quiet (0.05 to 0.15**, `k.sound` refuses
  above 0.18), never two inside 0.3 s (`k.write` warns), about 3 to 6 in a whole Short. A B-roll or transition
  can go silent. The subtitles' own punch whooshes count.

Subtitles come from the same spec (`captions.json`, read by `subtitles.py`): the next font in the NOTES round robin,
a `"preset"` for the animation, y ~1380 under a letterboxed picture, `em` on ~5 meaning words, 2 `punch` phrases (one
mid-clip, the payoff). Keep them plain. The presets (`youtube-shorts/templates/subtitle-presets.json`; each sets style,
size, line length and case, and a key in the spec still wins): `clean` (words rise in), `box` (yellow box jumps word
to word, uppercase), `bounce` (each word bounces in yellow), `karaoke` (dim line, words light up), `wipe` (each word
wipes in left to right, uppercase), `calm` (whole line fades in, only em words change). Every preset runs captions to
**two rows** (`"rows": 2`, split evenly) so each stays up long enough to read; a punch stays on one row. **No
underline or bar under any word.** Use a different preset from the last Short (NOTES 24).

## 6. Build, check, render

```bash
python <subs>/build-motion.py
python youtube-shorts/scripts/subtitles.py --video <subs>/edit.mp4 --spec <subs>/captions.json --out <subs>/public --shared videos/_shared --snap
npx hyperframes check <subs>/public                 # 0 errors; fix contrast warnings (an avatar colour, a grey word)
npx hyperframes render <subs>/public --fps 30 --video-bitrate 12M --workers 1 -o <subs>/render-raw.mp4    # ~1.5-2 min per 18 s
python .claude/skills/pro-shorts/scripts/strips.py --render <subs>/render-raw.mp4 --out <subs>/strips name:start:end ...
python .claude/skills/pro-shorts/scripts/hookcheck.py --subs <subs> --claim "<the claim's words, as said>"
```
`hookcheck.py` FLAGs late speech, a claim after 3.5 s, no hook text at frame 0 and graphics before the claim; it
lists each shot change before the claim as LOOK and writes `hook-strip.png`: open it and confirm the speaker is
on screen in every frame up to the claim (an angle change is fine, a cutaway is not). Fix every FLAG before mix.
**Checkpoint: the snapshot sheet** before the first render of a clip. **After every render, review the motion in
strips** (12 to 30 fps around each element and transition), not stills: stills hid leftover dots, a hazy leak and a
trophy too dark. Fix, re-render.

## 7. Mix, verify, deliver

```bash
python .claude/skills/pro-shorts/scripts/mix.py --subs <subs> --name <ep>-NN-<slug>-short-vN --deliver <episode-folder>
```
Levels to -14 LUFS, measures the bed until it sits ~18 dB under the voice (the right gain differs per track:
always measured), runs `verify-render.py` with the clipped-words check, copies the Short and its no-music twin to
`~/Videos/YouTube Shorts/<folder>/`. A "clipped word" on a fast or overlapping line is usually ASR noise: transcribe
that stretch alone before calling it a clip. Black flashes that are in the source edit stay.

Report: what is on screen and when (a short table), what you fixed in review, the checks, your own concerns
(a guessed word, a name to confirm, rights for someone else's show), and update the font line in NOTES.md.
Offer a title and description when asked (for a show: its name and platform worked into the text, its hashtag).

## Basic edit (one moment, no extras)

When the user asks for a "very basic" edit, or just a plain Short from a moment in `moments.json`, skip steps 3 to 7
and run the basic builder. It puts the fresh cut on a 1080x1920 black frame (the whole 16:9 picture, not cropped),
burns the transcript's own words under it as plain subtitles, keeps the original voice, and writes the upload .txt:

```bash
PYTHONUTF8=1 python .claude/skills/pro-shorts/scripts/basic_short.py --moments "E:/AutoEdit/<video>/moments.json" \
    --id m03 --prefix <show> --transcript videos/<episode>/transcript.json
```
It writes `E:/AutoEdit/<video>/edited/<prefix>-NN-<slug>-short-v1.mp4` and `.txt`, and marks the moment `edited` in
`moments.json`. It refuses to overwrite. The moment's `caption` field (own words, the positive line about the guest,
`#Ad` on its own line for the Clipping Culture campaign) goes into the .txt, so set it before running. No music, no
B-roll, no motion: add those with the full steps above only when asked.

## Keep it learning

Every note the creator gives becomes a rule: a standing correction goes in `youtube-shorts/NOTES.md`; a technique
goes in the right reference file here; a reusable move goes into `motionkit.py`. Version every Short (v1, v2...)
and keep each builder (`build-motion-vN.py`) so changes can be compared. Still open on the roadmap (offer them,
one at a time): face tracking, a larger layered sound library, a finishing pass (grade, grain, vignette),
speaker-coloured subtitles, making depth + beats automatic for every clip, and more rules from real retention
graphs (the first one is NOTES 13; read each Short's curve in YouTube Studio a few days after upload).
