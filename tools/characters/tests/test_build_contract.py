import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

class ConstructionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='coastal-build-', dir='/private/tmp')
        self.repo = Path(self.temp.name)
        self.lib = self.repo / 'art/characters'
        def fixed_names(value):
            # Full-package fixtures exercise the production identity gate with
            # synthetic pixels; they do not claim visual or native approval.
            if not getattr(self, 'fixed_profile', False): return value
            if isinstance(value, str):
                for old, new in [('templates/test/', 'templates/adult-standard-v1/'),
                                 ('/motions/motion/', '/motions/review-motion-v1/'),
                                 ('/test/motion/', '/adult-standard-v1/review-motion-v1/'),
                                 ('parts/top/top/', 'parts/top/top03/'),
                                 ('parts/hair/hair/', 'parts/hair/hair-chestnut-short-v1/'),
                                 ('parts/hat/hat/', 'parts/hat/hat-straw-navy-band-v1/')]:
                    value = value.replace(old, new)
            elif isinstance(value, dict):
                for key, item in list(value.items()):
                    if key == 'template_id' and item == 'test': value[key] = 'adult-standard-v1'
                    elif key == 'motion_set_id' and item == 'motion': value[key] = 'review-motion-v1'
                    elif key == 'design_id': value[key] = {'top': 'top03', 'hair': 'hair-chestnut-short-v1', 'hat': 'hat-straw-navy-band-v1'}.get(item, item)
                    else: value[key] = fixed_names(item)
            elif isinstance(value, list):
                for index, item in enumerate(value): value[index] = fixed_names(item)
            return value
        def write(path, data):
            path = fixed_names(path)
            data = fixed_names(data)
            p = self.lib / path
            p.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(data, dict):
                p.write_text(json.dumps(data))
            else:
                data.save(p)
            return {'file': path, 'sha256': sha(p)}
        self.write = write
        source = write('sources/test/originals/source.png', Image.new('RGBA', (2, 2), (10, 20, 30, 255)))
        bundle = write('sources/test/source.json', {'source_id':'test', 'assets':[{'new_path':'art/characters/'+source['file'], 'new_sha256':source['sha256']}]})
        texture = write('parts/top/top/test/motion/r001/view.png', Image.new('RGBA', (2, 2), (200, 0, 0, 128)))
        body = write('templates/test/motions/motion/body-views/body.png', Image.new('RGBA', (2, 2), (10, 20, 30, 255)))
        mask = write('parts/top/top/test/motion/r001/mask.png', Image.new('L', (2, 2), 255))
        definition = write('parts/top/top/design.json', {'design_id':'top', 'category':'top'})
        clips=[];actions={}
        for action, count in [('idle',1),('wave',3)]:
            frames=[]
            for index in range(count):
                pose=f'{action}_west_{index}'
                layers=[]
                for slot, ref in [('body',body),('top',texture)]:
                    layers.append({'id':slot, 'slot':slot, 'pose_id':pose, 'texture':ref, 'source':source, 'source_bundle':bundle, 'ownership':None if slot=='body' else mask, 'coverage':None if slot=='body' else mask, 'occlusion':None if slot=='body' else mask, 'interface_scope':'same-pose-reference' if slot=='body' else 'registered-component', 'placement_mode':'full_frame', 'offset_px':[0,0], 'local_scale':[1,1]})
                frames.append({'pose_id':pose,'duration_ms':100,'layers':layers,'layer_order':['body','top'],'registration':None,'composition':'alpha-over'})
            geo={'canvas_px':[2,2],'root_anchor_px':[1,1],'display_scale':1}
            poses=write(f'templates/test/motions/motion/actions/{action}/r001/west/poses.json', {'template_id':'test','action_id':action,'direction':'west','variants':{'A':dict(geo,frames=[{'pose_id':f['pose_id'],'duration_ms':100} for f in frames])}})
            act=write(f'templates/test/motions/motion/actions/{action}/r001/action.json',{'action_id':action,'revision':'r001','loop':True,'directions':{'west':poses['file']}})
            actions[action]=act['file']
            clips.append(dict(geo,action_id=action,direction='west',action=act,poses=poses,variant='A',frames=frames))
        motion=write('templates/test/motions/motion/motion-set.json',{'template_id':'test','motion_set_id':'motion','actions':actions})
        template=write('templates/test/template.json',{'template_id':'test','active_revision':'r001','motion_set':motion['file']})
        self.recipe={'kind':'coastal-character-construction-v1','schema_version':1,'resource_root':'art/characters','character_model_id':'unified-composable-character-v1','recipe_id':'test','revision':'r001','template':template,'motion_set':motion,'slots':{'body':None,'top':definition},'required_capabilities':[{'action_id':x,'direction':'west'} for x in ['idle','wave']],'clips':clips,'authoring_inputs':[source]}
        self.path=self.lib/'recipes/test/r001.json'
        self.save()

    def tearDown(self):
        self.temp.cleanup()

    def save(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.path.write_text(json.dumps(self.recipe))

    def validate(self):
        import build_contract
        self.save()
        return build_contract.validate(self.repo, self.path)

    def rejected(self, change, message):
        change(self.recipe)
        with self.assertRaisesRegex(ValueError, message):
            self.validate()


    def test_rejects_changed_authoring_input(self):
        ref=self.write('sources/test/originals/registration.json',{'offset':[0,0]})
        self.recipe['authoring_inputs'].append(ref)
        (self.lib/ref['file']).write_text('{}')
        with self.assertRaisesRegex(ValueError,'SHA'):
            self.validate()

    def test_part_definition_uses_category_and_stable_design_identity(self):
        self.recipe['slots']['top'] = self.write(
            'parts/top/top/design.json', {'design_id': 'top', 'category': 'top'})
        self.validate()

    def test_part_definition_rejects_wrong_category_directory(self):
        self.recipe['slots']['top'] = self.write(
            'parts/pants/top/design.json', {'design_id': 'top', 'category': 'top'})
        with self.assertRaisesRegex(ValueError, 'Part identity/path mismatch'):
            self.validate()

    def test_part_definition_rejects_wrong_design_directory(self):
        self.recipe['slots']['top'] = self.write(
            'parts/top/another/design.json', {'design_id': 'top', 'category': 'top'})
        with self.assertRaisesRegex(ValueError, 'Part identity/path mismatch'):
            self.validate()


    def test_whole_frame_registration_is_bound_not_part_transform(self):
        for clip in self.recipe['clips']:
            data=json.loads((self.lib/clip['poses']['file']).read_text())
            data['variants']['A']['canvas_px']=[4,4]
            for original in data['variants']['A']['frames']:
                original['whole_frame_translation_px']=[1,1]
                original['source_box_px']=[0,0,2,2]
            self.write(clip['poses']['file'], data)
            clip['poses']['sha256']=sha(self.lib/clip['poses']['file'])
            clip['canvas_px']=[4,4]
            records={'frames':[{'pose_id':f['pose_id'],'duration_ms':100,'source_box_px':[0,0,2,2],'whole_frame_translation_px':[1,1],'density_normalization':None} for f in clip['frames']]}
            ref=self.write('sources/test/originals/'+clip['action_id']+'-registration.json', records)
            for i, frame in enumerate(clip['frames']):
                frame['registration']={'document':ref,'record':'/frames/'+str(i)}
        import build
        out=self.repo/'coastal-registered'
        self.save();build.construct(self.repo,self.path,out);build.verify(self.repo,out)
        with Image.open(out/'frames/wave/west/wave_west_0.png') as im:
            self.assertEqual(im.size,(4,4));self.assertEqual(im.getpixel((0,0))[3],0);self.assertEqual(im.getpixel((1,1))[3],255)


    def test_ownership_replace_preserves_soft_alpha(self):
        for clip in self.recipe['clips']:
            for frame in clip['frames']:
                frame['composition']='ownership-replace'
        self.save()
        import build
        out=self.repo/'coastal-owned'
        build.construct(self.repo,self.path,out)
        with Image.open(out/'frames/idle/west/idle_west_0.png') as image:
            self.assertEqual(image.getpixel((0,0)),(200,0,0,128))
        build.verify(self.repo,out)


    def test_unrelated_resource_does_not_invalidate_build(self):
        import build
        out=self.repo/'coastal-output'
        build.construct(self.repo,self.path,out)
        self.write('sources/unrelated/originals/new.png',Image.new('RGBA',(2,2)))
        build.verify(self.repo,out)

    def test_output_paths_keep_action_direction_pose_boundaries(self):
        import build
        out=self.repo/'coastal-output'
        result=build.construct(self.repo,self.path,out)
        self.assertEqual(result['outputs'][0]['file'],'frames/idle/west/idle_west_0.png')

    def test_unknown_schema_rejected(self):
        self.rejected(lambda d:d.update(schema_version=2),'schema')

    def test_unknown_slot_rejected(self):
        self.rejected(lambda d:d['slots'].update(cape=None),'slot')

    def test_missing_source_rejected(self):
        self.rejected(lambda d:d['clips'][0]['frames'][0]['layers'][0]['source'].update(file='sources/missing.png'),'path')

    def test_missing_texture_rejected(self):
        path=self.lib/self.recipe['clips'][0]['frames'][0]['layers'][1]['texture']['file']
        path.unlink()
        with self.assertRaisesRegex(ValueError,'path'):
            self.validate()


    def test_symlink_library_parent_rejected(self):
        art=self.repo/'art';destination=self.repo/'actual-art';art.rename(destination);art.symlink_to(destination, target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'symlink'):
            self.validate()


    def test_ownership_must_be_an_actual_mask_image(self):
        ref=self.write('parts/top/top/test/motion/r001/not-mask.json',{'alpha':255})
        self.rejected(lambda d:d['clips'][0]['frames'][0]['layers'][1].update(ownership=ref),'mask')

    def test_source_bundle_must_be_canonical(self):
        bundle=json.loads((self.lib/'sources/test/source.json').read_text())
        ref=self.write('sources/test/other.json',bundle)
        self.rejected(lambda d:d['clips'][0]['frames'][0]['layers'][0].update(source_bundle=ref),'bundle')


    def test_source_must_decode_as_png_even_when_hashes_agree(self):
        layer=self.recipe['clips'][0]['frames'][0]['layers'][0]
        source=self.lib/layer['source']['file'];source.write_bytes(b'not a png')
        new_sha=sha(source)
        bundle_path=self.lib/layer['source_bundle']['file']
        bundle=json.loads(bundle_path.read_text());bundle['assets'][0]['new_sha256']=new_sha
        bundle_path.write_text(json.dumps(bundle))
        for clip in self.recipe['clips']:
            for frame in clip['frames']:
                for item in frame['layers']:
                    item['source']['sha256']=new_sha
                    item['source_bundle']['sha256']=sha(bundle_path)
        self.recipe['authoring_inputs'][0]['sha256']=new_sha
        with self.assertRaisesRegex(ValueError,'Source PNG'):
            self.validate()

    def test_three_frame_action_and_matching_idle(self):
        result=self.validate()
        self.assertEqual(len(result.recipe['clips'][1]['frames']),3)
        self.assertTrue(result.dependencies)

    def test_rejects_old_recipe_and_unknown_schema(self):
        self.rejected(lambda d:d.pop('kind'), 'fields')

    def test_rejects_unknown_field(self):
        self.rejected(lambda d:d.update(user_accepted=True), 'fields')

    def test_rejects_wrong_model(self):
        self.rejected(lambda d:d.update(character_model_id='another-model'), 'model')

    def test_rejects_missing_capability(self):
        self.rejected(lambda d:d['required_capabilities'].append({'action_id':'hoe','direction':'east'}), 'capabilit')

    def test_rejects_missing_idle(self):
        self.rejected(lambda d:(d['clips'].pop(0),d['required_capabilities'].pop(0)), 'idle')

    def test_rejects_missing_pose(self):
        self.rejected(lambda d:d['clips'][1]['frames'].pop(), 'pose')

    def test_rejects_wrong_duration(self):
        self.rejected(lambda d:d['clips'][1]['frames'][0].update(duration_ms=99), 'timing')

    def test_rejects_missing_mask(self):
        self.rejected(lambda d:d['clips'][1]['frames'][0]['layers'][1].update(coverage=None), 'mask')

    def test_rejects_resize(self):
        self.rejected(lambda d:d['clips'][1]['frames'][0]['layers'][1].update(local_scale=[.9,1]), 'registration')

    def test_rejects_wrong_layer_pose(self):
        self.rejected(lambda d:d['clips'][1]['frames'][0]['layers'][1].update(pose_id='idle_west_0'), 'pose')

    def test_rejects_duplicate_or_missing_layer(self):
        self.rejected(lambda d:d['clips'][1]['frames'][0].update(layer_order=['body','body']), 'order')

    def test_rejects_wrong_texture_dimensions(self):
        ref=self.write('parts/top/top/test/motion/r001/small.png',Image.new('RGBA',(1,1)))
        self.rejected(lambda d:d['clips'][1]['frames'][0]['layers'][1].update(texture=ref), 'canvas')

    def test_rejects_hash_change(self):
        p=self.lib/self.recipe['clips'][0]['frames'][0]['layers'][1]['texture']['file']
        p.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'SHA'):
            self.validate()

    def test_rejects_traversal_and_wrong_semantic_root(self):
        self.rejected(lambda d:d['template'].update(file='../outside.json'), 'path')
        self.recipe['template']['file']='sources/test/source.json'
        with self.assertRaisesRegex(ValueError,'namespace'):
            self.validate()

    def test_rejects_symlink(self):
        p=self.lib/'parts/top/top/test/motion/r001/link.png';p.symlink_to(self.lib/self.recipe['clips'][0]['frames'][0]['layers'][1]['texture']['file'])
        ref={'file':str(p.relative_to(self.lib)),'sha256':sha(p)}
        self.rejected(lambda d:d['clips'][0]['frames'][0]['layers'][1].update(texture=ref), 'symlink')

    def test_build_verify_stale_and_immutable(self):
        import build
        out=self.repo/'result'
        # Use a sanctioned /private/tmp/coastal-* output boundary.
        out=self.repo/'coastal-output'
        build.construct(self.repo,self.path,out)
        manifest=json.loads((out/'manifest.json').read_text())
        self.assertEqual(manifest['status'],'review-only')
        self.assertFalse(manifest['release_eligible'])
        build.verify(self.repo,out)
        with self.assertRaisesRegex(ValueError,'exists'):
            build.construct(self.repo,self.path,out)
        self.recipe['clips'][1]['frames'][0]['duration_ms']=99
        self.save()
        with self.assertRaisesRegex(ValueError,'SHA|timing|stale'):
            build.verify(self.repo,out)

    def test_rejects_tampered_output_even_with_updated_hash(self):
        import build
        out=self.repo/'coastal-output'
        build.construct(self.repo,self.path,out)
        p=out/'manifest.json';m=json.loads(p.read_text());entry=m['outputs'][0]
        image=out/entry['file'];Image.new('RGBA',(2,2),(0,0,0,0)).save(image)
        entry['sha256']=sha(image);p.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError,'pixel|digest'):
            build.verify(self.repo,out)

    def test_output_must_be_managed(self):
        import build
        with self.assertRaisesRegex(ValueError,'output'):
            build.construct(self.repo,self.path,self.repo/'godot2d/assets/characters/new')

if __name__=='__main__':unittest.main()
