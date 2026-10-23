"""voice-pitch.py finds the second voice; edge-levels.py marks every cut edge. Synthetic voices: harmonic tones."""
import os, unittest
from .helpers import ffmpeg, needs_ffmpeg, run, scratch, write

# three "words": the guest at 200 Hz, the host at 95 Hz, the guest again; gaps of silence between them
VOICES = [(0.2, 0.7, 200), (1.0, 1.4, 95), (1.7, 2.3, 205)]


def voice_wav(d):
    parts = ["aevalsrc='%s':s=16000:d=2.6" % "+".join(
        "if(between(t,%.2f,%.2f),0.3*sin(2*PI*%d*t)+0.15*sin(4*PI*%d*t)+0.08*sin(6*PI*%d*t),0)" % (a, b, f, f, f) for a, b, f in VOICES)]
    path = os.path.join(d, "audio-raw.wav")
    ffmpeg("-f", "lavfi", "-i", parts[0], "-acodec", "pcm_s16le", "-ac", "1", path)
    words = write(os.path.join(d, "words.json"), [{"text": t, "start": a, "end": b} for (a, b, _), t in zip(VOICES, ["Guest", "Yeah.", "again"])])
    return path, words


@needs_ffmpeg
class PodcastTools(unittest.TestCase):
    def test_host_word_is_flagged(self):
        d = scratch(self)
        wav, words = voice_wav(d)
        r = run("voice-pitch.py", "--audio", wav, "--transcript", words)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertRegex(r.stdout, r"Yeah\.\s+9\d Hz  <-- another voice\?")
        self.assertIn("1 word(s) flagged", r.stdout)

    def test_edges_are_charted(self):
        d = scratch(self)
        wav, words = voice_wav(d)
        cl = write(os.path.join(d, "cut-list.json"), {"kept": [{"start": 0.1, "end": 0.85}, {"start": 1.6, "end": 2.45}]})
        r = run("edge-levels.py", "--audio", wav, "--cut-list", cl, "--transcript", words, "--pad", "0.2")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.count("<== cut"), 4)
        self.assertIn("---- segment 1: 1.60 - 2.45", r.stdout)


if __name__ == "__main__":
    unittest.main()
