"""Independent raw observation checks; synthetic samples prove the tool only."""
import copy
import importlib
import json
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def f64(value):return struct.pack('<d',value).hex()


def locomotion_case(scenario='replay-once'):
    key='walk-south';clip={'action_id':'walk','direction':'south','pose_ids':['w0','w1'],'duration_ms':[100,100]}
    profiles={'walk-south':dict(clip,rgba={'w0':'a','w1':'b'}),'idle-south':{'rgba':{'i0':'i'}}}
    case={'case':key+'/'+scenario,'clip':key,'scenario':scenario,'base_world_speed':72,
          'speed_factor':1 if scenario=='playback-rate' else .75,
          'physics_ticks_per_second':5 if scenario=='low-frame-rate' else 60,
          'max_fps':5 if scenario=='low-frame-rate' else 0,'pose_ids':['w0','w1'],'durations_ms':[100,100],
          'initial_position_f64':[f64(0),f64(0)],'initial_phase_f64':f64(0),
          'segments':2 if scenario=='replay-once' else 1,'journal':[],'physics_samples':[]}
    phase=distance=y=0;frame=0
    for segment in range(1,case['segments']+1):
        plan=[('move',True)]*17+[('idle',True)]*3
        if scenario=='focus-pause':plan=plan[:2]+[('move',False)]*4+plan[2:]
        for action,focused in plan:
            frame+=1;delta=.2 if scenario=='low-frame-rate' else .05
            moved=72*case['speed_factor']*delta if action=='move' and focused else 0
            distance+=moved;y+=moved;phase=(phase+moved/72*1000)%200
            pose='w0' if phase<100 else 'w1';texture={'clip':key,'pose_id':pose,'rgba_sha256':profiles[key]['rgba'][pose]}
            if action=='idle':texture={'clip':'idle-south','pose_id':'i0','rgba_sha256':'i'}
            case['physics_samples'].append({'case':case['case'],'segment':segment,'physics_frame':frame,
                'delta_f64':f64(delta),'focused':focused,'speed_factor_f64':f64(case['speed_factor']),
                'phase_f64':f64(phase),'step_distance_f64':f64(moved),'distance_f64':f64(distance),
                'position_f64':[f64(0),f64(y)],'state':{'action':'idle' if action=='idle' else 'walk','direction':'south'},
                'texture':texture,'slide_collisions':0})
    return case,profiles


class VerifierMixin:
    def verifier(self):
        self.assertTrue((Path(__file__).resolve().parents[1]/'all_actions_evidence.py').is_file(),
                        'Independent raw observation verifier is missing')
        return importlib.import_module('all_actions_evidence')


class LocomotionRawEvidenceTests(VerifierMixin,unittest.TestCase):
    def test_replay_recomputes_two_segments_and_preserves_actual_phase(self):
        case,profiles=locomotion_case()
        result=self.verifier().locomotion_timing_evidence(case,profiles,72,.75)
        self.assertEqual(result['segments'],2)
        self.assertGreaterEqual(min(result['cycles_per_segment']),2)

    def test_rejects_a_short_second_segment_despite_claimed_count(self):
        case,profiles=locomotion_case();case['physics_samples']=[r for r in case['physics_samples'] if r['segment']==1]+case['physics_samples'][20:22]
        with self.assertRaisesRegex(ValueError,'two.*cycles'):
            self.verifier().locomotion_timing_evidence(case,profiles,72,.75)

    def test_rejects_replay_clock_reset_without_teleport(self):
        case,profiles=locomotion_case();next(r for r in case['physics_samples'] if r['segment']==2)['phase_f64']=f64(37.5)
        with self.assertRaisesRegex(ValueError,'distance.*phase|phase.*distance'):
            self.verifier().locomotion_timing_evidence(case,profiles,72,.75)

    def test_actual_gpu_texture_and_public_speed_are_authoritative(self):
        for defect in ['texture','speed']:
            case,profiles=locomotion_case('playback-rate')
            if defect=='texture':case['physics_samples'][0]['texture']['rgba_sha256']='wrong'
            else:case['physics_samples'][0]['speed_factor_f64']=f64(2)
            with self.subTest(defect=defect),self.assertRaises(ValueError):
                self.verifier().locomotion_timing_evidence(case,profiles,72,.75)

    def test_low_fps_and_focus_use_actual_ticks(self):
        for scenario in ['low-frame-rate','focus-pause']:
            case,profiles=locomotion_case(scenario)
            result=self.verifier().locomotion_timing_evidence(case,profiles,72,.75)
            self.assertGreaterEqual(result['physics_samples'],19)
        case,profiles=locomotion_case('focus-pause');case['physics_samples']=[r for r in case['physics_samples'] if r['focused']]
        with self.assertRaises(ValueError):self.verifier().locomotion_timing_evidence(case,profiles,72,.75)

    def test_malformed_numbers_are_contract_errors(self):
        case,profiles=locomotion_case();case['physics_samples'][0]['delta_f64']=True
        with self.assertRaises(ValueError):self.verifier().locomotion_timing_evidence(case,profiles,72,.75)


class WorldRawEvidenceTests(VerifierMixin,unittest.TestCase):
    def verifier(self):
        module=super().verifier()
        self.assertTrue(callable(getattr(module,'world_evidence',None)), 'World raw recomputation is missing')
        return module

    def setUp(self):
        import tempfile
        import hashlib
        from PIL import Image
        self.temp=tempfile.TemporaryDirectory(prefix='coastal-evidence-world-',dir='/private/tmp');self.addCleanup(self.temp.cleanup);self.evidence=Path(self.temp.name)
        _,self.profiles=locomotion_case();self.contract={'capture_every_rendered_frame':True,'runtime':{'movement':{'walk':{'base_world_speed':72}}}}
        rows=[];draw=[];hashes={};phase=distance=0
        for i in range(60):
            moved=2.7;distance+=moved;phase=(phase+37.5)%200;pose='w0' if phase<100 else 'w1';texture={'clip':'walk-south','pose_id':pose,'rgba_sha256':self.profiles['walk-south']['rgba'][pose]};row={'clip':'walk-south','physics_frame':i+1,'delta_f64':f64(.05),'phase_f64':f64(phase),'step_distance_f64':f64(moved),'distance_f64':f64(distance),'position_f64':[f64(0),f64(distance)],'state':{'action':'walk','direction':'south'},'texture':texture,'slide_collisions':0};rows.append(row)
            name=f'draw-{i}.png';Image.new('RGBA',(1,1),(10,20,30,255)).save(self.evidence/name);hashes[name]=hashlib.sha256((self.evidence/name).read_bytes()).hexdigest();draw.append({'clip':'walk-south','mode':'world-ten-cycles','process_frame':i+1,'physics_frame':i+1,'ticks_usec':(i+1)*50000,'process_delta_f64':f64(.05),'world_elapsed_f64':f64(phase),'world_state':row['state'],'actor_position_f64':row['position_f64'][:],'texture':copy.deepcopy(texture),'capture':name})
        idle={'clip':'idle-south','pose_id':'i0','rgba_sha256':'i'};name='idle.png';Image.new('RGBA',(1,1),(1,2,3,255)).save(self.evidence/name);hashes[name]=hashlib.sha256((self.evidence/name).read_bytes()).hexdigest();draw.append({'clip':'walk-south','mode':'released-to-idle','process_frame':63,'physics_frame':63,'ticks_usec':3150000,'process_delta_f64':f64(.05),'world_elapsed_f64':f64(0),'world_state':{'action':'idle','direction':'south'},'actor_position_f64':[f64(0),f64(distance)],'texture':idle,'capture':name})
        self.report={'capture_every_rendered_frame':True,'clips':{'walk-south':{'pose_ids':['w0','w1'],'durations_ms':[100,100],'base_world_speed':72,'initial_position_f64':[f64(0),f64(0)]}},'farm_clips':{},'physics_samples':rows,'farm_physics_samples':[],'samples':draw,'output_hashes':hashes}

    def test_world_recomputes_ten_actual_cycles_and_every_draw(self):
        v=self.verifier();result=v.world_evidence(self.contract,self.report,self.profiles,self.evidence)
        self.assertGreaterEqual(result['motion']['walk-south']['cycles'],10)
        self.assertEqual(result['captured_draws'],61)

    def test_false_producer_cycle_count_cannot_hide_short_raw(self):
        self.report['physics_samples']=self.report['physics_samples'][:4];self.report['clips']['walk-south']['cycles']=100
        with self.assertRaisesRegex(ValueError,'ten actual'):self.verifier().world_evidence(self.contract,self.report,self.profiles,self.evidence)

    def test_missing_draw_capture_or_active_process_gap_is_rejected(self):
        for defect in ['capture','gap']:
            r=copy.deepcopy(self.report)
            if defect=='capture':r['samples'][3].pop('capture')
            else:r['samples'].pop(3)
            with self.subTest(defect=defect),self.assertRaises(ValueError):self.verifier().world_evidence(self.contract,r,self.profiles,self.evidence)

    def test_wrong_draw_texture_or_timing_is_rejected(self):
        for defect in ['rgba','phase']:
            r=copy.deepcopy(self.report)
            if defect=='rgba':r['samples'][3]['texture']['rgba_sha256']='false'
            else:r['samples'][3]['world_elapsed_f64']=f64(50)
            with self.subTest(defect=defect),self.assertRaises(ValueError):self.verifier().world_evidence(self.contract,r,self.profiles,self.evidence)

    def test_world_physical_direction_must_match_bound_clip(self):
        for row in self.report['physics_samples']:
            distance=struct.unpack('<d',bytes.fromhex(row['distance_f64']))[0]
            row['position_f64']=[f64(-distance),f64(0)]
        with self.assertRaises(ValueError):self.verifier().world_evidence(self.contract,self.report,self.profiles,self.evidence)


