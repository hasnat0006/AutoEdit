---
name: youtube-shorts
description: Edit a YouTube Short end to end in Claude Code. A Short here is always 9:16, 1080x1920, 30 fps and 60 seconds at most. Takes a raw phone or camera clip (retakes and all), a landscape recording to reframe, or a section of a longer video, cuts it, reframes it vertical, adds word-by-word captions, animated overlays, B-roll, camera punches and the few sounds that earn a place, then renders locally with HyperFrames and delivers a loudness-levelled MP4. Use whenever the user says "make a Short", "edit this Short", "vertical video", "9:16", "Reels/TikTok-style", "cut this into a Short", "add captions to this Short", or drops a clip and asks for a Short.
---

# YouTube Shorts editor

Turns raw footage into a finished Short: the cut, the vertical frame, captions, overlays, camera moves, sound and an
upload-ready MP4. Everything runs on your own machine through HyperFrames (Chrome + FFmpeg); no footage leaves it.

**The fixed spec. Every Short, no exceptions:**

| | |
|---|---|
| Frame | 1080x1920 (9:16), rendered 1:1 with `--resolution portrait`; never 4K, never a different shape |
| Frame rate | 30 fps |
| Length | 60.0 s at most. `compose.py` refuses a longer storyboard and `verify-render.py` / `finish.py` fail a longer file |
| Video | H.264, ~12 Mb/s, BT.709 tags |
| Audio | voice at -14 LUFS, true peak under -1 dBTP, AAC 48 kHz stereo |

**The house style:** light glass cards, DM Sans 700, cyan for key words, amber
for money, magenta for punchlines, a camera anchored to the top of the frame, and silence unless something on screen
makes a sound. `STYLE-GUIDE.md` (in the kit folder) is the look; when it changes, update the matching rules here and the
`:root` colour tokens in `scripts/compose.py`.

**Before every Short, read `NOTES.md`** (next to this file): the creator's corrections from past Shorts. Every note
there applies to every Short, and beats a rule here when they disagree.

**This skill keeps learning.** When you give a note worth keeping, say **"save this to the skill"**: Claude writes it into
the right section here as one plain rule. See "Keeping the skill yours".

Commands run from your project folder with `SK=".claude/skills/youtube-shorts"` and `W="videos/<short>"` (one folder per
Short).

## Setup check (first use, and after any update)

| Needs | Check | Install when missing |
|---|---|---|
| Node.js 22+ | `node -v` | nodejs.org |
| HyperFrames CLI | `npx hyperframes --version`, then `npx hyperframes doctor` | comes through npx |
| FFmpeg + ffprobe | `ffmpeg -version` | `winget install ffmpeg` (Windows), `brew install ffmpeg` (Mac) |
| Python 3 + numpy | `python3 -c "import numpy"` | `python3 -m pip install numpy` |
| auto-editor | `auto-editor --version` | `pip install auto-editor` |
| Parakeet | transcribe a 5 s WAV with `--engine parakeet --json` | `npx hyperframes models install parakeet` |
| Google Chrome | snapshots and renders run in it | google.com/chrome |
| GSAP (local) | `$SK/assets/vendor/gsap.min.js` exists | ships with the skill; otherwise the first render needs internet |

Then `cd "$SK/scripts" && python3 -m unittest tests` must end with `OK`. Run it after touching any script.

**Windows:** `python3` must be the real Python, not the Microsoft Store stub (a `python3.exe` copy next to `python.exe`
fixes it), and `PYTHONUTF8=1` must be set (the scripts write UTF-8). Never call `npx` from Python as a bare `"npx"`;
resolve it with `shutil.which("npx")` (it is `npx.cmd`).

**Low memory (8 GB or less):** always render with `--workers 1`. HyperFrames switches to its low-memory profile by
itself at 8 GB; close Chrome tabs and other apps before a render.

- **What ships:** the scripts and the DM Sans 400/500/700 subsets in `assets/fonts/` (SIL OFL). **No sounds, images,
  logos or footage.** Keep yours in a shared folder that compose.py copies with `--shared DIR` (`DIR/img/`, `DIR/sfx/`):
  sounds from Epidemic Sound or the free HyperFrames library (`npx hyperframes skills update media-use`), logos from
  the brands' press kits.

## The routes

| Input | Route |
|---|---|
| **Any raw clip, "edit this clip"** (the default) | **The house structure** (below): cut, letterbox, hook, animated subtitles, sounds, music |
| One vertical phone clip (1080x1920 or 2160x3840) | Cut stage → `reframe.py` (scales) → Pipeline |
| One landscape clip (podcast, interview, camera) | Cut stage → **the card look** (the flat cut whole in a card, graphics around it) → Pipeline. `reframe.py --x` (a 9:16 crop) only for a 4K source when the creator asks for full-frame |
| Several clips for one Short | `ingest.py --concat` → the same on `source.mp4` |
| A section of a longer video | `phrase-times.py` finds the start and end lines → `hand-cut.py --keep A-B` → Cut stage from tighten-cut on |
| A raw take over 60 s | the Cut stage, then cut lines at Checkpoint A until the flat cut is under 60 s |
| **A clip that is already edited** ("just animate the subtitles") | **Captions only** (below): no cut, no reframe, no headline or graphics; `subtitles.py` adds motion-graphic captions and their sounds over the picture as it is |

Two checkpoints, everything else unattended. **A, the cut:** `PAPER-CUT.md` plus the flat length; you answer in plain
words ("drop the line about pricing"). **B, the plan:** `storyboard.json` + `snaps/sheet.png`. Then render, finish,
verify, deliver.

**The hook gate** (every Short, at Checkpoint B):
- **The first frame is the hook.** Frame 0 shows the promise as text (a `text` beat with `"in": 0`, on screen with no
  entrance) over a meaningful picture, not a settling camera. The feed autoplays: there is no title card and no intro.
- **It works muted.** The first line on screen says the promise on its own; captions carry every word after it.
- **Something changes in the first 1.5 s:** a punch-in on the first stressed word, a card, or a cutaway.
- **One promise, paid off before the end.** Close the loop, then stop: no outro, no "thanks for watching".
- **Loop it:** the last line leads back into the first (the Short replays); end on the payoff word, not on silence.

## Recording so the cut works

