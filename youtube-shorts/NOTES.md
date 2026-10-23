# Notes: the creator's corrections

Every note here applies to **every Short**. Claude reads this file before starting any Short and follows all of it.
A note here beats a rule in `SKILL.md` when the two disagree.

Write one note per line, in plain words. Optionally say which Short it came from, so it's clear what you were looking at.
Example: `The Pitch meter is too small and comes in late. (demi-01)`

## Corrections

From demi-01 v1 (2026-10-17):

1. **The main clip sits in the centre of the screen**, vertically and horizontally. (v1's card sat high, y 470 to 1032;
   its centre should be at y 960.)
2. **The clip may be scaled up, but it must never look low quality.** Scale only as far as it stays sharp; if the
   source can't take it, keep it smaller.
3. **Fonts: Inter and Montserrat, taking turns (round robin).** Each new Short uses the other font from the last one,
   for captions, titles and every other piece of text. Both files are in `assets/fonts/`: set
   `"theme": {"font": "Inter", "font_file": "Inter-700.woff2"}` or
   `"theme": {"font": "Montserrat", "font_file": "Montserrat-700.woff2"}`. No other font. After delivering, update the
   line below.

   **Last font used:** Montserrat (pete-02 AI two futures, 2026-10-23; before that pete-01 Inter). **Next Short: Inter.**
4. **Captions are simple.** Nothing on screen should feel forced on the viewer.
5. **Motion graphics were good, but push them further.** More polish and better ideas, not more of them.
6. **No progress bar.** Never add the bar that shows how much of the video has played (`"progress": false`, always).
7. **All text is plain.** No border, no stroke, no outline, no shadow, no glow, nothing like it, on captions, titles
   and every other piece of text. (v1 used `-webkit-text-stroke` and `text-shadow`; both are out.)
8. **It must look professionally edited**, like a real video editor made it.

From cam-09 (2026-10-18):

9. **The default edit is the `pro-shorts` skill** (`.claude/skills/pro-shorts/`, approved on codpod12-03 v5,
   2026-10-18): fresh cut, letterbox, animated subtitles, shaded motion elements tied to the footage (depth behind
   the speakers, punch-ins, shakes, flashes), 2 to 3 transitions, sounds, a beat-timed Pixabay bed. No card look, no
   headline swaps, no meters or charts unless the creator asks. (Earlier default: the cam-09 "house structure".)
10. **A landscape (16:9) clip is letterboxed:** the whole frame, sharp (scaled to 1080 wide, never cropped or
    upscaled), centred on black in 1080x1920 (`scale=1080:608,pad=1080:1920:0:656:black`), subtitles in the black
    below it (y ~1380). Ask before cropping to full-frame vertical.
11. **The hook, the sounds and the music are part of every edit** (cam-09 v2, approved): the hook in the black
    above the footage from frame 0; a buzzer or hit on the opening line, a whoosh before each punchline, a thud on
    the mic-drop line, a riser into the last line; a Pixabay bed (never "Content ID Registered") whose drop lands
    on the payoff line, measured 16 to 20 dB under the voice. (No-music twin: see note 16, no longer delivered.)

From clash-03 v1 (2026-10-19):

12. **Never use the scribble sound** (`sfx/scribble.wav`, the marker-stroke sound). Not in any video, not for a
    slash, an X or a drawn arrow: leave the stroke silent or give it a soft sound from the rest of the kit.

From real retention graphs (YouTube Studio, 2026-10-19):