class PoseRawEvidenceTests(unittest.TestCase):
    def setUp(self):
        import tempfile,hashlib
        from PIL import Image
        self.temp=tempfile.TemporaryDirectory(prefix='coastal-evidence-pose-',dir='/private/tmp');self.addCleanup(self.temp.cleanup);self.evidence=Path(self.temp.name)
        _,self.profiles=locomotion_case();self.profiles['idle-south'].update(action_id='idle',direction='south',pose_ids=['i0'],duration_ms=[100])
        self.contract={'runtime':{'clips':{'walk-south':{'playback_rate':1},'idle-south':{'playback_rate':1}},'default_speed_factor':.75}}
        rows=[];hashes={};frame=0
        def capture(row,name):
            nonlocal frame
            frame+=1;row.update(process_frame=frame,ticks_usec=frame*50000,process_delta_f64=f64(.05));(self.evidence/name).parent.mkdir(parents=True,exist_ok=True);Image.new('RGBA',(1,1),(1,2,3,255)).save(self.evidence/name);hashes[name]=hashlib.sha256((self.evidence/name).read_bytes()).hexdigest();row['capture']=name;rows.append(row)
        for key,p in self.profiles.items():
            for bg in ['dark','light']:
                phase=0
                for i,pose in enumerate(p['pose_ids']):
                    capture({'clip':key,'mode':'stopped-'+bg,'panel_phase_f64':f64(phase),'panel_pose':i,'panel_texture':{'clip':key,'pose_id':pose,'rgba_sha256':p['rgba'][pose]}},f'stills/{key}-{bg}-{i}.png');phase+=p['duration_ms'][i]
            if p['action_id']=='idle':continue
            elapsed=0
            for i in range(54):
                elapsed+=37.5;phase=elapsed%200;pose='w0' if phase<100 else 'w1';capture({'clip':key,'mode':'panel-continuous','panel_phase_f64':f64(phase),'panel_pose':0 if phase<100 else 1,'unwrapped_ms':elapsed,'panel_texture':{'clip':key,'pose_id':pose,'rgba_sha256':p['rgba'][pose]}},f'{key}-panel-{i}.png')
        for key,p in self.profiles.items():
            phase=0
            for i,pose in enumerate(p['pose_ids']):
                capture({'clip':key,'mode':'world-idle' if p['action_id']=='idle' else 'world-continuous','world_elapsed_f64':f64(phase),'world_state':{'action':p['action_id'],'direction':p['direction']},'world_texture':{'clip':key,'pose_id':pose,'rgba_sha256':p['rgba'][pose]}},f'world/{key}-pose-{i}.png');phase+=p['duration_ms'][i]
        self.contract['plan']={'required_pngs':[n for n in hashes if n.startswith(('stills/','world/'))]}
        self.report={'samples':rows,'output_hashes':hashes}

    def verifier(self):
        module=importlib.import_module('all_actions_evidence');self.assertTrue(callable(getattr(module,'poses_evidence',None)), 'Pose raw verifier missing');return module

    def test_every_plan_pose_on_both_backgrounds_and_ten_raw_panel_cycles(self):
        result=self.verifier().poses_evidence(self.contract,self.report,self.profiles,self.evidence)
        self.assertEqual(result['stopped_poses'],6)

    def test_missing_actual_panel_identity_is_rejected(self):
        self.report['samples'][0].pop('panel_texture')
        with self.assertRaises(ValueError):self.verifier().poses_evidence(self.contract,self.report,self.profiles,self.evidence)

    def test_wrong_actual_texture_cannot_be_hidden_by_panel_index(self):
        self.report['samples'][0]['panel_texture']['pose_id']='w1'
        with self.assertRaises(ValueError):self.verifier().poses_evidence(self.contract,self.report,self.profiles,self.evidence)

    def test_claimed_ten_cycles_cannot_hide_short_raw_phase(self):
        self.report['samples']=self.report['samples'][:5];self.report['checks']={'ten_cycles':True}
        with self.assertRaises(ValueError):self.verifier().poses_evidence(self.contract,self.report,self.profiles,self.evidence)


