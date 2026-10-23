# The HyperFrames catalog and the motion-graphics skill (integrated 2026-10-19)

`.claude/skills/motion-graphics/` (HeyGen's HyperFrames skill) builds **standalone, unnarrated** motion graphics under
~10 s from its block catalog. A Short is narrated live-action, so pro-shorts does not run that skill's pipeline; it
uses the **catalog** as a library of render-tested moves to port. Run the motion-graphics skill itself only when the
creator asks for a standalone piece (an intro sting, an end card, a pure stat/kinetic-type graphic), and follow its
render-approval gate.

## When designing a moment (SKILL.md step 5)

1. Name the idea in plain words ("name the guest", "they quote a tweet", "a number lands", "a list of reasons").
2. `python .claude/skills/pro-shorts/scripts/catalog.py search "<the move>"`: about 450 blocks.
3. Promising one: `catalog.py fetch <name> --out <subs>/blocks` (the file comes from GitHub: ask the first time per
   session). Read it. The audit lists what breaks NOTES.md.
4. **Port, don't paste.** Rebuild its look and motion with `k.front()` + `k.J()` on the shared `tl`, at its word,
   sized for 1080x1920 (front elements live in the band y 200-640 above a letterboxed picture), SubFont only, plain
   text, assets frozen locally. If it will be reused, make it a `Kit` method in `motionkit.py`.

## Already ported (motionkit)

| Moment in a Short | Kit method | From |
|---|---|---|
| Name a speaker / guest on first appearance | `lower_third(eid, kicker, name, t_in, t_out)` | `lt-kicker-name` |
| Someone quotes a post or a comment | `post_card(eid, name, handle, text, likes, t_in, t_like, likes_after)` | `x-post` |
| The person being talked about is not on screen | `photo_card(...)` + `fly_right()`, found in the browser, out within 3 s (NOTES 14, 18) | clash-06 v3 |
| A line worth reading as type ("10 BEERS", "ONLINE CLASSES") | `type_beat(eid, label, lines, times)` | clash-06 v3 |
| A list said item by item | `checklist(eid, header, rows)` | clash-06 v2 |
| A number that counts | `number()` + `count()` (catalog: `count-up`, `number-wheel`, `mk-usage-arc`) | codpod12-03 |

## Good catalog leads for Shorts (search these words)

- `lower-third` (lt-clean-bar, lt-stack-bars, lt-kicker-name): naming people.
- `social`: x-post, yt / tiktok / ig follow cards, reddit, spotify: when the speaker cites a platform.
- `count-up`, `number-wheel`, `number-pop-in`, `mk-usage-arc`: stats and scores.
- `data-chart`, `bar-chart-race`: comparisons (keep it to one hit, no "card look", NOTES 9).
- `grain-overlay`, `vignette`: the finishing-pass roadmap item.
- `north-korea-locked-down` annotation kit (circle draw-on, pointer pill): circling something in a photo or frame.

## Never port (NOTES)

`caption-neon-glow`, `glow` emphasis, `text-shadow` on any text (NOTES 7); other font families (NOTES 3); progress
bars (NOTES 6); emoji or generic icon art (NOTES 15); the scribble sound (NOTES 12); a full "card look" layout (NOTES 9).

## Network and keys

`catalog.py search` runs `npx hyperframes catalog` (no install, no key). The motion-graphics skill's
`grounding/locate.mjs` can send frames to Google Gemini when `GEMINI_API_KEY` is set, and `categories/maps/
bake-basemap.mjs` downloads map tiles: both only with the creator's OK.
