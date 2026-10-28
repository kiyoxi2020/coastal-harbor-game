import unittest,tempfile,json,hashlib
from pathlib import Path
import evidence_contract as m
class ContractTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='coastal-wardrobe-test-');self.root=Path(self.tmp.name);self.catalog=self.root/'catalog.json';records=[]
  for id in sorted(m.IDS):
   folder=self.root/id;folder.mkdir();(folder/'source.bin').write_bytes(b'source')
   (folder/'sample.json').write_text(json.dumps({'action_id':id.split('-')[0],'direction':id.split('-')[1],'inputs':{'source.bin':m.sha(folder/'source.bin')}}))
   records.append({'id':id,'sample':id+'/sample.json','sha256':m.sha(folder/'sample.json')})
  self.data={'schema_version':1,'scope':'sampled-not-exhaustive','samples':records};self.save()
 def tearDown(self):self.tmp.cleanup()
 def save(self):self.catalog.write_text(json.dumps(self.data))
 def test_complete_closure(self):self.assertEqual(len(m.collect(self.root,self.catalog)),11)
 def test_missing_action_rejected(self):
  self.data['samples'].pop();self.save()
  with self.assertRaises(ValueError):m.collect(self.root,self.catalog)
 def test_duplicate_action_rejected(self):
  self.data['samples'][1]=self.data['samples'][0];self.save()
  with self.assertRaises(ValueError):m.collect(self.root,self.catalog)
 def test_parent_traversal_rejected(self):
  self.data['samples'][0]['sample']='../outside.json';self.save()
  with self.assertRaises(ValueError):m.collect(self.root,self.catalog)
 def test_changed_source_rejected(self):
  (self.root/self.data['samples'][0]['id']/'source.bin').write_bytes(b'changed')
  with self.assertRaises(ValueError):m.collect(self.root,self.catalog)
 def test_receipt_does_not_overwrite_contract(self):
  contract=self.root/'contract.json';report=self.root/'report.json';contract.write_bytes(b'{}');report.write_bytes(b'{}')
  with self.assertRaises(ValueError):m.validate(contract,report,contract)
  self.assertEqual(contract.read_bytes(),b'{}');self.assertEqual(report.read_bytes(),b'{}')
 def test_receipt_does_not_overwrite_report(self):
  contract=self.root/'contract.json';report=self.root/'report.json';contract.write_bytes(b'{}');report.write_bytes(b'{}')
  with self.assertRaises(ValueError):m.validate(contract,report,report)
  self.assertEqual(contract.read_bytes(),b'{}');self.assertEqual(report.read_bytes(),b'{}')
 def test_receipt_symlink_alias_rejected(self):
  contract=self.root/'contract.json';report=self.root/'report.json';alias=self.root/'receipt.json';contract.write_bytes(b'{}');report.write_bytes(b'{}');alias.symlink_to(contract)
  with self.assertRaises(ValueError):m.validate(contract,report,alias)
  self.assertEqual(contract.read_bytes(),b'{}')
 def test_receipt_hardlink_alias_rejected(self):
  contract=self.root/'contract.json';report=self.root/'report.json';alias=self.root/'receipt.json';contract.write_bytes(b'{}');report.write_bytes(b'{}');alias.hardlink_to(contract)
  with self.assertRaises(ValueError):m.validate(contract,report,alias)
  self.assertEqual(contract.read_bytes(),b'{}')
if __name__=='__main__':unittest.main()
