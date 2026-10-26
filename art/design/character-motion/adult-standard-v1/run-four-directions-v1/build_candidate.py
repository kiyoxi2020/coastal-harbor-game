"""Whole-cell registration only. No resampling, painting, or part transforms."""
from pathlib import Path
import hashlib, json, shutil
from PIL import Image

ROOT = Path(__file__).resolve().parent
WEST = ROOT.parent / 'run-west-proof-v1'
DIRECTIONS = ['south', 'west', 'east', 'north']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(name, value):
    (ROOT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')

def reflected(image):
    out = Image.new('RGBA', image.size)
    out.paste(image.transpose(Image.Transpose.FLIP_LEFT_RIGHT), (1, 0))
    return out

def main():
    for d in ['sources', 'registered', 'evidence']:
        (ROOT/d).mkdir(exist_ok=True)
    provenance = []
    for name in ['candidate.json', 'user-acceptance.json']:
        if (WEST/name).exists():
            dst = ROOT/'sources'/('west-'+name)
            shutil.copyfile(WEST/name, dst)
            provenance.append({'original': str((WEST/name).relative_to(ROOT.parents[4])), 'copy': str(dst.relative_to(ROOT)), 'sha256':sha(dst)})
    frames = []
    # The corrected source v3 has the complete reciprocal four-pose sequence.
    for direction in DIRECTIONS:
        source = ROOT/f'sources/run-{direction}-a-v{3 if direction=="south" else 2}.png'
        sheet = Image.open(source).convert('RGBA') if direction in ['south','north'] else None
        for i in range(4):
            meta = {'pose_id':f'run_{direction}_{i}', 'direction':direction, 'duration_ms':80}
            if direction == 'west':
                src = WEST/f'registered/run_west_{i}.png'
                out = ROOT/f'registered/run_west_{i}.png'
                shutil.copyfile(src, out)
                meta.update(source_box=[0,0,512,768], whole_frame_translation_px=[0,0], provenance={'source_project_path':str(src.relative_to(ROOT.parents[4])), 'source_sha256':sha(src), 'operation':'byte-for-byte copy of user-approved west A'})
            else:
                if direction == 'east':
                    src = ROOT/f'registered/run_west_{i}.png'
                    image = reflected(Image.open(src).convert('RGBA'))
                    meta.update(source_box=[0,0,512,768], whole_frame_translation_px=[1,0], provenance={'source':str(src.relative_to(ROOT)), 'source_sha256':sha(src), 'operation':'whole-frame horizontal reflection x=511-x, then integer +1x to preserve root256; anatomical left/right exchanged'})
                else:
                    box = [512*i,0,512*(i+1),768]
                    image = Image.new('RGBA',(512,768))
                    image.paste(sheet.crop(tuple(box)),(0,11))
                    meta.update(source_box=box,whole_frame_translation_px=[0,11],provenance={'source':str(source.relative_to(ROOT)), 'source_sha256':sha(source),'operation':'complete-cell crop and integer whole-frame +11y only'})
                out=ROOT/f'registered/run_{direction}_{i}.png'
                image.save(out)
            alpha=Image.open(out).getchannel('A')
            meta.update(file=str(out.relative_to(ROOT)), sha256=sha(out), visible_alpha_bbox=list(alpha.point(lambda a:255 if a>=128 else 0).getbbox()))
            frames.append(meta)
    inputs = {}
    for p in sorted([ROOT/'build_candidate.py']+list((ROOT/'sources').glob('*a-v*'))+list((ROOT/'sources').glob('west-*.json'))+list((ROOT/'prompts').glob('*a-v*'))+list((ROOT/'registered').glob('*.png'))):
        if p.is_file():inputs[str(p.relative_to(ROOT))]=sha(p)
    m={'template_id':'adult-standard-v1', 'motion_set_id':'run-four-directions-v1', 'status':'unapproved_complete_frame_proof', 'canvas_px':[512,768], 'root_anchor_px':[256,708], 'display_scale':0.23711340206185566, 'base_world_speed':108, 'playback_rate':0.75, 'walk_artifact_digest':'166c5a0da9249a8da537e86406b12f3889ace5fa150aefc854265608703bd603', 'directions':DIRECTIONS, 'phase_map':[0,1,2,3], 'phase_map_status':'candidate contact/flight observations; exact target trajectories and transition mapping not frozen', 'frames':frames, 'inputs':inputs, 'scope':'four-direction complete-frame run A candidate; west acceptance remains west only; not complete body/garment/pants/shoes release', 'provenance':provenance}
    write('candidate.json',m)
    records=[]
    for f in frames:
        d=f['direction'];i=int(f['pose_id'].split('_')[-1]);phase=['left_contact_candidate','airborne_after_left_candidate','right_contact_candidate','airborne_after_right_candidate'][i] if d in ['north','south'] else ['near_contact_candidate','flight_after_near_candidate','far_contact_candidate','flight_after_far_candidate'][i]
        records.append({'pose_id':f['pose_id'],'texture_sha256':f['sha256'],'root_anchor_px':[256,708],'observed_phase':phase,'observed_opaque_bbox':f['visible_alpha_bbox'],'joint_anchors':{k:None for k in ['neck_root','left_shoulder','right_shoulder','left_elbow','right_elbow','left_wrist','right_wrist','waist','left_hip','right_hip','left_knee','right_knee','left_ankle','right_ankle','left_foot','right_foot']},'foot_contacts':{'status':'visible support/flight silhouette only; exact sole contacts and hidden joint coordinates not frozen'},'status':'registered; source silhouette reviewed; native and user review pending'})
    write('poses.json',{'status':'draft_not_frozen','method':'actual full-source visual inspection; no percentage landmarks or guessed hidden joints','frames':records})
    print('Registered 16 complete frames, no resampling/local transforms.')

if __name__=='__main__': main()
