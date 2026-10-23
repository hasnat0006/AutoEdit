"""compose.py (Shorts): every format builds into a 1080x1920 page, the captions follow the words, and the guards hold."""
import os, re, unittest
from .helpers import run, scratch, write, read

WORDS = [{"text": w, "start": round(0.2 + 0.3 * i, 3), "end": round(0.45 + 0.3 * i, 3)}
         for i, w in enumerate("I edit every Short with Claude. It saves a thousand dollars a month.".split())]
ALL = [
    {"type": "text", "id": "h1", "text": "I edit every Short", "em": [3], "in": 0.0, "out": 2.0, "anchor": "-"},
    {"type": "logo", "id": "lg", "src": "img/logo.svg", "pop": 2.2, "in": 2.1, "out": 3.4, "anchor": "Claude"},
    {"type": "chip", "id": "ch", "text": "it saves money", "em": [2], "in": 3.5, "out": 4.6, "anchor": "-"},
    {"type": "list", "id": "ls", "items": [["A phone", 4.9], ["One script", 5.4, "-"]], "marker": "check", "in": 4.7, "out": 6.4, "anchor": "-"},
    {"type": "stat", "id": "st", "value": 1000, "prefix": "$", "label": "a month", "color": "amber", "at": 6.7, "in": 6.5, "out": 8.0, "anchor": "-"},
    {"type": "image", "id": "im", "src": "img/post.png", "in": 8.1, "out": 9.0, "anchor": "-"},
    {"type": "clip", "id": "br", "src": "broll/desk.mp4", "label": "My desk", "in": 9.1, "out": 9.9, "anchor": "-"},
    {"type": "image", "id": "if", "src": "img/post.png", "frame": "full", "label": "The post", "in": 10.0, "out": 11.0, "anchor": "-", "hide_captions": True},
    {"type": "split", "id": "sp", "src": "broll/half.mp4", "in": 11.2, "out": 13.0, "anchor": "-"},
    {"type": "vignette", "id": "vg", "in": 13.1, "out": 13.8, "anchor": "-"},
    {"type": "cta", "id": "ct", "text": "Follow for part 2", "in": 14.0, "out": 15.5, "anchor": "-"},
]


