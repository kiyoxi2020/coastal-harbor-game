"""Behavioral coverage for fixed head composition over a strict base recipe."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import io
import unittest

from PIL import Image

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import test_build_contract as base_fixture
import build
from build_contract import validate


class CompositionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = base_fixture.ConstructionTests(methodName='test_three_frame_action_and_matching_idle')
        self.fixture.setUp()
        self.repo = self.fixture.repo
        self.lib = self.fixture.lib
        self.path = self.lib/'recipes/head-bare/r001.json'
        self.recipe = {
            'kind': 'coastal-character-construction-v1', 'schema_version': 2,
            'resource_root': 'art/characters', 'character_model_id': 'unified-composable-character-v1',
            'recipe_id': 'head-bare', 'revision': 'r001',
            'base_recipe': {'file': 'recipes/test/r001.json', 'sha256': hashlib.sha256(self.fixture.path.read_bytes()).hexdigest()},
            'head_state': 'bare', 'slots': {},
            'clips': [{'action_id': c['action_id'], 'direction': c['direction'],
                       'frames': [{'pose_id': f['pose_id'], 'operation': 'none', 'layers': [], 'layer_order': ['base']} for f in c['frames']]}
                      for c in self.fixture.recipe['clips']], 'authoring_inputs': []}
        self.save()

    def tearDown(self):
        self.fixture.tearDown()

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.recipe))

    def test_nonobject_recipe_and_layers_are_rejected_cleanly(self):
        original=copy.deepcopy(self.recipe)
        for kind in ['root','layer']:
            with self.subTest(kind=kind):
                self.recipe=[] if kind=='root' else copy.deepcopy(original)
                if kind=='layer':self.recipe['clips'][0]['frames'][0]['layers']=[7]
                self.save()
                with self.assertRaisesRegex(ValueError,'fields|layer'):
                    validate(self.repo,self.path)

    def test_schema2_bare_renders_validated_base_in_memory(self):
        self.save()
        try:
            derived = validate(self.repo, self.path)
        except ValueError as exc:
            self.fail("schema2 fixed-head recipe must be accepted: " + str(exc))
        base = validate(self.repo, self.fixture.path)
        self.assertEqual([(n, im.tobytes()) for n, im in build.render(derived)],
                         [(n, im.tobytes()) for n, im in build.render(base)])
        self.assertIn('recipes/test/r001.json', derived.dependencies)
        self.assertIn('recipes/head-bare/r001.json', derived.dependencies)


class ProceduralCompositionTests(unittest.TestCase):
    def test_procedural_bare_composition_keeps_all_base_rgba(self):
        from composition_fixture import CompositionFixture
        fixture = CompositionFixture()
        self.addCleanup(fixture.cleanup)
        base = validate(fixture.repo, fixture.base.path)
        bare = validate(fixture.repo, fixture.recipes['bare'])
        self.assertEqual([(n, image.tobytes()) for n, image in build.render(base)],
                         [(n, image.tobytes()) for n, image in build.render(bare)])

    def test_hair_replaces_rgba_and_stack_preserves_transparent_base_rgb(self):
        from composition_contract import compose
        base=Image.new('RGBA',(2,1),(10,20,30,255));base.putpixel((1,0),(41,42,43,0))
        hair=Image.new('RGBA',(2,1));hair.putpixel((0,0),(220,11,33,128))
        layer={'id':'hair','texture':'hair'}
        frame={'operation':'binary-rgba-replace','layers':[layer],'layer_order':['base','hair']}
        output=compose(base,frame,lambda _:hair)
        self.assertEqual(output.getpixel((0,0)),(220,11,33,128))
        self.assertEqual(output.getpixel((1,0)),(41,42,43,0))
        frame={'operation':'supported-alpha-stack','layers':[{'id':'near_hat','texture':'hat'}], 'layer_order':['base','near_hat']}
        output=compose(base,frame,lambda _:hair)
        self.assertEqual(output.getpixel((0,0)),(115,15,32,255))
        self.assertEqual(output.getpixel((1,0)),(41,42,43,0))

    def test_all_head_states_have_exact_procedural_pixel_oracles(self):
        from composition_fixture import CompositionFixture
        fixture = CompositionFixture()
        self.addCleanup(fixture.cleanup)
        # Oracles are explicit arithmetic, independent of the compositor.
        # Base top (200, 0, 0, 128) alpha-over opaque body (10, 20, 30).
        base = (105, 10, 15, 255)
        for state, path in fixture.recipes.items():
            rendered = list(build.render(validate(fixture.repo, path)))
            self.assertEqual(len(rendered), 4)
            for i, (_, image) in enumerate(rendered):
                with self.subTest(state=state, frame=i):
                    index = i if i < 3 else 0
                    hair = (190, 40+index, 60, 128)
                    self.assertEqual(image.getpixel((1, 1)), base)
                    self.assertEqual(image.getpixel((0, 1)), base)
                    if state == 'hair':
                        self.assertEqual(image.getpixel((0, 0)), hair)
                    elif state == 'hair_hat':
                        expected = tuple((hair[c]*128+base[c]*127+127)//255 for c in range(3))+(255,)
                        self.assertEqual(image.getpixel((0, 0)), expected)
                    else:
                        self.assertEqual(image.getpixel((0, 0)), base)
                    if state in {'hat', 'hair_hat'}:
                        near = (60,180,70+index,210)
                        expected = tuple((near[c]*210+base[c]*45+127)//255 for c in range(3))+(255,)
                        self.assertEqual(image.getpixel((1, 0)), expected)
                    else:
                        self.assertEqual(image.getpixel((1, 0)), base)


class RejectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from composition_fixture import CompositionFixture
        cls.fixture = CompositionFixture()
        cls.repo, cls.lib = cls.fixture.repo, cls.fixture.lib
        for path in cls.fixture.recipes.values():
            validate(cls.repo, path)

    @classmethod
    def tearDownClass(cls):
        cls.fixture.cleanup()

    def setUp(self):
        self.changed = {}
        self.path = self.lib/'recipes/headwear-hoe-west-hair-hat/r001.json'
        self.recipe = json.loads(self.path.read_text())

    def tearDown(self):
        for path, data in self.changed.items():
            if data is None:
                path.unlink()
            else:
                path.write_bytes(data)

    def write(self, path, data):
        path = Path(path)
        self.changed.setdefault(path, path.read_bytes() if path.exists() else None)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data if isinstance(data, bytes) else json.dumps(data).encode())

    def rejected(self, change, message):
        change(self.recipe)
        self.write(self.path, self.recipe)
        with self.assertRaisesRegex(ValueError, message):
            validate(self.repo, self.path)

    def test_registered_direct_hair_cannot_rehash_changed_pixels(self):
        self.path=self.lib/'recipes/headwear-hoe-west-hair/r001.json'
        self.recipe=json.loads(self.path.read_text())
        ref=self.recipe['clips'][0]['frames'][0]['layers'][0]['texture']
        path=self.lib/ref['file']
        with Image.open(path) as original:
            changed=original.convert('RGBA');changed.putpixel((0,0),(17,18,19,0))
            data=io.BytesIO();changed.save(data,format='PNG')
        self.write(path,data.getvalue());newsha=hashlib.sha256(path.read_bytes()).hexdigest();name=ref['file']
        def rebind(o):
            if isinstance(o,dict):
                if o.get('file')==name:o['sha256']=newsha
                for v in o.values():rebind(v)
            elif isinstance(o,list):
                for v in o:rebind(v)
        self.rejected(rebind,'Registered input SHA')

    def test_registered_direct_hair_cannot_rehash_changed_ownership(self):
        self.path=self.lib/'recipes/headwear-hoe-west-hair/r001.json'
        self.recipe=json.loads(self.path.read_text())
        ref=self.recipe['clips'][0]['frames'][0]['layers'][0]['provenance']['source_views'][0]['source_ownership']
        path=self.lib/ref['file']
        with Image.open(path) as original:
            changed=original.copy();value=original.getpixel((0,0));changed.putpixel((0,0),(0 if value else 255) if original.mode=='L' else (0,0,0,0))
            data=io.BytesIO();changed.save(data,format='PNG')
        self.write(path,data.getvalue());newsha=hashlib.sha256(path.read_bytes()).hexdigest();name=ref['file']
        def rebind(o):
            if isinstance(o,dict):
                if o.get('file')==name:o['sha256']=newsha
                for v in o.values():rebind(v)
            elif isinstance(o,list):
                for v in o:rebind(v)
        self.rejected(rebind,'Registered input SHA')

    def test_registration_cannot_remove_entire_inputs_map(self):
        self.path=self.lib/'recipes/headwear-hoe-west-hair/r001.json'
        self.recipe=json.loads(self.path.read_text())
        layer=self.recipe['clips'][0]['frames'][0]['layers'][0]
        docref=copy.deepcopy(layer['registration']['document']);path=self.lib/docref['file'];doc=json.loads(path.read_text());del doc['inputs']
        self.write(path,doc);newsha=hashlib.sha256(path.read_bytes()).hexdigest()
        def rebind(o):
            if isinstance(o,dict):
                if o.get('file')==docref['file']:o['sha256']=newsha
                for value in o.values():rebind(value)
            elif isinstance(o,list):
                for value in o:rebind(value)
        self.rejected(rebind,'registered inputs')

    def test_missing_registered_input_without_original_manifest_is_rejected(self):
        self.path=self.lib/'recipes/headwear-hoe-west-hair/r001.json'
        self.recipe=json.loads(self.path.read_text())
        layer=self.recipe['clips'][0]['frames'][0]['layers'][0]
        source=layer['provenance']['source_views'][0]['source']['file']
        docref=copy.deepcopy(layer['registration']['document']);path=self.lib/docref['file'];doc=json.loads(path.read_text());del doc['inputs'][source]
        self.write(path,doc);newsha=hashlib.sha256(path.read_bytes()).hexdigest()
        def rebind(o):
            if isinstance(o,dict):
                if o.get('file')==docref['file']:o['sha256']=newsha
                for v in o.values():rebind(v)
            elif isinstance(o,list):
                for v in o:rebind(v)
        self.rejected(rebind,'Registered input missing')

    def test_original_manifest_must_itself_be_a_registered_input(self):
        layer=self.recipe['clips'][0]['frames'][2]['layers'][1]
        extraction=layer['provenance']['source_views'][1]['registration']['extraction']['file']
        docref=copy.deepcopy(layer['registration']['document']);path=self.lib/docref['file'];doc=json.loads(path.read_text());del doc['inputs'][extraction]
        self.write(path,doc);newsha=hashlib.sha256(path.read_bytes()).hexdigest()
        def rebind(o):
            if isinstance(o,dict):
                if o.get('file')==docref['file']:o['sha256']=newsha
                for value in o.values():rebind(value)
            elif isinstance(o,list):
                for value in o:rebind(value)
        self.rejected(rebind,'Registered input missing')

    def test_self_consistent_under_hat_claim_must_match_selected_hat(self):
        docref=copy.deepcopy(self.recipe['clips'][0]['frames'][0]['layers'][1]['registration']['document'])
        path=self.lib/docref['file'];sample=json.loads(path.read_text())
        sample['frames'][0]['parts']['hair_under_hat']['compatible_hat_manifest_sha256']='0'*64
        self.write(path,sample);newsha=hashlib.sha256(path.read_bytes()).hexdigest()
        adaptation=self.lib/'parts/hair/hair-chestnut-short-v1/adult-standard-v1/review-motion-v1/r001/views.json'
        data=json.loads(adaptation.read_text())
        for view in data['views']:
            if view['recipe_id']=='headwear-hoe-west' and view['pose_id']=='hoe_west_key_0' and view['part_id']=='hair_under_hat':
                view['view']['compatible_hat_manifest_sha256']='0'*64
        self.write(adaptation,data)
        def rebind(o):
            if isinstance(o,dict):
                if o.get('file')==docref['file']:o['sha256']=newsha
                for value in o.values():rebind(value)
            elif isinstance(o,list):
                for value in o:rebind(value)
        self.rejected(rebind,'compatibility')

    def test_near_and_far_must_share_exact_hat_registration(self):
        near=self.recipe['clips'][0]['frames'][0]['layers'][-1]
        reg=near['registration'];old_extraction=copy.deepcopy(reg['extraction']);old_document=copy.deepcopy(reg['document'])
        new_extraction=str(Path(old_extraction['file']).parent/'second-manifest.json')
        self.write(self.lib/new_extraction,(self.lib/old_extraction['file']).read_bytes())
        new_ext_ref={'file':new_extraction,'sha256':old_extraction['sha256']}
        source=near['provenance']['source_views'][0];bundle_ref=copy.deepcopy(source['source_bundle']);bundle_path=self.lib/bundle_ref['file'];bundle=json.loads(bundle_path.read_text())
        alias=next(x for x in bundle['assets'] if x.get('new_path')=='art/characters/'+old_extraction['file'])
        new_alias=copy.deepcopy(alias);new_alias['old_path']=str(Path(alias['old_path']).parent/'second-manifest.json');new_alias['new_path']='art/characters/'+new_extraction
        bundle['assets'].append(new_alias);self.write(bundle_path,bundle);new_bundle_sha=hashlib.sha256(bundle_path.read_bytes()).hexdigest()
        sample=json.loads((self.lib/old_document['file']).read_text());sample['frames'][0]['parts']['hat']['extraction_manifest']=new_extraction;sample['inputs'][new_extraction]=old_extraction['sha256']
        new_document='builds/second-hat-registration/sample.json';self.write(self.lib/new_document,sample)
        new_doc_ref={'file':new_document,'sha256':hashlib.sha256((self.lib/new_document).read_bytes()).hexdigest()}
        near['registration']['document']=new_doc_ref;near['registration']['extraction']=new_ext_ref
        near['provenance']['source_views'][0]['registration']=copy.deepcopy(near['registration'])
        adaptation=self.lib/'parts/hat/hat-straw-navy-band-v1/adult-standard-v1/review-motion-v1/r001/views.json';data=json.loads(adaptation.read_text())
        original=next(v for v in data['views'] if v['recipe_id']=='headwear-hoe-west' and v['pose_id']=='hoe_west_key_0')
        duplicate=copy.deepcopy(original);duplicate['view']['extraction_manifest']=new_extraction;data['views'].append(duplicate);self.write(adaptation,data)
        def rebind(o):
            if isinstance(o,dict):
                if o.get('file')==bundle_ref['file']:o['sha256']=new_bundle_sha
                for value in o.values():rebind(value)
            elif isinstance(o,list):
                for value in o:rebind(value)
        self.rejected(rebind,'same hat')

    def test_near_far_roles_cannot_be_exchanged(self):
        def change(d):
            layers = d['clips'][0]['frames'][0]['layers']
            layers[0]['texture'], layers[-1]['texture'] = layers[-1]['texture'], layers[0]['texture']
            layers[0]['registration'], layers[-1]['registration'] = layers[-1]['registration'], layers[0]['registration']
            layers[0]['provenance'], layers[-1]['provenance'] = layers[-1]['provenance'], layers[0]['provenance']
        self.rejected(change, 'role')

    def test_all_contract_object_levels_reject_unknown_fields(self):
        targets = [lambda d:d, lambda d:d['base_recipe'], lambda d:d['clips'][0],
                   lambda d:d['clips'][0]['frames'][0], lambda d:d['clips'][0]['frames'][0]['layers'][0],
                   lambda d:d['clips'][0]['frames'][0]['layers'][0]['registration'],
                   lambda d:d['clips'][0]['frames'][0]['layers'][0]['provenance'],
                   lambda d:d['clips'][0]['frames'][0]['layers'][0]['provenance']['source_views'][0]]
        original = copy.deepcopy(self.recipe)
        for target in targets:
            with self.subTest(target=target):
                self.recipe = copy.deepcopy(original)
                self.rejected(lambda d:target(d).update(local_scale=[1,1]), 'fields')

    def test_wrong_pose_timing_capability_and_head_operation_rejected(self):
        changes = [lambda d:d['clips'][0].update(direction='east'),
                   lambda d:d['clips'][0]['frames'][0].update(pose_id='hoe_west_key_3'),
                   lambda d:d['clips'][0]['frames'][0].update(duration_ms=99),
                   lambda d:d['clips'][0]['frames'][0].update(operation='alpha-over'),
                   lambda d:d['clips'][0]['frames'].pop(),
                   lambda d:d.update(head_state='custom')]
        original = copy.deepcopy(self.recipe)
        for change in changes:
            with self.subTest(change=change):
                self.recipe = copy.deepcopy(original)
                self.rejected(change, 'mismatch|pose|fields|state|capability')

    def test_binary_selection_rejects_missing_and_unrelated_ownership(self):
        def change(d):
            v=d['clips'][0]['frames'][2]['layers'][1]['provenance']['source_views'][0]
            v['selection']=None
        self.rejected(change, 'selection')

    def test_selection_requires_binary_target_canvas_mask(self):
        for mode,canvas in [('gray',(2,2)),('small',(1,1))]:
            with self.subTest(mode=mode):
                self.recipe=json.loads(self.path.read_text())
                ref=self.recipe['clips'][0]['frames'][2]['layers'][1]['provenance']['source_views'][0]['selection']
                path=self.lib/ref['file']
                data=io.BytesIO();Image.new('L',canvas,128 if mode=='gray' else 255).save(data,format='PNG')
                self.write(path,data.getvalue())
                ref['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
                # Reauthor the cloned registration input map as well so this
                # test reaches binary/canvas validation, rather than the
                # stronger frozen-input SHA check tested separately.
                docref=copy.deepcopy(self.recipe['clips'][0]['frames'][2]['layers'][1]['registration']['document'])
                docpath=self.lib/docref['file'];doc=json.loads(docpath.read_text());doc['inputs'][ref['file']]=ref['sha256']
                self.write(docpath,doc);newsha=hashlib.sha256(docpath.read_bytes()).hexdigest()
                def rebind(o):
                    if isinstance(o,dict):
                        if o.get('file')==docref['file']:o['sha256']=newsha
                        for value in o.values():rebind(value)
                    elif isinstance(o,list):
                        for value in o:rebind(value)
                rebind(self.recipe)
                self.write(self.path,self.recipe)
                with self.assertRaisesRegex(ValueError,'binary|canvas'):
                    validate(self.repo,self.path)
                for changed,original in self.changed.items():changed.write_bytes(original)
                self.changed={}

    def test_exact_extraction_alias_cannot_be_replaced_by_basename(self):
        source=self.recipe['clips'][0]['frames'][2]['layers'][1]['provenance']['source_views'][1]
        ref=source['source_bundle'];path=self.lib/ref['file'];data=json.loads(path.read_text())
        for asset in data['assets']:
            if asset.get('new_path')=='art/characters/'+source['source']['file']:
                asset['old_path']='unrelated/directory/source-full-frame.png'
        self.write(path,data)
        ref['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        self.write(self.path,self.recipe)
        with self.assertRaisesRegex(ValueError,'exact extraction alias'):
            validate(self.repo,self.path)

    def test_idle_registration_action_must_match_bound_parent(self):
        idle=self.recipe['clips'][1]['frames'][0]
        source_ref=copy.deepcopy(idle['layers'][0]['registration']['document'])
        doc=json.loads((self.lib/source_ref['file']).read_text());doc['action_id']='run'
        path=self.lib/'builds/foreign-head-scope/sample.json';path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(doc))
        new_ref={'file':str(path.relative_to(self.lib)), 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        def rebind(o):
            if isinstance(o,dict):
                if o.get('file')==source_ref['file']:o.update(new_ref)
                else:
                    for value in o.values():rebind(value)
            elif isinstance(o,list):
                for value in o:rebind(value)
        rebind(idle)
        self.write(self.path,self.recipe)
        try:
            with self.assertRaisesRegex(ValueError,'parent action'):
                validate(self.repo,self.path)
        finally:
            path.unlink();path.parent.rmdir()

    def test_registered_multi_source_selection_must_be_disjoint(self):
        layer=self.recipe['clips'][0]['frames'][2]['layers'][1]
        first=layer['provenance']['source_views'][0]['selection']
        layer['provenance']['source_views'][1]['selection']=copy.deepcopy(first)
        ref=layer['registration']['document'];sample_path=self.lib/ref['file'];sample=json.loads(sample_path.read_text())
        sample['frames'][2]['parts']['hair_under_hat']['source_views'][1]['ownership']=first['file']
        self.write(sample_path,sample)
        newsha=hashlib.sha256(sample_path.read_bytes()).hexdigest()
        def rebind(o):
            if isinstance(o,dict):
                if o.get('file')==ref['file']:o['sha256']=newsha
                for value in o.values():rebind(value)
            elif isinstance(o,list):
                for value in o:rebind(value)
        rebind(self.recipe)
        adaptation=self.lib/'parts/hair/hair-chestnut-short-v1/adult-standard-v1/review-motion-v1/r001/views.json'
        data=json.loads(adaptation.read_text())
        for view in data['views']:
            if view['recipe_id']=='headwear-hoe-west' and view['pose_id']=='hoe_west_key_2' and view['part_id']=='hair_under_hat':
                view['view']['source_views'][1]['ownership']=first['file']
        self.write(adaptation,data);self.write(self.path,self.recipe)
        with self.assertRaisesRegex(ValueError,'Overlapping'):
            validate(self.repo,self.path)

    def test_nested_schema2_base_is_rejected(self):
        other=self.lib/'recipes/headwear-hoe-west-bare/r001.json'
        self.rejected(lambda d:d.update(base_recipe={'file':str(other.relative_to(self.lib)), 'sha256':hashlib.sha256(other.read_bytes()).hexdigest()}),'schema1')

    def test_unknown_schema_boolean_is_rejected(self):
        self.rejected(lambda d:d.update(schema_version=True),'fields|schema')

    def test_missing_multi_source_is_rejected(self):
        self.rejected(lambda d:d['clips'][0]['frames'][2]['layers'][1]['provenance']['source_views'].pop(), 'count')

    def test_actual_mask_change_invalidates_sha(self):
        ref=self.recipe['clips'][0]['frames'][2]['layers'][1]['provenance']['source_views'][0]['selection']
        path=self.lib/ref['file']
        self.write(path, path.read_bytes()+b'changed')
        with self.assertRaisesRegex(ValueError,'SHA'):
            validate(self.repo,self.path)

    def test_registered_source_must_match_source_and_bundle(self):
        def change(d):
            source=d['clips'][0]['frames'][0]['layers'][0]['provenance']['source_views'][0]
            other=d['clips'][0]['frames'][1]['layers'][0]['provenance']['source_views'][0]
            source['source']=other['source']; source['source_bundle']=other['source_bundle']
        self.rejected(change, 'provenance')

    def test_missing_registration_is_a_contract_error(self):
        self.rejected(lambda d:d['clips'][0]['frames'][0]['layers'][0].update(registration=None),'registration')

    def test_source_registration_must_match_frame_pose(self):
        def change(d):
            source=d['clips'][0]['frames'][0]['layers'][0]['provenance']['source_views'][0]
            source['registration']=d['clips'][0]['frames'][1]['layers'][0]['provenance']['source_views'][0]['registration']
        self.rejected(change, 'pose')

    def test_registration_document_parent_is_not_freeform(self):
        ref=self.recipe['clips'][0]['frames'][0]['layers'][0]['registration']['document']
        p=self.lib/ref['file'];doc=json.loads(p.read_text());doc['parent_sha256']='0'*64
        self.write(p,doc)
        newsha=hashlib.sha256(p.read_bytes()).hexdigest()
        def replace_refs(o):
            if isinstance(o,dict):
                if o.get('file')==ref['file']:o['sha256']=newsha
                for value in o.values():replace_refs(value)
            elif isinstance(o,list):
                for value in o:replace_refs(value)
        self.rejected(replace_refs,'parent SHA')

    def test_nested_or_self_base_rejected(self):
        self.rejected(lambda d:d.update(base_recipe={'file':str(self.path.relative_to(self.lib)),'sha256':hashlib.sha256(self.path.read_bytes()).hexdigest()}),'SHA|Self')

    def test_build_verify_boundaries_and_dependency_staleness(self):
        with tempfile.TemporaryDirectory(prefix='coastal-head-verify-',dir='/private/tmp') as tmp:
            out=Path(tmp)/'result'
            manifest=build.construct(self.repo,self.path,out)
            self.assertEqual(set(manifest),set('kind schema_version status release_eligible recipe artifact_digest inputs engine outputs'.split()))
            self.assertIn('composition_contract.py',manifest['engine']['code'])
            self.assertEqual(manifest['schema_version'],1)
            self.assertFalse(manifest['release_eligible'])
            build.verify(self.repo,out)
            ref=self.recipe['clips'][0]['frames'][2]['layers'][1]['provenance']['source_views'][0]['selection']
            path=self.lib/ref['file'];self.write(path,path.read_bytes()+b'changed')
            with self.assertRaisesRegex(ValueError,'SHA'):
                build.verify(self.repo,out)


if __name__ == '__main__':
    unittest.main()
