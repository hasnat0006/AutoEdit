---
name: edit-with-capcut
description: Edit a Short together with the creator in CapCut. Claude makes the Short in the house style (the pro-shorts skill), hands it over as an editable CapCut desktop project (footage cut at every shot, one clip per graphic, real text subtitles, every sound and the music on their own tracks), then works in rounds - reads what the creator changed in CapCut, makes the next changes inside that same project on top of theirs - until the creator exports from CapCut. Use whenever the user says "edit with CapCut", "give me the CapCut project", "I changed it in CapCut", "make these changes in the project", "open it in CapCut", mentions their CapCut edits, or asks to keep working on a Short they have already edited in CapCut - even if they don't name the skill.
---

# Edit with CapCut: the Short as a shared CapCut project

The creator edits in CapCut desktop (9.6, Windows). This skill makes Claude's edit something they can change by
hand, and lets Claude keep working on *their* version instead of starting over:

```
pro-shorts edit -> capcut_export.py -> creator edits in CapCut -> capcut_changes.py -> capcut_edit.py -> ... -> creator exports
```

**The style is pro-shorts.** Read `.claude/skills/pro-shorts/SKILL.md` and `youtube-shorts/NOTES.md` first, every
time: the moments, cuts, motion, subtitles, sounds and music rules all come from there. This skill adds the CapCut
hand-off and the rounds after it. On Windows set `PYTHONUTF8=1`; run from the project root.

## The one rule: CapCut closed while Claude writes

CapCut keeps edits in memory and rewrites the project when it saves or exits. Every round starts with the creator
**saving and closing CapCut**; the scripts refuse to write while `CapCut.exe` runs. Never ask them to kill it from
Task Manager (unsaved work is lost); ask them to save and close.

## 1. Make the Short (pro-shorts steps 1-6)

Follow pro-shorts through "Build, check, render" with its checkpoints (the cut, the snapshot sheet, motion
review in strips). Running `mix.py` is optional here: the creator exports the final file from CapCut. Two extras
for CapCut:

- **Group the graphics by idea** in `<subs>/capcut-groups.json`, one group per thing a viewer sees, using the
  element ids from `build-motion.py` (bursts follow their element on their own: `bTb` joins the group with `Tb`):
  ```json
  {"manziel-card": ["Jm"], "ten-beers": ["Nb", "Tb"], "joe-card": ["Jb"], "checklist": ["Cl"]}
  ```
  Each group becomes its own CapCut clip and its own file, so the creator can move, trim or delete one without
  the others, and Claude can re-render one alone. A word that is not its own idea goes with its idea (the two-line
  "THE NIGHT BEFORE / 10 BEERS" is one group). Without the file, every element is its own clip.
- **Graphics behind the speakers** (`layer="behind"`) live inside the footage window, so they are baked into the
  footage layer: changing one means a fresh export.

## 2. Export to CapCut

```bash
python .claude/skills/edit-with-capcut/scripts/capcut_export.py --subs <subs> --name <ep>-NN-<slug>-vN     # background: ~2 min per graphic + footage
```
Renders the footage layer (camera, flashes and transitions baked in, the hook, subtitles and graphics left off)
and one transparent ProRes clip per graphic group, trimmed to when it is on screen. Then it writes the project
straight into CapCut's project list:

| Track | What | The creator can |
|---|---|---|
| Footage | cut at every shot change; the voice on the clips, at -14 LUFS | trim, reorder, cut lines out |
| Graphics 1..n | one clip per group (`<subs>/capcut/gfx/<group>-<time>.mov`) | move, trim, delete, scale |
| Hook, Subtitles | real CapCut text, one clip per caption line, accent words yellow | retype, restyle, retime |
| Music | the bed, measured to sit 18 dB under the voice | change the level, swap the track |
| SFX 1..n | every sound its own clip at its pro-shorts volume | move, delete, re-level |

