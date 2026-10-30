"""Raw execution checks for full-package native evidence (not art approval).

Capture/receipt integration is under construction. These checks recompute
physics-driven repetition and event multiplicity instead of trusting counts.
"""
import math
import struct
from build_contract import require


def number64(value):
    require(isinstance(value,str) and len(value)==16,'Invalid binary64 evidence')
    try: result=struct.unpack('<d',bytes.fromhex(value))[0]
    except (ValueError,struct.error) as error:raise ValueError('Invalid binary64 evidence') from error
    require(math.isfinite(result),'Non-finite binary64 evidence')
    return result


def motion_evidence(clip,base_speed,rows,initial_position,expected_rgba):
    require(clip['action_id'] in ['walk','run'] and type(base_speed) in [int,float]
            and math.isfinite(base_speed) and base_speed>0,'Invalid native motion profile')
    require(isinstance(rows,list) and rows,'Missing native physics samples')
    duration=sum(clip['duration_ms']);require(duration>0,'Invalid native clip duration')
    key=clip['action_id']+'-'+clip['direction'];previous_phase=0;distance=0;seen=set()
    previous_position=initial_position;last_frame=-1;elapsed=0
    for row in rows:
        frame=row['physics_frame']
        require(type(frame) is int and frame>last_frame,'Repeated/out-of-order physics frame')
        if last_frame>=0:require(frame==last_frame+1,'Missing physics frame')
        last_frame=frame
        delta=number64(row['delta_f64']);require(delta>0,'Nonpositive actual physics delta');elapsed+=delta
        moved=number64(row['step_distance_f64']);require(moved>=0,'Negative movement distance')
        position=[number64(v) for v in row['position_f64']]
        require(len(position)==2 and abs(math.dist(position,previous_position)-moved)<1e-5,'Position disagrees with measured movement')
        previous_position=position;distance+=moved
        require(abs(number64(row['distance_f64'])-distance)<1e-6,'Cumulative actual distance differs')
        phase=number64(row['phase_f64']);expected=(previous_phase+moved/base_speed*1000)%duration
        require(abs(math.remainder(phase-expected,duration))<1e-6,'Clock is not driven by actual distance')
        previous_phase=phase
        state=row['state'];texture=row['texture']
        if state['action']=='idle' and moved==0 and distance==0:continue
        require(state['action']==clip['action_id'] and state['direction']==clip['direction'],'Wrong active native action')
        remaining=phase;index=0
        for index,length in enumerate(clip['duration_ms']):
            if remaining<length:break
            remaining-=length
        pose=clip['pose_ids'][index]
        require(texture.get('clip')==key and texture.get('pose_id')==pose
                and texture.get('rgba_sha256')==expected_rgba.get(pose),'Unbound or wrongly timed actual GPU texture')
        seen.add(texture['pose_id'])
    cycles=distance/base_speed*1000/duration
    require(cycles>=10-1e-9,'Fewer than ten actual world cycles')
    require(seen==set(clip['pose_ids']),'Native world poses missing')
    return {'cycles':cycles,'distance':distance,'physics_seconds':elapsed,'observed_pose_ids':sorted(seen)}


def one_shot_evidence(clip,events,journal,instances):
    require(clip['action_id'] in ['hoe','water','harvest'],'Not a one-shot action')
    require(isinstance(instances,list) and len(instances)>=10 and all(type(v) is int and v>0 for v in instances)
            and len(set(instances))==len(instances),'Ten unique native instances required')
    expected=[(e['event_id'],e['at_ms'],e['pose_id']) for e in events]+[('complete',sum(clip['duration_ms']),None)]
    selected={instance:[] for instance in instances}
    for row in journal:
        if row.get('instance_id') not in selected:continue
        require(row.get('action')==clip['action_id'] and row.get('direction')==clip['direction']
                and row.get('loop')==0,'Native event belongs to wrong clip/loop')
        selected[row['instance_id']].append((row['event_id'],row['at_ms'],row.get('pose_id')))
    require(all(rows==expected for rows in selected.values()),'Missing/duplicate/out-of-order native event or completion')
    return {'instance_count':len(instances),'complete_count':len(instances),'events_per_instance':len(expected)}


