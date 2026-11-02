"""Recompute bounded native observations; never infer art or user acceptance.

A complete input snapshot and raw records, rather than producer check counts,
are the authority. Synthetic package evidence remains tool evidence only.
"""
import functools
import math
from all_actions_native import number64
from build_contract import require


def contract_errors(function):
    @functools.wraps(function)
    def checked(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except (KeyError, TypeError, IndexError, AttributeError, OverflowError) as error:
            raise ValueError('Malformed native observation: '+str(error)) from error
    return checked


def directional_step(previous, position, direction):
    dx,dy=position[0]-previous[0],position[1]-previous[1]
    vx,vy={'south':(0,1),'west':(-1,0),'east':(1,0),'north':(0,-1)}[direction]
    require(abs(dx*vy-dy*vx)<1e-5 and dx*vx+dy*vy>=-1e-5,
            'Actual physical movement direction differs from bound clip')


def focus_span(rows):
    longest=current=0
    for row in rows:
        current=current+1 if row['focused'] is False else 0
        longest=max(longest,current)
    require(longest>=4, 'Four consecutive actual paused physics ticks required')


def bound_texture(texture, profiles, clip=None):
    require(isinstance(texture, dict), 'Missing actual GPU texture')
    key=texture.get('clip')
    require(key in profiles and (clip is None or key==clip)
            and texture.get('pose_id') in profiles[key]['rgba']
            and texture.get('rgba_sha256')==profiles[key]['rgba'][texture['pose_id']],
            'Actual GPU texture differs from bound clip/pose/RGBA')
    return key


def timed_pose(clip, phase):
    require(type(phase) in [int,float] and math.isfinite(phase)
            and 0<=phase<sum(clip['duration_ms']), 'Actual phase outside clip range')
    remaining=phase
    for pose, duration in zip(clip['pose_ids'], clip['duration_ms']):
        if remaining<duration:
            return pose
        remaining-=duration
    raise ValueError('Native phase outside clip duration')


@contract_errors
def locomotion_timing_evidence(case, profiles, base_speed, default_factor):
    """Distance-clock scenarios, including two uninterrupted restart segments."""
    key=case['clip'];clip=profiles[key];action=clip['action_id'];direction=clip['direction']
    scenario=case['scenario']
    require(action in ['walk','run'] and scenario in
            ['low-frame-rate','focus-pause','playback-rate','replay-once'], 'Unknown locomotion timing scenario')
    require(case['case']==key+'/'+scenario and case['pose_ids']==clip['pose_ids']
            and case['durations_ms']==clip['duration_ms'], 'Locomotion timing clip/pose/duration mismatch')
    factor=1.0 if scenario=='playback-rate' else default_factor
    require(case['base_world_speed']==base_speed and case['speed_factor']==factor,
            'Locomotion timing public speed differs')
    if scenario=='low-frame-rate':
        require(case['physics_ticks_per_second']==5 and case['max_fps']==5, 'Low FPS setup missing')
    segments=2 if scenario=='replay-once' else 1
    require(type(case['segments']) is int and case['segments']==segments and not case['journal'],
            'Locomotion segments/events differ')
    rows=case['physics_samples'];require(isinstance(rows,list) and rows, 'Missing locomotion timing physics')
    previous=[number64(v) for v in case['initial_position_f64']]
    require(len(previous)==2, 'Invalid initial position')
    phase=number64(case['initial_phase_f64']);require(phase==0, 'Initial phase differs')
    duration=sum(clip['duration_ms']);distance=0;last=None;current=1;paused=0
    moved_by_segment=[0.0]*segments;idle_ticks=[0]*segments
    for row in rows:
        frame=row['physics_frame'];require(type(frame) is int and (last is None or frame==last+1),
                                            'Locomotion timing physics gap')
        last=frame;segment=row['segment']
        require(type(segment) is int and 1<=segment<=segments and segment in [current,current+1], 'Wrong timing segment')
        if segment!=current:
            require(idle_ticks[current-1]>=3, 'Restart did not release to canonical idle')
            current=segment
        require(row['case']==case['case'], 'Timing row belongs to another case')
        delta=number64(row['delta_f64']);require(delta>0, 'Invalid actual timing delta')
        if scenario=='low-frame-rate':require(abs(delta-.2)<1e-6, 'Not actual low FPS physics')
        require(type(row['focused']) is bool, 'Invalid actual focus state')
        require(abs(number64(row['speed_factor_f64'])-factor)<1e-12, 'Actual public speed differs')
        moved=number64(row['step_distance_f64']);position=[number64(v) for v in row['position_f64']]
        require(len(position)==2 and moved>=0 and abs(math.dist(position,previous)-moved)<1e-5,
                'Timing actual position/distance differs')
        directional_step(previous,position,direction)
        previous=position;distance+=moved
        require(abs(number64(row['distance_f64'])-distance)<1e-6, 'Timing cumulative distance differs')
        expected=(phase+moved/base_speed*1000)%duration;actual=number64(row['phase_f64'])
        require(abs(math.remainder(actual-expected,duration))<1e-6, 'Actual distance-driven phase differs')
        require(0<=actual<duration, 'Actual phase outside clip range')
        phase=actual;state=row['state'];require(state['direction']==direction, 'Timing direction changed')
        require(row['slide_collisions']==0, 'Timing lane collision')
        if not row['focused']:
            require(scenario=='focus-pause' and moved==0, 'Focus pause moved actor');paused+=1
        key_actual=bound_texture(row['texture'],profiles)
        if state['action']=='idle':
            require(moved==0 and key_actual=='idle-'+direction, 'Release did not install canonical idle')
            idle_ticks[segment-1]+=1
        else:
            require(state['action']==action and key_actual==key and row['texture']['pose_id']==timed_pose(clip,phase),
                    'Locomotion actual GPU pose has wrong timing')
            if row['focused']:
                require(abs(moved-base_speed*factor*delta)<1e-4, 'Actual speed differs from public factor')
            moved_by_segment[segment-1]+=moved
    cycles=[d/base_speed*1000/duration for d in moved_by_segment]
    require(current==segments and all(c>=2-1e-9 for c in cycles), 'Each segment requires two actual cycles')
    require(all(v>=3 for v in idle_ticks), 'Timing does not end in released canonical idle')
    if scenario=='focus-pause':active_focus_pause(rows,key)
    return {'scenario':scenario,'segments':segments,'cycles_per_segment':cycles,
            'physics_samples':len(rows),'paused_ticks':paused}


def png_inventory(evidence, report):
    from pathlib import Path
    from PIL import Image
    from build_contract import safe_file, digest
    hashes=report.get('output_hashes',{})
    require(isinstance(hashes,dict), 'Invalid native PNG inventory')
    actual={p.relative_to(evidence).as_posix() for p in Path(evidence).rglob('*.png')}
    require(actual==set(hashes), 'Native PNG inventory differs')
    for name, expected in hashes.items():
        path=safe_file(evidence,name)
        require(digest(path)==expected, 'Native PNG hash differs: '+name)
        try:
            with Image.open(path) as image:
                require(image.format=='PNG', 'Native capture is not PNG')
                image.verify()
        except OSError as error:
            raise ValueError('Invalid native PNG: '+name) from error
    return set(hashes)


def draw_continuity(rows):
    require(isinstance(rows,list) and rows, 'Missing rendered observations')
    last_frame=None;last_ticks=None
    for row in rows:
        frame=row['process_frame'];ticks=row['ticks_usec']
        require(type(frame) is int and (last_frame is None or frame==last_frame+1),
                'Missing/duplicate active rendered process frame')
        require(type(ticks) is int and (last_ticks is None or ticks>last_ticks), 'Unordered actual draw time')
        require(number64(row['process_delta_f64'])>0, 'Invalid actual process delta')
        last_frame,last_ticks=frame,ticks


def actual_state_texture(row, profiles, texture_field='texture', state_field='world_state'):
    state=row[state_field];key=state['action']+'-'+state['direction']
    bound_texture(row[texture_field],profiles,key)
    if state['action']!='idle':
        phase=number64(row['world_elapsed_f64'])
        require(row[texture_field]['pose_id']==timed_pose(profiles[key],phase), 'Draw texture disagrees with actual clock')
    return key


def ordered_physics(rows):
    previous=-1;frames=[]
    for row in rows:
        frame=row['physics_frame']
        require(type(frame) is int and frame>previous, 'Shared-player physics frames reused/out of order')
        previous=frame;frames.append(frame)
    return frames


def rendered_ledger_interval(clip, physics, draws, initial_position, clock_field, farm=False):
    """Link every draw to its actual tick, without assuming one draw per tick."""
    from bisect import bisect_right
    require(bool(physics) and bool(draws), 'Missing rendered/physics interval')
    frames=[r['physics_frame'] for r in physics];deltas=[number64(r['delta_f64']) for r in physics]
    maximum_delta=max(deltas);first,last=frames[0],frames[-1]
    first_draw=draws[0]['physics_frame'];last_draw=draws[-1]['physics_frame']
    require(type(first_draw) is int and type(last_draw) is int, 'Invalid draw physics frame')
    require(first-1<=first_draw<=last, 'Rendered interval starts outside actual physics')
    elapsed=sum(d for frame,d in zip(frames,deltas) if frame<=first_draw)
    require(elapsed<=number64(draws[0]['process_delta_f64'])+maximum_delta+1e-6,
            'Rendered interval omits its initial physics span')
    require(last_draw>=last if farm else last_draw==last, 'Rendered interval omits final physics span')
    previous=None
    for row in draws:
        frame=row['physics_frame'];require(type(frame) is int and frame>=first-1, 'Draw before actual interval')
        if previous is not None:
            require(frame>=previous, 'Rendered physics clock moved backwards')
            ticks=sum(d for tick,d in zip(frames,deltas) if previous<tick<=frame)
            if frame>last:ticks+=(frame-max(previous,last))*deltas[-1]
            require(ticks<=number64(row['process_delta_f64'])+maximum_delta+1e-6,
                    'Rendered delta cannot contain the declared physics span')
        previous=frame;index=bisect_right(frames,frame)-1
        point=[number64(v) for v in row['actor_position_f64']]
        if frame<first:
            require(farm and frame==first-1, 'Motion draw preceded actual active physics')
            require(math.dist(point,initial_position)<1e-6 and number64(row['world_elapsed_f64'])==0,
                    'Initial farm draw differs from actual setup')
            require(row['texture']['pose_id']==clip['pose_ids'][0], 'Initial farm draw is not first pose')
        else:
            actual=physics[min(index,len(physics)-1)]
            expected_point=[number64(v) for v in actual['position_f64']]
            require(len(point)==2 and math.dist(point,expected_point)<1e-6, 'Draw position differs from actual physics')
            if frame>last:
                require(farm and row['world_state']['action']=='idle', 'Draw continued outside active physics')
                require((frame-last)*deltas[-1]<=number64(row['process_delta_f64'])+maximum_delta+1e-6,
                        'Completion draw is detached from actual physics')
            else:
                require(row['texture']==actual['texture'] and all(row['world_state'][k]==actual['state'][k]
                        for k in ['action','direction']), 'Draw GPU/state differs from the same actual tick')
                if actual['state']['action']!='idle':
                    require(abs(number64(row['world_elapsed_f64'])-number64(actual[clock_field]))<1e-6,
                            'Draw clock differs from the same actual physics tick')
                    if 'instance_id' in actual['state']:
                        require(row['world_state']['instance_id']==actual['state']['instance_id'], 'Draw player instance differs from actual tick')
    return {'first_physics_frame':first,'last_physics_frame':last,
            'first_draw_physics_frame':first_draw,'last_draw_physics_frame':last_draw,'draws':len(draws)}


def active_focus_pause(rows, key):
    indices=[i for i,row in enumerate(rows) if row['focused'] is False]
    require(len(indices)>=4 and indices==list(range(indices[0],indices[-1]+1)),
            'Four consecutive active focus-pause ticks required')
    start,end=indices[0],indices[-1]
    require(start>0 and end<len(rows)-1, 'Active focus pause needs preceding and resumed movement')
    action,direction=key.split('-')
    block=rows[start-1:end+2]
    require(all(r['state']['action']==action and r['state']['direction']==direction
                and r['texture']['clip']==key for r in block), 'Focus pause occurred outside active locomotion')
    require(rows[start-1]['focused'] is True and rows[end+1]['focused'] is True
            and number64(rows[start-1]['step_distance_f64'])>0
            and number64(rows[end+1]['step_distance_f64'])>0, 'Active focus pause did not resume movement')
    original=rows[start-1]
    for row in rows[start:end+1]:
        require(row['phase_f64']==original['phase_f64'] and row['position_f64']==original['position_f64']
                and row['distance_f64']==original['distance_f64'] and row['texture']==original['texture'],
                'Active paused phase/position/GPU advanced')


@contract_errors
def world_evidence(contract, report, profiles, evidence):
    from all_actions_native import motion_evidence, farm_physics_evidence, one_shot_evidence
    require(contract.get('capture_every_rendered_frame') is True
            and report.get('capture_every_rendered_frame') is True, 'Every rendered frame capture required')
    pngs=png_inventory(evidence,report);motion={};farm={}
    motion_keys={k for k,p in profiles.items() if p.get('action_id') in ['walk','run']}
    farm_keys={k for k,p in profiles.items() if p.get('action_id') in ['hoe','water','harvest']}
    require(set(report['clips'])==motion_keys and set(report['farm_clips'])==farm_keys, 'World clip scope differs')
    physics=report['physics_samples'];farm_rows=report['farm_physics_samples']
    require(all(r['clip'] in motion_keys for r in physics)
            and all(r['clip'] in farm_keys for r in farm_rows), 'Unbound world physics clip')
    movement_frames=ordered_physics(physics);farming_frames=ordered_physics(farm_rows)
    require(not set(movement_frames)&set(farming_frames), 'Shared-player motion/farm physics tick reused')
    for key in motion_keys:
        clip=profiles[key];meta=report['clips'][key]
        require(meta['pose_ids']==clip['pose_ids'] and meta['durations_ms']==clip['duration_ms'], 'World motion pose/duration differs')
        speed=contract['runtime']['movement'][clip['action_id']]['base_world_speed']
        require(meta['base_world_speed']==speed, 'World base movement speed differs')
        rows=[r for r in physics if r['clip']==key]
        require(all(r['slide_collisions']==0 for r in rows), 'World open lane blocked')
        require(all(0<=number64(r['phase_f64'])<sum(clip['duration_ms']) for r in rows), 'Actual phase outside clip range')
        previous=[number64(v) for v in meta['initial_position_f64']]
        for row in rows:
            position=[number64(v) for v in row['position_f64']]
            directional_step(previous,position,clip['direction']);previous=position
        motion[key]=motion_evidence(clip,speed,rows,[number64(v) for v in meta['initial_position_f64']],clip['rgba'])
    for key in farm_keys:
        clip=profiles[key];meta=report['farm_clips'][key];runtime=contract['runtime']['clips'][key]
        require(meta['pose_ids']==clip['pose_ids'] and meta['durations_ms']==clip['duration_ms']
                and meta['events']==runtime['events'] and meta['playback_rate']==runtime['playback_rate'],
                'World farm pose/timing/event profile differs')
        idle=next(iter(profiles['idle-'+clip['direction']]['rgba'].values()))
        rows=[r for r in farm_rows if r['clip']==key]
        require(all(type(row['instance_id']) is int and row['instance_id'] in meta['instances']
                    and (row['state']['action']=='idle' or type(row['state']['instance_id']) is int
                         and row['state']['instance_id']==row['instance_id']) for row in rows),
                'Actual farm player instance differs from physics group')
        farm[key]=farm_physics_evidence(clip,runtime['playback_rate'],rows,meta['instances'],
                [number64(v) for v in meta['initial_position_f64']],clip['rgba'],idle)
        require(all(row.get('instance_id') in meta['instances'] for row in meta['journal']), 'Unbound extra farm world event')
        farm[key].update(one_shot_evidence(clip,runtime['events'],meta['journal'],meta['instances']))
    samples=report['samples'];require(isinstance(samples,list) and samples, 'Missing world rendered rows')
    used=set();groups={};endings={};previous_process=-1
    for row in samples:
        key=row['clip'];require(key in motion_keys|farm_keys, 'Unbound world draw clip')
        name=row.get('capture');require(name in pngs and name not in used, 'Missing/duplicate actual draw capture')
        used.add(name);require(type(row['process_frame']) is int and row['process_frame']>previous_process,
                               'World draw order differs');previous_process=row['process_frame']
        actual=actual_state_texture(row,profiles)
        if 'world_texture' in row:require(row['world_texture']==row['texture'], 'Actual world GPU identities differ')
        if row['mode']=='released-to-idle':
            require(key in motion_keys and actual=='idle-'+profiles[key]['direction'] and key not in endings,
                    'Missing matching ending idle');endings[key]=row;continue
        if key in motion_keys:
            require(row['mode']=='world-ten-cycles' and actual==key, 'Wrong active world motion draw')
            group=(key,None)
        else:
            require(row['mode']=='farm-world-ten-instances' and row['instance_id'] in report['farm_clips'][key]['instances'],
                    'Unbound farm draw instance')
            require(actual in [key,'idle-'+profiles[key]['direction']], 'Wrong active farm draw')
            require(type(row['instance_id']) is int and (actual!=key
                    or type(row['world_state']['instance_id']) is int
                    and row['world_state']['instance_id']==row['instance_id']),
                    'Actual farm player instance differs from draw group')
            group=(key,row['instance_id'])
        groups.setdefault(group,[]).append(row)
    require(set(endings)==motion_keys, 'World ending-idle captures missing')
    for key in motion_keys:
        rows=groups.get((key,None),[]);draw_continuity(rows)
        require({r['texture']['pose_id'] for r in rows}==set(profiles[key]['pose_ids']), 'Rendered world poses missing')
        ledger=[r for r in physics if r['clip']==key]
        initial=[number64(v) for v in report['clips'][key]['initial_position_f64']]
        motion[key]['rendered_interval']=rendered_ledger_interval(profiles[key],ledger,rows,initial,'phase_f64')
        ending=endings[key]
        require(ending['physics_frame']>ledger[-1]['physics_frame']
                and math.dist([number64(v) for v in ending['actor_position_f64']],
                              [number64(v) for v in ledger[-1]['position_f64']])<1e-6,
                'Ending idle is detached from actual motion/release')
    for key in farm_keys:
        farm[key]['rendered_instances']={}
        for instance in report['farm_clips'][key]['instances']:
            rows=groups.get((key,instance),[]);draw_continuity(rows)
            require({r['texture']['pose_id'] for r in rows if r['texture']['clip']==key}==set(profiles[key]['pose_ids']),
                    'Rendered farm instance poses missing')
            require(rows[-1]['texture']['clip']=='idle-'+profiles[key]['direction'], 'Farm draw completion idle missing')
            ledger=[r for r in farm_rows if r['clip']==key and r['instance_id']==instance]
            initial=[number64(v) for v in report['farm_clips'][key]['initial_position_f64']]
            farm[key]['rendered_instances'][str(instance)]=rendered_ledger_interval(profiles[key],ledger,rows,initial,'elapsed_f64',farm=True)
    require(pngs-used in [set(),{'lane-overview.png'}], 'PNG not bound to an actual draw')
    return {'motion':motion,'farm':farm,'captured_draws':len(used),'pngs':len(pngs)}


@contract_errors
def poses_evidence(contract, report, profiles, evidence):
    pngs=png_inventory(evidence,report);rows=report['samples']
    require(isinstance(rows,list) and rows, 'Missing actual pose observations')
    stopped={};panels={};used=set();world={};world_captured=set()
    for row in rows:
        key=row['clip'];require(key in profiles, 'Unbound pose observation clip')
        mode=row['mode'];clip=profiles[key]
        capture=row.get('capture')
        if capture is not None:
            require(capture in pngs and capture not in used, 'Missing/duplicate pose PNG capture');used.add(capture)
        if mode.startswith('stopped-') or mode=='panel-continuous':
            bound_texture(row['panel_texture'],profiles,key)
            phase=number64(row['panel_phase_f64']);pose=timed_pose(clip,phase)
            require(type(row['panel_pose']) is int and 0<=row['panel_pose']<len(clip['pose_ids'])
                    and clip['pose_ids'][row['panel_pose']]==pose and row['panel_texture']['pose_id']==pose,
                    'Actual panel GPU texture differs from index/clock')
            if mode.startswith('stopped-'):
                bg=mode.removeprefix('stopped-');require(bg in ['dark','light'], 'Unknown stopped background')
                identity=(key,bg,row['panel_pose']);require(identity not in stopped and capture is not None,
                                                         'Stopped pose missing/duplicated')
                require(abs(phase-sum(clip['duration_ms'][:row['panel_pose']]))<1e-6, 'Stopped phase differs')
                require(capture==f'stills/{key}-{bg}-{row["panel_pose"]}.png', 'Stopped PNG names differ from frozen plan')
                stopped[identity]=capture
            else:
                require(clip['action_id']!='idle', 'Unexpected idle continuous panel');panels.setdefault(key,[]).append(row)
        elif mode in ['world-continuous','world-idle']:
            actual=actual_state_texture(row,profiles,'world_texture')
            if mode=='world-idle':require(clip['action_id']=='idle' and actual==key, 'Wrong world idle GPU texture')
            if capture is not None and actual==key:
                index=clip['pose_ids'].index(row['world_texture']['pose_id'])
                require(capture==f'world/{key}-pose-{index}.png', 'World pose PNG names differ from actual GPU pose')
                world_captured.add((key,index))
            world.setdefault(key,[]).append(row)
        else:raise ValueError('Unknown pose observation mode')
    expected={(key,bg,i) for key,p in profiles.items() for bg in ['dark','light'] for i in range(len(p['pose_ids']))}
    require(set(stopped)==expected, 'Stopped pose/background coverage differs')
    active={k for k,p in profiles.items() if p['action_id']!='idle'}
    require(set(panels)==active, 'Continuous panel clips missing')
    cycles={}
    for key in active:
        samples=panels[key];draw_continuity(samples);clip=profiles[key];duration=sum(clip['duration_ms'])
        rate=contract['runtime']['clips'][key]['playback_rate']
        if clip['action_id'] in ['walk','run']:rate*=contract['runtime']['default_speed_factor']
        elapsed=0;previous=0;seen=set()
        for row in samples:
            delta=number64(row['process_delta_f64'])*1000*rate
            require(delta<duration, 'Ambiguous panel clock crossed an entire cycle in one draw')
            expected_phase=(previous+delta)%duration;phase=number64(row['panel_phase_f64'])
            require(abs(math.remainder(phase-expected_phase,duration))<1e-5, 'Panel phase differs from actual process delta/rate')
            elapsed+=delta;previous=phase
            require(type(row['unwrapped_ms']) in [int,float] and math.isfinite(row['unwrapped_ms'])
                    and abs(row['unwrapped_ms']-elapsed)<1e-4, 'Panel unwrapped duration differs from raw delta')
            seen.add(row['panel_texture']['pose_id'])
        require(elapsed>=duration*10-1e-5 and seen==set(clip['pose_ids']), 'Fewer than ten actual panel cycles/poses')
        cycles[key]=elapsed/duration
    require(set(contract['plan']['required_pngs'])<=pngs, 'Frozen pose PNG plan incomplete')
    require(world_captured=={(key,i) for key,p in profiles.items() for i in range(len(p['pose_ids']))}, 'Actual world pose PNG coverage incomplete')
    require(pngs-used in [set(),{'overview.png'}], 'PNG unbound to raw pose observation')
    return {'stopped_poses':len(stopped),'actual_pose_count':len(expected)//2,
            'panel_cycles':cycles,'pngs':len(pngs),
            'scope':'Dark/light stopped pose and process-clock panel observations. Ten physics world cycles verified separately.'}


def bound_profiles(repo, contract):
    from pathlib import Path
    import hashlib
    from PIL import Image
    from build_contract import read_json, safe_file, digest
    repo=Path(repo);manifest_path=safe_file(repo,contract['manifest']['manifest'],'art/characters/builds')
    require(digest(manifest_path)==contract['manifest']['sha256'], 'Actual manifest changed')
    manifest=read_json(manifest_path);outputs={row['file']:row for row in manifest['outputs']};profiles={}
    for key, clip in contract['plan']['clips'].items():
        profile=dict(clip);profile['rgba']={}
        for pose in clip['pose_ids']:
            relative=f'frames/{clip["action_id"]}/{clip["direction"]}/{pose}.png'
            require(relative in outputs, 'Missing actual bound pose output')
            row=outputs[relative];path=safe_file(manifest_path.parent,relative)
            require(digest(path)==row['sha256'], 'Actual output PNG changed')
            with Image.open(path) as image:
                rgba=image.convert('RGBA')
                require(list(rgba.size)==clip['canvas_px'], 'Actual output geometry differs')
                actual=hashlib.sha256(rgba.tobytes()).hexdigest()
            require(actual==row['rgba_sha256'], 'Actual output RGBA differs')
            profile['rgba'][pose]=actual
        profile['events']=contract['runtime']['clips'][key]['events']
        profiles[key]=profile
    return profiles


def same_json_value(actual, expected):
    """Godot may serialize integral JSON numbers as floats; bool is not a number."""
    if type(expected) in [int,float]:
        return type(actual) in [int,float] and math.isfinite(actual) and actual==expected
    if isinstance(expected,dict):
        return isinstance(actual,dict) and set(actual)==set(expected) and all(same_json_value(actual[k],v) for k,v in expected.items())
    if isinstance(expected,list):
        return isinstance(actual,list) and len(actual)==len(expected) and all(same_json_value(a,b) for a,b in zip(actual,expected))
    return type(actual) is type(expected) and actual==expected


@contract_errors
def loaded_input_binding(repo, contract, report):
    from pathlib import Path
    from build_contract import read_json, safe_file
    proof=report.get('loaded_input_binding')
    fields={'passed','full_package','actual_suite_path','catalog_sha256','manifest_binding',
            'runtime','producer_script','capture_scene'}
    require(isinstance(proof,dict) and set(proof)==fields and proof['passed'] is True
            and proof['full_package'] is True, 'Missing/rejected actual loaded input binding')
    require(proof['actual_suite_path']==str(Path(repo)/contract['suite'])
            and proof['catalog_sha256']==contract['files'][contract['suite']], 'Actual loaded suite differs from frozen inputs')
    manifest=read_json(safe_file(repo,contract['manifest']['manifest'],'art/characters/builds'))
    expected={**contract['manifest'],'recipe':manifest['recipe'],
              'recipe_sha256':manifest['inputs'][manifest['recipe']],'artifact_digest':manifest['artifact_digest']}
    require(proof['manifest_binding']==expected and expected['artifact_digest']==contract['artifact_digest'],
            'Actual loaded manifest/recipe/artifact differs')
    require(same_json_value(proof['runtime'],contract['runtime']), 'Actual loaded runtime differs')
    require(proof['producer_script']=='res://'+contract['observer_script'].removeprefix('godot2d/')
            and proof['capture_scene']==contract['capture_scene'], 'Actual producer script or capture scene differs')
    return proof


def gap_matrix(contract, observer, observed):
    plan=contract['plan'];poses=sum(len(p['pose_ids']) for p in plan['clips'].values())
    matrix={
        'poses':{'required':poses*2,'observed':observed.get('stopped_poses',0) if observer=='poses' else 0},
        'world':{'required':20,'observed':20 if observer=='world' else 0},
        'farm_timing':{'required':48,'observed':observed.get('timing_cases',0) if observer=='timing' else 0},
        'locomotion_timing':{'required':32,'observed':observed.get('timing_cases',0) if observer=='locomotion-timing' else 0},
        'transitions':{'required':len(plan['transitions']),'observed':observed.get('transition_count',0) if observer=='transitions' else 0},
        'spatial_raw':{'required':14,'observed':observed.get('routes',0) if observer=='spatial' else 0},
    }
    for row in matrix.values():row['missing']=row['required']-row['observed']
    return matrix


@contract_errors
def validate_observation(repo, evidence):
    """Validate one complete observer report against its actual full snapshot."""
    from pathlib import Path
    import all_actions_capture as capture
    from build_contract import digest, read_json, safe_file
    repo=Path(repo).resolve();evidence=Path(evidence).absolute()
    require(not any(p.is_symlink() for p in [evidence,*evidence.parents]), 'Evidence symlink forbidden')
    cp=safe_file(evidence,'input-contract.json');rp=safe_file(evidence,'report.json')
    contract_sha,report_sha=digest(cp),digest(rp)
    contract=read_json(cp)
    require(isinstance(contract,dict), 'Invalid native input contract object')
    if contract.get('suite_kind')=='coastal-body-character-review-v1':
        from body_review import verify_inputs as verify_body_inputs
        verify_body_inputs(repo,evidence)
    else:
        capture.verify_inputs(repo,evidence)
    report=read_json(rp)
    require(isinstance(report,dict) and report.get('input_contract_sha256')==contract_sha,
            'Report binds another frozen input contract')
    require(isinstance(report.get('renderer'),str) and report['renderer'] not in ['', 'headless'], 'Actual GPU observation required')
    checks=report.get('checks');require(isinstance(checks,dict) and checks
                                      and all(type(v) is bool and v for v in checks.values()), 'Producer reported failure')
    kinds={'poses':'coastal-registered-native-observation-v1','world':'coastal-registered-actions-world-observation-v1',
           'timing':'coastal-registered-farm-timing-observation-v1','locomotion-timing':'coastal-registered-locomotion-timing-observation-v1',
           'transitions':'coastal-registered-transition-observation-v1','spatial':'coastal-registered-harbor-spatial-observation-v1'}
    require(report.get('kind')==kinds[contract['observer']], 'Wrong observer report kind')
    loaded=loaded_input_binding(repo,contract,report)
    profiles=bound_profiles(repo,contract);observer=contract['observer']
    if observer=='locomotion-timing':
        require(report.get('kind')=='coastal-registered-locomotion-timing-observation-v1', 'Wrong observer report kind')
        expected={key+'/'+scenario for key,p in profiles.items() if p['action_id'] in ['walk','run']
                  for scenario in contract['plan']['time_scenarios'][key]}
        cases=report['cases'];require(isinstance(cases,list) and len(cases)==len(expected)
                                      and {c['case'] for c in cases}==expected, 'Locomotion timing cases missing/duplicated')
        results={}
        for case in cases:
            action=profiles[case['clip']]['action_id']
            results[case['case']]=locomotion_timing_evidence(case,profiles,
                    contract['runtime']['movement'][action]['base_world_speed'],contract['runtime']['default_speed_factor'])
        require(not png_inventory(evidence,report), 'Unexpected locomotion timing PNG inventory')
        observed={'timing_cases':len(results),'cases':results}
    elif observer=='world':
        require(report.get('kind')=='coastal-registered-actions-world-observation-v1', 'Wrong observer report kind')
        observed=world_evidence(contract,report,profiles,evidence)
    elif observer=='poses':
        require(report.get('kind')=='coastal-registered-native-observation-v1', 'Wrong observer report kind')
        observed=poses_evidence(contract,report,profiles,evidence)
    elif observer=='timing':
        require(report.get('kind')=='coastal-registered-farm-timing-observation-v1', 'Wrong observer report kind')
        observed=farm_timing_report(contract,report,profiles)
        require(not png_inventory(evidence,report), 'Unexpected farm timing PNG inventory')
    elif observer=='transitions':
        require(report.get('kind')=='coastal-registered-transition-observation-v1', 'Wrong observer report kind')
        observed=transition_report(contract,report,profiles,evidence)
    elif observer=='spatial':
        require(report.get('kind')=='coastal-registered-harbor-spatial-observation-v1', 'Wrong observer report kind')
        observed=spatial_report(repo,contract,report,profiles,evidence)
    else:raise ValueError('Unknown native observer')
    require(digest(cp)==contract_sha and digest(rp)==report_sha, 'Evidence changed during validation')
    for relative,expected in contract['files'].items():
        require(digest(safe_file(repo,relative))==expected, 'Actual input changed during validation')
    return {'kind':'coastal-all-actions-internal-observation-v1','schema_version':1,
            'status':'internal-observation-only','observer':observer,'passed':True,
            'scope':'Raw execution and bound PNG/texture observations only; synthetic assets prove tools only.',
            'artifact_digest':contract['artifact_digest'],'manifest':contract['manifest'],
            'suite':contract['suite'],'suite_sha256':contract['files'][contract['suite']],
            'input_contract_sha256':contract_sha,'report_sha256':report_sha,
            'validator_sha256':digest(__file__),'inputs_verified':len(contract['files']),
            'loaded_input_binding':loaded,'observed':observed,'gap_matrix':gap_matrix(contract,observer,observed),
            'art_acceptance':False,'physical_contact_acceptance':False,'spatial_visual_acceptance':False,
            'user_approval':False,'release_eligible':False}


@contract_errors
def farm_timing_report(contract, report, profiles):
    from all_actions_native import farm_timing_evidence
    expected={key+'/'+scenario for key,p in profiles.items() if p.get('action_id') in ['hoe','water','harvest']
              for scenario in contract['plan']['time_scenarios'][key]}
    cases=report['cases'];require(isinstance(cases,list) and len(cases)==len(expected)
                                  and {c['case'] for c in cases}==expected, 'Farm timing cases missing/duplicated')
    ids=set();results={}
    for case in cases:
        key=case['clip'];clip=profiles[key];config=contract['runtime']['clips'][key]
        require(case['case']==key+'/'+case['scenario'] and case['pose_ids']==clip['pose_ids']
                and case['durations_ms']==clip['duration_ms'] and case['events']==config['events'],
                'Farm timing pose/duration/events differ from actual runtime')
        instance=case['instance_id'];require(type(instance) is int and instance>0 and instance not in ids,
                                            'Farm timing instance reused');ids.add(instance)
        require(config['playback_rate']==1, 'Farm timing observer requires bound normal rate1')
        idle=next(iter(profiles['idle-'+clip['direction']]['rgba'].values()))
        require(all(row['case']==case['case'] and type(row['instance_id']) is int
                    and row['instance_id']==instance and (row['state']['action']=='idle'
                    or type(row['state']['instance_id']) is int and row['state']['instance_id']==instance)
                    for row in case['physics_samples']), 'Actual timing player instance differs from case')
        results[case['case']]=farm_timing_evidence(case,clip['rgba'],idle)
        if case['scenario']=='focus-pause':focus_span(case['physics_samples'])
    return {'scope':'farm-timing-only','timing_cases':len(results),'cases':results,
            'limits':'A fresh unique instance per scenario; ten repeated normal instances and locomotion timing are separate observations.'}


@contract_errors
def transition_report(contract, report, profiles, evidence):
    from all_actions_native import transition_evidence
    expected=contract['plan']['transitions'];transitions=report['transitions'];pngs=png_inventory(evidence,report)
    result=transition_evidence(expected,transitions,profiles,contract['runtime']['locomotion_transition']['duration_ms'])
    captures=set()
    for transition in transitions:
        name=transition['target'].get('capture')
        require(name=='transition-'+transition['id']+'.png' and name in pngs and name not in captures,
                'Transition endpoint PNG missing/duplicated')
        captures.add(name)
    require(pngs==captures, 'Unbound transition PNG')
    result['pngs']=len(pngs)
    return result


def spatial_plan(repo, contract):
    """Read only the bounded route declarations of the frozen observer script."""
    import re
    from build_contract import safe_file
    text=safe_file(repo,contract['observer_script'],'godot2d/tests/characters').read_text()
    routes={}
    for name,body in re.findall(r'await\s+inspect_route\("([^"]+)",\[(.*?)\]\)',text):
        points=[[float(x),float(y)] for x,y in re.findall(r'Vector2\(([-\d.]+),\s*([-\d.]+)\)',body)]
        require(name not in routes and len(points)==5, 'Unsupported frozen spatial route declaration')
        routes[name]={'setup':points[0],'waypoints':points,'type':'path'}
    settings=re.search(r'for setting in (\[.*?\]):',text,re.S)
    require(len(routes)==2 and settings is not None and re.search(r'for pose in range\(3\)',text),
            'Unknown frozen spatial observer plan')
    tools=re.findall(r'\{"id":"([^"]+)","position":Vector2\(([-\d.]+),\s*([-\d.]+)\),"facing":"([^"]+)"\}',settings.group(1))
    require(len(tools)==3, 'Unknown frozen spatial tool settings')
    for pose in range(3):routes['door-pose-'+str(pose)]={'setup':[209,190],'door_pose':pose,'type':'door'}
    for name,x,y,direction in tools:
        for action in ['hoe','water','harvest']:
            routes[name+'-'+action]={'setup':[float(x),float(y)],'clip':action+'-'+direction,'type':'tool'}
    require(len(routes)==14, 'Frozen spatial cases overlap')
    return routes


def finite_vector(value, length):
    require(isinstance(value,list) and len(value)==length
            and all(type(v) in [int,float] and math.isfinite(v) for v in value), 'Invalid actual transform/vector')
    return value


def _real32_ulp(value):
    """Spacing at a binary32 world coordinate, including zero/subnormals."""
    if value==0:return math.ldexp(1.0,-149)
    return math.ldexp(1.0,max(-149,math.frexp(abs(value))[1]-24))


def _binary64_vector(value):
    require(isinstance(value,list) and len(value)==2, 'Missing actual recovery vector')
    return [number64(v) for v in value]


def _door_idle_recovery(setting, row, previous, position, previous_phase):
    """Recognize bounded contact recovery, never requested walking travel.

    Normal separation has a strictly preserved/reset walking clock. The
    independent contact-jitter branch permits only two binary32 coordinate
    spacings and two binary64 clock spacings; it never widens the normal
    displacement or clock rules for a larger recovery.
    """
    require(setting['type']=='door', 'Idle spatial actor moved outside bounded door recovery')
    requested=_binary64_vector(row['requested_f64'])
    require(requested in [[0.0,0.0],[0.0,-1.0]], 'Door recovery requested input differs from frozen north/release plan')
    margin=number64(row['safe_margin_f64'])
    require(0<margin<=.08+_real32_ulp(.08), 'Door recovery safe margin differs from bounded real32 default')
    step=[position[i]-previous[i] for i in range(2)];distance=math.hypot(*step)
    require(0<distance<=margin, 'Door recovery exceeds actual safe margin')
    motion=_binary64_vector(row['motion_delta_f64'])
    require(math.dist(motion,step)<=1e-6, 'Door recovery motion delta differs from actual position change')
    # This is the exact walking-clock activation condition in the frozen
    # runtime. It is not a phase tolerance or an additional displacement bound.
    require(sum(step[i]*requested[i] for i in range(2))<=.001, 'Door idle recovery contains requested walking advancement')
    phase=number64(row['phase_f64'])
    require(previous_phase is not None, 'Door recovery lacks previous actual walking phase')
    colliders=row['colliders'];normals=row['collision_normals_f64']
    require(isinstance(colliders,list) and isinstance(normals,list) and len(colliders)==len(normals)
            and all(isinstance(c,str) for c in colliders), 'Door recovery collider/normal correspondence differs')
    suffix=('/HarborExterior/DepthSortedObjects/ExteriorDoor/DoorCollision' if setting['door_pose'] in [0,1]
            else '/HarborExterior/DepthSortedObjects/House/HouseLintel')
    angular_bound=4*_real32_ulp(1.0);parallel=[]
    for collider,normal in zip(colliders,normals):
        normal=_binary64_vector(normal);length=math.hypot(*normal)
        require(abs(length-1)<=angular_bound, 'Door recovery normal is not an actual unit normal')
        if collider.endswith(suffix):
            cross=abs(step[0]*normal[1]-step[1]*normal[0])
            if cross<=angular_bound*distance*length:
                parallel.append(sum(step[i]*normal[i] for i in range(2)))
    require(parallel, 'Door recovery step does not follow its corresponding allowed collision normal')
    unchanged=phase==previous_phase or phase==0
    if unchanged and any(dot>0 for dot in parallel):return 'normal-separation'
    coordinate_jitter=all(abs(step[i])<=2*max(_real32_ulp(previous[i]),_real32_ulp(position[i])) for i in range(2))
    clock_jitter=unchanged or abs(phase-previous_phase)<=2*max(math.ulp(phase),math.ulp(previous_phase))
    require(coordinate_jitter and clock_jitter, 'Door contact jitter exceeds two real32 coordinate or binary64 phase ULP')
    return 'contact-jitter'


@contract_errors
def spatial_report(repo, contract, report, profiles, evidence):
    clock=report.get('engine_clock')
    require(isinstance(clock,dict), 'Missing actual spatial Engine clock settings')
    require(type(clock['physics_ticks_per_second']) is int and clock['physics_ticks_per_second']==60
            and type(clock['max_physics_steps_per_frame']) is int and clock['max_physics_steps_per_frame']==8,
            'Actual spatial Engine physics configuration differs')
    require(number64(clock['time_scale_f64'])==1 and number64(clock['physics_jitter_fix_f64'])>=0,
            'Actual spatial Engine time scale/jitter configuration differs')
    plan=spatial_plan(repo,contract);routes=report['routes'];pngs=png_inventory(evidence,report)
    require(isinstance(routes,list) and len(routes)==len(plan) and {r['id'] for r in routes}==set(plan),
            'Spatial route scope missing/duplicated')
    max_speed=max(v['base_world_speed'] for v in contract['runtime']['movement'].values())*contract['runtime']['default_speed_factor']
    capture_cases={};physics_count=0;results={};route_ledgers={};last_route_frame=-1
    all_physics=[];last_physics_ticks=-1
    for route in routes:
        name=route['id'];setting=plan[name];require(route['setup_position']==setting['setup'], 'Spatial setup differs from frozen GDS')
        rows=route['physics_samples'];require(isinstance(rows,list) and rows, 'Missing spatial physics')
        require(rows[0]['physics_frame']>last_route_frame, 'Spatial routes reused actual physics interval')
        ordered_physics(rows);last_route_frame=rows[-1]['physics_frame'];route_ledgers[name]=rows
        previous=setting['setup'];previous_phase=0.0;last=None;positions=[];observed=set();collisions=[]
        recoveries={'normal-separation':0,'contact-jitter':0}
        for row in rows:
            frame=row['physics_frame'];require(type(frame) is int and (last is None or frame==last+1), 'Spatial physics gap')
            last=frame;require(row['case']==name, 'Spatial row case differs')
            ticks=row['ticks_usec']
            require(type(ticks) is int and ticks>0 and ticks>last_physics_ticks,
                    'Spatial actual physics wall clock missing/reused/out of order')
            last_physics_ticks=ticks;all_physics.append(row)
            dt=number64(row['delta_f64']);require(dt>0, 'Invalid actual spatial delta')
            position=[number64(v) for v in row['position_f64']];require(len(position)==2, 'Invalid spatial position')
            require(math.dist(position,previous)<=max_speed*dt+1e-4, 'Spatial teleport or impossible physical step')
            key=row['state']['action']+'-'+row['state']['direction'];bound_texture(row['texture'],profiles,key)
            phase=number64(row['phase_f64']) if 'phase_f64' in row else None
            if phase is not None:
                require(phase>=0, 'Negative actual spatial walking phase')
                if setting['type']=='door':
                    require(phase<sum(profiles['walk-north']['duration_ms']), 'Door walking phase outside actual north clip')
            if row['state']['action'] in ['walk','run']:directional_step(previous,position,row['state']['direction'])
            elif row['state']['action']=='idle' and math.dist(position,previous)>=1e-5:
                recoveries[_door_idle_recovery(setting,row,previous,position,previous_phase)]+=1
            previous=position;previous_phase=phase;positions.append(position);physics_count+=1
            observed.add((key,row['texture']['pose_id']));require(isinstance(row['colliders'],list)
                    and all(isinstance(c,str) for c in row['colliders']), 'Invalid actual collision identity')
            collisions.extend(row['colliders'])
            if setting['type']=='tool':
                require(key in [setting['clip'],'idle-'+setting['clip'].split('-')[1]]
                        and math.dist(position,setting['setup'])<1e-6, 'Spatial tool moved/wrong clip')
            elif setting['type']=='door':require(key in ['walk-north','idle-north'], 'Wrong door movement clip')
            else:require(row['state']['action'] in ['idle','walk','run'], 'Wrong route action')
        if setting['type']=='path':
            require(route['waypoints']==setting['waypoints'], 'Spatial waypoints differ from frozen GDS')
            cursor=0
            for target in setting['waypoints'][1:]:
                found=next((i for i in range(cursor,len(positions)) if math.dist(positions[i],target)<=1.2),None)
                require(found is not None, 'Actual physical waypoint missing');cursor=found
            expected=[name+'-start.png']+[name+'-waypoint-'+str(i)+'.png' for i in range(1,5)]
        elif setting['type']=='door':
            pose=setting['door_pose'];require(route['door_pose']==pose, 'Door pose differs')
            require(positions[-1][1]<155 if pose==2 else positions[-1][1]>160, 'Actual door collision/passage differs')
            require(pose==2 or any(c.endswith('/DoorCollision') for c in collisions), 'Actual DoorCollision missing')
            require(math.dist(route['final_position'],positions[-1])<1e-6, 'Door final position differs from actual physics')
            expected=[name+'-start.png']+[name+'-tick-'+str(i)+'.png' for i in [15,30,45]]+[name+'-end.png']
        else:
            require(route['spatial_observation_playback_rate']==.25, 'Spatial tool observation rate differs')
            clip=profiles[setting['clip']]
            require({p for k,p in observed if k==setting['clip']}==set(clip['pose_ids']), 'Spatial tool actual poses missing')
            expected=[name+'-pose-'+str(i)+'.png' for i in range(len(clip['pose_ids']))]
        require(route['captures']==expected, 'Spatial route PNG scope differs')
        for capture in expected:
            require(capture in pngs and capture not in capture_cases, 'Missing/duplicate spatial PNG')
            capture_cases[capture]=name
        results[name]={'physics_samples':len(rows),'captures':len(expected),
                       'idle_normal_separation_ticks':recoveries['normal-separation'],
                       'idle_contact_jitter_ticks':recoveries['contact-jitter']}
    next_tick_time={a['physics_frame']:b['ticks_usec'] for a,b in zip(all_physics,all_physics[1:])}
    records=report['capture_records'];require(isinstance(records,list) and len(records)==len(capture_cases),
                                              'Spatial capture records missing/duplicated')
    seen=set();last_process=-1;last_ticks=-1;last_capture_frame=-1
    matched_captures=setup_captures=0
    for row in records:
        name=row['capture'];require(name in capture_cases and name not in seen and row['case']==capture_cases[name],
                                    'Unbound spatial capture record');seen.add(name)
        case=row['case'];setting=plan[case];actual=actual_state_texture(row,profiles,'world_texture')
        if setting['type']=='tool':
            clip=setting['clip'];pose=row['world_texture']['pose_id'];index=profiles[clip]['pose_ids'].index(pose)
            require(actual==clip and name==case+'-pose-'+str(index)+'.png', 'Spatial PNG actual GPU pose differs')
        elif setting['type']=='door':
            allowed=actual.startswith('idle-') if name.endswith('-start.png') else actual in ['walk-north','idle-north']
            require(allowed, 'Spatial door capture GPU clip differs')
        else:require(actual.split('-')[0] in ['idle','walk','run'], 'Spatial route capture GPU clip differs')
        finite_vector(row['capture_origin_px'],2);finite_vector(row['sprite_offset'],2)
        transform=finite_vector(row['render_source_to_screen'],6)
        require(abs(transform[0]*transform[3]-transform[1]*transform[2])>1e-12, 'Degenerate actual render transform')
        require(all(type(row[k]) is int and row[k]>0 for k in ['ticks_usec','process_frame','physics_frame']),
                'Missing actual capture clock identity')
        require(row['process_frame']>last_process and row['ticks_usec']>last_ticks
                and row['physics_frame']>=last_capture_frame, 'Spatial capture clocks reused/out of order')
        last_process,last_ticks,last_capture_frame=row['process_frame'],row['ticks_usec'],row['physics_frame']
        point=[number64(v) for v in row['actor_position_f64']]
        require(len(point)==2 and math.dist(point,finite_vector(row['actor_position'],2))<1e-6,
                'Spatial capture numeric/binary64 position differs')
        ledger=route_ledgers[case];frame=row['physics_frame'];by_frame={r['physics_frame']:r for r in ledger}
        setup=name.endswith('-start.png')
        initial_tool=(setting['type']=='tool' and name.endswith('-pose-0.png') and frame==ledger[0]['physics_frame']-1)
        if setup or initial_tool:
            require(frame==ledger[0]['physics_frame']-1 and math.dist(point,setting['setup'])<1e-6,
                    'Spatial setup capture is detached from actual route start')
            if initial_tool:require(number64(row['world_elapsed_f64'])==0, 'Initial tool capture has nonzero clock')
            else:require(actual.startswith('idle-'), 'Spatial setup is not a canonical idle')
            require(row['ticks_usec']<ledger[0]['ticks_usec'], 'Spatial setup PNG is not before the first actual physics tick')
            setup_captures+=1
        else:
            require(frame in by_frame, 'Spatial capture physics frame is outside its route')
            physics=by_frame[frame];expected_point=[number64(v) for v in physics['position_f64']]
            require(math.dist(point,expected_point)<1e-6 and row['world_texture']==physics['texture']
                    and all(row['world_state'][k]==physics['state'][k] for k in ['action','direction']),
                    'Spatial capture position/GPU/state differs from the same actual tick')
            elapsed=physics['state']['elapsed_ms']
            require(type(elapsed) in [int,float] and math.isfinite(elapsed)
                    and abs(number64(row['world_elapsed_f64'])-elapsed)<1e-6
                    and abs(row['world_state']['elapsed_ms']-elapsed)<1e-6,
                    'Spatial capture clock differs from the same actual tick')
            if 'instance_id' in physics['state']:
                require(row['world_state']['instance_id']==physics['state']['instance_id'], 'Spatial capture player instance differs')
            require(physics['ticks_usec']<=row['ticks_usec'], 'Spatial PNG precedes its matched actual physics tick')
            if frame in next_tick_time:
                require(row['ticks_usec']<next_tick_time[frame], 'Spatial PNG was captured after the next actual physics tick')
            matched_captures+=1
        if setting['type']=='path' and '-waypoint-' in name:
            index=int(name.rsplit('-waypoint-',1)[1].removesuffix('.png'))
            require(math.dist(point,setting['waypoints'][index])<=1.2, 'Spatial waypoint PNG was captured at the wrong point')
        if setting['type']=='door' and name.endswith('-end.png'):
            require(frame==ledger[-1]['physics_frame'] and math.dist(point,
                    [number64(v) for v in ledger[-1]['position_f64']])<1e-6, 'Door end PNG is detached from final physics')
        # Engine.physics_jitter_fix can decouple accumulated game delta from
        # real time. Use recorded tick causality above, never wall+N*delta.
    require(pngs==seen, 'Unbound spatial output PNG')
    return {'routes':len(routes),'physics_samples':physics_count,'pngs':len(pngs),'route_results':results,
            'engine_clock':dict(clock),'clock_causality':{'observed_physics_ticks':len(all_physics),
                'matched_captures':matched_captures,'pre_first_tick_captures':setup_captures,
                'scope':'Recorded actual tick_time <= same-tick capture_time < next recorded tick_time when available; setup before first tick. No inferred delta-to-wall-time bound.'},
            'scope':'Frozen routes, raw physical positions/colliders, actual GPU identities and linked PNG bytes only. Spatial art occlusion and gameplay contact not inferred.'}


@contract_errors
def write_receipt(repo, evidence, output):
    from pathlib import Path
    import json
    from build_contract import digest, safe_file
    evidence=Path(evidence).absolute();output=Path(output).absolute()
    require(output.parent==evidence and output.name not in ['report.json','input-contract.json']
            and output.suffix=='.json' and not output.exists() and not output.is_symlink(),
            'Receipt must be a fresh evidence JSON')
    receipt=validate_observation(repo,evidence)
    require(digest(safe_file(evidence,'input-contract.json'))==receipt['input_contract_sha256']
            and digest(safe_file(evidence,'report.json'))==receipt['report_sha256'], 'Evidence changed before receipt')
    try:
        with output.open('x') as stream:stream.write(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    except FileExistsError as error:raise ValueError('Receipt already exists') from error
    return receipt


@contract_errors
def aggregate_observations(repo, evidence_paths):
    """Revalidate all raw reports; cached receipts alone cannot fill a gap."""
    require(isinstance(evidence_paths,list) and evidence_paths, 'Missing raw observation directories')
    receipts=[validate_observation(repo,path) for path in evidence_paths]
    baseline=receipts[0];scopes=set();matrix={k:dict(v,observed=0,missing=v['required']) for k,v in baseline['gap_matrix'].items()}
    for receipt in receipts:
        require(receipt['observer'] not in scopes, 'Duplicate observer scope')
        scopes.add(receipt['observer'])
        require(all(receipt[k]==baseline[k] for k in ['artifact_digest','manifest','suite','suite_sha256']),
                'Observations bind different full package/runtime inputs')
        for key,row in receipt['gap_matrix'].items():
            require(row['required']==matrix[key]['required'], 'Observation plans differ')
            matrix[key]['observed']=max(matrix[key]['observed'],row['observed'])
            matrix[key]['missing']=matrix[key]['required']-matrix[key]['observed']
    return {'kind':'coastal-all-actions-internal-observation-set-v1','schema_version':1,
            'status':'internal-observation-only','passed':True,'artifact_digest':baseline['artifact_digest'],
            'manifest':baseline['manifest'],'suite':baseline['suite'],'suite_sha256':baseline['suite_sha256'],
            'observers':sorted(scopes),'gap_matrix':matrix,
            'raw_observer_matrix_complete':all(row['missing']==0 for row in matrix.values()),
            'observations':[{'observer':r['observer'],'input_contract_sha256':r['input_contract_sha256'],
                             'report_sha256':r['report_sha256'],'validator_sha256':r['validator_sha256']} for r in receipts],
            'art_acceptance':False,'physical_contact_acceptance':False,'spatial_visual_acceptance':False,
            'user_approval':False,'release_eligible':False,
            'unverified':['Source semantic admission and animation art review','Physical gameplay contact','Spatial visual occlusion','OS focus/input','User approval','Production release'],
            'scope':'Raw observer coverage only. Synthetic package runs prove the tools and never actual character art.'}



def main():
    import argparse
    import json
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[2])
    commands=parser.add_subparsers(dest='command',required=True)
    validate=commands.add_parser('validate')
    validate.add_argument('--evidence',type=Path,required=True)
    validate.add_argument('--receipt',type=Path)
    aggregate=commands.add_parser('aggregate')
    aggregate.add_argument('--evidence',type=Path,action='append',required=True)
    aggregate.add_argument('--output',type=Path)
    args=parser.parse_args()
    try:
        if args.command=='validate':
            result=(write_receipt(args.repo,args.evidence,args.receipt) if args.receipt
                    else validate_observation(args.repo,args.evidence))
        else:
            require(args.output is None or (not args.output.exists() and not args.output.is_symlink()),
                    'Aggregate output must be fresh')
            result=aggregate_observations(args.repo,args.evidence)
            if args.output:
                with args.output.open('x') as stream:
                    stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(result,ensure_ascii=False))
    except (ValueError,OSError) as error:
        print(json.dumps({'passed':False,'error':str(error)},ensure_ascii=False))
        return 2
    return 0


if __name__=='__main__':
    raise SystemExit(main())
