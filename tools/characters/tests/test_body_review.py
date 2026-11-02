"""Real pack + strict schema3 fixtures for body-only full action reviews."""
import copy
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from PIL import Image

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import build
import pack_sources
from build_contract import digest

ACTIONS = {'idle': 1, 'walk': 2, 'run': 3, 'hoe': 4, 'water': 2, 'harvest': 1}
DIRECTIONS = ['north', 'west', 'south', 'east']


def fixture(root, representations=None):
    lib = root/'art/characters'
    representations = representations or {}
    def write(name, value):
        p=lib/name; p.parent.mkdir(parents=True,exist_ok=True)
        if isinstance(value, Image.Image): value.save(p)
        else: p.write_text(json.dumps(value))
        return ref(name)
    def ref(name): return {'file':name,'sha256':digest(lib/name)}
    geometry={'canvas_px':[2,2],'root_anchor_px':[1,1],'display_scale':1.0}
    plan={'kind':'coastal-character-source-atlas-plan-v1','schema_version':1,
          'resource_root':'art/characters','source_id':'body','revision':'r001',
          'cell_px':[2,2],'root_px':[1,1],'rows':DIRECTIONS,'frames':[]}
    for ai,(action,count) in enumerate(ACTIONS.items()):
        for di,direction in enumerate(DIRECTIONS):
            for i in range(count):
                pose=f'{action}_{direction}_{i}'
                raw=write(f'sources/body/originals/{pose}.png',Image.new('RGBA',(2,2),(40+ai*20,40+di*30,30+i*30,255)))
                plan['frames'].append({'representation':representations.get(action,'body'),'action':action,'direction':direction,
                    'frame_index':i,'pose_id':pose,'duration_ms':60+i*10,
                    'source':{**raw,'size_px':[2,2],'box_px':[0,0,2,2]},
                    'source_root_px':[1,1],'scale':[1,1],'authoring_inputs':[]})
    write('sources/body/packing/r001.json',plan)
    packed=lib/'sources/body/derived/r001'
    pm=pack_sources.pack(root,lib/'sources/body/packing/r001.json',packed)
    layout=json.loads((packed/'layout.json').read_text())
    atlas_refs={}
    for action in ACTIONS:
        im=Image.open(packed/f"atlases/{representations.get(action,'body')}/{action}.png").copy()
        atlas_refs[action]=write(f'sources/review-body/prepared/body-{action}.png',im)
    bundle=write('sources/review-body/source.json',{'source_id':'review-body','assets':[
        {'new_path':'art/characters/'+r['file'],'new_sha256':r['sha256']} for r in atlas_refs.values()]})
    clips=[]; motion_actions={}
    for action,count in ACTIONS.items():
        action_path=f'templates/body/motions/motion/actions/{action}/r001/action.json'
        paths={d:f'templates/body/motions/motion/actions/{action}/r001/{d}/poses.json' for d in DIRECTIONS}
        ar=write(action_path,{'action_id':action,'revision':'r001','loop':action in ['idle','walk','run'],'directions':paths})
        motion_actions[action]=action_path
        for direction in DIRECTIONS:
            lc=next(c for c in layout['clips'] if c['action']==action and c['direction']==direction)
            frames=[];canonical=[]
            for row in lc['frames']:
                x,y,w,h=row['region_px'];pose=row['pose_id']
                im=Image.open(packed/row['atlas']).crop((x,y,x+w,y+h))
                texture=write(f'templates/body/motions/motion/body-views/r001/{pose}.png',im)
                canonical.append({'pose_id':pose,'duration_ms':row['duration_ms'],**texture})
                layer={'id':'body','slot':'body','pose_id':pose,'texture':texture,'source':atlas_refs[action],
                    'source_bundle':bundle,'ownership':None,'coverage':None,'occlusion':None,
                    'interface_scope':'same-pose-reference','placement_mode':'full_frame',
                    'offset_px':[0,0],'local_scale':[1,1]}
                frames.append({'pose_id':pose,'duration_ms':row['duration_ms'],'layers':[layer],
                    'layer_order':['body'],'registration':None,'composition':'ownership-replace'})
            pr=write(paths[direction],{'template_id':'body','action_id':action,'direction':direction,
                'variants':{'visible':{**geometry,'frames':canonical}}})
            clips.append({'action_id':action,'direction':direction,'action':ar,'poses':pr,'variant':'visible',**geometry,'frames':frames})
    motion=write('templates/body/motions/motion/motion-set.json',{'template_id':'body','motion_set_id':'motion','actions':motion_actions})
    template=write('templates/body/template.json',{'template_id':'body','active_revision':'r001','motion_set':motion['file']})
    pack_ref=ref('sources/body/derived/r001/manifest.json')
    authoring=[ref(n) for n in pm['inputs']]+[pack_ref]
    authoring += [ref('sources/body/derived/r001/'+r['file']) for r in pm['outputs']]
    recipe={'kind':'coastal-character-construction-v1','schema_version':3,'resource_root':'art/characters',
        'character_model_id':'unified-composable-character-v1','recipe_id':'body','revision':'r001',
        'template':template,'motion_set':motion,'slots':{'body':None},'adaptations':{},
        'required_capabilities':[{'action_id':c['action_id'],'direction':c['direction']} for c in clips],
        'clips':clips,'authoring_inputs':authoring}
    write('recipes/body/r001.json',recipe)
    output=lib/'builds/body-r001';build.construct(root,lib/'recipes/body/r001.json',output)
    suite={'kind':'coastal-body-character-review-v1','schema_version':1,'resource_root':'art/characters',
        'scope':'review-only','manifest':ref('builds/body-r001/manifest.json'),'packed_sources':[pack_ref],
        'runtime':{'schema_version':1,'movement':{'walk':{'base_world_speed':72},'run':{'base_world_speed':108}},
            'default_speed_factor':.75,'locomotion_transition':{'kind':'stable-idle-v1','duration_ms':100},
            'clips':{c['action_id']+'-'+c['direction']:{'playback_rate':1,'events':[]} for c in clips}}}
    path=lib/'reviews/body-actions/review.json';write('reviews/body-actions/review.json',suite)
    return {'root':root,'lib':lib,'suite':suite,'path':path,'recipe':recipe,'output':output,'write':write,'ref':ref,'packed':packed}


class BodyReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='coastal-body-review-',dir='/private/tmp')
        self.addCleanup(self.temp.cleanup)
        self.f=fixture(Path(self.temp.name))

    def module(self):
        self.assertTrue((TOOLS/'body_review.py').is_file(),'body review consumer missing')
        return importlib.import_module('body_review')

    def preflight(self):
        self.f['write']('reviews/body-actions/review.json',self.f['suite'])
        return self.module().preflight(self.f['root'],self.f['path'])

    def rebuild(self):
        self.f['write']('recipes/body/r001.json',self.f['recipe'])
        shutil.rmtree(self.f['output'])
        build.construct(self.f['root'],self.f['lib']/'recipes/body/r001.json',self.f['output'])
        self.f['suite']['manifest']=self.f['ref']('builds/body-r001/manifest.json')

    def test_real_full_body_package_keeps_variable_pose_counts(self):
        result=self.preflight()
        self.assertEqual(result['suite'],self.f['suite'])
        self.assertEqual(len(result['clips']),24)
        self.assertEqual(len(result['clips']['hoe','east']['frames']),4)
        self.assertEqual(len(result['clips']['run','east']['frames']),3)
        self.assertTrue(result['full_package'])

    def test_farming_visible_body_frames_preserve_actual_tool_representation(self):
        self.f=fixture(self.f['root']/'visible',{'hoe':'hoe-visible','water':'water-visible','harvest':'harvest-visible'})
        result=self.preflight()
        self.assertEqual(len(result['clips']),24)
        self.assertEqual(result['recipe']['slots'],{'body':None})

    def test_farming_representation_cannot_be_mislabelled_for_another_tool(self):
        self.f=fixture(self.f['root']/'wrong-tool',{'hoe':'water-visible'})
        with self.assertRaisesRegex(ValueError,'source|pose|atlas'):self.preflight()

    def test_suite_schema_scope_fields_and_runtime_fail_closed(self):
        original=copy.deepcopy(self.f['suite'])
        for defect in ['schema','scope','extra','runtime']:
            with self.subTest(defect=defect):
                self.f['suite']=copy.deepcopy(original)
                if defect=='schema':self.f['suite']['schema_version']=True
                if defect=='scope':self.f['suite']['scope']='production'
                if defect=='extra':self.f['suite']['prepared_sources']=[]
                if defect=='runtime':self.f['suite']['runtime']['clips']['walk-east']['playback_rate']=2
                with self.assertRaises(ValueError):self.preflight()

    def test_missing_duplicate_bad_hash_or_prepared_source_refused(self):
        good=copy.deepcopy(self.f['suite']['packed_sources'])
        bad=self.f['write']('sources/prepared/manifest.json',{'kind':'coastal-prepared-registered-source-v1'})
        for refs in [[],good*2,[{**good[0],'sha256':'0'*64}],[bad]]:
            with self.subTest(refs=refs):
                self.f['suite']['packed_sources']=refs
                with self.assertRaises(ValueError):self.preflight()

    def test_missing_packed_layout_direct_dependency_refused_after_strict_build(self):
        self.f['recipe']['authoring_inputs'][:]=[r for r in self.f['recipe']['authoring_inputs'] if not r['file'].endswith('layout.json')]
        self.rebuild()
        with self.assertRaisesRegex(ValueError,'closure|bound'):self.preflight()

    def test_wrong_source_action_refused_even_when_canonical_build_valid(self):
        frame=self.f['recipe']['clips'][0]['frames'][0]
        frame['layers'][0]['source']=self.f['ref']('sources/review-body/prepared/body-walk.png')
        self.rebuild()
        with self.assertRaisesRegex(ValueError,'source|atlas|pose'):self.preflight()

    def test_canonical_same_pixels_copy_is_outside_review_contract(self):
        frame=self.f['recipe']['clips'][0]['frames'][0];texture=frame['layers'][0]['texture']
        frame['layers'][0]['texture']=self.f['write']('templates/body/motions/motion/body-views/r001/copy.png',Image.open(self.f['lib']/texture['file']))
        self.rebuild()
        with self.assertRaisesRegex(ValueError,'canonical'):self.preflight()

    def test_rgb_build_output_is_refused_even_with_correct_pixels_and_sha(self):
        p=self.f['output']/'manifest.json';m=json.loads(p.read_text());o=m['outputs'][0]
        target=self.f['output']/o['file'];Image.open(target).convert('RGB').save(target)
        o['sha256']=digest(target);p.write_text(json.dumps(m));self.f['suite']['manifest']=self.f['ref']('builds/body-r001/manifest.json')
        build.verify(self.f['root'],self.f['output'])
        with self.assertRaisesRegex(ValueError,'RGBA'):self.preflight()

    def test_partial_capabilities_are_refused_after_strict_valid_rebuild(self):
        self.f['recipe']['clips'][:]=[c for c in self.f['recipe']['clips'] if c['action_id']!='run']
        self.f['recipe']['required_capabilities'][:]=[c for c in self.f['recipe']['required_capabilities'] if c['action_id']!='run']
        self.rebuild()
        with self.assertRaisesRegex(ValueError,'complete|coverage|capabilit'):self.preflight()

    def test_source_symlink_ancestor_refused(self):
        d=self.f['lib']/'sources/review-body/prepared';moved=d.with_name('moved');d.rename(moved);d.symlink_to(moved,target_is_directory=True)
        with self.assertRaises(ValueError):self.preflight()

    def test_snapshot_binds_body_and_transitive_observer_closure(self):
        module=self.module();root=self.f['root']
        for name in ['body_review.py','review.py','build.py','build_contract.py','composition_contract.py','pack_sources.py','all_actions_capture.py','all_actions_evidence.py','all_actions_native.py','construction_native.py','native_contract.py']:
            p=root/'tools/characters'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(TOOLS/name,p)
        for name,text in {'godot2d/project.godot':'config_version=5\n',
            'godot2d/tests/characters/capture_registered_actions_world.gd':'extends "res://tests/shared.gd"\n',
            'godot2d/tests/shared.gd':'extends SceneTree\n',
            'godot2d/dev/characters/character_motion_lane.tscn':'[gd_scene format=3]\n'}.items():
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
        evidence=root/'native-evidence'
        c=module.snapshot(root,self.f['path'],evidence)
        self.assertEqual(c['suite_kind'],'coastal-body-character-review-v1')
        self.assertEqual(c['plan']['head_state'],'body')
        self.assertEqual(len(c['plan']['clips']),24)
        self.assertEqual(len(c['plan']['transitions']),96)
        self.assertTrue(c['full_package'])
        self.assertIn('godot2d/tests/shared.gd',c['files'])
        self.assertIn('tools/characters/all_actions_evidence.py',c['files'])
        self.assertTrue(module.verify_inputs(root,evidence)['passed'])
        (root/'godot2d/tests/shared.gd').write_text('extends MainLoop\n')
        with self.assertRaisesRegex(ValueError,'changed'):module.verify_inputs(root,evidence)


if __name__=='__main__':unittest.main()
