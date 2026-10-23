"""gap-scan.py on a Short: the picture must change every few seconds; a camera move counts, a set at a jump cut does not."""
import os, unittest
from .helpers import run, scratch, write

PAGE = """<div id="stage" data-composition-id="t" data-start="0" data-duration="20.000">
<div class="video-wrapper" id="video-wrap"><div id="video-zoom"><video id="bg-video" src="input-video.mp4" data-start="0" data-duration="20"></video></div></div>
<div class="card-host clip" id="host-a" data-start="0.000" data-duration="2.000" data-anchor="Hi"></div>
<div class="card-host clip" id="host-b" data-start="6.500" data-duration="2.000" data-anchor="this"></div>
<div id="captions"><div class="cap shadow" id="cap0" style="top:1180px">every word</div></div>
<script>
const tl = gsap.timeline({ paused: true });
tl.set('#video-zoom', { scale: 1.0 }, 0);
%s
</script>
</div>
"""
MOVES = """tl.to('#video-zoom', { scale: 1.080, duration: 0.30, ease: 'power2.out' }, 4.000);
tl.set('#video-zoom', { scale: 1.000 }, 6.000);
tl.to('#video-zoom', { scale: 1.06, duration: 3.000, ease: 'power1.inOut' }, 11.000);
tl.to('#video-zoom', { scale: 1.08, duration: 0.30, ease: 'power2.out' }, 17.000);"""


class GapScan(unittest.TestCase):
    def scan(self, js):
        d = scratch(self)
        return run("gap-scan.py", "--index", write(os.path.join(d, "public", "index.html"), PAGE % js))

    def test_moves_keep_the_picture_alive(self):
        r = self.scan(MOVES)
        self.assertEqual(r.returncode, 0, r.stdout)          # gaps 2.0, 2.2 (hook), 2.5, 3.0, 2.7 s: none over its limit
        self.assertIn("2 overlay(s), 3 camera move(s)", r.stdout)
        self.assertIn("4.30 -    6.50    2.2s", r.stdout)       # the set at 6.0 did not split this gap; captions do not count
        self.assertIn("density: 1.0 overlays + 1.5 camera moves per 10 s", r.stdout)

    def test_hook_and_body_limits(self):
        r = self.scan("tl.set('#video-zoom', { scale: 1.000 }, 6.000);")
        self.assertEqual(r.returncode, 1)
        self.assertIn("2.00 -    6.50    4.5s  <-- over 2.5s", r.stdout)       # starts inside the 5 s hook
        self.assertIn("8.50 -   20.00   11.5s  <-- over the 6s ceiling", r.stdout)


if __name__ == "__main__":
    unittest.main()
