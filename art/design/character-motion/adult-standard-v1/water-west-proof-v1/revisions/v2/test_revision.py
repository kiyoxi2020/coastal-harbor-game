from pathlib import Path
import hashlib
import json
import unittest
from PIL import Image

ROOT=Path(__file__).resolve().parent

class WaterRevisionCheck(unittest.TestCase):
    def candidate(self):
        self.assertTrue((ROOT/'candidate.json').is_file(),'v2 registration must be built')
        return json.loads((ROOT/'candidate.json').read_text())

    def test_full_source_is_partitioned_without_gaps_or_overlap(self):
        self.candidate()
        cfg=json.loads((ROOT/'registration-config.json').read_text())
        boxes=[x['source_box_px'] for x in cfg['frames']]
        self.assertEqual(boxes[0][0],0)
        self.assertEqual(boxes[-1][2],2048)
        self.assertEqual([b[2] for b in boxes[:-1]],[b[0] for b in boxes[1:]])
        self.assertTrue(all(b[1]==0 and b[3]==768 for b in boxes))

    def test_registered_frames_are_only_exact_crop_and_whole_translation(self):
        data=self.candidate()
        cfg=json.loads((ROOT/'registration-config.json').read_text())
        source=Image.open(ROOT/cfg['source']).convert('RGBA')
        for spec,record in zip(cfg['frames'],data['frames']):
            expected=Image.new('RGBA',tuple(cfg['canvas_px']))
            expected.paste(source.crop(spec['source_box_px']),tuple(spec['whole_frame_translation_px']))
            self.assertEqual(expected.tobytes(),Image.open(ROOT/record['file']).convert('RGBA').tobytes())
            self.assertGreater(record['duration_ms'],0)

    def test_actual_dependencies_match_manifest_hashes(self):
        for path,expected in self.candidate()['inputs'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),expected,path)

    def test_peak_handle_uses_extended_source_crop_coordinates(self):
        poses=json.loads((ROOT/'poses.json').read_text())['poses']
        # Independently observed handle point in nominal cell2 is(194,436).
        self.assertEqual(poses[2]['landmarks_px']['handle_contact'],[277,436])

if __name__=='__main__':
    unittest.main()