class ComposeShorts(unittest.TestCase):
    def build(self, beats, duration=15.5, words=WORDS, **extra):
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), words)
        spec = dict({"id": "t", "duration": duration, "beats": beats, "captions": {"transcript": "transcript.json"}}, **extra)
        sp = write(os.path.join(d, "storyboard.json"), spec)
        r = run("compose.py", "--spec", sp, "--out", os.path.join(d, "public"))
        page = read(os.path.join(d, "public", "index.html")) if r.returncode == 0 else ""
        return r, page

    def test_every_format_builds_vertical(self):
        r, page = self.build(ALL, progress=True, camera=[["punch", 2.1, 1.08], ["release", 3.4, 0.4]])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('data-width="1080" data-height="1920"', page)
        for needle in ('id="h1"', 'id="lg-glass"', 'id="ch-chip"', 'id="ls-i1"', "countUp('#st-n', 1000", 'id="im-img"', 'id="if-img"',
                       'class="cutaway-video clip" id="br"', 'class="split-video clip" id="sp"', 'id="ct-btn"', 'id="vg-vig"',
                       'id="progress"', 'src="sfx/pop.mp3"', 'id="cap0"'):
            self.assertIn(needle, page)
        self.assertIn('data-at="4.900" data-anchor="A phone"', page)          # list items carry their anchors for beat-check
        self.assertNotIn("WARN", r.stdout)

    def test_hook_title_is_on_the_first_frame(self):
        r, page = self.build(ALL[:1])
        self.assertNotIn("tl.fromTo('#h1 .w'", page)                          # in = 0: no entrance, it is simply there
        r, page = self.build([dict(ALL[0], **{"in": 1.0})], duration=4.0)
        self.assertIn("tl.fromTo('#h1 .w'", page)

    def test_captions_group_follow_the_words(self):
        r, page = self.build([], duration=6.0)
        self.assertEqual(r.returncode, 0, r.stderr)
        groups = re.findall(r'<div class="cap shadow" id="(cap\d+)"', page)
        # "I edit every" / "Short with Claude." / "It saves a" / "thousand dollars a" / "month."
        self.assertEqual(len(groups), 5, groups)
        self.assertIn('>Claude.</span></div>', page)
        self.assertIn("tl.set('#cap0', { visibility: 'visible' }, 0.160);", page)
        self.assertIn("tl.set('#cap0-w1', { color: '#0AF0F0' }, 0.500);", page)   # karaoke: "edit" lights on its word

    def test_captions_step_aside_and_ride_the_seam(self):
        spread = [{"text": "word%d" % i, "start": 0.2 + 1.2 * i, "end": 0.6 + 1.2 * i} for i in range(13)]   # one word every 1.2 s
        r, page = self.build(ALL, words=spread)
        self.assertEqual(r.returncode, 0, r.stderr)
        sets = [(v, float(t)) for v, t in re.findall(r"tl\.set\('#cap\d+', \{ visibility: '(visible|hidden)' \}, ([\d.]+)\)", page)]
        self.assertTrue([t for v, t in sets if v == "visible" and t < 10.0])
        self.assertFalse([t for v, t in sets if v == "visible" and 10.0 <= t < 11.0])        # hidden under the full-frame image
        self.assertIn(("hidden", 10.0), sets)                                                  # a group cut short where it starts
        self.assertIn("tl.to('#captions', { y: -280", page)                                    # split: up to the seam

    def test_held_to_the_last_frame_has_no_exit(self):
        r, page = self.build([dict(ALL[-1], **{"in": 1.0, "out": 4.0})], duration=4.0)   # the follow pill to the end
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("glassIn('#ct-glass'", page)
        self.assertNotIn("glassOut('#ct-glass'", page)

    def test_over_sixty_seconds_is_refused(self):
        r, _ = self.build([], duration=61.0)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("60 s at most", r.stdout + r.stderr)

    def test_bottom_position_is_refused(self):
        r, _ = self.build([dict(ALL[2], pos="bottom")])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("captions and YouTube's own UI", r.stdout + r.stderr)

    def test_warnings(self):
        late = dict(ALL[2], **{"in": 1.0, "out": 2.0})
        d = scratch(self)
        sp = write(os.path.join(d, "storyboard.json"), {"id": "t", "duration": 8.0, "beats": [late, dict(late, id="c2", **{"in": 3.0, "out": 4.0})],
                                                         "camera": [["punch", 1.0, 1.25]]})
        r = run("compose.py", "--spec", sp, "--out", os.path.join(d, "public"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("WARN hook gate", r.stdout)
        self.assertIn("WARN same device twice in a row: chip", r.stdout)
        self.assertIn("soft past ~1.15", r.stdout)

    def test_card_theme_and_motion_formats(self):
        beats = [
            {"type": "credit", "id": "src", "text": "Some podcast", "in": 0.0, "out": 15.5, "anchor": "-"},
            {"type": "title", "id": "tt", "text": "It wasn't|bad luck", "em": [1], "pulse": True, "in": 0.0, "out": 15.5, "anchor": "-",
             "strike": {"line": 1, "at": 3.0}, "swap": {"at": 6.0, "text": "It was|overconfidence", "em": [1]}},
            {"type": "emoji", "id": "die", "char": "\U0001F3B2", "spin": True, "in": 1.0, "out": 3.0, "anchor": "-"},
            {"type": "dots", "id": "od", "n": 20, "hit": [3], "label": "1 in 20", "at": 7.2, "in": 7.0, "out": 9.0, "anchor": "-"},
            {"type": "meter", "id": "mt", "label": "Certainty", "to": 1.3, "over_label": "Too much", "fill_at": 10.2, "in": 10.0, "out": 15.5, "anchor": "-"}]
        r, page = self.build(beats, theme={}, frame={"mode": "card"}, progress=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for needle in ('id="bg"', '<div id="card">', '<div id="progress"></div>\n    </div>', "RubikMonoOne-Regular.ttf",
                       'class="cap disp outl"', "scale: 1.12", 'id="tt-a-s1"', 'id="tt-b"', 'src="emoji/emoji_u1f3b2.svg"',
                       "#od .dt.hit", "#mt-fil", 'id="mt-over"'):
            self.assertIn(needle, page)
        self.assertIn('style="top:1208px;font-size:56px"', page)    # captions sit under the card: 600 + 562 + 46
        self.assertNotIn("same device", r.stdout)                    # emoji, credit and title are accents

    def test_hand_made_formats(self):
        beats = [
            {"type": "title", "id": "tt", "text": "It wasn't|bad luck", "em": [1], "in": 0.0, "out": 15.5, "anchor": "-",
             "strike": {"line": 1, "at": 3.0}, "swap": {"at": 6.0, "text": "It was|overconfidence", "em": [1], "underline": 1}},
            {"type": "draw", "id": "dr", "in": 0.9, "out": 2.5, "anchor": "-",
             "shapes": [{"shape": "burst", "cx": 560, "cy": 580, "n": 4, "at": 1.0}, {"shape": "arrow", "x1": 100, "y1": 100, "x2": 300, "y2": 200, "at": 1.4}]},
            {"type": "dice", "id": "dc", "face": 1, "in": 2.6, "out": 4.0, "anchor": "-"},
            {"type": "dots", "id": "od", "n": 20, "hit": [3], "ring": True, "at": 7.2, "in": 7.0, "out": 9.0, "anchor": "-"},
            {"type": "chart", "id": "ch", "in": 9.5, "out": 11.5, "anchor": "-",
             "lines": [{"label": "Reality", "points": [[0, .3], [1, .35]], "color": "text"}, {"label": "Expected", "points": [[0, .3], [1, 1]], "arrow": True}]}]
        r, page = self.build(beats, theme={}, frame={"mode": "card"})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(page.count('pathLength="100"'), 4 + 3 + 1 + 1 + 2 + 2)   # burst 4, arrow 3, ring 1, axis 1, lines 2, arrowhead 2 (strike and underline wipe in)
        self.assertIn("tl.fromTo('#tt-b-u1', { clipPath: 'inset(0% 100% 0% 0%)' }", page)
        self.assertIn('id="tt-a-s1b"', page)
        self.assertEqual(page.count('class="dice-face"'), 6)
        self.assertEqual(page.count('class="pip red"'), 1)            # face 1 is the only red pip
        self.assertIn("rotationX: -16, rotationY: 22", page)          # lands face-on, a little turned
        self.assertIn('id="ch-l1-t"', page)
        r2, page2 = self.build(beats, theme={}, frame={"mode": "card"})
        self.assertEqual(page, page2)                                 # the wobble is seeded: a rebuild draws the same strokes

    def test_motion_formats_need_a_theme(self):
        r, _ = self.build([{"type": "meter", "id": "mt", "label": "x", "in": 0.0, "out": 2.0, "anchor": "-"}])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('needs a "theme"', r.stdout + r.stderr)

    def test_missing_emoji_image_is_named(self):
        r, _ = self.build([{"type": "emoji", "id": "e", "char": "\U0001F984", "in": 0.0, "out": 2.0, "anchor": "-"}])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("emoji_u1f984.svg", r.stdout + r.stderr)

    def test_unknown_type_is_named(self):
        r, _ = self.build([{"type": "world", "id": "w", "in": 0.0, "out": 1.0}])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("unknown beat type 'world'", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
