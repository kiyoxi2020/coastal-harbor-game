import copy
import hashlib
import importlib.util
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
MODULE = Path(__file__).parents[1] / 'construction_native.py'
STATES = ['bare', 'hair', 'hat', 'hair_hat']

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

class ConstructionNativeTests(unittest.TestCase):
    def module(self):
        self.assertTrue(MODULE.exists(), 'Construction native validator is not implemented')
        spec = importlib.util.spec_from_file_location('construction_native_test', MODULE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def fixture(self, m, repo):
        evidence = repo / 'evidence'; evidence.mkdir()
        source = repo / 'input.txt'; source.write_text('frozen source')
        contract = {'kind': m.KIND, 'schema_version': 1, 'validator_sha256': sha(MODULE),
                    'files': {'input.txt': sha(source)}, 'suite_sha256': 'b'*64,
                    'sample_id': 'hoe-west', 'duration_ms': [100,100,100,100],
                    'pose_ids': ['p0','p1','p2','p3'], 'states': STATES,
                    'manifest_sha256': {s: str(i)*64 for i,s in enumerate(STATES,1)}}
        contract['contract_digest'] = m.contract_digest(contract)
        write(evidence/'input-contract.json', contract)
        hashes = {}
        for name in m.required_pngs('hoe-west', STATES):
            p = evidence/name; p.parent.mkdir(parents=True,exist_ok=True)
            Image.new('RGBA',(300,320) if '-world-' in name else (20,4) if name.startswith('boards/') else (4,4), (20,80,160,255)).save(p)
            hashes[name] = sha(p)
        checks = {key: True for key in m.required_checks('hoe-west',STATES)}
        samples=[]
        for state in STATES:
            for i in range(41):
                phase=float(i*100%400); unwrapped=float(i*100)
                row={'clip':'hoe-west','state':state,'wall_ms':i*100,
                                'phase_ms':phase,'unwrapped_ms':unwrapped,'pose':int(phase//100),
                                'phase_f64le':struct.pack('<d',phase).hex(),
                                'unwrapped_f64le':struct.pack('<d',unwrapped).hex()}
                if i%2==0:
                    name=f'sequence/hoe-west-{state}-cycle-{i//2:04d}.png'
                    path=evidence/name;Image.new('RGBA',(4,4),(20,80,160,255)).save(path);hashes[name]=sha(path);row['capture']=name
                samples.append(row)
        report={'input_contract_sha256':sha(evidence/'input-contract.json'), 'catalog_sha256':'b'*64,
                'renderer':{'display_server':'macOS','rendering_method':'gl_compatibility','adapter':'Test GPU'},
                'manifest_sha256':contract['manifest_sha256'], 'checks':checks,
                'clips':{'hoe-west':{'pose_ids':contract['pose_ids'],'durations_ms':contract['duration_ms'],'states':STATES}},
                'samples':samples,'captures':list(hashes), 'output_hashes':hashes}
        write(evidence/'report.json',report)
        return evidence,contract,report

    def test_accept_complete_four_state_capture(self):
        m=self.module()
        with tempfile.TemporaryDirectory(prefix='coastal-native-tests-',dir='/private/tmp') as t:
            repo=Path(t);e,c,r=self.fixture(m,repo)
            result=m.validate_capture(repo,e)
            self.assertTrue(result['passed']); self.assertEqual(result['states'],STATES)
            self.assertEqual(result['panel_cycles_per_state'],10)

    def test_reject_missing_states_poses_cycles_and_bad_binary_timing(self):
        m=self.module()
        with tempfile.TemporaryDirectory(prefix='coastal-native-tests-',dir='/private/tmp') as t:
            repo=Path(t);e,c,r=self.fixture(m,repo)
            for defect in ['state','pose','cycles','binary','nonfinite','accumulation','check','headless','manifest','suite','png_set','capture_path','malformed_sample','row_capture','missing_row_capture']:
                bad=copy.deepcopy(r)
                if defect=='state':bad['samples']=[x for x in bad['samples'] if x['state']!='hat']
                elif defect=='pose':bad['samples'][2]['pose']=0
                elif defect=='cycles':bad['samples']=[x for x in bad['samples'] if x['unwrapped_ms']<4000]
                elif defect=='binary':bad['samples'][2]['phase_f64le']='00'
                elif defect=='nonfinite':bad['samples'][2]['phase_f64le']=struct.pack('<d',float('nan')).hex()
                elif defect=='accumulation':bad['samples'][2]['unwrapped_f64le']=struct.pack('<d',201.0).hex()
                elif defect=='check':bad['checks'].pop(next(iter(bad['checks'])))
                elif defect=='headless':bad['renderer']['display_server']='headless'
                elif defect=='manifest':bad['manifest_sha256']['hat']='0'*64
                elif defect=='suite':bad['catalog_sha256']='0'*64
                elif defect=='png_set':bad['output_hashes'].pop(next(iter(bad['output_hashes'])))
                elif defect=='capture_path':bad['captures'][0]='../escaped.png'
                elif defect=='malformed_sample':bad['samples'][0]=[]
                elif defect=='row_capture':bad['samples'][0]['capture']='sequence/missing.png'
                elif defect=='missing_row_capture':bad['samples'][0].pop('capture')
                write(e/'report.json',bad)
                with self.subTest(defect=defect),self.assertRaises((ValueError,KeyError,TypeError)):
                    m.validate_capture(repo,e)

    def test_reject_changed_input_output_and_unsafe_receipt(self):
        m=self.module()
        with tempfile.TemporaryDirectory(prefix='coastal-native-tests-',dir='/private/tmp') as t:
            repo=Path(t);e,c,r=self.fixture(m,repo)
            (repo/'input.txt').write_text('changed')
            with self.assertRaises(ValueError):m.validate_capture(repo,e)
            (repo/'input.txt').write_text('frozen source')
            image=e/next(iter(r['output_hashes'])); old=image.read_bytes();image.write_bytes(b'broken')
            with self.assertRaises(ValueError):m.validate_capture(repo,e)
            image.write_bytes(old)
            for target in [e/'report.json',e/'input-contract.json',repo/'input.txt']:
                with self.assertRaises(ValueError):m.write_receipt(repo,e,target)
            link=e/'alias.json';link.symlink_to(e/'report.json')
            with self.assertRaises(ValueError):m.write_receipt(repo,e,link)
            receipt=e/'receipt.json';m.write_receipt(repo,e,receipt)
            self.assertTrue(receipt.is_file())
            with self.assertRaises(ValueError):m.write_receipt(repo,e,receipt)

    def test_reject_path_escape(self):
        m=self.module()
        with self.assertRaises(ValueError):m._new_evidence_path(Path('/private/tmp/coastal-missing/../escaped-native'))

    def test_reject_report_changed_while_reading(self):
        m=self.module()
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(prefix='coastal-native-tests-',dir='/private/tmp') as t:
            repo=Path(t);e,c,r=self.fixture(m,repo)
            original=m.read_json
            def change_after_read(path):
                value=original(path)
                if Path(path)==e/'report.json':Path(path).write_text(json.dumps(value)+'\n')
                return value
            with patch.object(m,'read_json',side_effect=change_after_read):
                with self.assertRaises(ValueError):m.validate_capture(repo,e)

    def test_reject_long_gap_between_two_captured_rows(self):
        m=self.module()
        with tempfile.TemporaryDirectory(prefix='coastal-native-tests-',dir='/private/tmp') as t:
            repo=Path(t);e,c,r=self.fixture(m,repo)
            indices={state:0 for state in STATES}
            for row in r['samples']:
                state=row['state'];i=indices[state];indices[state]+=1
                name=f'sequence/hoe-west-{state}-cycle-{i:04d}.png'
                path=e/name;Image.new('RGBA',(4,4),(20,80,160,255)).save(path)
                r['output_hashes'][name]=sha(path)
                if name not in r['captures']:r['captures'].append(name)
                row['capture']=name;row['wall_ms']=i*1000
            write(e/'report.json',r)
            with self.assertRaises(ValueError):m.validate_capture(repo,e)

    def test_reject_contract_change_after_validation_before_receipt(self):
        m=self.module()
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(prefix='coastal-native-tests-',dir='/private/tmp') as t:
            repo=Path(t);e,c,r=self.fixture(m,repo);original=m.validate_capture
            def change_after_validation(*args):
                result=original(*args)
                path=e/'input-contract.json';path.write_text(path.read_text()+'\n')
                return result
            with patch.object(m,'validate_capture',side_effect=change_after_validation):
                with self.assertRaises(ValueError):m.write_receipt(repo,e,e/'receipt.json')
            self.assertFalse((e/'receipt.json').exists())

if __name__=='__main__':unittest.main()