class FullObservationBindingTests(unittest.TestCase):
    def setUp(self):
        import test_all_actions_capture as fixture
        import all_actions_capture as capture
        from build_contract import digest
        self.fixture=fixture.FullCaptureSnapshotTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.repo=self.fixture.repo;self.evidence=self.fixture.output
        (self.repo/'godot2d/tests/characters/capture_registered_farm_timing.gd').write_text('extends \"res://tests/helper.gd\"\n')
        self.contract=capture.snapshot(self.repo,self.fixture.fixture.suite_path,self.evidence,'locomotion-timing')
        manifest_path=self.repo/self.contract['manifest']['manifest'];m=json.loads(manifest_path.read_text());outputs={o['file']:o for o in m['outputs']};self.report={'kind':'coastal-registered-locomotion-timing-observation-v1','input_contract_sha256':digest(self.evidence/'input-contract.json'),'renderer':'synthetic-test-GPU','checks':{'tool_fixture':True},'cases':[]}
        self.report['loaded_input_binding']={'passed':True,'full_package':True,
            'actual_suite_path':str(self.repo/self.contract['suite']),
            'catalog_sha256':self.contract['files'][self.contract['suite']],
            'manifest_binding':{**self.contract['manifest'],'recipe':m['recipe'],
                'recipe_sha256':m['inputs'][m['recipe']],'artifact_digest':m['artifact_digest']},
            'runtime':copy.deepcopy(self.contract['runtime']),
            'producer_script':'res://'+self.contract['observer_script'].removeprefix('godot2d/'),
            'capture_scene':self.contract['capture_scene']}
        for key,p in self.contract['plan']['clips'].items():
            if p['action_id'] not in ['walk','run']:continue
            for scenario in ['low-frame-rate','focus-pause','playback-rate','replay-once']:
                case,_=locomotion_case(scenario);case.update(case=key+'/'+scenario,clip=key,pose_ids=p['pose_ids'],durations_ms=p['duration_ms'],base_world_speed=self.contract['runtime']['movement'][p['action_id']]['base_world_speed']);case['physics_samples']=[]
                base=case['base_world_speed'];duration=sum(p['duration_ms']);phase=distance=0;frame=0;factor=case['speed_factor'];ticks=int(duration*2.5/(1000*factor*.05))+1
                for segment in range(1,case['segments']+1):
                    plan=[('move',True)]*ticks+[('idle',True)]*3
                    if scenario=='focus-pause':plan=plan[:2]+[('move',False)]*4+plan[2:]
                    for action,focus in plan:
                        frame+=1;dt=.2 if scenario=='low-frame-rate' else .05;moved=base*factor*dt if action=='move' and focus else 0;distance+=moved;phase=(phase+moved/base*1000)%duration;remaining=phase;index=0
                        for index,length in enumerate(p['duration_ms']):
                            if remaining<length:break
                            remaining-=length
                        pose=p['pose_ids'][index];active_key=key
                        if action=='idle':active_key='idle-'+p['direction'];pose=self.contract['plan']['clips'][active_key]['pose_ids'][0]
                        out=outputs[f'frames/{active_key.split("-")[0]}/{p["direction"]}/{pose}.png'];vx,vy={'south':(0,1),'west':(-1,0),'east':(1,0),'north':(0,-1)}[p['direction']];case['physics_samples'].append({'case':case['case'],'segment':segment,'physics_frame':frame,'delta_f64':f64(dt),'focused':focus,'speed_factor_f64':f64(factor),'phase_f64':f64(phase),'step_distance_f64':f64(moved),'distance_f64':f64(distance),'position_f64':[f64(vx*distance),f64(vy*distance)],'state':{'action':action if action=='idle' else p['action_id'],'direction':p['direction']},'texture':{'clip':active_key,'pose_id':pose,'rgba_sha256':out['rgba_sha256']},'slide_collisions':0})
                self.report['cases'].append(case)
        self.save()

    def save(self):
        (self.evidence/'report.json').write_text(json.dumps(self.report))

    def verifier(self):
        module=importlib.import_module('all_actions_evidence');self.assertTrue(callable(getattr(module,'validate_observation',None)), 'Frozen full-package observation entry point missing');return module

    def test_actual_full_snapshot_and_raw32_cases_produce_bounded_scope(self):
        result=self.verifier().validate_observation(self.repo,self.evidence)
        self.assertEqual(result['kind'],'coastal-all-actions-internal-observation-v1')
        self.assertEqual(result['observed']['timing_cases'],32)
        self.assertFalse(result['art_acceptance'])
        self.assertEqual(result['gap_matrix']['farm_timing']['observed'],0)

    def test_changed_real_texture_input_is_rejected(self):
        name=next(p for p in self.contract['files'] if '/frames/' in p);path=self.repo/name;path.write_bytes(path.read_bytes()+b'changed')
        with self.assertRaisesRegex(ValueError,'changed'):self.verifier().validate_observation(self.repo,self.evidence)

    def test_fake_texture_or_mismatched_timing_profile_is_rejected(self):
        for defect in ['texture','duration']:
            old=copy.deepcopy(self.report)
            if defect=='texture':self.report['cases'][0]['physics_samples'][0]['texture']['rgba_sha256']='0'*64
            else:self.report['cases'][0]['durations_ms'][0]+=1
            self.save()
            with self.subTest(defect=defect),self.assertRaises(ValueError):self.verifier().validate_observation(self.repo,self.evidence)
            self.report=old

    def test_missing_case_cannot_be_replaced_by_producer_count(self):
        self.report['cases'].pop();self.report['case_count']=32;self.save()
        with self.assertRaises(ValueError):self.verifier().validate_observation(self.repo,self.evidence)

    def test_cli_writes_a_bounded_fresh_receipt(self):
        import subprocess
        tool=Path(__file__).resolve().parents[1]/'all_actions_evidence.py'
        command=[sys.executable,str(tool),'--repo',str(self.repo),'validate','--evidence',str(self.evidence),'--receipt',str(self.evidence/'cli-observation.json')]
        result=subprocess.run(command,text=True,capture_output=True)
        self.assertIn('coastal-all-actions-internal-observation-v1',result.stdout)
        self.assertEqual(result.returncode,0,result.stderr)
        receipt=json.loads((self.evidence/'cli-observation.json').read_text())
        self.assertEqual(receipt['observed']['timing_cases'],32)
        self.assertFalse(receipt['art_acceptance'])
        self.assertEqual(subprocess.run(command,text=True,capture_output=True).returncode,2)


class FarmTimingBindingTests(unittest.TestCase):
    def fixture(self):
        profiles={'hoe-south':{'action_id':'hoe','direction':'south','pose_ids':['ready','hit'],'duration_ms':[200,300],'rgba':{'ready':'a','hit':'b'}},'idle-south':{'rgba':{'idle':'i'}}}
        events=[{'event_id':'contact','at_ms':200,'pose_id':'hit'}];contract={'plan':{'time_scenarios':{'hoe-south':['low-frame-rate','focus-pause','playback-rate','replay-once']}},'runtime':{'clips':{'hoe-south':{'events':events,'playback_rate':1}}}};cases=[]
        for instance,scenario in enumerate(contract['plan']['time_scenarios']['hoe-south'],1):
            rate=2 if scenario=='playback-rate' else 1;dt=.2 if scenario=='low-frame-rate' else .1;case={'case':'hoe-south/'+scenario,'clip':'hoe-south','scenario':scenario,'rate':rate,'instance_id':instance,'physics_ticks_per_second':5 if scenario=='low-frame-rate' else 60,'max_fps':5 if scenario=='low-frame-rate' else 0,'pose_ids':['ready','hit'],'durations_ms':[200,300],'events':copy.deepcopy(events),'initial_position_f64':[f64(10),f64(20)],'physics_samples':[],'journal':[]};elapsed=0;frame=0
            ticks=[True]*int((.5/(dt*rate))+.999)
            if scenario=='focus-pause':ticks=ticks[:1]+[False]*4+ticks[1:]
            for focused in ticks:
                frame+=1;elapsed+=dt*1000*rate if focused else 0;done=elapsed>=500;pose='ready' if elapsed<200 else 'hit';case['physics_samples'].append({'case':case['case'],'instance_id':instance,'physics_frame':frame,'delta_f64':f64(dt),'focused':focused,'elapsed_f64':f64(0 if done else elapsed),'position_f64':[f64(10),f64(20)],'state':{'action':'idle' if done else 'hoe','direction':'south','instance_id':instance},'texture':{'clip':'idle-south' if done else 'hoe-south','pose_id':'idle' if done else pose,'rgba_sha256':'i' if done else profiles['hoe-south']['rgba'][pose]},'journal_size':0})
            common={'instance_id':instance,'action':'hoe','direction':'south','loop':0};case['journal']=[{**common,**events[0]},{**common,'event_id':'complete','at_ms':500}];cases.append(case)
        return contract,{'cases':cases},profiles

    def verifier(self):
        m=importlib.import_module('all_actions_evidence');self.assertTrue(callable(getattr(m,'farm_timing_report',None)),'Farm timing report binding missing');return m

    def test_four_timing_cases_bind_actual_runtime_events_and_unique_instances(self):
        c,r,p=self.fixture();self.assertEqual(self.verifier().farm_timing_report(c,r,p)['timing_cases'],4)

    def test_report_cannot_replace_bound_events_or_reuse_instances(self):
        for defect in ['events','instance']:
            c,r,p=self.fixture()
            if defect=='events':r['cases'][0]['events'][0]['at_ms']=199
            else:r['cases'][1]['instance_id']=r['cases'][0]['instance_id']
            with self.subTest(defect=defect),self.assertRaises(ValueError):self.verifier().farm_timing_report(c,r,p)

    def test_48_farm_cases_are_not_an_eighty_case_claim(self):
        c,r,p=self.fixture();result=self.verifier().farm_timing_report(c,r,p)
        self.assertEqual(result['scope'],'farm-timing-only')
        self.assertNotIn('locomotion_timing_complete',result)

    def test_focus_pause_requires_four_consecutive_complete_ticks(self):
        c,r,p=self.fixture();case=next(v for v in r['cases'] if v['scenario']=='focus-pause');elapsed=0
        for row,focused in zip(case['physics_samples'],[False,True,False,True,False,True,False,True,True]):
            elapsed+=100 if focused else 0;done=elapsed>=500;pose='ready' if elapsed<200 else 'hit'
            row.update(focused=focused,elapsed_f64=f64(0 if done else elapsed),state={'action':'idle' if done else 'hoe','direction':'south','instance_id':case['instance_id']},texture={'clip':'idle-south' if done else 'hoe-south','pose_id':'idle' if done else pose,'rgba_sha256':'i' if done else p['hoe-south']['rgba'][pose]})
        with self.assertRaises(ValueError):self.verifier().farm_timing_report(c,r,p)

    def test_timing_player_instance_is_bound_to_the_case(self):
        c,r,p=self.fixture();case=r['cases'][0]
        case['physics_samples'][0]['state']['instance_id']=999
        with self.assertRaises(ValueError):self.verifier().farm_timing_report(c,r,p)