def farm_physics_evidence(clip,rate,rows,instances,initial_position,expected_rgba,idle_rgba):
    """Recompute each one-shot clock from actual ticks, independent of journal."""
    require(clip['action_id'] in ['hoe','water','harvest'] and type(rate) in [int,float]
            and math.isfinite(rate) and rate>0,'Invalid farm physics profile')
    require(len(instances)>=10 and len(set(instances))==len(instances),'Ten distinct farm instances required')
    grouped={instance:[] for instance in instances};key=clip['action_id']+'-'+clip['direction']
    for row in rows:
        require(row.get('instance_id') in grouped,'Unbound farm instance')
        grouped[row['instance_id']].append(row)
    duration=sum(clip['duration_ms']);observed=set()
    for instance,samples in grouped.items():
        require(bool(samples),'Missing farm physics instance')
        elapsed=0;last_frame=None;completed=False
        for row in samples:
            require(not completed,'Farm physics continued beyond completion')
            frame=row['physics_frame']
            require(type(frame) is int and (last_frame is None or frame==last_frame+1),'Missing/duplicate farm physics frame')
            last_frame=frame
            delta=number64(row['delta_f64']);require(delta>0,'Invalid farm physics delta')
            elapsed+=delta*1000*rate
            position=[number64(value) for value in row['position_f64']]
            require(len(position)==2 and math.dist(position,initial_position)<1e-6,'Stationary farm actor moved')
            texture=row['texture'];state=row['state']
            require(state['direction']==clip['direction'],'Farm direction changed')
            if elapsed>=duration:
                require(state['action']=='idle' and texture.get('clip')=='idle-'+clip['direction']
                        and texture.get('rgba_sha256')==idle_rgba,'Farm completion did not install canonical idle')
                completed=True;continue
            require(state['action']==clip['action_id'] and abs(number64(row['elapsed_f64'])-elapsed)<1e-6,
                    'Farm clock disagrees with actual physics delta/rate')
            remaining=elapsed;index=0
            for index,length in enumerate(clip['duration_ms']):
                if remaining<length:break
                remaining-=length
            pose=clip['pose_ids'][index]
            require(texture.get('clip')==key and texture.get('pose_id')==pose
                    and texture.get('rgba_sha256')==expected_rgba.get(pose),'Farm GPU texture differs from actual timed pose')
            observed.add(pose)
        require(completed,'Farm physics completion missing')
    require(observed==set(clip['pose_ids']),'Farm poses missing from actual physics')
    return {'instances':len(instances),'physics_samples':len(rows),'observed_pose_ids':sorted(observed)}


def farm_timing_evidence(case,expected_rgba,idle_rgba):
    """One explicitly modified native timing scenario, never a ten-run receipt."""
    action,direction=case['clip'].split('-');scenario=case['scenario'];rate=case['rate']
    require(action in ['hoe','water','harvest'] and scenario in
            ['low-frame-rate','focus-pause','playback-rate','replay-once'],'Unknown native timing scenario')
    require(rate==(2 if scenario=='playback-rate' else 1),'Wrong timing scenario rate')
    if scenario=='low-frame-rate':
        require(case['physics_ticks_per_second']==5 and case['max_fps']==5,'Low-frame-rate setup missing')
    rows=case['physics_samples'];require(bool(rows),'Missing actual timing physics')
    initial=[number64(v) for v in case['initial_position_f64']]
    elapsed=0;last=None;paused=[];completed=False;duration=sum(case['durations_ms'])
    for row in rows:
        require(not completed,'Timing instance contains post-completion ticks')
        frame=row['physics_frame'];require(type(frame) is int and (last is None or frame==last+1),'Timing physics gap')
        last=frame;delta=number64(row['delta_f64']);require(delta>0,'Timing delta must be actual positive')
        if scenario=='low-frame-rate':require(abs(delta-.2)<1e-6,'Not actual low-frame-rate physics')
        require(math.dist([number64(v) for v in row['position_f64']],initial)<1e-6,'Timing farm actor moved')
        require(type(row['focused']) is bool,'Missing actual logical focus state')
        if not row['focused']:
            require(scenario=='focus-pause','Unexpected inactive timing sample');paused.append(row)
        else:elapsed+=delta*1000*rate
        texture=row['texture'];state=row['state'];require(state['direction']==direction,'Timing direction changed')
        if elapsed>=duration:
            require(state['action']=='idle' and texture.get('clip')=='idle-'+direction
                    and texture.get('rgba_sha256')==idle_rgba,'Timing did not end on canonical idle')
            completed=True;continue
        require(state['action']==action and abs(number64(row['elapsed_f64'])-elapsed)<1e-6,
                'Timing clock disagrees with actual delta/focus/rate')
        remaining=elapsed;index=0
        for index,length in enumerate(case['durations_ms']):
            if remaining<length:break
            remaining-=length
        pose=case['pose_ids'][index]
        require(texture.get('clip')==case['clip'] and texture.get('pose_id')==pose
                and texture.get('rgba_sha256')==expected_rgba.get(pose),'Timing actual GPU pose differs')
    require(completed,'Timing did not complete')
    if scenario=='focus-pause':
        require(len(paused)>=4 and len({r['journal_size'] for r in paused})==1,'Focus pause missing or emitted events')
    expected=[(e['event_id'],e['at_ms'],e['pose_id']) for e in case['events']]+[('complete',duration,None)]
    actual=[]
    for row in case['journal']:
        require(row.get('instance_id')==case['instance_id'] and row.get('action')==action
                and row.get('direction')==direction and row.get('loop')==0,'Timing journal instance mismatch')
        actual.append((row['event_id'],row['at_ms'],row.get('pose_id')))
    require(actual==expected,'Timing event/completion missing or repeated')
    return {'scenario':scenario,'completed':True,'physics_samples':len(rows),'paused_ticks':len(paused)}


