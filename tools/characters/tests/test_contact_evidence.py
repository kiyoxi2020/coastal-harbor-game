"""Bounded source/native raster correspondence; tiny PNG fixtures prove tools."""
from pathlib import Path
import copy
import hashlib
import importlib
import json
import sys
import tempfile
import unittest
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from build_contract import stable


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ContactEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='coastal-contact-evidence-',dir='/private/tmp');self.addCleanup(self.temp.cleanup)
        self.repo=Path(self.temp.name);self.library=self.repo/'art/characters';self.library.mkdir(parents=True)
        self.raw=Image.new('RGBA',(60,60))
        for y in range(60):
            for x in range(60):self.raw.putpixel((x,y),((x*37+y*11)%251,(x*17+y*43)%251,(x*53+y*19)%251,255))
        self.inputs={}
        self.ref=self.image('sources/canonical.png',self.raw)
        self.poses=self.doc('templates/poses.json',{'variants':{'B':{'canvas_px':[60,60],'root_anchor_px':[30,55],'display_scale':.25,'frames':[{'pose_id':'hoe_south_key_2',**self.ref}]}}})
        shoe=Image.new('L',(60,60));shoe.paste(255,(5,43,55,57));self.shoe=self.image('parts/shoes.png',shoe)
        self.frame={'pose_id':'hoe_south_key_2','duration_ms':100,'layers':[{'slot':'shoes','coverage':self.shoe}]}
        self.base={'kind':'coastal-character-construction-v1','schema_version':3,'clips':[{'action_id':'hoe','direction':'south','variant':'B','poses':self.poses,'canvas_px':[60,60],'root_anchor_px':[30,55],'display_scale':.25,'frames':[self.frame]}]}
        self.base_ref=self.doc('recipes/body/r001.json',self.base)
        self.head={'kind':'coastal-character-construction-v1','schema_version':2,'base_recipe':self.base_ref,'clips':[{'action_id':'hoe','direction':'south','output_padding_px':[3,5,1,2],'frames':[{'pose_id':'hoe_south_key_2','layers':[],'layer_order':['base']}]}]}
        self.head_ref=self.doc('recipes/head/r001.json',self.head)
        self.output=Image.new('RGBA',(64,67));self.output.paste(self.raw,(3,5));self.build=self.library/'builds/tiny';self.build.mkdir(parents=True)
        self.output_path=self.build/'frames/hoe/south/hoe_south_key_2.png';self.output_path.parent.mkdir(parents=True);self.output.save(self.output_path)
        self.pointrow={'action':'hoe','direction':'south','pose_id':'hoe_south_key_2','variant':'B','canonical_pose_document':self.poses,'canonical_reference':self.ref,'full_original_or_legacy_derived_source':self.ref,'whole_frame_translation_px':[0,0],'canvas_px':[60,60],'root_anchor_px':[30,55],'display_scale':.25,'points':[{'id':'hand','canonical_px':[30,30],'source_px':[30,30],'RGBA':list(self.raw.getpixel((30,30))),'material':'observed hand','visible':True,'hidden_mechanical_contact_observable':False}],'grip_observation':'Visible material; hidden palm centre not fabricated.','target':{'kind':'soil-candidate','source_ground_contact_proven':False}}
        self.points=self.repo/'points.json';self.savepoints();self.savemanifest();self.evidence=self.repo/'native';self.evidence.mkdir()

    def image(self,name,im):
        p=self.library/name;p.parent.mkdir(parents=True,exist_ok=True);im.save(p);self.inputs[name]=sha(p);return {'file':name,'sha256':sha(p)}

    def doc(self,name,value):
        p=self.library/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value));self.inputs[name]=sha(p);return {'file':name,'sha256':sha(p)}

    def savepoints(self):self.points.write_text(json.dumps({'kind':'coastal-independent-actual-farm-contact-source-review-v1','rows':[self.pointrow]}))

    def savemanifest(self):
        self.manifest={'kind':'coastal-character-review-build-v1','schema_version':1,'recipe':self.head_ref['file'],'artifact_digest':hashlib.sha256(stable({'inputs':self.inputs,'engine':{}})).hexdigest(),'inputs':copy.deepcopy(self.inputs),'engine':{},'outputs':[{'file':self.output_path.relative_to(self.build).as_posix(),'sha256':sha(self.output_path),'rgba_sha256':hashlib.sha256(self.output.tobytes()).hexdigest(),'size':list(self.output.size)}]}
        self.mp=self.build/'manifest.json';self.mp.write_text(json.dumps(self.manifest))

    def module(self):
        self.assertTrue((Path(__file__).resolve().parents[1]/'contact_evidence.py').is_file(),'contact correspondence tool missing')
        return importlib.import_module('contact_evidence')

    def tool(self):return self.module().BoundContactEvidence(self.repo,self.mp,sha(self.mp),self.manifest['artifact_digest'],self.points,sha(self.points))

    def native(self,im=None,transform=None,missing_origin=False):
        if im is None:
            im=Image.new('RGBA',(160,160),(220,210,200,255))
            # Independent actual2x screenshot, output registration x+3/y+5,
            # transform translation10,12 and actual crop origin4,6.
            for y in range(self.output.height):
                for x in range(self.output.width):
                    q=self.output.getpixel((x,y))
                    if q[3]:
                        for dy in range(2):
                            for dx in range(2):im.putpixel((6+x*2+dx,6+y*2+dy),q)
        p=self.evidence/'actual.png';im.save(p)
        texture={'clip':'hoe-south','pose_id':'hoe_south_key_2','rgba_sha256':self.manifest['outputs'][0]['rgba_sha256']}
        row={'capture':'actual.png','mode':'farm-world-ten-instances','clip':'hoe-south','world_state':{'action':'hoe','direction':'south'},'texture':texture,'world_texture':copy.deepcopy(texture),'render_source_to_screen':transform or [2,0,0,2,10,12],'sprite_offset':[0,0],'actor_capture_origin_px':[4,6],'texture_size_px':[64,67],'physics_frame':1,'process_frame':1,'ticks_usec':100}
        if missing_origin:row.pop('actor_capture_origin_px')
        files={'art/characters/'+k:v for k,v in self.inputs.items()};files[self.mp.relative_to(self.repo).as_posix()]=sha(self.mp);files[self.output_path.relative_to(self.repo).as_posix()]=sha(self.output_path)
        c={'kind':'coastal-all-actions-native-input-v1','schema_version':1,'observer':'world','manifest':{'manifest':self.mp.relative_to(self.repo).as_posix(),'sha256':sha(self.mp)},'artifact_digest':self.manifest['artifact_digest'],'files':files};c['contract_digest']=hashlib.sha256(stable(c)).hexdigest();cp=self.evidence/'input-contract.json';cp.write_text(json.dumps(c));report={'kind':'coastal-registered-actions-world-observation-v1','input_contract_sha256':sha(cp),'renderer':'synthetic-test-GPU','checks':{'fixture':True},'samples':[row],'output_hashes':{'actual.png':sha(p)}};(self.evidence/'report.json').write_text(json.dumps(report));return row

    def test_static_reference_and_fixed41_roi_follow_whole_output_padding(self):
        item=self.tool().static_points()[0]
        self.assertEqual(item['final_px'],[33,35]);self.assertEqual(item['fixed_source_roi_px'],[10,10,51,51]);self.assertEqual(item['fixed_final_roi_px'],[13,15,54,56]);self.assertEqual(item['source_status'],'visible-unchanged');self.assertFalse(item['hidden_mechanical_contact_observable']);self.assertFalse(item['target']['source_ground_contact_proven'])

    def test_stale_canonical_reference_or_wrong_rgba_are_rejected(self):
        for bad in ['sha','rgba','variant']:
            old=copy.deepcopy(self.pointrow)
            if bad=='sha':self.pointrow['canonical_reference']['sha256']='0'*64
            if bad=='rgba':self.pointrow['points'][0]['RGBA'][0]^=1
            if bad=='variant':self.pointrow['variant']='A'
            self.savepoints()
            with self.subTest(bad=bad),self.assertRaises(ValueError):self.tool().static_points()
            self.pointrow=old

    def test_final_png_hash_cannot_be_replaced(self):
        self.output_path.write_bytes(self.output_path.read_bytes()+b'changed')
        with self.assertRaises(ValueError):self.tool().static_points()

    def test_native_correct_bound_unique_raster_with_fixed_roi(self):
        self.native();r=self.tool().native_receipt(self.evidence)
        row=r['measurements'][0];self.assertEqual(row['status'],'within-one-pixel');self.assertEqual(row['measurement']['offset_px'],[0,0]);self.assertTrue(r['raster_matrix_complete']);self.assertFalse(r['physical_contact_acceptance']);self.assertFalse(r['release_eligible'])

    def test_wrong_transform_measures_two_pixel_error_without_adjusting_roi(self):
        self.native(transform=[2,0,0,2,12,12]);r=self.tool().native_receipt(self.evidence);row=r['measurements'][0]
        self.assertEqual(row['status'],'mismatch');self.assertEqual(row['measurement']['offset_px'],[-2,0]);self.assertEqual(row['fixed_source_roi_px'],[10,10,51,51]);self.assertFalse(r['raster_matrix_complete'])

    def test_missing_actual_capture_origin_is_unverified_without_fallback(self):
        self.native(missing_origin=True);r=self.tool().native_receipt(self.evidence);self.assertEqual(r['measurements'][0]['status'],'unverified');self.assertIn('origin',r['measurements'][0]['reason'])

    def test_wrong_actual_texture_or_capture_digest_is_rejected(self):
        for bad in ['texture','png','contract']:
            self.native();rp=self.evidence/'report.json';r=json.loads(rp.read_text())
            if bad=='texture':r['samples'][0]['texture']['rgba_sha256']='wrong'
            if bad=='png':r['output_hashes']['actual.png']='0'*64
            if bad=='contract':r['input_contract_sha256']='0'*64
            rp.write_text(json.dumps(r))
            with self.subTest(bad=bad),self.assertRaises(ValueError):self.tool().native_receipt(self.evidence)

    def test_ambiguous_uniform_patch_is_unverified_even_near_one_pixel(self):
        self.raw=Image.new('RGBA',(60,60),(40,50,60,255));self.ref=self.image('sources/canonical.png',self.raw);self.pointrow['canonical_reference']=self.ref;self.pointrow['full_original_or_legacy_derived_source']=self.ref;self.pointrow['points'][0]['RGBA']=[40,50,60,255];self.poses=self.doc('templates/poses.json',{'variants':{'B':{'canvas_px':[60,60],'root_anchor_px':[30,55],'display_scale':.25,'frames':[{'pose_id':'hoe_south_key_2',**self.ref}]}}});self.pointrow['canonical_pose_document']=self.poses;self.base['clips'][0]['poses']=self.poses;self.base_ref=self.doc('recipes/body/r001.json',self.base);self.head['base_recipe']=self.base_ref;self.head_ref=self.doc('recipes/head/r001.json',self.head);self.output=Image.new('RGBA',(64,67));self.output.paste(self.raw,(3,5));self.output.save(self.output_path);self.savepoints();self.savemanifest();self.native();r=self.tool().native_receipt(self.evidence);self.assertEqual(r['measurements'][0]['status'],'unverified');self.assertIn('ambig',r['measurements'][0]['reason'].lower())

    def test_missing_pose_capture_remains_explicit_gap(self):
        self.native();rp=self.evidence/'report.json';r=json.loads(rp.read_text());r['samples']=[];rp.write_text(json.dumps(r));receipt=self.tool().native_receipt(self.evidence);self.assertFalse(receipt['raster_matrix_complete']);self.assertEqual(receipt['missing_points'],['hoe-south/hoe_south_key_2/hand'])

    def test_shoes_use_actual_base_mask_and_same_whole_frame_padding(self):
        item=self.tool().shoe_surfaces(actions=('hoe',))[0];self.assertEqual(item['mask'].size,(64,67));self.assertEqual(item['mask'].getbbox(),(8,48,58,62));self.assertEqual(item['coverage'],self.shoe)

    def test_near_only_ambiguity_is_bounded_but_any_far_optimum_unverified(self):
        classify=getattr(self.module(),'classify_raster',None);self.assertTrue(callable(classify),'bounded ambiguity classifier missing')
        good={'equally_good_offsets':[[0,0],[1,0]],'mean_rgb_error':1,'mean_rgb_error_limit':3,'within_one_pixel':True}
        self.assertEqual(classify(good)[0],'within-one-pixel')
        bad={**good,'equally_good_offsets':[[0,0],[2,0]],'within_one_pixel':False};self.assertEqual(classify(bad)[0],'unverified')

    def test_actual_after_base_head_occlusion_keeps_original_point_and_roi(self):
        overlay=Image.new('RGBA',(64,67));overlay.putpixel((33,35),(80,30,10,128));ref=self.image('parts/hair.png',overlay);self.head['clips'][0]['frames'][0].update(layers=[{'id':'hair','texture':ref}],layer_order=['base','hair']);self.head_ref=self.doc('recipes/head/r001.json',self.head);self.output=Image.alpha_composite(self.output,overlay);self.output.save(self.output_path);self.savemanifest();self.native();tool=self.tool();item=tool.static_points()[0];self.assertEqual(item['source_status'],'occluded-by-selected-head-support');self.assertEqual(item['canonical_px'],[30,30]);self.assertEqual(item['fixed_source_roi_px'],[10,10,51,51]);self.assertEqual(tool.native_receipt(self.evidence)['measurements'][0]['status'],'unverified')

    def test_unobservable_source_point_never_fabricates_a_coordinate(self):
        self.pointrow['points']=[{'id':'hidden','material':'occluded finger','visible':False,'hidden_mechanical_contact_observable':False}];self.savepoints();self.native();r=self.tool().native_receipt(self.evidence);self.assertEqual(r['measurements'][0]['status'],'unverified');self.assertNotIn('canonical_px',r['measurements'][0])

    def test_less_than_four_near_opaque_samples_stays_unverified(self):
        self.raw.putalpha(249);self.ref=self.image('sources/canonical.png',self.raw);self.pointrow['canonical_reference']=self.ref;self.pointrow['full_original_or_legacy_derived_source']=self.ref;self.pointrow['points'][0]['RGBA'][-1]=249;self.poses=self.doc('templates/poses.json',{'variants':{'B':{'canvas_px':[60,60],'root_anchor_px':[30,55],'display_scale':.25,'frames':[{'pose_id':'hoe_south_key_2',**self.ref}]}}});self.pointrow['canonical_pose_document']=self.poses;self.base['clips'][0]['poses']=self.poses;self.base_ref=self.doc('recipes/body/r001.json',self.base);self.head['base_recipe']=self.base_ref;self.head_ref=self.doc('recipes/head/r001.json',self.head);self.output=Image.new('RGBA',(64,67));self.output.paste(self.raw,(3,5));self.output.save(self.output_path);self.savepoints();self.savemanifest();self.native();r=self.tool().native_receipt(self.evidence);self.assertEqual(r['measurements'][0]['status'],'unverified');self.assertIn('opaque',r['measurements'][0]['reason'])

    def test_world_continuous_viewport_uses_zero_origin_not_actor_crop(self):
        self.native(transform=[2,0,0,2,6,6]);cp=self.evidence/'input-contract.json';c=json.loads(cp.read_text());c['observer']='poses';c['contract_digest']=hashlib.sha256(stable({k:v for k,v in c.items() if k!='contract_digest'})).hexdigest();cp.write_text(json.dumps(c));rp=self.evidence/'report.json';r=json.loads(rp.read_text());r.update(kind='coastal-registered-native-observation-v1',input_contract_sha256=sha(cp));r['samples'][0].update(mode='world-continuous',actor_capture_origin_px=[999,999]);rp.write_text(json.dumps(r));row=self.tool().native_receipt(self.evidence)['measurements'][0];self.assertEqual(row['actual_capture_origin_px'],[0,0]);self.assertEqual(row['status'],'within-one-pixel')

    def test_boolean_transform_is_unverified_as_invalid_measurement_metadata(self):
        self.native(transform=[True,0,0,2,10,12]);row=self.tool().native_receipt(self.evidence)['measurements'][0];self.assertEqual(row['status'],'unverified');self.assertIn('transform',row['reason'])

    def test_cli_source_check_is_bounded_and_refuses_overwrite(self):
        m=self.module();p=self.repo/'receipt.json';args=['--repo',str(self.repo),'--manifest',str(self.mp),'--manifest-sha256',sha(self.mp),'--artifact',self.manifest['artifact_digest'],'--points',str(self.points),'--points-sha256',sha(self.points),'--output',str(p)];self.assertEqual(m.main(args),0);r=json.loads(p.read_text());self.assertFalse(r['native_verified']);self.assertFalse(r['physical_contact_acceptance']);self.assertEqual(m.main(args),2)

    def test_static_cli_receipt_keeps_manifest_binding_and_dependency_hashes(self):
        m=self.module();p=self.repo/'bound-static.json';args=['--repo',str(self.repo),'--manifest',str(self.mp),'--manifest-sha256',sha(self.mp),'--artifact',self.manifest['artifact_digest'],'--points',str(self.points),'--points-sha256',sha(self.points),'--output',str(p)];self.assertEqual(m.main(args),0);r=json.loads(p.read_text());self.assertIn('manifest',r);self.assertEqual(r['manifest']['sha256'],sha(self.mp));self.assertIn(str(self.mp),r['bound_files'])

    def test_fixed_roi_crossing_source_canvas_is_not_clamped_to_fit(self):
        self.pointrow['points'][0].update(canonical_px=[5,5],source_px=[5,5],RGBA=list(self.raw.getpixel((5,5))));self.savepoints();self.native();r=self.tool().native_receipt(self.evidence);row=r['measurements'][0];self.assertEqual(row['fixed_source_roi_px'],[-15,-15,26,26]);self.assertEqual(row['status'],'unverified');self.assertIn('never shrink',row['reason'])

    def test_native_snapshot_for_another_artifact_is_rejected(self):
        self.native();cp=self.evidence/'input-contract.json';c=json.loads(cp.read_text());c['artifact_digest']='0'*64;c['contract_digest']=hashlib.sha256(stable({k:v for k,v in c.items() if k!='contract_digest'})).hexdigest();cp.write_text(json.dumps(c));rp=self.evidence/'report.json';r=json.loads(rp.read_text());r['input_contract_sha256']=sha(cp);rp.write_text(json.dumps(r))
        with self.assertRaisesRegex(ValueError,'artifact'):self.tool().native_receipt(self.evidence)

    def test_source_target_cannot_claim_unobserved_ground_proof(self):
        self.pointrow['target']['source_ground_contact_proven']=True;self.savepoints()
        with self.assertRaisesRegex(ValueError,'ground|target'):self.tool().static_points()

    def test_shoes_flag_without_native_samples_is_not_silently_ignored(self):
        m=self.module();p=self.repo/'no-native-shoes.json';args=['--repo',str(self.repo),'--manifest',str(self.mp),'--manifest-sha256',sha(self.mp),'--artifact',self.manifest['artifact_digest'],'--points',str(self.points),'--points-sha256',sha(self.points),'--shoes','--output',str(p)];self.assertEqual(m.main(args),2);self.assertFalse(p.exists())