class TransitionReportTests(unittest.TestCase):
    def setUp(self):
        import tempfile,hashlib
        from PIL import Image
        self.temp=tempfile.TemporaryDirectory(prefix='coastal-evidence-transition-',dir='/private/tmp');self.addCleanup(self.temp.cleanup);self.evidence=Path(self.temp.name)
        key='walk-west-to-run-west';name='transition-'+key+'.png';Image.new('RGBA',(1,1),(1,2,3,255)).save(self.evidence/name)
        self.profiles={a+'-west':{'rgba':{a+'0':a},'duration_ms':[300],'events':[]} for a in ['idle','walk','run']}
        self.contract={'plan':{'transitions':[key]},'runtime':{'locomotion_transition':{'duration_ms':100}}}
        state=lambda a:{'action':a,'direction':'west'};texture=lambda a:{'clip':a+'-west','pose_id':a+'0','rgba_sha256':a}
        t={'id':key,'source':{'world_state':state('walk'),'texture':texture('walk')},'target':{'world_state':state('run'),'texture':texture('run'),'capture':name},'journal':[],'physics_samples':[]}
        for i in range(7):
            a='idle' if i<6 else 'run';t['physics_samples'].append({'physics_frame':i+1,'delta_f64':f64(1/60),'state':state(a),'texture':texture(a),'position_f64':[f64(10),f64(20)],'pending_locomotion_action':'run' if i<6 else '', 'phase_f64':f64(0),'stable_remaining_f64':f64(100-i*1000/60)})
        self.report={'transitions':[t],'output_hashes':{name:hashlib.sha256((self.evidence/name).read_bytes()).hexdigest()}}

    def verifier(self):
        m=importlib.import_module('all_actions_evidence');self.assertTrue(callable(getattr(m,'transition_report',None)),'Transition report entry missing');return m

    def test_bound_transition_plan_recomputes_stable_idle_and_capture(self):
        r=self.verifier().transition_report(self.contract,self.report,self.profiles,self.evidence);self.assertEqual(r['stable_idle_transitions'],1)

    def test_missing_transition_or_replaced_png_is_rejected(self):
        for defect in ['missing','png']:
            r=copy.deepcopy(self.report)
            if defect=='missing':r['transitions']=[]
            else:r['output_hashes'][next(iter(r['output_hashes']))]='0'*64
            with self.subTest(defect=defect),self.assertRaises(ValueError):self.verifier().transition_report(self.contract,r,self.profiles,self.evidence)


class SpatialReportTests(unittest.TestCase):
    def setUp(self):
        import tempfile,hashlib,math
        from PIL import Image
        self.repo=Path(__file__).resolve().parents[3]
        self.temp=tempfile.TemporaryDirectory(prefix='coastal-evidence-spatial-',dir='/private/tmp');self.addCleanup(self.temp.cleanup);self.evidence=Path(self.temp.name)
        self.profiles={a+'-'+d:{'action_id':a,'direction':d,'pose_ids':[a+d+'0',a+d+'1'],'duration_ms':[100,100],'rgba':{a+d+'0':a+d+'0',a+d+'1':a+d+'1'}} for a in ['idle','walk','run','hoe','water','harvest'] for d in ['south','west','east','north']}
        self.contract={'observer_script':'godot2d/tests/characters/capture_registered_spatial.gd','runtime':{'movement':{'walk':{'base_world_speed':72},'run':{'base_world_speed':108}},'default_speed_factor':.75}}
        self.report={'routes':[],'capture_records':[],'output_hashes':{},'engine_clock':{'physics_ticks_per_second':60,'physics_jitter_fix_f64':f64(.5),'time_scale_f64':f64(1),'max_physics_steps_per_frame':8}}
        frame=100
        def texture(key,index=0):
            p=self.profiles[key];pose=p['pose_ids'][index];return {'clip':key,'pose_id':pose,'rgba_sha256':p['rgba'][pose]}
        def setup(point):
            nonlocal frame
            frame+=2
            return {'physics_frame':frame,'position_f64':[f64(v) for v in point],
                    'state':{'action':'idle','direction':'north','elapsed_ms':0},'texture':texture('idle-north')}
        def capture(name,case,row):
            name+='.png';point=[struct.unpack('<d',bytes.fromhex(v))[0] for v in row['position_f64']]
            Image.new('RGBA',(1,1),(10,20,30,255)).save(self.evidence/name)
            self.report['output_hashes'][name]=hashlib.sha256((self.evidence/name).read_bytes()).hexdigest()
            self.report['capture_records'].append({'case':case,'capture':name,'world_state':copy.deepcopy(row['state']),
                'world_texture':copy.deepcopy(row['texture']),'world_elapsed_f64':f64(row['state']['elapsed_ms']),
                'actor_position_f64':row['position_f64'][:],'actor_position':point,
                'capture_origin_px':[int(point[0])-140,int(point[1])-245],
                'render_source_to_screen':[1,0,0,1,point[0],point[1]],'sprite_offset':[0,0],
                'process_frame':frame*2 if row['physics_frame']==frame else row['physics_frame']*2,
                'physics_frame':row['physics_frame'],'ticks_usec':row['physics_frame']*50000+1000})
            return name
        def physics(points,point0,case,farm=None,door=False):
            nonlocal frame
            out=[];previous=point0;heading='north';phase=0
            for i,point in enumerate(points):
                frame+=1;dx,dy=point[0]-previous[0],point[1]-previous[1]
                if farm:
                    key=farm;phase=i*100
                elif dx or dy:
                    heading=('east' if dx>0 else 'west') if abs(dx)>abs(dy) else ('south' if dy>0 else 'north')
                    key='walk-'+heading;phase=(phase+math.hypot(dx,dy)/72*1000)%200
                else:key='idle-'+heading;phase=0
                index=0 if phase<100 else 1
                out.append({'case':case,'physics_frame':frame,'ticks_usec':frame*50000,'delta_f64':f64(1/60),
                    'position_f64':[f64(v) for v in point],
                    'state':{'action':key.split('-')[0],'direction':key.split('-')[1],'elapsed_ms':phase},
                    'texture':texture(key,index),'colliders':['/root/HarborExterior/DepthSortedObjects/ExteriorDoor/DoorCollision'] if door else []})
                previous=point
            return out
        for key,points in [('tree-around',[[286,130],[330,130],[330,90],[286,90],[286,130]]),('counter-around',[[362,252],[548,252],[548,184],[362,184],[362,252]])]:
            initial=setup(points[0]);captures=[capture(key+'-start',key,initial)];path=[];ends=[];previous=points[0]
            for target in points[1:]:
                n=int(math.dist(previous,target));path.extend([[previous[0]+(target[0]-previous[0])*i/n,previous[1]+(target[1]-previous[1])*i/n] for i in range(1,n+1)]);ends.append(len(path)-1);previous=target
            rows=physics(path,points[0],key)
            captures.extend(capture(key+'-waypoint-'+str(i+1),key,rows[end]) for i,end in enumerate(ends))
            self.report['routes'].append({'id':key,'setup_position':points[0],'waypoints':points,'physics_samples':rows,'captures':captures})
        for pose in range(3):
            key='door-pose-'+str(pose);initial=setup([209,190]);captures=[capture(key+'-start',key,initial)]
            path=[[209,max(170,190-i*.9)] if pose<2 else [209,190-i*.9] for i in range(1,66)]
            rows=physics(path,[209,190],key,door=pose<2)
            captures.extend(capture(key+'-tick-'+str(i),key,rows[i]) for i in [15,30,45]);captures.append(capture(key+'-end',key,rows[-1]))
            self.report['routes'].append({'id':key,'door_pose':pose,'setup_position':[209,190],'physics_samples':rows,'final_position':path[-1],'captures':captures})
        for prefix,point,direction in [('tree-tools',[330,130],'west'),('counter-tools',[510,250],'north'),('door-tools',[235,190],'west')]:
            for action in ['hoe','water','harvest']:
                key=prefix+'-'+action;setup(point);rows=physics([point,point],point,key,action+'-'+direction)
                self.report['routes'].append({'id':key,'spatial_observation_playback_rate':.25,'setup_position':point,'physics_samples':rows,'captures':[capture(key+'-pose-'+str(i),key,rows[i]) for i in range(2)]})

    def verifier(self):
        m=importlib.import_module('all_actions_evidence');self.assertTrue(callable(getattr(m,'spatial_report',None)),'Spatial raw report entry missing');return m

    def test_frozen_gds_routes_collisions_and_actual_capture_texture_bind(self):
        self.assertEqual(self.verifier().spatial_report(self.repo,self.contract,self.report,self.profiles,self.evidence)['routes'],14)

    def test_forged_route_or_capture_gpu_identity_is_rejected(self):
        for defect in ['waypoint','door','texture','missing-capture','teleport']:
            r=copy.deepcopy(self.report)
            if defect=='waypoint':r['routes'][0]['waypoints'][1]=[999,999]
            if defect=='door':r['routes'][2]['physics_samples'][-1]['position_f64'][1]=f64(140)
            if defect=='texture':r['capture_records'][0]['world_texture']['rgba_sha256']='false'
            if defect=='missing-capture':r['capture_records'].pop()
            if defect=='teleport':r['routes'][0]['physics_samples'][2]['position_f64'][0]=f64(900)
            with self.subTest(defect=defect),self.assertRaises(ValueError):self.verifier().spatial_report(self.repo,self.contract,r,self.profiles,self.evidence)


    def test_door_setup_start_can_retain_a_matching_previous_idle_direction(self):
        row=next(r for r in self.report['capture_records'] if r['case']=='door-pose-0')
        pose=self.profiles['idle-south']['pose_ids'][0]
        row['world_state']={'action':'idle','direction':'south'}
        row['world_texture']={'clip':'idle-south','pose_id':pose,'rgba_sha256':self.profiles['idle-south']['rgba'][pose]}
        row['world_elapsed_f64']=f64(0)
        self.assertEqual(self.verifier().spatial_report(self.repo,self.contract,self.report,self.profiles,self.evidence)['routes'],14)


