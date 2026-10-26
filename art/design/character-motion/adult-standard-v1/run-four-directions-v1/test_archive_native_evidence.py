"""Final evidence gate must reject incomplete/stale captures before publishing."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('archive_under_test', Path(__file__).with_name('archive_native_evidence.py'))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class ArchiveGateTests(unittest.TestCase):
    def test_empty_native_records_never_publish_success_summary(self):
        with tempfile.TemporaryDirectory(prefix='coastal-archive-gate-', dir='/private/tmp') as folder:
            root = Path(folder)
            old = MODULE.ROOT, MODULE.SOURCE, MODULE.OUTPUT
            MODULE.ROOT = root / 'art/design/character-motion/adult-standard-v1/run-four-directions-v1'
            MODULE.SOURCE = root / 'captures'
            MODULE.OUTPUT = MODULE.ROOT / 'evidence/native'
            MODULE.ROOT.mkdir(parents=True)
            MODULE.SOURCE.mkdir()
            candidate = {'directions': ['south', 'west', 'east', 'north'], 'frames': []}
            (MODULE.ROOT / 'candidate.json').write_text(json.dumps(candidate))
            (MODULE.ROOT / 'run-garments.json').write_text(json.dumps({'recipes': {'A': {d: [] for d in candidate['directions']}, 'B': {'west': [], 'east': []}}}))
            (MODULE.SOURCE / 'checks.json').write_text('{"native_renderer":true}')
            (MODULE.SOURCE / 'boards.json').write_text(json.dumps({'candidate_manifest_sha256': MODULE.digest(MODULE.ROOT / 'candidate.json'), 'run_garments_sha256': MODULE.digest(MODULE.ROOT / 'run-garments.json'), 'script_sha256':'stale', 'boards':[]}))
            try:
                with self.assertRaises(ValueError):
                    MODULE.main()
                self.assertFalse(MODULE.OUTPUT.exists(), 'Do not partially publish rejected evidence')
            finally:
                MODULE.ROOT, MODULE.SOURCE, MODULE.OUTPUT = old



class CompleteCaptureGateTests(unittest.TestCase):
    def setUp(self):
        from PIL import Image
        self.temporary = tempfile.TemporaryDirectory(prefix='coastal-capture-gate-',dir='/private/tmp')
        self.project = Path(self.temporary.name)
        self.old = MODULE.ROOT, MODULE.SOURCE, MODULE.OUTPUT
        MODULE.ROOT = self.project/'art/design/character-motion/adult-standard-v1/run-four-directions-v1'
        MODULE.SOURCE = self.project/'captures'
        MODULE.OUTPUT = MODULE.ROOT/'evidence/native'
        MODULE.ROOT.mkdir(parents=True)
        MODULE.SOURCE.mkdir()
        for name in ['dev/character_walk_trial.gd','tests/test_character_run_directions_native.gd','tests/capture_character_run_direction_boards.gd']:
            path=self.project/'godot2d'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('fixture script '+name)
        directions=['south','west','east','north']
        recipes={'A':{d:[] for d in directions},'B':{'west':[],'east':[]}}
        self.combinations={(d,g) for g,ds in recipes.items() for d in ds}
        candidate={'directions':directions,'playback_rate':0.75,'walk_artifact_digest':'fixture-walk',
                   'frames':[{'direction':d,'pose_id':f'run_{d}_{i}','duration_ms':80} for d in directions for i in range(4)]}
        (MODULE.ROOT/'candidate.json').write_text(json.dumps(candidate))
        (MODULE.ROOT/'run-garments.json').write_text(json.dumps({'recipes':recipes}))
        candidate_hash=MODULE.digest(MODULE.ROOT/'candidate.json');garment_hash=MODULE.digest(MODULE.ROOT/'run-garments.json')
        (MODULE.SOURCE/'checks.json').write_text(json.dumps({k:True for k in MODULE.required_checks(directions,self.combinations)}))
        self.boards={'candidate_manifest_sha256':candidate_hash,'run_garments_sha256':garment_hash,'walk_artifact_digest':'fixture-walk',
                     'script_sha256':MODULE.digest(self.project/'godot2d/tests/capture_character_run_direction_boards.gd'),
                     'renderer':'macOS','output_px':[2560,1440],'scale':138/582,'magnifications':[1,2],'boards':[]}
        for d,g in sorted(self.combinations):
            key=d+'-'+g
            filename='board-'+key+'.png'
            Image.new('RGB',(2560,1440)).save(MODULE.SOURCE/filename)
            self.boards['boards'].append({'direction':d,'garment':g,'file':filename,'sha256':MODULE.digest(MODULE.SOURCE/filename)})
            # Tiny files test the archival path contract, not rendered art.
            for i in range(4):(MODULE.SOURCE/(key+str(i)+'.png')).write_bytes(b'fixture capture')
            data={'direction':d,'garment':g,'candidate_manifest_sha256':candidate_hash,'run_garments_sha256':garment_hash,
                  'trial_script_sha256':MODULE.digest(self.project/'godot2d/dev/character_walk_trial.gd'),
                  'test_script_sha256':MODULE.digest(self.project/'godot2d/tests/test_character_run_directions_native.gd'),
                  'samples':[{'wall_ms':i*40,'pose_id':f'run_{d}_{i%4}','capture_file':key+str(i%4)+'.png'} for i in range(110)]}
            (MODULE.SOURCE/('metadata-'+key+'.json')).write_text(json.dumps(data))
        self.write_boards()

    def tearDown(self):
        MODULE.ROOT,MODULE.SOURCE,MODULE.OUTPUT=self.old
        self.temporary.cleanup()

    def write_boards(self):
        (MODULE.SOURCE/'boards.json').write_text(json.dumps(self.boards))

    def reject(self,message):
        with self.assertRaisesRegex(ValueError,message):MODULE.main()
        self.assertFalse(MODULE.OUTPUT.exists())

    def test_complete_six_combinations_validate_without_publishing(self):
        self.assertEqual(len(MODULE.validate_inputs()[3]),6)
        self.assertFalse(MODULE.OUTPUT.exists())

    def test_missing_combination_is_rejected(self):
        (MODULE.SOURCE/'metadata-west-B.json').unlink()
        self.reject('metadata combinations')

    def test_duplicate_board_is_rejected(self):
        self.boards['boards'].append(self.boards['boards'][0]);self.write_boards()
        self.reject('board combinations')

    def test_stale_board_script_is_rejected(self):
        self.boards['script_sha256']='stale';self.write_boards()
        self.reject('Stale board script')

    def test_wrong_direction_pose_is_rejected(self):
        path=MODULE.SOURCE/'metadata-north-A.json';data=json.loads(path.read_text())
        data['samples'][0]['pose_id']='run_west_0';path.write_text(json.dumps(data))
        self.reject('native poses')

    def test_short_sequence_is_rejected(self):
        path=MODULE.SOURCE/'metadata-north-A.json';data=json.loads(path.read_text())
        for sample in data['samples']:sample['wall_ms']/=2
        path.write_text(json.dumps(data));self.reject('shorter than ten cycles')

    def test_missing_capture_is_rejected(self):
        (MODULE.SOURCE/'north-A0.png').unlink();self.reject('Missing or unsafe capture')

if __name__ == '__main__': unittest.main()