What CapCut does not get: the word-by-word pop of the subtitles and the punch-letter animation (CapCut text
appears per line; the creator can add a CapCut text animation), and the camera moves stay baked into the footage.
Say so when handing it over. The export writes `<subs>/capcut/manifest.json` and snapshot `001-export.json`, the
baseline for step 3.

Hand-off: the project name, a short table of what is on each track, and the round rule (save, close, tell me).

## 3. A round: read their changes first

When the creator says they changed it (or asks for more changes), have them save and close CapCut, then:
```bash
python .claude/skills/edit-with-capcut/scripts/capcut_changes.py --subs <subs>
```
It lists every change since Claude last wrote the project, clip by clip: deleted, moved, trimmed, volume, text,
position, size, added clips and effects. **Their version is the base from now on**: never undo a change of theirs
to make room for yours; if a request conflicts with something they did, ask. Tell them in a line what you saw
("you cut the jail line, dropped the checklist and turned the music down 4 dB") so they know you are working on
their version.

**Learn from it** (pro-shorts "Keep it learning"): a change they make on more than one Short is a standing note.
Offer to add it to `youtube-shorts/NOTES.md` or the right pro-shorts reference (for example, the music always
lowered: change mix.py's target; a kind of graphic always deleted: stop making it).

## 4. Make the next changes in the project

Write the operations and apply them in one go (selectors and every operation: `capcut_edit.py --help`):
```bash
python .claude/skills/edit-with-capcut/scripts/capcut_edit.py --subs <subs> --ops <subs>/capcut/ops-N.json --label round-N
```
```json
[{"op": "text", "what": "sub~manziel", "text": "Johnny *Manziel*."},
 {"op": "volume", "what": "music", "db": -3},
 {"op": "remove_range", "start": 20.1, "end": 21.4},
 {"op": "add_sfx", "file": "videos/clash/m06/subs/public/sfx/pop.wav", "at": 12.3, "volume": 0.25}]
```
- **In the project directly** (seconds): cut a stretch out of everything (`remove_range`), trim, move, delete,
  retype or restyle text, add text, volumes, add or move sounds. Times are the creator's timeline *now*, after
  their edits: read them from `capcut_changes.py`, not from the old render.
- **A graphic itself** (its words, photo, colour, animation): change `build-motion.py`, rebuild the page
  (pro-shorts step 6: `build-motion.py`, `subtitles.py`, `hyperframes check`), then `{"op": "regraphic", "group":
  "joe-card"}` re-renders only that group and puts it back where the creator had it (their move is kept).
  Review the new graphic in strips as usual.
- **The footage layer** (camera moves, a transition, a behind-the-speaker graphic) or a new cut from the master:
  a fresh export under a new version name; tell the creator their hand edits stay in the old project and list
  the ones `capcut_changes.py` reported so you can repeat them in the new one with `capcut_edit.py`.

After saving, tell them to reopen it. Every write keeps a snapshot in `<subs>/capcut/snapshots/`
(`NNN-before-<label>.json` is their version just before yours): to undo a round, copy that file over the
project's `draft_content.json` with CapCut closed.

## 5. Export

The creator exports from CapCut (it is exactly what they see). Remind them once: 1080x1920, 30 fps, and loudness
normalisation on (the house level is -14 LUFS). If they want the final file checked, run
`youtube-shorts/scripts/verify-render.py --render <their export> --index <subs>/public/index.html --out
<subs>/capcut/VERIFY.md` and report (a Duration FAIL is expected when their cuts changed the length).

## Files

- `scripts/capcut_export.py` the Short -> a project. `scripts/capcut_changes.py` what the creator changed.
  `scripts/capcut_edit.py` Claude's next changes. `scripts/capcut_lib.py` the shared reader/writer.
- `capcut/template-9.6.json` CapCut's own data shapes, taken from a project CapCut 9.6 saved.
- `references/capcut-format.md` how a CapCut project is laid out and the traps (read it before changing the scripts,
  or when a CapCut update breaks something).