def transition_evidence(expected,transitions,profiles,stable_ms):
    """Check actual transition state/texture chains and distance-free stable idle."""
    require(len(expected)==len(set(expected)) and len(transitions)==len(expected)
            and {row['id'] for row in transitions}==set(expected),'Transition set missing/duplicated')
    stable_count=0;physics_count=0
    def bound(state,texture):
        key=state['action']+'-'+state['direction']
        require(key in profiles and texture.get('clip')==key
                and texture.get('rgba_sha256')==profiles[key]['rgba'].get(texture.get('pose_id'))
                and texture.get('pose_id') in profiles[key]['rgba'],'Transition actual state/texture differs')
        return key
    for transition in transitions:
        source,target=transition['id'].split('-to-');source_action=source.split('-')[0];target_action=target.split('-')[0]
        require(bound(transition['source']['world_state'],transition['source']['texture'])==source
                and bound(transition['target']['world_state'],transition['target']['texture'])==target,
                'Transition endpoints differ')
        samples=transition['physics_samples'];require(bool(samples),'Missing transition physics')
        last=None;idle=[]
        for row in samples:
            frame=row['physics_frame'];require(type(frame) is int and (last is None or frame==last+1),'Transition physics gap')
            last=frame;delta=number64(row['delta_f64']);require(delta>0,'Invalid transition physics delta')
            bound(row['state'],row['texture']);physics_count+=1
            if row['pending_locomotion_action']:
                require({source_action,target_action}=={'walk','run'} and source.split('-')[1]==target.split('-')[1]
                        and row['pending_locomotion_action']==target_action and row['state']['action']=='idle'
                        and number64(row['phase_f64'])==0,'Unexpected stable-idle transition state')
                idle.append(row)
        if {source_action,target_action}=={'walk','run'}:
            require(bool(idle) and abs(number64(idle[0]['stable_remaining_f64'])-stable_ms)<1e-6
                    and sum(number64(row['delta_f64'])*1000 for row in idle)>=stable_ms-1e-6,
                    'Stable idle duration missing/short')
            origin=[number64(v) for v in idle[0]['position_f64']];previous=stable_ms
            for index,row in enumerate(idle):
                require(math.dist(origin,[number64(v) for v in row['position_f64']])<1e-6,'Actor moved during stable idle')
                remaining=number64(row['stable_remaining_f64'])
                if index:require(abs(remaining-(previous-number64(row['delta_f64'])*1000))<1e-6,'Stable timer disagrees with actual delta')
                previous=remaining
            stable_count+=1
        if source_action in ['hoe','water','harvest'] or target_action in ['hoe','water','harvest']:
            farm=source if source_action in ['hoe','water','harvest'] else target
            config=profiles[farm];from_farm=farm==source
            initial=number64(transition['source']['world_elapsed_f64']) if from_farm else -1
            final=sum(config['duration_ms']) if from_farm else number64(transition['target']['world_elapsed_f64'])
            events=[(e['event_id'],e['at_ms'],e['pose_id']) for e in config['events'] if initial<e['at_ms']<=final]
            if from_farm:events.append(('complete',sum(config['duration_ms']),None))
            journal=transition['journal'];instance=transition['source' if from_farm else 'target']['world_state']['instance_id']
            action,direction=farm.split('-');actual=[]
            for row in journal:
                require(row.get('instance_id')==instance and row.get('action')==action and row.get('direction')==direction
                        and row.get('loop')==0,'Transition event instance mismatch')
                actual.append((row['event_id'],row['at_ms'],row.get('pose_id')))
            require(actual==events,'Transition event missing/repeated')
        else:require(not transition['journal'],'Unexpected locomotion transition event')
    return {'transition_count':len(transitions),'stable_idle_transitions':stable_count,'physics_samples':physics_count}