13. **The first 3 seconds: the speaker, then the claim.** The speaker is on screen from frame 0; the bold claim (or
    question, or the story's first line) is said by ~3 s; no B-roll, stock photo, title card or graphic covering
    the speaker before the claim. Photos of who is named come after, as a cutaway on the name. Why: "Stop calling
    Lamar Jackson" opened on a "Fan vs Hater" card, a top-10 graphic and a stock photo, the speaker first seen at
    ~6 s: 47.6% stayed to watch, 1.4K views, steepest drop 0:03 to 0:10. "Lamar Isn't Even a Top 3 QB" (podcast-02)
    had the speaker and a "Confronting Cam Newton to his face" header from frame 0: 72.7% stayed, 5.4K views.
    Checked by `.claude/skills/pro-shorts/scripts/hookcheck.py` after the render.

From clash-06 v1 (2026-10-19):

14. **Show the person being talked about (B-roll).** When the clip discusses someone who is not on screen (a player,
    a coach, a celebrity), find real photos of them (searched in the creator's Chrome; prefer freely licensed
    sources such as Wikimedia Commons, ask before each download) and use them as B-roll: in the picture window or as
    photo cards in the band, after the claim (note 13). Use B-roll whenever it clearly makes the clip better.
15. **No emoji-style motion graphics.** Generic icons (a heart, a beer mug, a bottle, a cartoon laptop, jail bars)
    look basic and don't match the clip. Graphics must come from the clip's own world: real photos, real UI, things
    on the set (e.g. the red LED shot clock), bold plain typography.

From clash02-01 v1 (2026-10-20):

16. **Don't deliver the no-music version.** Only the Short with music goes in the delivery folder; make the no-music
    twin only when the creator asks for it (mix.py still writes it in the work folder; don't copy it out).
17. **Every delivered Short gets an upload-info .txt** next to it (same name, `.txt`): 3 to 5 title suggestions
    (under 60 characters), a description with hashtags (#Shorts first; the show's name and platform worked in),
    and comma-separated YouTube tags.

From the creator (2026-10-20):

18. **B-roll: found in the browser, needed, 3 s at most.** Find B-roll for what is being talked about (a person,
    a place, a team, a product, an event) by searching the browser for it. Use it only where it helps the viewer
    understand the line more clearly: something named that isn't on screen and that they may not picture. Never
    as decoration. Each B-roll stays visible **3 seconds at most**, then the picture goes back to the speaker.
    Notes 13 to 15 still apply (after the claim, real photos, ask before each download).

19. **As few motion graphics as possible; simple, not "very professional".** Too many graphics, and their sounds
    were too loud. Add a graphic only when the line needs it to be understood. No graphic that is only text (a big
    word, a kinetic headline): if text is truly needed, it sits on a real element (a photo, a UI card, an object
    from the clip). Prefer simple B-roll and simple transitions (a plain cut or a short crossfade/zoom) over
    whips, flashes, shakes and bursts. Sounds only on the few things that move, and quiet (well under the voice).
    **Approved on clashcam-05 v1 (2026-10-20, "I love this edit"):** the reference for this style is
    `videos/clash-cam/m05/subs/build-motion.py` (2 B-roll moments in the band, 1 zoom-blur, 3 pops at 0.09).

From clashcam-01 v2 / 04 v2 (2026-10-20):

20. **More B-roll.** clashcam-01 v2 with no B-roll at all looked too bare. Still few motion graphics (note 19), but
    use B-roll more freely: not only people named off screen, also the concrete things a line paints (an action
    like a 400-foot home run, a game, a place, a team, an object). Aim for about one B-roll every 8 to 10 s of
    talk (roughly 3 to 5 in a 30 to 40 s Short), each 3 s at most, never before the claim (note 13), real photos
    or footage (note 15), ask before downloading.
21. **B-roll must match the topic, not just a word.** On clashcam-01 v3 a Holyfield boxing photo on "if I KNOCK the
    shit out you" was off topic: the clip is baseball vs football toughness, Cam was threatening Steve, not talking
    about boxing. Before each B-roll ask "is the clip *about* this?" A word that only sounds like a subject (knock ->
    boxing) is not a reason; skip the spot rather than force a picture.

From clashcam-02 v2 / 03 v2 / 07 v1 (2026-10-21):

22. **B-roll on every concrete thing named, on the exact word.** A card that lands a line late reads as a mismatch
    (03 v2: Harden on "Here's why" instead of "James Harden"). Cover the claims a line makes too: "regular season
    stats", "the MVP", "can't get it done in the playoffs", "the best version of Lamar", "me and Josh Allen". This
    includes the opening line: while the hook holds the band, a small pair of cards fits above it (motionkit
    `band_broll(..., y=40, w=260, photo_h=230)`, x 270 and 550), keeping the speaker on screen (note 13 still holds).
23. **Aim under ~36 s.** When a Short is ~40 s or more, cut a stretch that repeats a point (a fan's second reason, the
    first of two answers that say the same thing), on shot changes and in silences (`videos/clash-cam/recut.py`).
24. **Vary the subtitle animation between Shorts.** Styles in `subtitles.py`: "highlight" (box jumps word to word),
    "pop" (03 v3: words bounce in, yellow while said), "karaoke" (07 v2: the line slides up dim, words light up, a
    yellow underline jumps). A hook already used on an earlier version gets a new one.
    These are now presets (`"preset"` in captions.json, `templates/subtitle-presets.json`): clean, box, bounce,
    karaoke, wipe, calm. **Last preset used:** box (pete-02, 2026-10-23; before that pete-01 wipe). After delivering, update this line.
25. **No underline under subtitles**, in any style (karaoke's underline and the punch bar are gone). **Subtitles run to
    two rows** so the viewer has time to read each one (every preset sets `"rows": 2`). (2026-10-21)

## Saved to the skill

Filled in by Claude when you say "save this to the skill": which note became which rule, and where in `SKILL.md`.

- Notes 9 to 11 (cam-09, 2026-10-18) -> `SKILL.md` "The house structure (the default edit)": the full recipe, with
  `templates/captions.json` as the starting spec and `cam-09` as the worked example.
- Note 13 (retention, 2026-10-19) -> `SKILL.md` §2 (the cut) and §6 (`scripts/hookcheck.py`), and
  `references/moments.md` "What makes a moment".
- Notes 14, 15 and 18 (B-roll, 2026-10-20) -> `SKILL.md` §5, the "B-roll" bullet, and `references/catalog.md`.