class ReceiptAndDispatchTests(unittest.TestCase):
    setUp=FullObservationBindingTests.setUp
    save=FullObservationBindingTests.save
    verifier=FullObservationBindingTests.verifier

    def test_observer_kinds_have_separate_strict_dispatch(self):
        import all_actions_capture as capture
        import shutil
        for observer in ['timing','transitions','spatial']:
            dest=self.evidence.parent/(self.evidence.name+'-'+observer);self.addCleanup(lambda p=dest:shutil.rmtree(p,ignore_errors=True));capture.snapshot(self.repo,self.fixture.fixture.suite_path,dest,observer)
            from build_contract import digest
            (dest/'report.json').write_text(json.dumps({'kind':'wrong-observer-kind','input_contract_sha256':digest(dest/'input-contract.json'),'renderer':'synthetic-test-GPU','checks':{'ok':True}}))
            with self.subTest(observer=observer),self.assertRaisesRegex(ValueError,'Wrong observer report kind'):
                self.verifier().validate_observation(self.repo,dest)

    def test_receipt_is_fresh_bounded_and_does_not_overwrite_raw(self):
        v=self.verifier();self.assertTrue(callable(getattr(v,'write_receipt',None)),'Receipt writer missing')
        path=self.evidence/'internal-observation.json';v.write_receipt(self.repo,self.evidence,path)
        self.assertFalse(json.loads(path.read_text())['release_eligible'])
        with self.assertRaises(ValueError):v.write_receipt(self.repo,self.evidence,path)
        with self.assertRaises(ValueError):v.write_receipt(self.repo,self.evidence,self.evidence/'report.json')

    def test_aggregate_reports_actual_missing_matrix_and_rejects_duplicate_scope(self):
        v=self.verifier();self.assertTrue(callable(getattr(v,'aggregate_observations',None)),'Aggregate raw verifier missing')
        result=v.aggregate_observations(self.repo,[self.evidence]);self.assertEqual(result['gap_matrix']['farm_timing']['missing'],48);self.assertEqual(result['gap_matrix']['locomotion_timing']['missing'],0);self.assertFalse(result['art_acceptance'])
        with self.assertRaises(ValueError):v.aggregate_observations(self.repo,[self.evidence,self.evidence])


class FarmWorldJournalTests(VerifierMixin,unittest.TestCase):
    setUp=WorldRawEvidenceTests.setUp

    def farm_report(self):
        import hashlib
        from PIL import Image
        import shutil
        for path in self.evidence.glob('*.png'):path.unlink()
        events=[{'event_id':'contact','at_ms':200,'pose_id':'hit'}];profiles={'hoe-south':{'action_id':'hoe','direction':'south','pose_ids':['ready','hit'],'duration_ms':[200,300],'rgba':{'ready':'a','hit':'b'}},'idle-south':{'rgba':{'idle':'i'}}};contract={'capture_every_rendered_frame':True,'runtime':{'clips':{'hoe-south':{'playback_rate':1,'events':events}}}};rows=[];draw=[];hashes={};journal=[]
        for instance in range(1,11):
            common={'instance_id':instance,'action':'hoe','direction':'south','loop':0};journal.extend([{**common,**events[0]},{**common,'event_id':'complete','at_ms':500}])
            for tick in range(1,6):
                elapsed=tick*100;done=elapsed==500;pose='ready' if elapsed<200 else 'hit';texture={'clip':'idle-south' if done else 'hoe-south','pose_id':'idle' if done else pose,'rgba_sha256':'i' if done else profiles['hoe-south']['rgba'][pose]};state={'action':'idle' if done else 'hoe','direction':'south','instance_id':instance};frame=(instance-1)*5+tick;rows.append({'clip':'hoe-south','instance_id':instance,'physics_frame':frame,'delta_f64':f64(.1),'elapsed_f64':f64(0 if done else elapsed),'position_f64':[f64(0),f64(0)],'state':state,'texture':texture});name=f'{instance}-{tick}.png';Image.new('RGBA',(1,1),(1,2,3,255)).save(self.evidence/name);hashes[name]=hashlib.sha256((self.evidence/name).read_bytes()).hexdigest();draw.append({'clip':'hoe-south','mode':'farm-world-ten-instances','instance_id':instance,'process_frame':frame,'physics_frame':frame,'ticks_usec':frame*100000,'process_delta_f64':f64(.1),'world_elapsed_f64':f64(0 if done else elapsed),'world_state':state,'actor_position_f64':[f64(0),f64(0)],'texture':texture,'capture':name})
        report={'capture_every_rendered_frame':True,'clips':{},'farm_clips':{'hoe-south':{'pose_ids':['ready','hit'],'durations_ms':[200,300],'playback_rate':1,'events':events,'instances':list(range(1,11)),'initial_position_f64':[f64(0),f64(0)],'journal':journal}},'physics_samples':[],'farm_physics_samples':rows,'samples':draw,'output_hashes':hashes}
        return contract,report,profiles

    def test_farm_instance_journal_cannot_hide_unbound_extra_event(self):
        contract,report,profiles=self.farm_report()
        self.assertEqual(self.verifier().world_evidence(contract,report,profiles,self.evidence)['farm']['hoe-south']['instances'],10)
        report['farm_clips']['hoe-south']['journal'].append({'instance_id':999,'action':'hoe','direction':'south','loop':0,'event_id':'complete','at_ms':500})
        with self.assertRaises(ValueError):self.verifier().world_evidence(contract,report,profiles,self.evidence)

    def test_actual_player_instance_must_match_physics_and_draw_group(self):
        for section in ['farm_physics_samples','samples']:
            contract,report,profiles=self.farm_report()
            row=report[section][0]
            row['state' if section=='farm_physics_samples' else 'world_state']['instance_id']=999
            with self.subTest(section=section),self.assertRaises(ValueError):
                self.verifier().world_evidence(contract,report,profiles,self.evidence)


