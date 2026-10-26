"""Fail closed using in-memory file overrides; never alter approved inputs."""
import copy,importlib.util,json,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
MODULE=HERE/'dependency_contract.py'
API=None
if MODULE.exists():
 spec=importlib.util.spec_from_file_location('dependency_contract',MODULE)
 API=importlib.util.module_from_spec(spec);spec.loader.exec_module(API)
class DependencyGateTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.contract=API.make_contract(ROOT,include_git=False) if API else None
 def require_api(self):
  if API is None:self.skipTest('validator not implemented yet')
 def test_current_full_closure_valid(self):
  self.assertIsNotNone(API,'Missing dependency-contract builder/validator')
  self.assertTrue(API.validate(self.contract,ROOT)['input_hashes_current'])
 def test_missing_mandatory_roles_rejected(self):
  self.require_api()
  for role in ['locomotion','run_candidate','run_garments','world','camera','project']:
   with self.subTest(role=role):
    c=copy.deepcopy(self.contract);c['dependencies'].pop(c['required_roles'][role])
    with self.assertRaises(ValueError):API.validate(c,ROOT)
 def test_missing_role_declaration_rejected(self):
  self.require_api();c=copy.deepcopy(self.contract);c['required_roles'].pop('world')
  with self.assertRaises(ValueError):API.validate(c,ROOT)
 def test_missing_actual_mandatory_files_rejected(self):
  self.require_api()
  for role in ['locomotion','run_candidate','run_garments','world','camera','project']:
   with self.subTest(role=role):
    target=self.contract['required_roles'][role]
    def read(path):
     if path==target:raise FileNotFoundError(path)
     return (ROOT/path).read_bytes()
    with self.assertRaises(ValueError):API.validate(self.contract,ROOT,read=read)
 def test_real_idle_texture_tamper_rejected(self):self.tamper('idle_texture')
 def test_real_run_texture_tamper_rejected(self):self.tamper('run_texture')
 def test_real_camera_file_tamper_rejected(self):self.tamper('camera')
 def test_real_world_file_missing_rejected(self):
  self.require_api();target=self.contract['required_roles']['world']
  def read(path):
   if path==target:raise FileNotFoundError(path)
   return (ROOT/path).read_bytes()
  with self.assertRaises(ValueError):API.validate(self.contract,ROOT,read=read)
 def test_original_native_report_tamper_rejected(self):self.tamper('native_report')
 def test_added_static_dependency_missing_from_contract_rejected(self):
  self.require_api();c=copy.deepcopy(self.contract)
  target=next(p for p in c['dependencies'] if p.endswith('/terrain.tscn'))
  c['dependencies'].pop(target)
  with self.assertRaises(ValueError):API.validate(c,ROOT)
 def test_failed_gate_clears_preexisting_true_summary(self):
  self.require_api();target=self.contract['required_roles']['camera']
  def read(path):return (ROOT/path).read_bytes()+(b' changed' if path==target else b'')
  with tempfile.TemporaryDirectory(prefix='coastal-dependency-gate-',dir='/private/tmp') as directory:
   contract=Path(directory)/'contract.json';summary=Path(directory)/'summary.json'
   contract.write_text(json.dumps(self.contract));summary.write_text(json.dumps({'input_hashes_current':True}))
   with self.assertRaises(ValueError):API.record_validation(contract,summary,ROOT,read=read)
   self.assertFalse(json.loads(summary.read_text())['input_hashes_current'])
 def test_successful_gate_binds_exact_contract_sha(self):
  self.require_api()
  with tempfile.TemporaryDirectory(prefix='coastal-dependency-gate-',dir='/private/tmp') as directory:
   contract=Path(directory)/'contract.json';summary=Path(directory)/'summary.json'
   contract.write_text(json.dumps(self.contract));summary.write_text(json.dumps({'native_passed':True}))
   result=API.record_validation(contract,summary,ROOT)
   actual=json.loads(summary.read_text());self.assertTrue(actual['input_hashes_current']);self.assertTrue(actual['native_passed'])
   self.assertEqual(actual['dependency_contract_sha256'],API.sha(contract.read_bytes()))
 def tamper(self,role):
  self.require_api();target=self.contract['required_roles'][role]
  def read(path):return (ROOT/path).read_bytes()+(b' changed' if path==target else b'')
  with self.assertRaises(ValueError):API.validate(self.contract,ROOT,read=read)
if __name__=='__main__':unittest.main()
