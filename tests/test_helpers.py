import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills' / 'song-mv' / 'scripts'


def module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name+'.py'))
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


lrc = module('lrc_to_lyrics')
beat = module('beat_grid')
project = module('new_project')


class LyricsTests(unittest.TestCase):
    def test_milliseconds_repeated_tags_and_sort(self):
        rows = lrc.convert('[00:02.125][00:04.250]风\n[00:01.5]灯\n[00:05.000]', 0, 6)
        self.assertEqual([r[:3] for r in rows], [[1.5,2.125,'灯'],[2.125,4.25,'风'],[4.25,5,'风']])

    def test_positive_offset_advances(self):
        rows = lrc.convert('[00:01.000]早\n[offset:+500]\n[00:02.000]', 0, 3)
        self.assertEqual(rows[0][:2], [.5,1.5])

    def test_negative_offset_delays(self):
        self.assertEqual(lrc.convert('[offset:-200]\n[00:01]晚', 0, 3)[0][0], 1.2)

    def test_crossing_clip_boundary_preserves_singing_origin(self):
        rows = lrc.convert('[00:09]进入\n[00:12]下一句', 10, 4)
        self.assertEqual(rows[0][:2], [0,2]); self.assertEqual(rows[0][3]['singStart'], -1)

    def test_enhanced_timestamps_and_safe_lyric_content(self):
        rows = lrc.convert('[00:01]<00:01>风<00:01.5>灯`"<00:02>\n[00:03]', 0, 4)
        self.assertEqual(rows[0][2], '风灯`"')
        self.assertEqual(rows[0][3]['words'], [[1,'风'],[1.5,'灯`"'],[2,'']])
        self.assertEqual(json.loads(json.dumps(rows)), rows)

    def test_bilingual_duplicate_timestamp(self):
        rows = lrc.convert('[00:01]风\n[00:01]Wind\n[00:02]', 0, 3)
        self.assertEqual(rows[0][2], '风 · Wind')

    def test_utf_bom_and_gb18030(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'歌词.lrc'
            for encoding in ['utf-8-sig','utf-16','gb18030']:
                path.write_bytes('[00:01]风'.encode(encoding))
                self.assertEqual(lrc.decode(path), '[00:01]风')

    def test_invalid_lrc_and_parameters(self):
        for text in ['plain text','[00:99]bad']:
            with self.assertRaises(ValueError): lrc.parse_lrc(text)
        with self.assertRaises(ValueError): lrc.convert('[00:01]x', 0, float('nan'))
        with self.assertRaises(ValueError): lrc.parse_lrc('[00:01][00:03]<00:01>x')


class BeatTests(unittest.TestCase):
    def test_click_train_tempo_and_phase(self):
        sr=22050; x=np.zeros(sr*16, dtype=np.float32)
        for t in np.arange(.2,15.8,.5):
            start=round(t*sr); n=500
            x[start:start+n] += np.random.default_rng(1).normal(0,.3,n)*np.exp(-np.arange(n)/60)
        result=beat.estimate(x, sr, 100,140)
        self.assertLess(abs(result['bpm']-120), 1)
        phase=result['beat_at']; self.assertLess(min(abs(phase-.2), abs(phase-.7)), .07)

    def test_silence_and_short_audio_rejected(self):
        for x in [np.zeros(22050*8),np.ones(100)]:
            with self.assertRaises(ValueError): beat.estimate(x)


class ProjectTests(unittest.TestCase):
    def test_recursive_destination_and_nonfinite_duration_rejected(self):
        source=SCRIPTS.parent/'assets/template'
        with self.assertRaises(ValueError): project.create_project(source/'nested-new-project')
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError): project.create_project(Path(folder)/'bad',duration=float('nan'))

    def test_unicode_path_complete_project(self):
        with tempfile.TemporaryDirectory() as folder:
            dest=project.create_project(Path(folder)/'歌曲 工程', duration=4)
            self.assertTrue((dest/'lib/runtime.mjs').is_file())
            self.assertTrue((dest/'src/lyrics.js').is_file())
            self.assertIn('src/scenes/main.js',(dest/'studio.html').read_text(encoding='utf-8'))
            self.assertFalse((dest/'node_modules').exists())
            with self.assertRaises(ValueError): project.create_project(dest)

    def test_keep_demo(self):
        with tempfile.TemporaryDirectory() as folder:
            dest=project.create_project(Path(folder)/'demo',keep_demo=True)
            self.assertIn('src/scenes/demo.js',(dest/'studio.html').read_text(encoding='utf-8'))


if __name__ == '__main__': unittest.main()