class PhaseRangeTests(VerifierMixin,unittest.TestCase):
    setUp=WorldRawEvidenceTests.setUp

    def test_equivalent_negative_phase_is_not_a_real_clock_record(self):
        self.report['physics_samples'][0]['phase_f64']=f64(37.5-200)
        with self.assertRaises(ValueError):self.verifier().world_evidence(self.contract,self.report,self.profiles,self.evidence)


class EvidenceRepairRegressionTests(unittest.TestCase):
    def fixture(self,cls):
        value=cls();value.setUp();self.addCleanup(value.doCleanups);return value

    def prune_pngs(self,value):
        keep={row['capture'] for row in value.report['samples']}
        for path in value.evidence.glob('*.png'):
            if path.name not in keep:path.unlink()
        value.report['output_hashes']={k:h for k,h in value.report['output_hashes'].items() if k in keep}

    def test_ten_physics_cycles_require_full_rendered_interval(self):
        import all_actions_evidence as v
        o=self.fixture(WorldRawEvidenceTests)
        o.report['samples']=o.report['samples'][1:3]+o.report['samples'][-1:];self.prune_pngs(o)
        with self.assertRaises(ValueError):v.world_evidence(o.contract,o.report,o.profiles,o.evidence)

    def test_world_draw_must_match_its_actual_physics_state_position_and_clock(self):
        import all_actions_evidence as v
        for defect in ['position','frame','clock']:
            o=self.fixture(WorldRawEvidenceTests);row=o.report['samples'][3]
            if defect=='position':row['actor_position_f64']=[f64(999),f64(999)]
            elif defect=='frame':row['physics_frame']=12
            else:row['world_elapsed_f64']=f64(175)
            with self.subTest(defect=defect),self.assertRaises(ValueError):v.world_evidence(o.contract,o.report,o.profiles,o.evidence)

    def test_shared_player_farm_instances_cannot_reuse_physics_frames(self):
        import all_actions_evidence as v
        o=self.fixture(FarmWorldJournalTests);c,r,p=o.farm_report()
        for row in r['farm_physics_samples']:row['physics_frame']=(row['physics_frame']-1)%5+1
        with self.assertRaises(ValueError):v.world_evidence(c,r,p,o.evidence)

    def test_focus_pause_cannot_be_satisfied_after_release_to_idle(self):
        import all_actions_evidence as v
        case,p=locomotion_case('focus-pause');rows=[r for r in case['physics_samples'] if r['focused']]
        rows += [copy.deepcopy(rows[-1]) for _ in range(4)]
        for i,row in enumerate(rows):row['physics_frame']=i+1;row['focused']=i<len(rows)-4
        case['physics_samples']=rows
        with self.assertRaises(ValueError):v.locomotion_timing_evidence(case,p,72,.75)

    def test_spatial_moving_direction_is_bound_to_actual_displacement(self):
        import all_actions_evidence as v
        o=self.fixture(SpatialReportTests)
        for row in o.report['routes'][0]['physics_samples']:
            row['state'].update(action='walk',direction='south');pose=o.profiles['walk-south']['pose_ids'][0]
            row['texture']={'clip':'walk-south','pose_id':pose,'rgba_sha256':o.profiles['walk-south']['rgba'][pose]}
        with self.assertRaises(ValueError):v.spatial_report(o.repo,o.contract,o.report,o.profiles,o.evidence)

    def test_spatial_capture_position_and_actual_clocks_belong_to_route(self):
        import all_actions_evidence as v
        for defect in ['position','zero-clocks','different-physics','waypoint']:
            o=self.fixture(SpatialReportTests);row=o.report['capture_records'][1]
            if defect=='position':row['actor_position_f64']=[f64(999),f64(999)];row['actor_position']=[999,999]
            elif defect=='zero-clocks':
                for r in o.report['capture_records']:r.update(process_frame=0,physics_frame=0,ticks_usec=0)
            elif defect=='different-physics':row['physics_frame']+=5
            else:
                # Internally consistent record copied from the wrong point of the same route.
                old=o.report['capture_records'][2];row.update({k:copy.deepcopy(old[k]) for k in ['actor_position_f64','actor_position','physics_frame','world_state','world_texture','world_elapsed_f64']})
            with self.subTest(defect=defect),self.assertRaises(ValueError):v.spatial_report(o.repo,o.contract,o.report,o.profiles,o.evidence)

    def test_world_allows_multiple_physics_per_draw_and_multiple_draws_per_tick(self):
        import all_actions_evidence as v
        from build_contract import digest
        for cadence in ['sparse','dense']:
            o=self.fixture(WorldRawEvidenceTests);active=o.report['samples'][:-1];ending=o.report['samples'][-1]
            if cadence=='sparse':
                active=active[::2]+active[-1:];previous=0
                for i,row in enumerate(active):
                    row['process_frame']=i+1;row['process_delta_f64']=f64((row['physics_frame']-previous)*.05);previous=row['physics_frame']
            else:
                active=[copy.deepcopy(row) for row in active for _ in range(2)]
                for i,row in enumerate(active):
                    row['process_frame']=i+1;row['ticks_usec']=(i+1)*25000;row['process_delta_f64']=f64(.025)
                    original=o.evidence/row['capture'];name='dense-'+str(i)+'.png';(o.evidence/name).write_bytes(original.read_bytes());row['capture']=name;o.report['output_hashes'][name]=digest(o.evidence/name)
            ending['process_frame']=len(active)+3;o.report['samples']=active+[ending];self.prune_pngs(o)
            with self.subTest(cadence=cadence):self.assertGreaterEqual(v.world_evidence(o.contract,o.report,o.profiles,o.evidence)['motion']['walk-south']['cycles'],10)

    def test_farm_instances_may_have_real_setup_tick_gaps(self):
        import all_actions_evidence as v
        o=self.fixture(FarmWorldJournalTests);c,r,p=o.farm_report()
        for row in r['farm_physics_samples']:row['physics_frame']+=(row['instance_id']-1)*3
        for row in r['samples']:row['physics_frame']+=(row['instance_id']-1)*3
        self.assertEqual(v.world_evidence(c,r,p,o.evidence)['farm']['hoe-south']['instances'],10)


class ActualLoadedBindingTests(unittest.TestCase):
    setUp=FullObservationBindingTests.setUp
    save=FullObservationBindingTests.save
    verifier=FullObservationBindingTests.verifier

    def test_full_report_must_include_actual_loaded_binding(self):
        self.report.pop('loaded_input_binding');self.save()
        with self.assertRaises(ValueError):self.verifier().validate_observation(self.repo,self.evidence)

    def test_actual_loaded_authority_is_compared_field_by_field(self):
        v=self.verifier();self.assertTrue(callable(getattr(v,'loaded_input_binding',None)))
        expected=copy.deepcopy(self.report['loaded_input_binding'])
        for defect in ['passed','full_package','actual_suite_path','catalog_sha256','manifest','sha256','recipe','recipe_sha256','artifact_digest','runtime','producer_script','capture_scene','bool-rate']:
            proof=copy.deepcopy(expected)
            if defect in ['passed','full_package']:proof[defect]=False
            elif defect in ['actual_suite_path','catalog_sha256','producer_script','capture_scene']:proof[defect]='wrong'
            elif defect in ['manifest','sha256','recipe','recipe_sha256','artifact_digest']:proof['manifest_binding'][defect]='wrong'
            elif defect=='runtime':proof['runtime']['default_speed_factor']=.5
            else:proof['runtime']['clips']['walk-south']['playback_rate']=True
            with self.subTest(defect=defect),self.assertRaises(ValueError):v.loaded_input_binding(self.repo,self.contract,{'loaded_input_binding':proof})
        self.assertEqual(v.loaded_input_binding(self.repo,self.contract,self.report),expected)

    def test_loaded_runtime_allows_integral_float_serialization(self):
        v=self.verifier();proof=copy.deepcopy(self.report['loaded_input_binding'])
        proof['runtime']['schema_version']=1.0
        proof['runtime']['clips']['walk-south']['playback_rate']=1.0
        self.assertEqual(v.loaded_input_binding(self.repo,self.contract,{'loaded_input_binding':proof}),proof)


