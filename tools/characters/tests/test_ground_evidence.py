"""Independent target geometry only: synthetic raw data never proves soil impact."""
import copy
import importlib
import json
import math
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from PIL import Image
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
from build_contract import digest
import all_actions_capture as capture


def f64(value):return struct.pack('<d',value).hex()
def f32(value):return struct.unpack('<f',struct.pack('<f',value))[0]


class GroundEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import test_all_actions_capture as fixture
        cls.fixture=fixture.FullCaptureSnapshotTests();cls.fixture.setUp()
        cls.repo=cls.fixture.repo;cls.lib=cls.repo/'art/characters'
        cls.manifest_path=cls.lib/'builds/full-hair-hat-r001/manifest.json'
        cls.manifest=json.loads(cls.manifest_path.read_text());cls.output={r['file']:r for r in cls.manifest['outputs']}
        cls.base=cls.fixture.fixture.head.fixture.recipe
        files={
            'godot2d/dev/characters/character_headwear_trial.tscn':'[gd_scene load_steps=4 format=3]\n[ext_resource type="PackedScene" path="res://dev/characters/character_walk_trial.tscn" id="1"]\n[ext_resource type="Script" path="res://dev/characters/character_headwear_trial.gd" id="2"]\n[ext_resource type="PackedScene" path="res://scenes/world/harbor_exterior.tscn" id="3"]\n[node name="CharacterHeadwearTrial" instance=ExtResource("1")]\nscript=ExtResource("2")\n',
            'godot2d/dev/characters/character_walk_trial.tscn':'[gd_scene format=3]\n[node name="Walk" type="Node2D"]\n[node name="Pose" type="Sprite2D" parent="."]\nscale = Vector2(0.05927835, 0.05927835)\n[node name="WorldCamera" type="Camera2D" parent="."]\nzoom = Vector2(4, 4)\n',
            'godot2d/dev/characters/character_headwear_trial.gd':'extends Node2D\nvar full_density:Vector2\nfunc density(pose):\n full_density=pose.scale/(138.0/582.0)\n',
            'godot2d/scenes/world/harbor_exterior.tscn':'[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://scripts/farm_plot.gd" id="1"]\n[node name="HarborExterior" type="Node2D"]\n[node name="DepthSortedObjects" type="Node2D" parent="."]\n[node name="GardenA" type="Node2D" parent="DepthSortedObjects"]\nscript=ExtResource("1")\nposition = Vector2(84,224)\nregion_id = "garden_a"\n',
            'godot2d/scripts/farm_plot.gd':(Path(__file__).resolve().parents[3]/'godot2d/scripts/farm_plot.gd').read_text(),
        }
        for name,text in files.items():
            path=cls.repo/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
        cls.candidate_rel='godot2d/tests/characters/all_actions_ground_target_candidates.json';cls.data={'kind':'coastal-native-ground-target-candidates-v1','artifact_id':cls.manifest['artifact_digest'],'source_review_sha256':'5'*64,'target_selection_mode':'keyboard-forward-12','scope':'synthetic tool fixture only','cases':[]}
        for action in ['hoe','water']:
            for direction in ['south','west','east','north']:
                clip=next(c for c in cls.base['clips'] if c['action_id']==action and c['direction']==direction)
                variant=json.loads((cls.lib/clip['poses']['file']).read_text())['variants'][clip['variant']];frame=variant['frames'][1]
                point=[3,0] if direction=='north' else [2,2]
                with Image.open(cls.lib/frame['file']) as image:rgba=list(image.convert('RGBA').getpixel(tuple(point)))
                offset={'south':[8,8],'west':[-7,0],'east':[8,0],'north':[8,-8]}[direction]
                cls.data['cases'].append({'id':action+'-'+direction,'clip':action+'-'+direction,'pose_id':frame['pose_id'],'source_point_px':point,'canonical_point_px':point,'source_rgba':rgba,'source_image':'art/characters/'+frame['file'],'source_image_sha256':frame['sha256'],'standing_offset':offset,'cell_id':'garden_a:1:0','point_kind':'metal_working_edge' if action=='hoe' else 'splash_center','source_ground_contact_proven':False,'point_uncertainty_source_px':8})
        (cls.repo/cls.candidate_rel).write_text(json.dumps(cls.data))
        observer=cls.repo/'godot2d/tests/characters/capture_registered_spatial.gd';observer.write_text(observer.read_text()+'\nvar candidate_path="res://tests/characters/all_actions_ground_target_candidates.json"\n')
        cls.contract=capture.snapshot(cls.repo,cls.fixture.fixture.suite_path,cls.fixture.output,'spatial')
        cls.profiles=cls.contract['plan']['clips']
        cls.proof={'passed':True,'full_package':True,'actual_suite_path':str(cls.repo/cls.contract['suite']),'catalog_sha256':cls.contract['files'][cls.contract['suite']],'manifest_binding':{**cls.contract['manifest'],'recipe':cls.manifest['recipe'],'recipe_sha256':cls.manifest['inputs'][cls.manifest['recipe']],'artifact_digest':cls.manifest['artifact_digest']},'runtime':copy.deepcopy(cls.contract['runtime']),'producer_script':'res://tests/characters/capture_registered_spatial.gd','capture_scene':cls.contract['capture_scene']}

    @classmethod
    def tearDownClass(cls):cls.fixture.doCleanups()

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='coastal-ground-unit-',dir='/private/tmp');self.addCleanup(self.temp.cleanup);self.evidence=Path(self.temp.name)/'observation-ground';self.evidence.mkdir();(self.evidence/'input-contract.json').write_bytes((self.fixture.output/'input-contract.json').read_bytes())
        self.report={'kind':'coastal-native-ground-target-alignment-observation-v1','input_contract_sha256':digest(self.evidence/'input-contract.json'),'loaded_input_binding':copy.deepcopy(self.proof),'renderer':'synthetic-tool-fixture','candidate_file':'res://tests/characters/all_actions_ground_target_candidates.json','candidate_sha256':digest(self.repo/self.candidate_rel),'checks':[],'cases':[],'output_hashes':{}}
        frame_clock=100;center=[76,200]
        for n,candidate in enumerate(self.data['cases']):
            key=candidate['clip'];profile=self.profiles[key];action,direction=key.split('-');actor=[center[i]-candidate['standing_offset'][i] for i in range(2)];instance=n+10
            delta=min(profile['duration_ms'])/2000;duration=sum(profile['duration_ms']);rows=[];elapsed=0;selected=None
            while elapsed<duration-1e-7:
                frame_clock+=1;elapsed+=delta*1000;done=elapsed>=duration-1e-7;pose=profile['pose_ids'][0];left=elapsed
                if done:active='idle-'+direction;pose=self.profiles[active]['pose_ids'][0];clock=0
                else:
                    active=key;clock=elapsed
                    for pose,length in zip(profile['pose_ids'],profile['duration_ms']):
                        if left<length:break
                        left-=length
                entry=self.output[f'frames/{active.split("-")[0]}/{direction}/{pose}.png'];state={'action':active.split('-')[0],'direction':direction,'instance_id':instance+1000 if done else instance,'elapsed_ms':clock}
                row={'case':'ground-'+key,'physics_frame':frame_clock,'delta_f64':f64(delta),'position_f64':[f64(v) for v in actor],'state':state,'texture':{'clip':active,'pose_id':pose,'rgba_sha256':entry['rgba_sha256']},'colliders':[]};rows.append(row)
                if pose==candidate['pose_id'] and selected is None:selected=row
            self.assertIsNotNone(selected)
            scale=.25*profile['display_scale'];offset=[-v for v in profile['root_anchor_px']];local=[candidate['source_point_px'][i]+.5+offset[i] for i in range(2)]
            world=[f32(f32(scale*local[i])+actor[i]) for i in range(2)];screen=[f32(f32(scale*4*local[i])+500) for i in range(2)];name='ground-'+key+'.png'
            Image.new('RGBA',(280,300),(10,20,30,255)).save(self.evidence/name);self.report['output_hashes'][name]=digest(self.evidence/name)
            record={'clip':key,'mode':'native-ground-target-alignment','capture':name,'capture_origin_px':[360,255],'actor_capture_origin_px':[360,255],'actor_position_f64':[f64(v) for v in actor],'actor_position':actor[:],'world_state':copy.deepcopy(selected['state']),'world_texture':copy.deepcopy(selected['texture']),'world_elapsed_f64':f64(selected['state']['elapsed_ms']),'pose_position':[0,0],'pose_scale':[scale,scale],'sprite_offset':offset,'texture_size_px':profile['canvas_px'],'snap_2d_transforms_to_pixel':True,'render_source_to_screen':[scale*4,0,0,scale*4,500,500],'process_frame':selected['physics_frame']*2,'physics_frame':selected['physics_frame'],'ticks_usec':selected['physics_frame']*50000}
            case={'candidate_id':key,'capture_record':record,'physics_samples':rows,'actor_start_f64':[f64(v) for v in actor],'target_selection_mode':'keyboard-forward-12','forward_probe_cell_id':candidate['cell_id'],'target':{'cell_id':candidate['cell_id'],'node_path':'/root/CharacterHeadwearTrial/HarborExterior/DepthSortedObjects/GardenA','center_f64':[f64(v) for v in center],'cell_bounds_world':[68,192,16,16]},'distance_f64':f64(f32(math.dist(actor,center))),'ray_hit':False,'source_to_world_f64':[f64(v) for v in [scale,0,0,scale,*actor]],'point_world_f64':[f64(v) for v in world],'point_screen_f64':[f64(v) for v in screen],'point_cell_id':candidate['cell_id'],'source_ground_contact_proven':False}
            self.report['cases'].append(case)
            for suffix in ['started','legal_target','actual_pose_and_target','stationary','png_saved']:self.report['checks'].append({'name':key+'_'+suffix,'passed':True})
            frame_clock+=3
        self.save()

    def save(self):(self.evidence/'report.json').write_text(json.dumps(self.report))
    def verifier(self):
        self.assertTrue((Path(__file__).resolve().parents[1]/'ground_evidence.py').is_file(),'Independent ground geometry verifier missing')
        return importlib.import_module('ground_evidence')

    def test_eight_bound_cases_produce_geometry_only_receipt(self):
        r=self.verifier().validate(self.repo,self.evidence);self.assertEqual(r['aligned_cases'],8);self.assertFalse(r['source_ground_contact_proven']);self.assertFalse(r['physical_soil_impact_proven']);self.assertFalse(r['user_approval']);self.assertFalse(r['release_eligible'])

    def test_actual_loaded_authority_and_candidate_sha_are_required(self):
        for defect in ['missing-loaded','catalog','data-sha','source-soil']:
            old=copy.deepcopy(self.report)
            if defect=='missing-loaded':self.report.pop('loaded_input_binding')
            elif defect=='catalog':self.report['loaded_input_binding']['catalog_sha256']='0'*64
            elif defect=='data-sha':self.report['candidate_sha256']='0'*64
            else:self.report['cases'][0]['source_ground_contact_proven']=True
            self.save()
            with self.subTest(defect=defect),self.assertRaises(ValueError):self.verifier().validate(self.repo,self.evidence)
            self.report=old

    def test_duplicate_or_missing_case_is_rejected(self):
        for duplicate in [False,True]:
            old=copy.deepcopy(self.report)
            if duplicate:self.report['cases'][-1]=copy.deepcopy(self.report['cases'][0])
            else:self.report['cases'].pop()
            self.save()
            with self.assertRaises(ValueError):self.verifier().validate(self.repo,self.evidence)
            self.report=old

    def test_projection_gpu_and_point_screen_are_bound(self):
        for defect in ['world','matrix','screen','gpu','offset']:
            old=copy.deepcopy(self.report);case=self.report['cases'][0]
            if defect=='world':case['point_world_f64'][0]=f64(999)
            elif defect=='matrix':case['source_to_world_f64'][0]=f64(.5)
            elif defect=='screen':case['point_screen_f64'][0]=f64(999)
            elif defect=='gpu':case['capture_record']['world_texture']['rgba_sha256']='0'*64
            else:case['capture_record']['sprite_offset'][0]+=1
            self.save()
            with self.subTest(defect=defect),self.assertRaises(ValueError):self.verifier().validate(self.repo,self.evidence)
            self.report=old

    def test_plot_legal_range_ray_and_stationary_clock_cannot_be_claimed(self):
        for defect in ['bounds','center','ray','moving','wrong-instance','capture-tick','forward-cell']:
            old=copy.deepcopy(self.report);case=self.report['cases'][0]
            if defect=='bounds':case['target']['cell_bounds_world']=[0,0,16,16]
            elif defect=='center':case['target']['center_f64']=[f64(999),f64(999)]
            elif defect=='ray':case['ray_hit']=True
            elif defect=='moving':case['physics_samples'][1]['position_f64'][0]=f64(999)
            elif defect=='wrong-instance':case['capture_record']['world_state']['instance_id']=999
            elif defect=='capture-tick':case['capture_record']['physics_frame']+=1
            else:case['forward_probe_cell_id']='garden_a:2:0'
            self.save()
            with self.subTest(defect=defect),self.assertRaises(ValueError):self.verifier().validate(self.repo,self.evidence)
            self.report=old

    def test_changed_real_png_and_stale_material_source_are_rejected(self):
        path=self.evidence/self.report['cases'][0]['capture_record']['capture'];original=path.read_bytes();path.write_bytes(original+b'changed')
        with self.assertRaises(ValueError):self.verifier().validate(self.repo,self.evidence)
        path.write_bytes(original)
        source=self.repo/self.data['cases'][0]['source_image'];original=source.read_bytes();source.write_bytes(original+b'changed');self.addCleanup(source.write_bytes,original)
        with self.assertRaises(ValueError):self.verifier().validate(self.repo,self.evidence)

    def test_game_direction_ties_and_half_open_plot_bounds(self):
        v=self.verifier()
        self.assertEqual(v.facing([8,8]),'south')
        self.assertEqual(v.facing([-8,-8]),'north')
        self.assertTrue(v.inside([68,192],[68,192,16,16]))
        self.assertFalse(v.inside([84,200],[68,192,16,16]))
        self.assertFalse(v.inside([76,208],[68,192,16,16]))

    def test_actual_distance_and_unique_player_instances_are_required(self):
        for defect in ['distance','reused-instance']:
            old=copy.deepcopy(self.report)
            if defect=='distance':self.report['cases'][0]['distance_f64']=f64(25)
            else:
                first=self.report['cases'][0]['capture_record']['world_state']['instance_id'];second=self.report['cases'][1]
                second['capture_record']['world_state']['instance_id']=first
                for row in second['physics_samples']:
                    if row['state']['action']!='idle':row['state']['instance_id']=first
            self.save()
            with self.subTest(defect=defect),self.assertRaises(ValueError):self.verifier().validate(self.repo,self.evidence)
            self.report=old

    def test_cli_writes_fresh_bounded_geometry_receipt(self):
        import subprocess
        tool=Path(__file__).resolve().parents[1]/'ground_evidence.py';output=self.evidence/'target-alignment.json'
        command=[sys.executable,str(tool),'--repo',str(self.repo),'validate','--evidence',str(self.evidence),'--receipt',str(output)]
        result=subprocess.run(command,text=True,capture_output=True)
        self.assertIn('native-geometric-target-alignment-only',result.stdout)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse(json.loads(output.read_text())['physical_soil_impact_proven'])
        self.assertEqual(subprocess.run(command,text=True,capture_output=True).returncode,2)

    def test_source_material_hidden_by_final_head_cannot_be_admitted(self):
        v=self.verifier();data=copy.deepcopy(self.data)
        for row in data['cases']:
            if row['id']=='hoe-north':row['source_point_px']=[2,1];row['canonical_point_px']=[2,1]
        with self.assertRaises(ValueError):v.candidate_sources(self.repo,self.contract,data,self.profiles)

    def test_ground_completion_uses_exact_binary64_runtime_boundary(self):
        v=self.verifier();profile={'action_id':'hoe','direction':'south','pose_ids':['p0','p1','p2'],'duration_ms':[100,300,400],'rgba':{'p0':'a','p1':'b','p2':'c'}};profiles={'hoe-south':profile,'idle-south':{'rgba':{'idle':'i'}}};rows=[];elapsed=0;selected=None
        for tick in range(1,50):
            elapsed+=(1/60)*1000;done=elapsed>=800;pose='p0' if elapsed<100 else ('p1' if elapsed<400 else 'p2');state={'action':'idle' if done else 'hoe','direction':'south','instance_id':2 if done else 1,'elapsed_ms':0 if done else elapsed};row={'case':'ground-hoe-south','physics_frame':tick,'delta_f64':f64(1/60),'position_f64':[f64(0),f64(0)],'state':state,'texture':{'clip':'idle-south' if done else 'hoe-south','pose_id':'idle' if done else pose,'rgba_sha256':'i' if done else profile['rgba'][pose]}};rows.append(row)
            if pose=='p1' and selected is None:selected=row
        self.assertLess(rows[47]['state']['elapsed_ms'],800)
        self.assertEqual(rows[47]['state']['action'],'hoe')
        record={'physics_frame':selected['physics_frame'],'world_state':selected['state'],'world_texture':selected['texture'],'actor_position_f64':selected['position_f64'],'world_elapsed_f64':f64(selected['state']['elapsed_ms'])};case={'physics_samples':rows,'actor_start_f64':[f64(0),f64(0)],'capture_record':record}
        self.assertEqual(v.stationary_instance(case,{'id':'hoe-south','clip':'hoe-south'},profile,profiles,1,-1,set())[0],49)

    def test_actor_crop_allows_only_native_float_truncation_interval(self):
        case=self.report['cases'][0];row=case['capture_record'];row['render_source_to_screen'][4]=f32(500-2**-15)
        candidate=self.data['cases'][0];local_x=candidate['source_point_px'][0]+.5+row['sprite_offset'][0]
        case['point_screen_f64'][0]=f64(f32(row['render_source_to_screen'][0]*local_x+row['render_source_to_screen'][4]))
        self.save();self.assertEqual(self.verifier().validate(self.repo,self.evidence)['aligned_cases'],8)
        row['capture_origin_px'][0]+=2;row['actor_capture_origin_px'][0]+=2;self.save()
        with self.assertRaises(ValueError):self.verifier().validate(self.repo,self.evidence)
