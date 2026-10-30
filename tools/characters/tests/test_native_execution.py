"""Raw physics and journal evidence must substantiate native repetition claims."""
import copy
import math
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from all_actions_native import motion_evidence, one_shot_evidence

def encoded(value):return struct.pack('<d',value).hex()

class NativeExecutionTests(unittest.TestCase):
    def boundary_farm_rows(self):
        rows=[]
        for instance in range(1,11):
            elapsed=0
            for tick in range(1,62):
                elapsed+=(1/60)*1000
                done=elapsed>=1000
                rows.append({'instance_id':instance,'physics_frame':instance*100+tick,
                    'delta_f64':encoded(1/60),'elapsed_f64':encoded(0 if done else elapsed),
                    'focused':True,'journal_size':0,
                    'position_f64':[encoded(10),encoded(20)],
                    'state':{'action':'idle' if done else 'hoe','direction':'south'},
                    'texture':{'clip':'idle-south' if done else 'hoe-south',
                               'pose_id':'idle' if done else ('ready' if elapsed<500 else 'hit'),'rgba_sha256':'a'*64}})
        return rows

    def test_farm_does_not_complete_one_roundoff_before_exact_duration(self):
        import all_actions_native as native
        clip={'action_id':'hoe','direction':'south','pose_ids':['ready','hit'],'duration_ms':[500,500]}
        rows=self.boundary_farm_rows()
        self.assertLess(struct.unpack('<d',bytes.fromhex(rows[59]['elapsed_f64']))[0],1000)
        self.assertEqual(native.farm_physics_evidence(clip,1,rows,list(range(1,11)),[10,20],{'ready':'a'*64,'hit':'a'*64},'a'*64)['instances'],10)
        early=copy.deepcopy(rows);early[59]['state']['action']='idle';early[59]['texture']['clip']='idle-south'
        with self.assertRaises(ValueError):native.farm_physics_evidence(clip,1,early,list(range(1,11)),[10,20],{'ready':'a'*64,'hit':'a'*64},'a'*64)

    def test_timing_does_not_complete_one_roundoff_before_exact_duration(self):
        import all_actions_native as native
        case={'clip':'hoe-south','scenario':'replay-once','rate':1,'instance_id':1,
              'pose_ids':['ready','hit'],'durations_ms':[500,500],
              'initial_position_f64':[encoded(10),encoded(20)],'events':[],
              'journal':[{'instance_id':1,'event_id':'complete','at_ms':1000,'action':'hoe','direction':'south','loop':0}],
              'physics_samples':self.boundary_farm_rows()[:61]}
        self.assertTrue(native.farm_timing_evidence(case,{'ready':'a'*64,'hit':'a'*64},'a'*64)['completed'])

    def motion(self):
        clip={'action_id':'run','direction':'west','pose_ids':['r0','r1','r2','r3'],'duration_ms':[80]*4}
        rows=[];distance=0
        for i in range(256):
            distance+=1.35;phase=math.fmod(distance/108*1000,320)
            rows.append({'physics_frame':i+1,'delta_f64':encoded(1/60),
                'position_f64':[encoded(1600-distance),encoded(1600)],
                'step_distance_f64':encoded(1.35),'distance_f64':encoded(distance),'phase_f64':encoded(phase),
                'state':{'action':'run','direction':'west'},
                'texture':{'clip':'run-west','pose_id':clip['pose_ids'][int(phase//80)],'rgba_sha256':'a'*64}})
        return clip,rows

    def test_ten_cycles_are_computed_from_actual_distance_and_clock(self):
        clip,rows=self.motion()
        rgba={pose:'a'*64 for pose in clip['pose_ids']}
        self.assertGreaterEqual(motion_evidence(clip,108,rows,[1600,1600],rgba)['cycles'],10-1e-10)
        for defect in ['too-short','clock','physical-position','texture','wrong-timed-pose']:
            with self.subTest(defect=defect):
                bad=copy.deepcopy(rows)
                if defect=='too-short':bad=bad[:100]
                if defect=='clock':bad[3]['phase_f64']=encoded(0)
                if defect=='physical-position':bad[3]['position_f64'][0]=encoded(900)
                if defect=='texture':bad[3]['texture']['rgba_sha256']='b'*64
                if defect=='wrong-timed-pose':bad[3]['texture']['pose_id']='r3'
                with self.assertRaises(ValueError):motion_evidence(clip,108,bad,[1600,1600],rgba)

    def test_contact_and_completion_must_occur_once_per_unique_instance(self):
        clip={'action_id':'hoe','direction':'south','pose_ids':['ready','hit'],'duration_ms':[200,300]}
        events=[{'event_id':'contact','at_ms':200,'pose_id':'hit'}];journal=[]
        for instance in range(1,11):
            common={'instance_id':instance,'action':'hoe','direction':'south','loop':0}
            journal.extend([{**common,**events[0]},{**common,'event_id':'complete','at_ms':500}])
        self.assertEqual(one_shot_evidence(clip,events,journal,list(range(1,11)))['complete_count'],10)
        for defect in ['duplicate','missing','wrong-time','reused-instance']:
            with self.subTest(defect=defect):
                bad=copy.deepcopy(journal);ids=list(range(1,11))
                if defect=='duplicate':bad.append(bad[-1])
                if defect=='missing':bad.pop(0)
                if defect=='wrong-time':bad[0]['at_ms']=199
                if defect=='reused-instance':ids[-1]=ids[0]
                with self.assertRaises(ValueError):one_shot_evidence(clip,events,bad,ids)

    def test_farm_physics_must_substantiate_clock_texture_and_stationary_position(self):
        import all_actions_native as native
        self.assertTrue(hasattr(native,'farm_physics_evidence'))
        clip={'action_id':'hoe','direction':'south','pose_ids':['ready','hit'],'duration_ms':[200,300]}
        rows=[]
        for instance in range(1,11):
            for tick in range(1,6):
                elapsed=tick*100;done=elapsed==500;pose='ready' if elapsed<200 else 'hit'
                rows.append({'instance_id':instance,'physics_frame':instance*10+tick,'delta_f64':encoded(.1),
                    'elapsed_f64':encoded(0 if done else elapsed),
                    'position_f64':[encoded(10),encoded(20)],
                    'state':{'action':'idle' if done else 'hoe','direction':'south'},
                    'texture':{'clip':'idle-south' if done else 'hoe-south','pose_id':'idle' if done else pose,'rgba_sha256':'a'*64}})
        args=(clip,1,rows,list(range(1,11)),[10,20],{'ready':'a'*64,'hit':'a'*64},'a'*64)
        self.assertEqual(native.farm_physics_evidence(*args)['instances'],10)
        for defect in ['clock','moving','texture','missing-completion','gap']:
            with self.subTest(defect=defect):
                bad=copy.deepcopy(rows)
                if defect=='clock':bad[1]['elapsed_f64']=encoded(201)
                if defect=='moving':bad[1]['position_f64'][0]=encoded(11)
                if defect=='texture':bad[1]['texture']['pose_id']='ready'
                if defect=='missing-completion':bad.pop(4)
                if defect=='gap':bad[1]['physics_frame']+=1
                with self.assertRaises(ValueError):native.farm_physics_evidence(clip,1,bad,list(range(1,11)),[10,20],{'ready':'a'*64,'hit':'a'*64},'a'*64)

    def test_timing_scenario_checks_real_delta_not_declared_success(self):
        import all_actions_native as native
        self.assertTrue(hasattr(native,'farm_timing_evidence'))
        case={'clip':'hoe-south','scenario':'low-frame-rate','rate':1,'instance_id':1,
              'physics_ticks_per_second':5,'max_fps':5,'pose_ids':['ready','hit'],
              'durations_ms':[200,300],'initial_position_f64':[encoded(10),encoded(20)],
              'events':[{'event_id':'contact','at_ms':200,'pose_id':'hit'}],
              'journal':[{'instance_id':1,'event_id':'contact','at_ms':200,'pose_id':'hit','action':'hoe','direction':'south','loop':0},
                         {'instance_id':1,'event_id':'complete','at_ms':500,'action':'hoe','direction':'south','loop':0}], 'physics_samples':[]}
        for tick in range(1,4):
            done=tick==3
            case['physics_samples'].append({'physics_frame':tick,'delta_f64':encoded(.2),'elapsed_f64':encoded(0 if done else tick*200),'focused':True,
                'position_f64':[encoded(10),encoded(20)],'state':{'action':'idle' if done else 'hoe','direction':'south'},
                'texture':{'clip':'idle-south' if done else 'hoe-south','pose_id':'idle' if done else 'hit','rgba_sha256':'a'*64},'journal_size':tick})
        self.assertEqual(native.farm_timing_evidence(case,{'ready':'a'*64,'hit':'a'*64},'a'*64)['completed'],True)
        for defect in ['false-low-fps','clock','duplicate-event','moving']:
            with self.subTest(defect=defect):
                bad=copy.deepcopy(case)
                if defect=='false-low-fps':bad['physics_samples'][0]['delta_f64']=encoded(1/60)
                if defect=='clock':bad['physics_samples'][0]['elapsed_f64']=encoded(100)
                if defect=='duplicate-event':bad['journal'].append(bad['journal'][-1])
                if defect=='moving':bad['physics_samples'][0]['position_f64'][0]=encoded(11)
                with self.assertRaises(ValueError):native.farm_timing_evidence(bad,{'ready':'a'*64,'hit':'a'*64},'a'*64)

    def test_transitions_bind_states_textures_and_actual_stable_idle(self):
        import all_actions_native as native
        self.assertTrue(hasattr(native,'transition_evidence'))
        def state(action):return {'action':action,'direction':'west'}
        def texture(action):return {'clip':action+'-west','pose_id':action+'0','rgba_sha256':'a'*64}
        transition={'id':'walk-west-to-run-west','source':{'world_state':state('walk'),'texture':texture('walk')},
            'target':{'world_state':state('run'),'texture':texture('run')},'journal':[],'physics_samples':[]}
        for tick in range(7):
            action='idle' if tick<6 else 'run'
            transition['physics_samples'].append({'physics_frame':tick+1,'delta_f64':encoded(1/60),
                'state':state(action),'texture':texture(action),'position_f64':[encoded(10),encoded(20)],
                'pending_locomotion_action':'run' if tick<6 else '', 'phase_f64':encoded(0),
                'stable_remaining_f64':encoded(100-tick*1000/60)})
        profiles={a+'-west':{'rgba':{a+'0':'a'*64},'duration_ms':[300],'events':[]} for a in ['idle','walk','run']}
        self.assertEqual(native.transition_evidence([transition['id']],[transition],profiles,100)['transition_count'],1)
        for defect in ['missing','wrong-texture','moving-idle','short-idle','timer']:
            with self.subTest(defect=defect):
                bad=copy.deepcopy(transition)
                if defect=='missing':bad['id']='other'
                if defect=='wrong-texture':bad['target']['texture']['rgba_sha256']='b'*64
                if defect=='moving-idle':bad['physics_samples'][2]['position_f64'][0]=encoded(11)
                if defect=='short-idle':
                    bad['physics_samples'].pop(0)
                    for tick,row in enumerate(bad['physics_samples']):row['physics_frame']=tick+1
                if defect=='timer':bad['physics_samples'][2]['stable_remaining_f64']=encoded(30)
                with self.assertRaises(ValueError):native.transition_evidence([transition['id']],[bad],profiles,100)