class SpatialIdleRecoveryTests(unittest.TestCase):
    """Only actual door normal separation may move an idle player."""
    def setUp(self):
        self.fixture=SpatialReportTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.repo=self.fixture.repo;self.contract=self.fixture.contract;self.profiles=self.fixture.profiles;self.evidence=self.fixture.evidence

    def case(self,pose=0,amount=.0720672607421875):
        report=copy.deepcopy(self.fixture.report)
        for route in report['routes']:
            previous=route['setup_position'];phase=0
            for row in route['physics_samples']:
                point=[struct.unpack('<d',bytes.fromhex(v))[0] for v in row['position_f64']]
                if row['state']['action'] in ['walk','run']:phase=row['state']['elapsed_ms']
                row.update(requested_f64=[f64(0),f64(-1)],phase_f64=f64(phase),safe_margin_f64=f64(struct.unpack('<f',struct.pack('<f',.08))[0]),collision_normals_f64=[[f64(0),f64(1)] for _ in row['colliders']],motion_delta_f64=[f64(point[i]-previous[i]) for i in range(2)])
                previous=point
        route=next(r for r in report['routes'] if r['id']=='door-pose-'+str(pose));row=route['physics_samples'][-1];previous=route['physics_samples'][-2];normal=[0,1 if amount>0 else -1]
        row.update(state={'action':'idle','direction':'north','elapsed_ms':0},texture={'clip':'idle-north','pose_id':self.profiles['idle-north']['pose_ids'][0],'rgba_sha256':self.profiles['idle-north']['rgba'][self.profiles['idle-north']['pose_ids'][0]]},colliders=['/root/HarborExterior/DepthSortedObjects/'+('ExteriorDoor/DoorCollision' if pose<2 else 'House/HouseLintel')],collision_normals_f64=[[f64(v) for v in normal]])
        point=[struct.unpack('<d',bytes.fromhex(v))[0] for v in previous['position_f64']];point[1]+=amount;row['position_f64']=[f64(v) for v in point];row['motion_delta_f64']=[f64(0),f64(amount)];row['phase_f64']=previous['phase_f64'];route['final_position']=point
        capture=next(x for x in report['capture_records'] if x['capture']==route['id']+'-end.png');capture.update(actor_position=point,actor_position_f64=row['position_f64'][:],world_state=copy.deepcopy(row['state']),world_texture=copy.deepcopy(row['texture']),world_elapsed_f64=f64(0))
        return report,route,row,previous

    def validate(self,report):return importlib.import_module('all_actions_evidence').spatial_report(self.repo,self.contract,report,self.profiles,self.evidence)

    def accepted(self,report):
        try:return self.validate(report)
        except ValueError as error:self.fail('Legitimate bounded recovery rejected: '+str(error))

    def test_real072067_normal_separation_is_legal_on_each_door_pose(self):
        for pose in range(3):
            report,_,_,_=self.case(pose)
            with self.subTest(pose=pose):self.assertEqual(self.accepted(report)['routes'],14)

    def test_clock_can_reset_zero_but_cannot_advance_or_fake_wrap(self):
        report,_,row,previous=self.case();previous['phase_f64']=f64(150);row['phase_f64']=f64(0)
        self.assertEqual(self.accepted(report)['routes'],14)
        for phase in [150.001,149,199.99]:
            row['phase_f64']=f64(phase)
            with self.subTest(phase=phase),self.assertRaises(ValueError):self.validate(report)

    def test_normal_separation_below_runtime_walk_threshold_does_not_advance_clock(self):
        report,_,_,_=self.case(2,-.000030517578125)
        self.assertEqual(self.accepted(report)['routes'],14)

    def test_recovery_requires_every_actual_field_and_previous_clock(self):
        for name in ['requested_f64','phase_f64','safe_margin_f64','collision_normals_f64','motion_delta_f64','previous-phase']:
            report,_,row,previous=self.case()
            if name=='previous-phase':previous.pop('phase_f64')
            else:row.pop(name)
            with self.subTest(name=name),self.assertRaises(ValueError):self.validate(report)

    def test_wrong_or_missing_corresponding_collision_normal_is_rejected(self):
        for bad in ['none','foreign','wrong-door-surface','wrong-normal','reverse-normal','nonunit','count']:
            report,_,row,_=self.case()
            if bad=='none':row.update(colliders=[],collision_normals_f64=[])
            if bad=='foreign':row['colliders']=['/root/Unrelated/DoorCollision']
            if bad=='wrong-door-surface':row['colliders']=['/root/HarborExterior/DepthSortedObjects/House/HouseLintel']
            if bad=='wrong-normal':row['collision_normals_f64']=[[f64(1),f64(0)]]
            if bad=='reverse-normal':row['collision_normals_f64']=[[f64(0),f64(-1)]]
            if bad=='nonunit':row['collision_normals_f64']=[[f64(0),f64(2)]]
            if bad=='count':row['collision_normals_f64']=[]
            with self.subTest(bad=bad),self.assertRaises(ValueError):self.validate(report)

    def test_actual_margin_and_delta_cannot_be_forged_to_allow_motion(self):
        for bad in ['large-margin','zero-margin','motion-delta','too-far','bad-f64']:
            report,_,row,_=self.case(amount=.081 if bad=='too-far' else .0720672607421875)
            if bad=='large-margin':row['safe_margin_f64']=f64(.081)
            if bad=='zero-margin':row['safe_margin_f64']=f64(0)
            if bad=='motion-delta':row['motion_delta_f64']=[f64(0),f64(0)]
            if bad=='bad-f64':row['safe_margin_f64']=True
            with self.subTest(bad=bad),self.assertRaises(ValueError):self.validate(report)

    def test_requested_forward_walk_motion_is_not_relabelled_recovery(self):
        report,_,_,_=self.case(amount=-.0720672607421875)
        with self.assertRaises(ValueError):self.validate(report)

    def test_unrelated_normal_cannot_explain_a_tangential_step(self):
        report,_,row,_=self.case();row['collision_normals_f64']=[[f64(1),f64(0)],[f64(0),f64(1)]];row['colliders'].append('/root/Unrelated/Wall')
        with self.assertRaises(ValueError):self.validate(report)

    def test_regular_idle_and_tool_idle_remain_strictly_stationary(self):
        for kind in ['path','tool']:
            report,_,_,_=self.case();route=next(x for x in report['routes'] if x['id']==('tree-around' if kind=='path' else 'tree-tools-hoe'));row=route['physics_samples'][-1];previous=route['physics_samples'][-2];point=[struct.unpack('<d',bytes.fromhex(v))[0] for v in previous['position_f64']];point[1]+=.0720672607421875;direction='north' if kind=='path' else 'west';key='idle-'+direction;pose=self.profiles[key]['pose_ids'][0]
            row.update(position_f64=[f64(v) for v in point],state={'action':'idle','direction':direction,'elapsed_ms':0},texture={'clip':key,'pose_id':pose,'rgba_sha256':self.profiles[key]['rgba'][pose]},colliders=['/root/HarborExterior/DepthSortedObjects/ExteriorDoor/DoorCollision'],collision_normals_f64=[[f64(0),f64(1)]],motion_delta_f64=[f64(0),f64(.0720672607421875)],phase_f64=previous['phase_f64'])
            with self.subTest(kind=kind),self.assertRaisesRegex(ValueError,'Idle spatial|door recovery'):self.validate(report)

    def jitter_case(self,amount=-.000030517578125):
        import math
        report,route,row,previous=self.case(2,amount)
        # Preserve the actual binary32 positions. Earlier synthetic approach
        # ticks stop at the same wall so no unrelated positive movement appears.
        wall=137.0027313232422
        for item in route['physics_samples'][:-1]:
            point=[struct.unpack('<d',bytes.fromhex(v))[0] for v in item['position_f64']]
            if point[1]<wall:item['position_f64']=[f64(point[0]),f64(wall)]
        row['position_f64']=[f64(209),f64(wall+amount)];row['collision_normals_f64']=[[f64(0),f64(1)]]
        last=route['setup_position']
        for item in route['physics_samples']:
            point=[struct.unpack('<d',bytes.fromhex(v))[0] for v in item['position_f64']];item['motion_delta_f64']=[f64(point[i]-last[i]) for i in range(2)];last=point
        previous['phase_f64']=f64(96.07317606608045);row['phase_f64']=f64(math.nextafter(96.07317606608045,math.inf));route['final_position']=last
        capture=next(x for x in report['capture_records'] if x['capture']=='door-pose-2-end.png');capture.update(actor_position=last,actor_position_f64=row['position_f64'][:])
        return report,route,row,previous

    def test_actual_two_real32_ulp_contact_jitter_with_one_real64_ulp_phase_is_bounded(self):
        report,_,_,_=self.jitter_case();result=self.accepted(report)
        self.assertEqual(result['route_results']['door-pose-2']['idle_contact_jitter_ticks'],1)

    def test_contact_jitter_beyond_two_coordinate_ulp_is_rejected(self):
        report,_,_,_=self.jitter_case(-.0000457763671875)
        with self.assertRaises(ValueError):self.validate(report)

    def test_contact_jitter_three_real64_ulp_phase_drift_is_rejected(self):
        import math
        report,_,row,_=self.jitter_case();phase=96.07317606608045
        for _ in range(3):phase=math.nextafter(phase,math.inf)
        row['phase_f64']=f64(phase)
        with self.assertRaises(ValueError):self.validate(report)

    def test_contact_jitter_does_not_accept_an_unrelated_or_wrong_normal(self):
        for normal in [[1,0],[0,0],[1,1]]:
            report,_,row,_=self.jitter_case();row['collision_normals_f64']=[[f64(v) for v in normal]]
            with self.subTest(normal=normal),self.assertRaises(ValueError):self.validate(report)

    def test_new_door_phase_must_be_finite_nonnegative_and_inside_walk_duration(self):
        for value in [-1,200,float('inf'),float('nan')]:
            report,_,row,_=self.case();row['phase_f64']=f64(value)
            with self.subTest(value=value),self.assertRaises(ValueError):self.validate(report)
        report,_,row,previous=self.case();previous['phase_f64']=f64(-1);row['phase_f64']=f64(0)
        with self.assertRaises(ValueError):self.validate(report)


