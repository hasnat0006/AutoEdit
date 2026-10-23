"""speechv1.py: auto-editor's v1 export carries no timebase, so frames are divided by the source's own rate."""
import json, os, shutil, subprocess, sys, tempfile, unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import speechv1


class SpeechV1(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def write(self, d):
        p = os.path.join(self.dir, "speech.v1")
        json.dump(d, open(p, "w")); return p

    def test_timebase_wins(self):
        p = self.write({"timebase": "24000/1001", "source": "nope.mp4", "chunks": [[0, 24, 1.0], [24, 48, 99999.0], [48, 96, 1.0]]})
        c = speechv1.chunks(p)
        self.assertEqual(len(c), 2)                       # the cut chunk is dropped
        self.assertAlmostEqual(c[1][1], 96 * 1001 / 24000.0, places=6)

    def test_no_source_falls_back_to_30(self):
        p = self.write({"source": "missing.mp4", "chunks": [[0, 30, 1.0]]})
        self.assertAlmostEqual(speechv1.chunks(p)[0][1], 1.0)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "needs ffmpeg")
    def test_rate_from_source_relative_to_a_parent(self):
        # auto-editor ran from the project root, so "source" is relative to a folder above the export
        os.makedirs(os.path.join(self.dir, "w", "raw"))
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=64x36:r=24000/1001:d=1",
                        os.path.join(self.dir, "w", "raw", "c.mp4")], check=True)
        p = os.path.join(self.dir, "w", "speech.v1")
        json.dump({"source": "w/raw/c.mp4", "chunks": [[0, 24, 1.0]]}, open(p, "w"))
        self.assertAlmostEqual(speechv1.chunks(p)[0][1], 24 * 1001 / 24000.0, places=4)


if __name__ == "__main__":
    unittest.main()
