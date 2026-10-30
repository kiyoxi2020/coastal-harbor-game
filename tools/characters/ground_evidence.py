"""Bounded native projection onto legal plot cells, never physical soil impact.

This is separate from the six full-package observers. The original painted
material point remains a candidate even when its native world geometry aligns.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct
from PIL import Image
import all_actions_capture as capture
import all_actions_evidence as observation
from all_actions_native import number64
from build_contract import digest, read_json, require, safe_file

CANDIDATES='godot2d/tests/characters/all_actions_ground_target_candidates.json'
KIND='coastal-native-ground-target-alignment-observation-v1'
EXPECTED={a+'-'+d for a in ['hoe','water'] for d in ['south','west','east','north']}
REPO=Path(__file__).resolve().parents[2]


def f32(value):return struct.unpack('<f',struct.pack('<f',value))[0]


def pair(value):
    require(isinstance(value,list) and len(value)==2 and all(type(v) is int for v in value), 'Invalid integer material point')
    return value


def vector64(value, size=2):
    require(isinstance(value,list) and len(value)==size, 'Invalid binary64 vector')
    return [number64(v) for v in value]


def project(matrix, point):
    # Transform2D/Vector2 store real32 values in this build. Round each native
    # vector operation; comparisons below allow two representation ULPs.
    return [f32(f32(f32(matrix[i]*point[0])+f32(matrix[i+2]*point[1]))+matrix[i+4]) for i in [0,1]]


def native_tolerance(value):
    value=abs(f32(value))
    return max(1e-6,math.ldexp(1.0,math.frexp(value)[1]-24)*2) if value else 1e-6


def near(a,b):
    require(len(a)==len(b), 'Vector dimension differs')
    return all(abs(x-y)<=max(native_tolerance(x),native_tolerance(y)) for x,y in zip(a,b))


def facing(delta):
    require(delta!=[0,0], 'Zero standing offset has no intended facing')
    if abs(delta[0])>abs(delta[1]):return 'east' if delta[0]>0 else 'west'
    return 'south' if delta[1]>0 else 'north'


def inside(point, bounds):
    x,y,w,h=bounds
    return x<=point[0]<x+w and y<=point[1]<y+h


def frozen_text(repo, contract, relative):
    require(relative in contract['files'], 'Geometry rule missing from frozen runtime closure')
    path=safe_file(repo,relative)
    require(digest(path)==contract['files'][relative], 'Frozen geometry rule changed')
    return path.read_text()


def node_block(text, name):
    blocks=[body for header,body in re.findall(r'^\[node ([^\n]+)\]\n(.*?)(?=^\[|\Z)',text,re.M|re.S)
            if re.search(r'\bname="'+re.escape(name)+r'"',header)]
    require(len(blocks)==1, 'Unsupported frozen scene node')
    return blocks[0]


def scene_vector(block, field):
    value=re.search(r'^'+field+r'\s*=\s*Vector2\(([-\d.eE+]+),\s*([-\d.eE+]+)\)',block,re.M)
    require(value is not None, 'Missing frozen '+field)
    return [float(v) for v in value.groups()]


def frozen_geometry(repo, contract):
    scene=frozen_text(repo,contract,'godot2d/scenes/world/harbor_exterior.tscn')
    garden=node_block(scene,'GardenA')
    require('region_id = "garden_a"' in garden, 'Unexpected actual plot region')
    for block in [garden,node_block(scene,'HarborExterior'),node_block(scene,'DepthSortedObjects')]:
        require(not re.search(r'^(scale|rotation|transform)\s*=',block,re.M), 'Unsupported transformed plot ancestry')
    for name in ['HarborExterior','DepthSortedObjects']:
        require(not re.search(r'^position\s*=',node_block(scene,name),re.M), 'Unsupported translated plot ancestry')
    origin=scene_vector(garden,'position')
    rules=re.sub(r'\s+','',frozen_text(repo,contract,'godot2d/scripts/farm_plot.gd'))
    require(all(rule in rules for rule in ['GRID_ORIGIN:=Vector2(-32,-32)','Vector2(x*16+8,y*16+8)','point.x/16','x>=4','y>=2']),
            'Unsupported frozen plot grid rules')
    trial=frozen_text(repo,contract,'godot2d/dev/characters/character_walk_trial.tscn')
    scale=scene_vector(node_block(trial,'Pose'),'scale');zoom=scene_vector(node_block(trial,'WorldCamera'),'zoom')
    implementation=re.sub(r'\s+','',frozen_text(repo,contract,'godot2d/dev/characters/character_headwear_trial.gd'))
    require('full_density=pose.scale/(138.0/582.0)' in implementation, 'Unsupported registered density rule')
    density=[f32(f32(v)/f32(138.0/582.0)) for v in scale]
    return origin,density,zoom


def cell_geometry(cell, origin):
    parts=cell.split(':')
    require(len(parts)==3 and parts[0]=='garden_a' and all(v.isdigit() for v in parts[1:]), 'Invalid actual target cell')
    x,y=map(int,parts[1:]);require(0<=x<4 and 0<=y<2, 'Target cell outside frozen grid')
    corner=[origin[0]-32+x*16,origin[1]-32+y*16]
    return [corner[0]+8,corner[1]+8],[*corner,16,16]


def candidate_sources(repo, contract, data, profiles):
    library=repo/'art/characters';manifest=read_json(safe_file(repo,contract['manifest']['manifest']))
    head=read_json(safe_file(library,manifest['recipe']));base=read_json(safe_file(library,head['base_recipe']['file']))
    clips={c['action_id']+'-'+c['direction']:c for c in base['clips']}
    heads={c['action_id']+'-'+c['direction']:c for c in head['clips']};outputs={r['file']:r for r in manifest['outputs']}
    require(data.get('kind')=='coastal-native-ground-target-candidates-v1' and data.get('artifact_id')==contract['artifact_digest']
            and data.get('target_selection_mode')=='keyboard-forward-12', 'Candidate package/artifact/selection differs')
    require(isinstance(data.get('source_review_sha256'),str) and re.fullmatch('[0-9a-f]{64}',data['source_review_sha256']), 'Missing source review fingerprint')
    candidates=data['cases'];require(isinstance(candidates,list) and len(candidates)==8
            and {c['id'] for c in candidates}==EXPECTED, 'Eight unique source candidates required')
    result={}
    for candidate in candidates:
        key=candidate['id'];clip=clips[key];profile=profiles[key]
        require(candidate['clip']==key,
                'Candidate clip differs')
        pose=candidate['pose_id'];require(pose in profile['pose_ids'], 'Candidate pose absent from actual package')
        require(candidate['source_ground_contact_proven'] is False and type(candidate['point_uncertainty_source_px']) is int
                and candidate['point_uncertainty_source_px']==8, 'Source point cannot assert physical ground proof')
        require(candidate['point_kind']==('metal_working_edge' if key.startswith('hoe-') else 'splash_center'), 'Unexpected visible point material kind')
        doc=read_json(safe_file(library,clip['poses']['file']));variant=doc['variants'][clip['variant']]
        frames=[f for f in variant['frames'] if f['pose_id']==pose];require(len(frames)==1, 'Canonical point pose missing')
        frame=frames[0];relative='art/characters/'+frame['file']
        require(candidate['source_image']==relative and candidate['source_image_sha256']==frame['sha256']
                and contract['files'].get(relative)==frame['sha256'], 'Candidate source image differs from actual canonical pose')
        xy=pair(candidate['canonical_point_px']);point=pair(candidate['source_point_px']);pad=heads[key].get('output_padding_px',[0,0,0,0])
        require(point==[xy[0]+pad[0],xy[1]+pad[1]], 'Candidate source/final whole-frame point differs')
        path=safe_file(repo,relative)
        with Image.open(path) as image:
            image=image.convert('RGBA');require(list(image.size)==clip['canvas_px'] and 0<=xy[0]<image.width and 0<=xy[1]<image.height, 'Canonical point outside actual frame')
            rgba=list(image.getpixel(tuple(xy)))
        name=f'frames/{clip["action_id"]}/{clip["direction"]}/{pose}.png';entry=outputs[name]
        final=safe_file(repo/Path(contract['manifest']['manifest']).parent,name)
        with Image.open(final) as image:actual=list(image.convert('RGBA').getpixel(tuple(point)))
        require(rgba==candidate['source_rgba']==actual and rgba[3]>0, 'Actual source/final visible material point RGBA differs')
        result[key]=candidate
    return result


def stationary_instance(case, candidate, profile, profiles, rate, previous_frame, seen_instances):
    rows=case['physics_samples'];require(isinstance(rows,list) and rows, 'Missing ground physics samples')
    observation.ordered_physics(rows);require(rows[0]['physics_frame']>previous_frame, 'Ground instances reused physics interval')
    start=vector64(case['actor_start_f64']);elapsed=0;completed=False;instance=None
    for row in rows:
        require(row['case']=='ground-'+candidate['id'] and math.dist(vector64(row['position_f64']),start)<1e-6,
                'Ground action moved or belongs to another case')
        dt=number64(row['delta_f64']);require(dt>0, 'Invalid actual ground physics delta')
        state=row['state'];key=state['action']+'-'+state['direction'];observation.bound_texture(row['texture'],profiles,key)
        require(state['direction']==profile['direction'], 'Ground action direction changed')
        if not completed:elapsed+=dt*1000*rate
        if elapsed>=sum(profile['duration_ms']):
            require(state['action']=='idle' and key=='idle-'+profile['direction'], 'Ground action did not complete into canonical idle');completed=True;continue
        require(not completed and key==candidate['clip'] and type(state['instance_id']) is int and state['instance_id']>0,
                'Wrong actual ground action/instance')
        if instance is None:instance=state['instance_id']
        require(state['instance_id']==instance and abs(state['elapsed_ms']-elapsed)<1e-6
                and row['texture']['pose_id']==observation.timed_pose(profile,elapsed), 'Ground physics clock/GPU/instance differs')
    require(completed and instance is not None and instance not in seen_instances, 'Ground instance missing/reused/incomplete')
    seen_instances.add(instance)
    record=case['capture_record'];frame=record['physics_frame'];matches=[r for r in rows if r['physics_frame']==frame]
    require(len(matches)==1, 'Ground capture not bound to actual physics tick');row=matches[0]
    require(record['world_texture']==row['texture'] and record['world_state']==row['state']
            and record['world_state']['instance_id']==instance and record['world_state']['action']==profile['action_id']
            and math.dist(vector64(record['actor_position_f64']),start)<1e-6
            and abs(number64(record['world_elapsed_f64'])-row['state']['elapsed_ms'])<1e-6,
            'Ground capture is detached from stationary actual player tick')
    return rows[-1]['physics_frame'],instance


@observation.contract_errors
def validate(repo, evidence):
    repo=Path(repo).resolve();evidence=Path(evidence).absolute()
    capture.verify_inputs(repo,evidence);cp=safe_file(evidence,'input-contract.json');rp=safe_file(evidence,'report.json')
    contract_sha,report_sha=digest(cp),digest(rp);contract=read_json(cp);report=read_json(rp)
    require(contract['observer']=='spatial' and report.get('kind')==KIND and report.get('input_contract_sha256')==contract_sha,
            'Ground report must bind the actual spatial input contract')
    loaded=observation.loaded_input_binding(repo,contract,report)
    require(isinstance(report.get('renderer'),str) and report['renderer'] not in ['', 'headless'], 'Native GPU observation required')
    path=safe_file(repo,CANDIDATES);candidate_sha=digest(path)
    require(report['candidate_file']=='res://'+CANDIDATES.removeprefix('godot2d/')
            and report['candidate_sha256']==candidate_sha==contract['files'].get(CANDIDATES), 'Actual frozen candidate file SHA differs')
    profiles=observation.bound_profiles(repo,contract);data=read_json(path);candidates=candidate_sources(repo,contract,data,profiles)
    origin,density,zoom=frozen_geometry(repo,contract);pngs=observation.png_inventory(evidence,report)
    cases=report['cases'];require(isinstance(cases,list) and len(cases)==8 and {c['candidate_id'] for c in cases}==EXPECTED,
                                  'Eight unique native ground cases required')
    checks=report['checks'];names={key+'_'+suffix for key in EXPECTED for suffix in ['started','legal_target','actual_pose_and_target','stationary','png_saved']}
    require(isinstance(checks,list) and len(checks)==len(names) and {c['name'] for c in checks}==names
            and all(c['passed'] is True for c in checks), 'Producer reported missing/failed ground checks')
    seen=set();instances=set();last_frame=-1;last_process=-1;last_ticks=-1;results=[]
    for case in cases:
        candidate=candidates[case['candidate_id']];key=candidate['clip'];profile=profiles[key];direction=profile['direction']
        require(case['source_ground_contact_proven'] is False and case['target_selection_mode']=='keyboard-forward-12'
                and case['ray_hit'] is False, 'Ground geometry cannot imply source impact or blocked target')
        center,bounds=cell_geometry(candidate['cell_id'],origin);target=case['target']
        require(target['cell_id']==candidate['cell_id']==case['point_cell_id']==case['forward_probe_cell_id']
                and target['node_path'].endswith('/HarborExterior/DepthSortedObjects/GardenA')
                and near(vector64(target['center_f64']),center) and target['cell_bounds_world']==bounds, 'Actual plot cell geometry differs')
        start=vector64(case['actor_start_f64']);offset=observation.finite_vector(candidate['standing_offset'],2)
        require(near(start,[center[i]-offset[i] for i in range(2)]) and facing(offset)==direction, 'Standing offset/facing differs from frozen candidate')
        distance=number64(case['distance_f64']);require(distance<=24 and abs(distance-math.dist(start,center))<1e-5, 'Target exceeds actual legal standing distance')
        forward={'north':[0,-1],'south':[0,1],'west':[-1,0],'east':[1,0]}[direction]
        require(inside([start[i]+12*forward[i] for i in range(2)],bounds), 'Keyboard forward probe selects another cell')
        last_frame,instance=stationary_instance(case,candidate,profile,profiles,contract['runtime']['clips'][key]['playback_rate'],last_frame,instances)
        row=case['capture_record'];require(row['clip']==key and row['mode']=='native-ground-target-alignment'
                and row['world_texture']['pose_id']==candidate['pose_id'], 'Ground capture has wrong actual pose')
        require(all(type(row[k]) is int and row[k]>0 for k in ['process_frame','physics_frame','ticks_usec'])
                and row['process_frame']>last_process and row['ticks_usec']>last_ticks, 'Ground capture clocks reused/out of order')
        last_process,last_ticks=row['process_frame'],row['ticks_usec']
        require(row['texture_size_px']==profile['canvas_px'] and row['sprite_offset']==[-v for v in profile['root_anchor_px']]
                and row['pose_position']==[0,0], 'Actual registered sprite geometry differs')
        scale=[f32(v*f32(profile['display_scale'])) for v in density]
        require(near(observation.finite_vector(row['pose_scale'],2),scale), 'Actual source density differs from frozen scene')
        matrix=vector64(case['source_to_world_f64'],6)
        require(near(matrix,[scale[0],0,0,scale[1],*start]), 'Actual source-to-world matrix differs from registered actor')
        local=[f32(candidate['source_point_px'][i]+.5+row['sprite_offset'][i]) for i in range(2)]
        world=vector64(case['point_world_f64']);require(near(world,project(matrix,local)) and inside(world,bounds), 'Actual painted point does not project inside legal target cell')
        render=observation.finite_vector(row['render_source_to_screen'],6)
        require(near(render[:4],[f32(scale[0]*zoom[0]),0,0,f32(scale[1]*zoom[1])]), 'Actual camera/source screen scale differs')
        screen=vector64(case['point_screen_f64']);require(near(screen,project(render,local)), 'Actual screen point differs from captured transform')
        crop=pair(row['capture_origin_px']);require(crop==row['actor_capture_origin_px'], 'Ground PNG uses another crop origin')
        require(row['snap_2d_transforms_to_pixel'] is True, 'Ground scope requires frozen viewport transform snapping')
        rounded=[math.floor(v+.5) if v>=0 else math.ceil(v-.5) for v in start]
        anchor=[render[4+i]+zoom[i]*(start[i]-rounded[i]) for i in range(2)]
        # Reconstructing canvas*global through a real32 inverse may straddle
        # an integer by one ULP. Preserve precisely that truncation interval;
        # this is not a fitted raster offset or a world-point tolerance.
        choices=[{int(v-native_tolerance(v)),int(v+native_tolerance(v))} for v in anchor]
        require(crop[0]+140 in choices[0] and crop[1]+245 in choices[1],
                'PNG crop is detached from actual actor anchor')
        name=row['capture'];require(name=='ground-'+key+'.png' and name in pngs and name not in seen, 'Ground PNG missing/duplicated');seen.add(name)
        with Image.open(safe_file(evidence,name)) as image:
            require(image.size==(280,300) and 0<=screen[0]-crop[0]<image.width and 0<=screen[1]-crop[1]<image.height,
                    'Projected material point outside actual PNG crop')
        results.append({'candidate_id':key,'pose_id':candidate['pose_id'],'instance_id':instance,'capture':name,
            'point_world':world,'point_screen':screen,'cell_id':candidate['cell_id'],'standing_distance':distance,
            'source_ground_contact_proven':False,'point_uncertainty_source_px':8,
            'crop_mapping_scope':'native-real32-truncation-interval-only'})
    require(seen==pngs and digest(cp)==contract_sha and digest(rp)==report_sha and digest(path)==candidate_sha, 'Ground evidence changed or contains unbound PNG')
    for relative,expected in contract['files'].items():require(digest(safe_file(repo,relative))==expected, 'Frozen ground input changed during validation')
    return {'kind':'coastal-native-geometric-target-alignment-receipt-v1','schema_version':1,'scope':'native-geometric-target-alignment-only',
        'artifact_digest':contract['artifact_digest'],'input_contract_sha256':contract_sha,'report_sha256':report_sha,
        'candidate_sha256':candidate_sha,'source_review_sha256':data['source_review_sha256'],'loaded_input_binding':loaded,
        'validator_sha256':digest(__file__),'observation_helper_sha256':digest(observation.__file__),
        'passed':True,'aligned_cases':len(results),'cases':results,'source_ground_contact_proven':False,'physical_soil_impact_proven':False,
        'soil_deformation_proven':False,'hidden_grip_proven':False,'gameplay_transaction_proven':False,
        'native_raster_correspondence_proven':False,'user_approval':False,'release_eligible':False}


@observation.contract_errors
def write_receipt(repo, evidence, output):
    evidence=Path(evidence).absolute();output=Path(output).absolute()
    require(output.parent==evidence and output.suffix=='.json' and output.name not in ['input-contract.json','report.json']
            and not output.exists() and not output.is_symlink(), 'Ground receipt must be a fresh sibling JSON')
    result=validate(repo,evidence)
    require(digest(safe_file(evidence,'input-contract.json'))==result['input_contract_sha256']
            and digest(safe_file(evidence,'report.json'))==result['report_sha256'], 'Ground evidence changed before receipt')
    try:
        with output.open('x') as stream:stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    except FileExistsError as error:raise ValueError('Ground receipt exists') from error
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=REPO)
    commands=parser.add_subparsers(dest='command',required=True)
    check=commands.add_parser('validate');check.add_argument('--evidence',type=Path,required=True);check.add_argument('--receipt',type=Path)
    args=parser.parse_args(argv)
    try:
        result=write_receipt(args.repo,args.evidence,args.receipt) if args.receipt else validate(args.repo,args.evidence)
        print(json.dumps(result,ensure_ascii=False))
    except (ValueError,OSError) as error:
        print(json.dumps({'passed':False,'error':str(error)},ensure_ascii=False));return 2
    return 0


if __name__=='__main__':raise SystemExit(main())