- **Vertical on a phone** (1080x1920 or 4K vertical, 30 fps), or landscape **in 4K** with you near the centre (a 1080p
  landscape clip gives a 608x1080 window, upscaled 1.78x: soft; `reframe.py` warns). Flat: no in-camera zooms or filters.
- Eyes in the top third of the vertical frame; a hand's width of headroom. Nothing important in the bottom quarter or the
  right edge (YouTube's buttons sit there).
- **Fluff a line? Pause two seconds and restart the whole sentence.** The last take wins. "Cut that" drops a stretch.
- Say numbers in full ("a thousand dollars a month"), name tools out loud, say lists as lists. Script to ~140 words for
  a 60 s Short; the cut always comes out shorter than the read.

## Scripts (`scripts/`)

| Script | Does | Options |
|---|---|---|
| `ingest.py` | probe, order and join several raw clips | `--raw --out [--concat] [--order A,B] [--only A,B]` |
| `paper-cut.py` | what to remove: restarts, "cut that", retakes (keeps the last), false starts, long pauses | `--transcript --duration --out-dir --speech` |
| `hand-cut.py` | rebuilds `cut-list.json` from the lines you keep | `--keep A-B` `--transcript --speech --duration --out-dir` |
| `tighten-cut.py` | trims lead-ins, tails and inner pauses by the sound | `--audio --cut-list --out [--lead 0.07] [--tail 0.11] [--maxgap 0.30]` |
| `sliver.py` | breath-only segments, leaked fragments, edges under 40 ms | `--cut-list --audio [--fix]` |
| `edge-audit.py` | every cut edge checked by the audio | `--audio --cut-list --transcript [--keeps FILE] [--fix]` |
| `apply-cut.py` | one frame-accurate re-encode + `cut-map.json` (every jump cut) | `--input --cut-list --out` |
| `dead-air.py` | every pause over 0.40 s after a sentence (0.45 s elsewhere) | `W [--plan] [--keep T] [--target 0.30]` |
| `patch-cut.py` | small fixes to a cut list | `--cut-list` with `--add A-B`, `--drop T` or `--drop-flat A-B` |
| `phrase-times.py` | where a phrase is said | `--transcript "phrase" ... [--after T]` |
| `voice-pitch.py` | which words another voice said (the host's "Yeah." inside a guest's answer), by pitch | `--audio --transcript [--ratio 0.7] [--all]` |
| `edge-levels.py` | the audio level around every cut edge, with the words: proves no edge sits inside a word | `--audio --cut-list --transcript [--pad 0.4]` |
| `reframe.py` | the flat cut → 1080x1920 footage (vertical scaled, landscape windowed), same length and audio | `--in --out [--x 0.5] [--keys "t:x,..."]` |
| `compose.py` | `storyboard.json` → `public/index.html`, 1080x1920; refuses over 60 s | `--spec --out [--shared DIR]` |
| `beat-check.py` | each anchored element enters 0.10 s after to 0.60 s before its word | `--index --transcript [--suggest]` |
| `gap-scan.py` | where the picture goes static (captions do not count): hook > 2.5 s, body > 4 s, ceiling 6 s | `--index [--hook 5 --early 2.5 --body 4 --max 6]` |
| `snap-beats.py` | the first frame, every beat, caption moments → `snaps/sheet.png` (5 across) | `--project [--at T ...]` |
| `broll-conform.py` | a stock or generated clip / still → a 1080x1920 cutaway (or 1080x960 with `--half` for a split) | `--in --out [--start] [--dur] [--focus 0.5] [--half] [--grade] [--push]` |
| `finish.py` | voice to -14 LUFS, optional ducked music bed, BT.709 tags, picture copied; fails a non-Short | `--in --out [--music F --music-db G [--no-duck]]` (measure G: see Sound) |
| `verify-render.py` | black frames, 1080x1920, tags, bitrate, duration, 60 s cap, A/V, clipped words | `--render [--index] [--words --kept]`; exit 1 on a FAIL |
| `storyboard-md.py` | the delivery `STORYBOARD.md` | `--title --project dir:slug:title --out` |
| `subtitles.py` | captions only: motion-graphic captions + their sounds over a finished edit, at the clip's own size | `--video --spec captions.json --out [--shared DIR] [--snap] [--at T]` |

## Cut stage (raw clip to flat cut)

```bash
mkdir -p "$W/raw" "$W/public" && cp "<clip>" "$W/raw/"
ffmpeg -y -v error -i "$W/raw/<clip>" -vn -acodec pcm_s16le -ar 16000 -ac 1 "$W/audio-raw.wav"
npx hyperframes transcribe "$W/audio-raw.wav" -d "$W" --engine parakeet --json && mv "$W/transcript.json" "$W/transcript-raw.json"
auto-editor "$W/raw/<clip>" --edit audio:-30dB --margin 0.12s,0.35s --export v1 -o "$W/speech.v1"
python3 "$SK/scripts/paper-cut.py" --transcript "$W/transcript-raw.json" --duration <seconds> --out-dir "$W" --speech "$W/speech.v1"
#   read PAPER-CUT.md; fix misreads with hand-cut.py
python3 "$SK/scripts/tighten-cut.py" --audio "$W/audio-raw.wav" --cut-list "$W/cut-list.json" --out "$W/cut-list.json"
python3 "$SK/scripts/sliver.py" --cut-list "$W/cut-list.json" --audio "$W/audio-raw.wav" --fix
python3 "$SK/scripts/edge-audit.py" --audio "$W/audio-raw.wav" --cut-list "$W/cut-list.json" --transcript "$W/transcript-raw.json" --fix
python3 "$SK/scripts/edge-audit.py" --audio "$W/audio-raw.wav" --cut-list "$W/cut-list.json" --transcript "$W/transcript-raw.json"   # 0 issues
python3 "$SK/scripts/edge-levels.py" --audio "$W/audio-raw.wav" --cut-list "$W/cut-list.json" --transcript "$W/transcript-raw.json"
#   read it: every edge in a quiet run BETWEEN words (the automatic fixes can land in a silence inside a word)
python3 "$SK/scripts/apply-cut.py" --input "$W/raw/<clip>" --cut-list "$W/cut-list.json" --out "$W/flat.mp4"
ffmpeg -y -v error -i "$W/flat.mp4" -vn -acodec pcm_s16le -ar 16000 -ac 1 "$W/audio.wav"
npx hyperframes transcribe "$W/audio.wav" -d "$W" --engine parakeet --json
python3 "$SK/scripts/dead-air.py" "$W" --plan       # patch-cut --drop-flat each range, edge-audit, apply-cut, again until 0
python3 "$SK/scripts/reframe.py" --in "$W/flat.mp4" --out "$W/public/input-video.mp4" [--x 0.5 | --keys "0:0.5,12.37:0.40"]
ffmpeg -y -v error -i "$W/public/input-video.mp4" -vn -acodec pcm_s16le -ar 16000 -ac 1 "$W/audio.wav"
npx hyperframes transcribe "$W/audio.wav" -d "$W" --engine parakeet --json      # transcript.json: captions and anchors
```

`<seconds>` is `ffprobe -v error -show_entries format=duration -of csv=p=0 <clip>`. **The length gate:** after the
first apply-cut, print the flat length. Over 60 s, propose at Checkpoint A which lines go (the weakest example, a second
reason, a setup the picture can show) before anything else runs.

**The cut rules** are tight: paper-cut keeps the last take; sentence starts come from Parakeet,
ends from the audio; audit every edge by the audio; dead air over 0.40 s after a sentence goes (a Short has no room for a
beat unless it is the joke's pause, `--keep T`). A cut in the quiet dip before a sentence's last word deletes the word:
after every apply, compare each segment's last word with the fresh transcript. After every apply, scan the flat
transcript for the same 3 to 4 words twice within 7 s (a restart hand-cut kept).

**Reframing a landscape clip:** `--x` is where your face is across the source (0.5 = centre). When you move, put a
`--keys` change on a jump cut from `cut-map.json` (never mid-shot: the window jumps). Snapshot the result before
composing: your eyes belong in the top third.

## Podcast and interview clips (learned on clip-03, a two-person podcast)

A clip cut from someone else's long conversation has problems a solo recording does not:

- **Two voices, one transcript.** The host's "Yeah." / "Right." sit inside the guest's answer and Parakeet does not
  say who spoke. Run `voice-pitch.py` on the raw audio: on clip-03 the guest measured ~200 Hz and the host's words 94 and
  90 Hz. It also flags the odd low word of the main speaker (a dropped "like" at 138 Hz), so listen before cutting.
  Cut an interjection in the quiet gaps either side of it; if there is no gap, keep the guest's words whole.
- **It starts and ends mid-sentence.** Start at the first full sentence (a restart like "they're almost, they're
  constantly" keeps the second take). End on the payoff line, ideally one that leads back into the first line, so the
  Short loops ("...the way the world was gonna work" → "They're constantly surprised...").
- **paper-cut misreads a deliberate repeat as a restart:** "five percent is going to happen five percent of the time"
  lost its first "five percent". Read `PAPER-CUT.md` against the meaning, then set the lines with `hand-cut.py`.
- **hand-cut can swallow the next speaker:** Parakeet stretched "overestimated." to 1.5 s, so the kept line ran on through
  the host's "Right." and merged with the next line. Check every segment end against `edge-levels.py`.
- **The automatic edge fixes can clip a word:** `edge-audit --fix` pulled one end back into the silent "t" inside
  "out|comes" (only "out-" would have played), and Parakeet placed "work" 0.2 s early so the end cut it off. The fix is
  the level chart: an edge belongs in a quiet run between two words. `verify-render.py --words --kept` on the finished
  file is the final proof (0 missing).
- **The source is already edited** (camera changes, a wide two-shot): find its cuts with
  `ffmpeg -i flat.mp4 -vf "select='gt(scene,0.2)',metadata=print:file=-" -f null -`. The card look needs nothing for them;
  a 9:16 crop needs the wide shot shown whole over a blurred fill.
- **Not 30 fps (learned on demi-01, a 23.976 fps interview):** auto-editor 29 writes no `timebase` into `speech.v1`,
  so the cut scripts used to read its frame counts as 30 fps and put every speech chunk at 80% of its real time
  (hand-cut dropped the last 4 s of the answer). `speechv1.py` now takes the rate from the source video; if a hand cut
  looks short, print `speechv1.chunks(...)` against the transcript. apply-cut converts to 30 fps and can come out one
  frame long (a DRIFT exit 2): re-encode with `-t <flat_duration>`.
- **The camera cuts to the other person on the last word:** end the audio where the word ends, and hold the guest's
  last frame over the remaining frames (`trim=end=<cut>,tpad=stop_mode=clone`) rather than flash 5 frames of the host.
- **Two voices at the same pitch** (two women, ~200 Hz each): `voice-pitch.py` cannot split them; find who is on
  screen with the scene-cut list and a contact sheet of frames instead.
- **Their brand stays theirs:** the source's own logo bug stays visible in the card; credit the show in the description.
  Reposting someone else's podcast needs their permission or a clipping programme: say so to the creator.

## The house structure (the default edit)

**"Edit this clip" means this**, unless the creator asks for something else (NOTES 9 to 11). Worked example:
`videos/cam-09/` (cut) and `videos/cam-09/subs/` (everything after it), delivered as `cam-09-short-v2.mp4`.

| Layer | What | Where it comes from |
|---|---|---|
| 1. Cut | the strongest 15 to 45 s: open on the hook line, end on the payoff (it loops) | Cut stage + `hand-cut.py`, Checkpoint A |
| 2. Frame | 16:9: the whole frame, sharp, on black (picture y 656 to 1264); 9:16: as it is | `ffmpeg scale=1080:608,pad=1080:1920:0:656:black` |
| 3. Hook | 2 lines, plain, the accent on one word, frame 0 to the end, in the black above the picture (y 470, 76 px) | `captions.json` `"hook"` |
| 4. Subtitles | word-exact, rising out of a blur; `em` on ~5 meaning words; 2 `punch` phrases (one mid-clip, the payoff) | `subtitles.py` |
| 5. Sounds | auto: whoosh before each punch, soft clicks on `em`; by hand: a buzzer/hit on the first word, a thud on the mic-drop line, a riser into the last line | `"sfx": "auto"` + `"sounds"` |
| 6. Music | a Pixabay bed, never "Content ID Registered", its drop on the payoff or the turn; 16 to 20 dB under the voice | `finish.py --music` |

```bash
SK=youtube-shorts; W=videos/<clip>; S="$W/subs"
# 1. cut (the Cut stage above): transcribe, voice-pitch for who speaks, hand-cut, edges by edge-levels AND by
#    transcribing each kept piece alone (a TV or podcast mix has music under it: edge-audit --fix misfires), apply-cut
# 2. frame
mkdir -p "$S" && ffmpeg -y -v error -i "$W/flat.mp4" -vf "scale=1080:608:flags=lanczos,pad=1080:1920:0:656:black,setsar=1,fps=30" \
  -c:v libx264 -preset slow -crf 14 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:a aac -b:a 256k -ar 48000 "$S/edit.mp4"
cp "$W/transcript.json" "$S/"            # the flat transcript, corrected: misheard words, "twenty six" -> "26", no invented words
cp "$SK/templates/captions.json" "$S/"   # then fill in: font (NOTES 3), hook, em, punch, sounds
# 3-5. hook, subtitles, sounds
python3 "$SK/scripts/subtitles.py" --video "$S/edit.mp4" --spec "$S/captions.json" --out "$S/public" --shared videos/_shared --snap
npx hyperframes check "$S/public"        # read snaps/sheet.png: every punch on one line, held long enough to read
npx hyperframes render "$S/public" --fps 30 --video-bitrate 12M --workers 1 -o "$S/render-raw.mp4"
# 6. music: cut the section so its drop lands on the line you chose: start = drop_in_track - line_time_in_flat
ffmpeg -y -v error -ss <start> -t <flat + 1.2> -i videos/_shared/music/<track>.mp3 -ar 48000 -ac 2 "$S/bed.wav"
python3 "$SK/scripts/finish.py" --in "$S/render-raw.mp4" --out "$S/<clip>-nomusic.mp4"
python3 "$SK/scripts/finish.py" --in "$S/render-raw.mp4" --out "$S/<clip>.mp4" --music "$S/bed.wav" --music-db -11
#    measure: (music file - no-music twin) = the bed alone; its RMS 16 to 20 dB under the voice, else change --music-db
python3 "$SK/scripts/verify-render.py" --render "$S/<clip>.mp4" --index "$S/public/index.html"
cp "$S/<clip>.mp4" "$S/<clip>-nomusic.mp4" "$HOME/Videos/YouTube Shorts/<clip>/"
```

- **Checkpoints:** A (the cut) and the snapshot sheet before the render. Both are the creator's call; keep each short.
- **Finding the drop:** RMS every 2 s, then every 0.1 s around the jump (cam-09: the breakdown 46 to 62 s, the drop at
  62.25 s, started at 52.57 s so it hit "You're not good, bro" at 9.68 s).
- **The sounds kit:** `videos/_shared/sfx/` (Pixabay, plus `thud.wav` synthesised here: a falling 62 Hz sine with a
  noise click, peak -3 dBFS). Volumes on cam-09: buzzer `error` 0.16, `thud` 0.42, `riser` 0.16, auto whoosh 0.26,
  clicks 0.14.
- **Deliver:** the music version, the no-music twin, `PAPER-CUT.md`, `CREDITS.md`; update the font line in NOTES.
  Offer a title and description (for a show: name it and its platform in the description, plus its hashtag).

## Captions only (an edited clip: animate the subtitles, add the sounds)

The creator's edit is final: never re-cut, reframe, re-grade or add other graphics. The clip keeps its own size and
frame rate. Same NOTES as every Short: the next font in the round robin, plain text, simple, professional.

```bash
W="videos/<clip>"; mkdir -p "$W" && cp "<clip>" "$W/edit.mp4"
ffmpeg -y -v error -i "$W/edit.mp4" -vn -acodec pcm_s16le -ar 16000 -ac 1 "$W/audio.wav"
npx hyperframes transcribe "$W/audio.wav" -d "$W" --engine parakeet --json      # then fix misheard words (same timings)
#   write $W/captions.json: font, em words, punch phrases (read the transcript for the meaning first)
python3 "$SK/scripts/subtitles.py" --video "$W/edit.mp4" --spec "$W/captions.json" --out "$W/public" --shared videos/_shared --snap
npx hyperframes check "$W/public"                                                # read snaps/sheet.png: the checkpoint
npx hyperframes render "$W/public" --fps <printed> --video-bitrate 12M --workers 1 -o "$W/render-raw.mp4"
python3 "$SK/scripts/finish.py" --in "$W/render-raw.mp4" --out "$W/<clip>-subs.mp4"   # 1080x1920 Shorts
python3 "$SK/scripts/verify-render.py" --render "$W/<clip>-subs.mp4" --index "$W/public/index.html"
```

- **The motion is the premium part, not decoration:** each word rises out of a light blur as it is said; the words to
  come hold their place (a line never re-centres); `em` words land in the accent a touch bigger; a `punch` phrase gets
  its own line at 1.45x, letters staggering in, an accent bar wiping in under it; a line lifts and blurs out in 0.12 s,
  ending exactly when the next starts.
- **Choosing them:** `em` on 1 word in ~4 lines (the meaning words: a number, a name, the thing the line is about);
  `punch` on the punchline or the hook payoff only, about one per 8 to 15 s ("a-b" keeps a short phrase together:
  "hate 'em."). Too many and nothing stands out.
- **Sounds (`"sfx": "auto"`):** a whoosh-short 0.08 s before each punch, a soft click on an emphasis word only when
  nothing sounded for 2 s, never two inside 0.3 s. Anything else by hand in `"sounds"`; the voice always wins.
- **Legibility without a shadow:** `scrim` (default 0.28) darkens a soft band behind the caption zone; raise it on a
  bright shot, 0 on a dark one. Captions sit at y 1250 on a 1080x1920 clip (above YouTube's bottom UI); move them
  (`y`) off a face or on-screen text, or blank a stretch with `off`.
- `finish.py` takes 1080x1920 Shorts only; any other shape: `loudnorm` to -14 LUFS and the BT.709 tags by hand.
- **On-screen hook** (when asked): `"hook": {"text": "Line one|line two", "em": ["26"], "y": 470}` is plain text on
  the first frame, no entrance, held to the end; on a letterboxed 16:9 clip it sits in the black above the footage.
- **Music** (when asked): Pixabay, never a track marked "Content ID Registered" on its page (a publisher/IPI block in
  the artist bio is the same warning). Credit it in `videos/_shared/music/CREDITS.md`. Start the section so the track's
  drop lands on the payoff line. Pixabay tracks are mastered hot: on cam-09 `--music-db 8` left the bed 1.9 dB under
  the voice and `-11` put it 16.8 dB under (the target is 16 to 20). It differs per track and per voice: on
  codpod12-03 (BombinSound "Warriors" under a hot podcast mix) `-11` was 23 dB under and `-6` was 18. Always measure,
  and keep the no-music twin.
- **Motion elements** (when asked, codpod12-03 v2): hand-drawn marker objects in the black band above the picture
  (y 200 to 660), one per idea, each on its word, via `"raw_html"` / `"raw_js"` (same timeline `tl`). On "no
  spoilers" a red no-sign through the word; "award" a trophy that gets an X; "this happened" x3 comment bubbles that
  pop in and drop away; "impressed" a heart and a "0"; "keep it to yourself" a padlock that snaps shut. Strokes are
  `pathLength=100`, `stroke-dasharray: 100 102`, drawn 0.1 to 0.35 s; set `"sfx": false` and place every sound by
  hand (scribble on a stroke, pop on a bubble, ping on a number, click on a lock). Builder: `videos/codpod-12/m03/subs/build-captions.py`.
- **Motion that looks professional** (codpod12-03 v3, after v2 was called "very simple"): thin line icons drawn on
  read as clip-art. Every element now gets:
  - **a designed look:** filled shapes with a gradient and a highlight (gold, steel, red), real-looking UI (comment
    cards with avatar, @name and text), never a bare outline;
  - **anticipation and settle:** a lift or squash before the move, `back.out` / `elastic.out` overshoot after it;
    impacts squash (`scaleX 1.15, scaleY 0.85`) then spring back;
  - **motion blur on fast moves:** `filter: blur(10 to 16px)` while it travels, 0 on arrival;
  - **secondary motion:** a burst of rays on each impact (`.ray`: hidden except while firing, or the round caps
    leave dots), sparkles that twinkle, a beat, a bob;
  - **ties to the footage:** `"window"` + `"camera"` in subtitles.py: a punch-in toward the face that speaks on the
    hit, a decaying shake and a white flash on impacts, slow pushes on long shots, a reset on every shot change; an
    element rises out of the picture's edge (`#emerge`, clipped at the window top) or flies out of a mouth;
  - **review in motion:** frame strips at 12 fps around each move (`ffmpeg -ss A -to B -vf fps=12,...,tile=8x2`),
    never only stills. Builder: `videos/codpod-12/m03/subs/build-motion.py`.
- **Depth** (codpod12-03 v4): cut the people out of the window crop, then put elements between the footage and them.
  ```bash
  ffmpeg -i "$S/edit.mp4" -vf "crop=1080:570:0:675" -an -c:v libx264 -crf 12 "$S/depth/picture.mp4"
  npx hyperframes remove-background "$S/depth/picture.mp4" -o "$S/depth/subject.webm" --quality best   # CPU: ~10 min for 18 s
  ```
  `"subject": "depth/subject.webm"` + `"behind_html"` (frame coordinates) in the spec; both sit in `#cam`, so every
  punch, push and shake keeps them locked. Check the matte over magenta first (`ffmpeg -c:v libvpx-vp9 -i subject.webm`
  + `overlay` on a magenta colour source). Best uses: a big word across the picture behind a wide shot of the guests,
  an object sliding out from behind a shoulder. Keep things that fly *toward* camera (comment cards) in front.
- **Beat sync** (codpod12-03 v4): `npx hyperframes beats <dir>` on a folder holding the bed and an index.html with
  `<audio src="bed.wav">` writes `beats/bed.wav.json` (time + strength). Snap every move the speech does not pin to the
  nearest beat within 0.13 s (rings, slashes, exits, landings, deletions, a count landing); keep word-locked hits on
  the word. Land the biggest entrance on the music's drop with a small picture punch + flash; let held elements
  pulse on the beats (a heart that beats, a lock that pulses) and the picture breathe (`#win` scale 1.012) in quiet
  stretches. Builder: `videos/codpod-12/m03/subs/build-motion-v4.py` (`beat()` helper).
- **Transitions on the source's cuts** (codpod12-03 v5): `"camera"` ops `["whip", cut, dir]` (the outgoing shot
  slides off under a horizontal-only blur, `feGaussianBlur stdDeviation="46 0"`, scaled 1.24 so the window edges never
  show, the incoming one slides in), `["zoomblur", cut, ox, oy]` (punch through: zoom + blur + overexpose, land zoomed,
  settle, flash) and `["leak", cut]` (a soft warm band sweeping across, `mix-blend-mode: screen`, no hard shapes: a
  round highlight read as a fake disc). Treat 2 to 3 cuts in a short, never every one; prefer cuts that sit on a beat
  and the ones into a turn (the rant, a reaction). Remove any camera `set` or push that overlaps a transition (two
  tweens on the same scale fight), and give each a sound (whoosh for the whip and the zoom, a soft one for the leak).
- **A fast speaker:** a one-word punch can vanish in half a second. Punch a phrase that holds over a second
  ("nobody's bothered."), and when it is too wide at 1.45x set `"punch_scale": 1.2` so it stays on one line.

## Pipeline (flat cut to the file you upload)

```bash
python3 "$SK/scripts/compose.py" --spec "$W/storyboard.json" --out "$W/public" --shared videos/_shared
npx hyperframes check "$W/public"
python3 "$SK/scripts/beat-check.py" --index "$W/public/index.html" --transcript "$W/transcript.json"
python3 "$SK/scripts/gap-scan.py" --index "$W/public/index.html"
python3 "$SK/scripts/snap-beats.py" --project "$W"              # Checkpoint B: read snaps/sheet.png before rendering
npx hyperframes render "$W/public" --resolution portrait --video-bitrate 12M --workers 1 -o "$W/render-raw.mp4"
python3 "$SK/scripts/finish.py" --in "$W/render-raw.mp4" --out "$W/<short>.mp4" [--music bed.wav --music-db 8]   # gain measured, see Sound
python3 "$SK/scripts/verify-render.py" --render "$W/<short>.mp4" --index "$W/public/index.html"   # exit 1 = do not deliver
mkdir -p "$HOME/Videos/YouTube Shorts/<short>" && cp "$W/<short>.mp4" "$HOME/Videos/YouTube Shorts/<short>/"
```

Snapshot before rendering (a snapshot is seconds, a render is minutes) and read the PNGs; never assume. Render time on
an 8 GB laptop with `--workers 1`: 5 to 15x real time (clip-03, 18 s: 99 s full-frame, 110 to 157 s in the card look
with motion graphics; plan 10 to 15 minutes for 60 s), so
every fix should be caught on the snapshot sheet, not in a render. Anything the composer does not build goes into
`raw_html` / `raw_js` (keep it inside the zones below). Beats held to the last frame get no exit animation.

## The frame: zones

YouTube draws its own interface over a Short. Design inside what is left:

| Zone | y (px) | What goes there |
|---|---|---|
| Keep out: top | 0 to 200 | search and menu icons (only the optional 8 px progress bar) |
| Top zone (`"pos": "top"`, default) | 230 to ~700 | headline, chip, logo, number, list, image card, follow pill |
| Your face | ~600 to 1100 | nothing, unless the beat matters more than you for a moment (`"pos": "center"`, from y 760) |
| Captions | ~1150 to 1420 | the word-by-word captions (they rise to the seam during a split) |
| Keep out: bottom | 1480 to 1920 | title, channel name, music ticker |
| Keep out: right edge | x 930 to 1080 below y 900 | like, comment, share, remix |

A card never covers your face. When copy will not fit the top zone, shorten it; never shrink text under 56 px.

## The composer (`compose.py`) and `storyboard.json`

```json
{"id": "short-01", "duration": 42.5, "video": "input-video.mp4", "origin": "50% 0%",
 "captions": {"transcript": "transcript.json", "max_words": 3, "max_chars": 18, "y": 1180, "size": 88, "style": "karaoke", "em": ["thousand"]},
 "progress": false,
 "beats": [
   {"type": "text", "id": "h1", "text": "I edit every Short with Claude", "em": [5], "in": 0.0, "out": 2.6, "anchor": "-"},
   {"type": "logo", "id": "lg", "src": "img/claude.svg", "pop": 2.92, "in": 2.85, "out": 4.6, "anchor": "Claude"},
   {"type": "stat", "id": "st", "value": 1000, "prefix": "$", "label": "a month", "color": "amber", "at": 9.2, "in": 9.0, "out": 11.5, "anchor": "a thousand dollars"}],
 "camera": [["punch", 0.4, 1.08], ["set", 3.10, 1.0], ["creep", 3.1, 8.0, 1.06], ["release", 8.9, 0.4]],
 "sounds": [{"src": "sfx/click.mp3", "at": 13.2, "dur": 0.4, "volume": 0.28}]}
```

Every beat has `type`, `id`, `in`, `out` and `anchor` (the spoken phrase; `"-"` = deliberately unanchored). Any beat can
take `"hide_captions": true`. The full key list is in the docstring at the top of `compose.py`.

| Type | Use for | Notes |
|---|---|---|
| `text` | the hook title; a headline line | `em` word indices cyan (`"color": "amber"` for money); `"in": 0` = on the first frame, no entrance; 96 px, wraps |
| `chip` | a punchline, a pattern interrupt | dark glass, 72 px, the `em` words magenta; on a bright set (white wall) `"chip_bg": "rgba(17,17,17,0.8)"` or the magenta greys out |
| `logo` | naming a tool | 360 px glass plate, logo only (you say the name); `pop` = the one earned sound |
| `list` | two to four items you count | glass card, items appear on their words (`[text, t, "anchor"]`); `"marker": "check"` for done / to-do |
| `stat` | one number that matters | every digit, counting up (`$1,000`, never `$1K`); amber for money |
| `image` | a screenshot, a post, a photo | `"frame": "card"` (glass, top zone) or `"full"` (full frame, slow push, optional `label`) |
| `clip` | B-roll, your screen, a cutaway | full frame, muted, slow drift; optional `label`; captions stay on top |
| `split` | showing something while you keep talking | the media fills the top half (a `--half` clip or an image), you slide to the bottom half, captions sit on the seam |
| `cta` | "follow for part 2" | glass pill with a red button pulsing three times; the last 2 to 3 s at most, only when there is a part 2 |
| `vignette` | the beat after a joke | radial darkening + grain |

`progress: true` adds a thin cyan bar filling across the top: a retention device, used sparingly (not on every Short).

## The card look (the default for landscape sources: podcasts, interviews, 16:9 recordings)

**A complete worked example** (cut list, three storyboard versions and the notes between them) is in
`examples/clip-03/`: start a new card-look Short from its `storyboard-v3.json`.

**Never upscale a landscape source to fill 9:16** (a 1080p crop is enlarged 1.78x and looks low quality; the creator
rejected it). Show the whole 16:9 frame in a rounded card instead, downscaled and sharp, and use the free space above
and below for the headline, captions and motion graphics. `reframe.py` is skipped: the flat cut is the footage.

```json
"theme": {},                                   // Rubik Mono One, white text with a black outline, yellow #FFD400 accent, red #FF3B30 alert
"frame": {"mode": "card", "y": 470},            // 1000x562 card, radius 32, on a dark background with slowly drifting light
"progress": true,                              // a yellow bar along the card's bottom edge
"origin": "38% 22%"                            // zoom toward the speaker's face (inside the card, up to ~1.6x stays sharp)
```

`theme` keys: `font`, `font_file` (in `assets/fonts/`), `text`, `accent`, `alert`, `outline`, `bg`. With a theme the
captions use the display font in caps, 56 px, outlined.

| Zone (card look) | y (px) | What goes there |
|---|---|---|
| Title | ~250 to 410 | the persistent headline, 70 px (a 14-letter word: 62 px) |
| Card | 470 to 1032 | the footage, whole; marker strokes may overlap its edges |
| Captions | ~1078 | 56 px, plain white, a few meaning words in the accent |
| Graphics | ~1175 to 1420 | dice, dots, chart, meter: one at a time (keep clear of 1480+: YouTube's title and music ticker) |

**Text size: smaller than you think.** Rubik Mono One is wide and heavy: 70 px title, 56 px captions, 28 to 40 px
labels read fine on a phone. The creator rejected 92 px titles and 74 px captions as too big. No source/credit chip on
screen (rejected): credit the show in the video description instead.

**It must feel edited by a person, not generated.** What gives an AI edit away, and what to do instead:
- Every word lit karaoke-style (the auto-caption tell) → `"style": "plain"` captions with `em` on the 4 to 6 words that
  carry the meaning ("surprised", "unlucky", "five percent", "overestimated", "certainty").
- Stock emoji stickers → elements drawn and animated here: marker strokes (`draw`), a real 3D die (`dice`), a chart
  that draws itself (`chart`), a ring drawn around a data point (`dots` `ring`). Strokes are hand-wobbled (seeded, so a
  rebuild draws the same) and drawn on in a marker's rhythm (fast start, short tail).
- Everything popping with the same ease and length → vary it: strokes draw in 0.15 to 0.45 s, the die bounces, the
  headline swaps with a lift, the meter shakes once.
- Sound on nothing → every animated element gets the sound a person would put there (below), quiet, on its exact frame.
- Do not stack: one graphic in the bottom zone at a time; a marker accent near the face at most every ~5 s.

Motion formats (need a `theme`):

| Type | Use for | Keys |
|---|---|---|
| `title` | the headline that tells the story: on screen from frame 0, then struck out and swapped as the argument turns | `text` ("Line one\|Line two"), `em` (line indices in the accent), `size`, `y`, `pulse`, `strike` {`line`, `at`} (two red marker passes), `swap` {`at`, `text`, `em`, `size`, `underline` (line index), `underline_at`, `underline_color`} |
| `draw` | marker accents on a word: shock lines by a face, a circle, an underline, an arrow | `shapes`: [{`shape`: `burst` (`cx cy n from to r0 r1`) / `circle` (`cx cy rx ry`) / `underline` (`x1 x2 y`) / `arrow` (`x1 y1 x2 y2 bow head`) / `path` (`d`), `at`, `dur`, `color`, `width`}] (frame px) |
| `dice` | luck, chance, a gamble | `x`, `y`, `size`, `face` (1 = the red snake-eye: bad luck), `land` (when it settles), `from_x` |
| `dots` | odds and shares ("5% = 1 in 20") | `n`, `hit`, `at`, `ring` (+ `ring_at`, `ring_color`), `label`, `label_em`, `label_at`, `size`, `gap`, `y` |
| `chart` | expected vs reality, before vs after | `x y w h`, `lines`: [{`label`, `points` [[0..1, 0..1], ...], `color`, `width`, `at`, `dur`, `arrow`}] |
| `meter` | too much / too little of something | `label`, `to` (1.33 = fills past 100% and turns red, then shakes), `over_label`, `fill_at`, `dur`, `x`, `y`, `w` |
| `emoji` | only if the creator asks for one; prefer a drawn element | `char` (an SVG in `assets/emoji/`), `x`, `y`, `size`, `spin` |
| `credit` | only if the creator asks; default is the description | `text`, `y` |

- A stroke that stretches with text (the title's strike and underline) is revealed by a wipe (`clip-path`), never by
  the dash trick: with a non-scaling stroke Chrome measures the dash in screen px and the stroke shows on frame 0.
- A wide two-shot needs nothing special in the card look: it is already whole.

**Sound effects in the card look** (the creator asked for them; this overrides "silence is the default" for Shorts):
every animated element gets one, quiet, peak-normalised, its transient on the element's first frame.

| Element | Sound | Volume |
|---|---|---|
| A punch-in on the face | `whoosh-short` 0.08 s before the move | 0.30 |
| The die tumbling | `dice-roll` (built from Pixabay clicks) as it enters | 0.42 |
| A marker strike / scribble | `scribble` on the stroke | 0.30 |
| A data point lighting up | `ping` | 0.26 |
| A line or arrow shooting up | `whoosh` | 0.28 |
| The headline swap | `pop` 0.1 s after the swap starts | 0.22 |
| A meter filling / overflowing | `riser` peaking on the overflow, then `error` on it | 0.20 / 0.26 |

The kit ships in `assets/sfx/`; copy it once to `videos/_shared/sfx/` (`compose.py --shared videos/_shared` stages it): the Pixabay files from the
HyperFrames media-use library (Pixabay Content License, no attribution needed; `CREDITS-pixabay.md`), each trimmed of
leading silence and peak-normalised to -3 dBFS, plus `dice-roll.wav` and `scribble.wav` made here. About 6 to 9 sounds in
a 20 s Short; never two inside 0.3 s; the voice always wins (check the mix by ear in the finished file).

**When two formats compete:** pick the one that fits what you say; tied, the one used least in this Short (compose.py
prints the counts). Never the same device twice in a row (compose.py warns: fix it, never ship past it).

## Captions

- **On by default, word-exact, from the flat transcript.** Up to 3 words or 18 characters a group; a new group at a
  sentence end or a pause over 0.45 s. Each group pops in (0.08 s, 94% → 100%), no bounce.
- **Karaoke:** the word being said turns cyan; `em` words (money, the key number) stay amber the whole time.
- 88 px, DM Sans 700, white with a dark outline shadow, centred at y 1180. `"upper": true` for an all-caps look.
- **They step aside** for a beat that carries its own words (`hide_captions` on the beat, or `"off": [[a, b]]`), and
  move up to the seam during a split. A caption never sits under a card's text.
- **Fix the transcript, not the caption:** a misheard word is fixed in `transcript.json` (same timings) and the Short is
  recomposed. Brand names get their real spelling.

## Camera

**Top-anchored origin** (`50% 0%`): a zoom never crops your head.

| Move | Numbers |
|---|---|
| Punch-in on a stressed word | 106 to 112%, 0.30 s `power2.out` |
| Slow creep across a thought | 104 to 108% over 3 to 6 s, `power1.inOut` |
| Snap back | `["set", t, 1.0]` at every jump cut in `cut-map.json`; never carry a zoom across a cut |
| Limit | 1080x1920 footage turns soft past ~115% (compose.py warns); a 4K-vertical source could take more, but it is reframed to 1080 |

- In a Short, jump cuts every 2 to 4 s are the rhythm: leave most of them naked, punch one in three.
- Put every reset on the jump frame (cut-map times are not frame-aligned: set at `jump/30 - 0.003`).

## Pacing

- **The picture changes at least every 4 s** (2.5 s in the first 5 s): a card, a cutaway, a punch, a split.
  `gap-scan.py` flags the stretches; captions do not count.
- About 1.5 overlays + 1 camera move per 10 s. One hero element at a time; cards hold 1.5 to 4 s.
- Enter 0.15 to 0.25 s ahead of the word (0.4 s `power2.out`), exit 0.3 s `power2.in`. No bounces, no flips.
- Every Short is a hook: there is no quiet stretch.

## Sound

**Silence is the default for the full-frame look. A sound has to earn its place:** what on screen makes this noise? One
or two per Short. The card look with motion graphics is different: the creator asked for sound on every animated
element; see "Sound effects in the card look" for the kit, the volumes and how to measure them.

| Sound | Allowed on | Volume |
|---|---|---|
| Pop | a logo appearing (`pop` on the logo beat) | 0.34 |
| Click | an on-screen cursor click (`sounds`) | 0.28 |
| Typing | real typing on screen, for exactly the typing time | 0.22 |
| Cha-ching | a money count landing | 0.07 |
| Whoosh | **never on text** | |

Peak-normalise each effect to -3 dBFS before using it (`volumedetect`, then `volume=`), and trim the silence before its
transient so the peak lands within two frames of its cause.

**Music:** optional, decided per Short. `finish.py --music bed.wav --music-db G` loops it under the whole Short, fades
it, ducks it under your voice and limits at -1 dB. Keep a no-music version (`finish.py` without `--music`) next to it.
- **Set the gain by measuring, not by a default.** When someone talks the whole time the sidechain holds the bed down
  almost throughout: on clip-03 `--music-db -12` left the bed 37 dB under the voice (inaudible); `+8` put it 18 dB under,
  the target (16 to 20 dB). Measure by subtracting the no-music twin from the music version (bed alone) and comparing its
  RMS with the voice's; do the same for SFX against a render without them (target 9 to 14 dB under).
- **Use a section, not the start:** cut the part of the track that builds (`ffmpeg -ss 20 -t <length+1>`), so the
  energy rises across the Short; a track's first seconds are often a quiet intro.
- **Rights first:** only tracks you have the rights to (YouTube Audio Library, Pixabay, Epidemic Sound). Pixabay files
  are named `artist-title-number.mp3`. A commercial song (or a "slowed" YouTube download) gets a Content ID claim that
  mutes or demonetises a Short: never use one, and tell the creator which files in their folder are risky.

## Animating glass (read before writing any entrance)

Never fade a glass element through an ancestor's `opacity`: Chrome drops `backdrop-filter` while any ancestor is below
opacity 1. Animate the glass's own background, border and shadow from transparent (`glassIn` / `glassOut` in the page)
and fade only the copy inside. Glass that has not arrived stays hidden, or it blurs the footage.

## B-roll

- **Stock:** Pexels first (free on YouTube, no credit), then Coverr, Mixkit's free licence. **Search vertical first**
  (it keeps the whole shot); a landscape clip is cropped with `broll-conform.py --focus` to keep its subject.
  Real people, no watermark, no readable logo, nobody looking into the lens. 1.5 to 3 s each.
- **Your own screen** is the strongest cutaway: it is proof. For a split, record or crop it to the top half (`--half`).
- **AI B-roll:** it stars you or nobody, never proof (no fake dashboards, results or screenshots), at most one per Short,
  labelled "Altered or synthetic content" on upload. Quote the credit cost and get a yes before every generation.
- `python3 "$SK/scripts/broll-conform.py" --in <file> --out "$W/public/broll/<name>.mp4" --dur <slot + 0.5> [--focus 0.4] [--half]`,
  then read its `.sheet.png`.

## Traps that waste a render

- **Memory:** `--workers 1` on 8 GB. Footage painted black in the render = the capture ran out of memory.
- **The render leaves the colour tags "unknown":** `finish.py` writes them; never upload `render-raw.mp4`.
- **The render keeps the camera level (~-25 LUFS):** `finish.py` levels it to -14; never skip it.
- **Every timed element needs `class="clip"`** or it shows for the whole Short; keep `data-has-audio="true"` on the
  footage or the render is silent. Every `<audio>` needs an `id` or it is silent in the render.
- **Never put CSS translate(), scale() or rotate() in the style of an element GSAP also moves:** centre with
  `left:0; right:0; margin:0 auto` (the `.centered` class), start states in a `tl.fromTo`.
- **A count-up or anything that changes step by step comes from one proxy tween** on the one timeline, never a
  `tl.set` per step (it leaves leftovers on a backward seek).
- **The linter's contrast warnings over bright footage** are worth a look in the snapshot, not an automatic fix.
- **Snapshots:** `snap-beats.py` asks HyperFrames for every moment in one call; never pass a bare `"npx"` to Python's
  subprocess on Windows.
- **The frame cache fills the temp folder** (`hyperframes-extract-cache-*`): delete it when no render runs.

## Verify and deliver

- **`verify-render.py` on the finished file:** 1080x1920, BT.709 tags, at least 6 Mb/s, duration = `data-duration` ±
  1 frame, 60 s at most, A/V within 0.12 s, no black frames; writes `VERIFY.md` and `render-sheet.png`. Exit 1 = do not
  deliver. **Clipped words:** transcribe the finished file and add `--words <that> --kept "$W/transcript.json"`.
- **Watch it once on a phone** (or a 9:16 window) with sound off: the hook and captions must carry it muted.
- **Deliver** to `~/Videos/YouTube Shorts/<short>/<short>.mp4` (md5 it against `finish.py`'s), with `STORYBOARD.md`
  (`storyboard-md.py`) and `PAPER-CUT.md` next to it. Open it from Explorer / Finder, never through a chat download.
- **Upload notes to hand over:** a title under 40 characters that is not the hook line word for word; `#Shorts` is not
  needed; mark AI B-roll as altered content; pick the cover frame from the hook.
- **Report** the folder, what was added and where, and **your own concerns** (a caption covering a gesture, a card held
  long, a soft reframe). Versions keep going (v2, v3...).

## Keeping the skill yours

- **`NOTES.md`** (next to this file) is the creator's running list of corrections. Read it before every Short and
  follow every note; a note beats a rule here when they disagree. New corrections go there, not in per-Short folders.
- **After every delivery:** your note in plain words → edit the storyboard (one number) or the format (one rule) →
  rebuild → snapshot → render.
- **"Save this to the skill":** write the note as one plain rule in the section it belongs to. When it changes the look,
  update `STYLE-GUIDE.md` and the composer's tokens too. A new rule that contradicts an old one replaces it.
- **A new format starts with a state sheet:** every state (what is on screen, where in the zones, size, colour) and
  every change between states (property, ease, time). Build to it, snapshot each state, add a test under
  `scripts/tests/`.
- **Model and tokens:** routine Shorts run fine on a mid-size model; a new format deserves the strongest. Most tokens go
  to snapshots: one per moment, scripts over retyping.
