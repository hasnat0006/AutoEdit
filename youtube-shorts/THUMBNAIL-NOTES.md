# Thumbnail notes: what the creator picked

One line per Short after the creator chooses a thumbnail: the Short, the version picked (or "none"), what they
changed or said. The `shorts-thumbnail` skill reads this before every thumbnail. A rule for every thumbnail goes
in the skill's "The look" too.

- clashcam-01/04/05/06 (2026-10): made before the skill, by `videos/clash-cam/thumbnails/make_thumbs.py`: a speaker
  close-up in a black frame, a 2-line headline with one yellow-box word, a team-colour photo inset on 04 and 05.
- clash02-01 v1 (2026-10-20): **none.** All three letterboxed versions (a black frame with a square close-up, the
  headline above, one with a small photo inset) rejected: "I don't like anyone. I want some more professional. key
  person face, and key moment on screen using text or image or something. and always make it full 9:16."
- clash02-01 v2 (2026-10-20): the full 9:16 cut-out look (Kawhi's shot behind, ball ringed, Rusty cut out). B
  (Rusty mouth open, 24.2 s): "B is good but the hook text should need to be more eye catchy."
- clash02-01 v3 (2026-10-20): B's picture with a sticker hook: H2 (white plate "HE SAW A" + Raptors-red plate
  "[5TH] BOUNCE", tilted -4°) and H3 ("WAIT…" / giant "A [5TH]" / red "BOUNCE?!"). **H3 picked**: "H3 is good
  but you can blur a bit of the background of the text" → a 10 px blurred band behind the hook (now the default).
- clashcam-02 v2 / 03 v2 / 07 / 08 / 09 / 10 (2026-10-21): made with the skill, 3 versions each, A suggested on each
  (waiting for the creator's pick). Cam's yellow hat brim is dropped by the person model: `person.keep_color`
  [217, 173, 64, 60-70] keeps it; crop the top at y 125 on Cam's shots so the show's top-left caption stays off the hat.
- coacho-01/02/03/04 (2026-10-22): 3 versions each; suggested 01 A, 02 B, 03 A, 04 A (waiting for the creator's pick). Coach O's
  close-ups have a mic beside him: crop [60,0,1200,1080] at width 1150 keeps the head below the headline, `fade` 320 hides
  the mic remnant. Commons B-roll as the moment; a photo whose face sits high (Burrow) needs `bottom` ~520.
- coco-01/02 (ClipFarm x CoCo Jones, 2026-10-22): 3 versions each, A suggested on both (waiting for the creator's pick). 4K vlog source: crop the person to the top ~1500-1650 px with `fade` 260-300 so the head clears the headline; check the person frame is not inside a cutaway insert.
- pete-01 (Buttigieg on Diary of a CEO, 2026-10-23): 3 versions, C suggested (Form 1040 behind, "BILLIONAIRE VS. [TEACHER] WHO PAYS LESS?"; waiting for the creator's pick). The cut is one wide shot, so Pete is cut out from the master's close-up just before the clip. B-roll at 600 px is too soft as the moment: fetch a 2000 px copy. A stranger's face as the moment (teacher photo) competes with the key person.
- pete-02 (Buttigieg on Diary of a CEO, 2026-10-23): 3 versions, B suggested (U.S. Capitol behind, "WHO DECIDES AI'S [FUTURE]?"; waiting for the creator's pick). A landmark photo (Capitol) reads far better as the moment than a generic office.
