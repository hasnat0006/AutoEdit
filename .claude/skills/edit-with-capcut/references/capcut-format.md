# CapCut desktop project format (9.6, Windows)

Learned from projects CapCut 9.6.0 saved on this machine (October 2026). CapCut changes this format without
notice: after an update, open a project the creator made in the new version and diff it against
`capcut/template-9.6.json` before trusting the scripts.

## Where things live

- Projects: `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\<project name>\`
- The project list: `root_meta_info.json` in that folder (`all_draft_store`, one entry per project, newest first,
  plus a `draft_ids` counter). A project folder that is not listed here does not show up in CapCut.
- Inside a project:
  - `draft_content.json`: the whole timeline (tracks, segments, materials). Plain JSON, **not encrypted** in 9.6.
  - `Timelines/project.json` names the `main_timeline_id`; `Timelines/<that id>/draft_content.json` is an identical
    copy. Write both, always the same content.
  - `draft_meta_info.json`: name, folder, duration, the media panel (`draft_materials`, type 0 = imported media).
  - `timeline_layout.json`, `draft_cover.jpg`. CapCut adds the rest itself on first open (`.locked`,
    `draft_agency_config.json`, `adjust_mask/`, `matting/` ...).
- Fonts CapCut has downloaded: `%LOCALAPPDATA%\CapCut\User Data\Cache\effect\<resource id>\<hash>\<file>.ttf`. A
  text style names a font by `{"path", "id"}` (id = resource id). The house font Inter is there as Inter-SemiBold
  (`155387742`); Inter 700 itself is not.

## CapCut must be closed

It holds the open project in memory and writes it on save and on exit, and rewrites `root_meta_info.json` on exit.
Anything written while it runs is lost or overwritten. `.locked` in a project folder is not a reliable signal;
check for the `CapCut.exe` process.

## Timeline

- Times: integer **microseconds**. `target_timerange` = where on the timeline, `source_timerange` = which part of
  the file (`null` for text). `speed` scales source to target.
- `tracks[]`: `type` video / text / audio; the first video track is the main track; overlay video tracks have
  `flag: 2`. Segments on one track must not overlap: put overlapping clips on another track. `name` shows in
  the track header (`is_default_name: false`).
- Every segment points at a `material_id` (`materials.videos` / `audios` / `texts`) and a list of
  `extra_material_refs`, one fresh object each, in this order:
  - video: speeds, placeholder_infos, canvases, material_animations, sound_channel_mappings, material_colors,
    vocal_separations
  - audio: speeds, placeholder_infos, beats, sound_channel_mappings, vocal_separations
  - text: material_animations
- `volume` is linear amplitude (1.0 = 0 dB; 0.071 = -23 dB).
- `clip.transform` x, y: -1..1 from the canvas centre, **+y is up**. Pixel y on the 1080x1920 frame:
  `y = (960 - px) / 960`. `clip.scale` 1.0 = the file's size fitted to the canvas.
- `render_index`: higher draws on top (text uses 14000+).
- Ids: uppercase UUIDs with the third group lowercase (`B6478CE1-4A6B-414b-A84C-AE148344B10D`). CapCut keeps
  clip ids when it saves, which is how `capcut_changes.py` follows a clip; it falls back to matching by file and
  time when an id is new.

## Text

`materials.texts[].content` is a JSON string: `{"text": "...", "styles": [{"fill": {...solid color rgb 0..1},
"font": {"path", "id"}, "size": 11, "bold": true, "range": [a, b]}]}`. Ranges are in **UTF-16 code units** (an
emoji counts 2). One style per run of the same colour. `size` is CapCut's font size number, not pixels: 11 is
about the 66 px house subtitle and 12 the hook; adjust from what the creator does.

## Media

- Paths are absolute with forward slashes. CapCut caches by path: a changed file gets a **new name**
  (`<group>-<time>.mov`), never overwritten in place.
- Transparent overlays: ProRes 4444 `.mov` (yuva444p12le) plays with alpha in CapCut. Its alpha reads 256 (empty)
  to 3774 (opaque) in 12-bit, so "is anything visible" is `YMAX > 320`, not `> 0`.
- `hyperframes render --format mov` gives the alpha render; the page's background must be transparent
  (`html, body, #stage`), and the `<video>` element can be dropped from graphics-only passes (faster).