class SpatialActualTickClockTests(unittest.TestCase):
    def setUp(self):
        self.fixture=SpatialReportTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)

    def validate(self,report):
        o=self.fixture
        return importlib.import_module('all_actions_evidence').spatial_report(o.repo,o.contract,report,o.profiles,o.evidence)

    def accepted(self,report):
        try:return self.validate(report)
        except ValueError as error:self.fail('Causal actual tick observation rejected: '+str(error))

    def test_jitter_fix_can_lead_real_wall_by_one_point_six_ticks(self):
        report=copy.deepcopy(self.fixture.report);route=report['routes'][0];start=report['capture_records'][0];end=report['capture_records'][1];count=end['physics_frame']-start['physics_frame'];game=count/60;wall=game-1.6/60
        end['ticks_usec']=start['ticks_usec']+round(wall*1e6)
        for row in route['physics_samples']:
            n=row['physics_frame']-start['physics_frame']
            if n<=count:row['ticks_usec']=start['ticks_usec']+round(wall*1e6*n/count)-1
        self.assertGreater(game,(end['ticks_usec']-start['ticks_usec'])/1e6+1/60)
        self.assertEqual(self.accepted(report)['routes'],14)

    def test_engine_clock_header_is_required_and_normal(self):
        for defect in ['missing','scale','tps','bool-tps','steps','negative-fix','nan-fix','infinite-fix','invalid-f64']:
            report=copy.deepcopy(self.fixture.report);clock=report['engine_clock']
            if defect=='missing':report.pop('engine_clock')
            if defect=='scale':clock['time_scale_f64']=f64(.5)
            if defect=='tps':clock['physics_ticks_per_second']=30
            if defect=='bool-tps':clock['physics_ticks_per_second']=True
            if defect=='steps':clock['max_physics_steps_per_frame']=16
            if defect=='negative-fix':clock['physics_jitter_fix_f64']=f64(-.01)
            if defect=='nan-fix':clock['physics_jitter_fix_f64']=f64(float('nan'))
            if defect=='infinite-fix':clock['physics_jitter_fix_f64']=f64(float('inf'))
            if defect=='invalid-f64':clock['time_scale_f64']=True
            with self.subTest(defect=defect),self.assertRaises(ValueError):self.validate(report)

    def test_actual_physics_wall_ticks_cannot_be_missing_or_reused(self):
        for defect in ['missing','zero','bool','same','backward','cross-route']:
            report=copy.deepcopy(self.fixture.report);rows=report['routes'][0]['physics_samples'];row=rows[2]
            if defect=='missing':row.pop('ticks_usec')
            if defect=='zero':row['ticks_usec']=0
            if defect=='bool':row['ticks_usec']=True
            if defect=='same':row['ticks_usec']=rows[1]['ticks_usec']
            if defect=='backward':row['ticks_usec']=rows[1]['ticks_usec']-1
            if defect=='cross-route':report['routes'][1]['physics_samples'][0]['ticks_usec']=rows[-1]['ticks_usec']
            with self.subTest(defect=defect),self.assertRaises(ValueError):self.validate(report)

    def test_matched_physics_tick_cannot_happen_after_the_png(self):
        report=copy.deepcopy(self.fixture.report);capture=report['capture_records'][1];rows=report['routes'][0]['physics_samples'];row=next(r for r in rows if r['physics_frame']==capture['physics_frame']);row['ticks_usec']=capture['ticks_usec']+1
        with self.assertRaises(ValueError):self.validate(report)

    def test_next_actual_physics_tick_must_not_precede_or_equal_the_png(self):
        for offset in [-1,0]:
            report=copy.deepcopy(self.fixture.report);capture=report['capture_records'][1];rows=report['routes'][0]['physics_samples'];row=next(r for r in rows if r['physics_frame']==capture['physics_frame']+1);row['ticks_usec']=capture['ticks_usec']+offset
            with self.subTest(offset=offset),self.assertRaises(ValueError):self.validate(report)

    def test_setup_capture_must_happen_before_first_actual_tick(self):
        report=copy.deepcopy(self.fixture.report);report['capture_records'][0]['ticks_usec']=report['routes'][0]['physics_samples'][0]['ticks_usec']
        with self.assertRaises(ValueError):self.validate(report)

    def test_capture_at_matched_tick_is_causal_and_at_next_tick_is_not(self):
        report=copy.deepcopy(self.fixture.report);capture=report['capture_records'][1];rows=report['routes'][0]['physics_samples'];row=next(r for r in rows if r['physics_frame']==capture['physics_frame']);capture['ticks_usec']=row['ticks_usec'];self.assertEqual(self.accepted(report)['routes'],14)

    def test_zero_or_one_collapsed_png_clocks_and_wrong_positions_stay_rejected(self):
        for defect in [0,1,'position']:
            report=copy.deepcopy(self.fixture.report)
            if defect=='position':report['capture_records'][1].update(actor_position=[999,999],actor_position_f64=[f64(999),f64(999)])
            else:
                for row in report['capture_records']:row['ticks_usec']=defect
            with self.subTest(defect=defect),self.assertRaises(ValueError):self.validate(report)
