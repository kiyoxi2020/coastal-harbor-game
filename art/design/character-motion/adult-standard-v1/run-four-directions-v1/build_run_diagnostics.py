"""Expose existing rejected art for explicit visual inspection, without repairs."""
from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def build():
    output=ROOT/'diagnostics/south';output.mkdir(parents=True,exist_ok=True)
    with Image.open(ROOT/'sources/run-south-b-v2.png') as sheet:
        if sheet.mode!='RGBA' or sheet.size!=(2048,768):raise ValueError('Unexpected original diagnostic canvas')
        if sheet.getchannel('A').crop((0,757,2048,768)).getbbox():raise ValueError('Registration would discard source alpha')
        for i in range(4):
            frame=Image.new('RGBA',(512,768));frame.paste(sheet.crop((i*512,0,(i+1)*512,768)),(0,11));frame.save(output/f'B_{i}.png')
    records=[]
    for direction,note,representation in [('south','南向长袖诊断稿：第三帧摆臂改变；完整源帧，待你确认。','complete_generated_frames'),('north','北向长袖诊断稿：颈口、腰线及腋下有小孔，待你确认。','layered_diagnostic')]:
        records.append({'direction':direction,'garment':'B','note':note,'representation':representation,'frames':[{'pose_id':f'run_{direction}_{i}','file':f'diagnostics/south/B_{i}.png' if direction=='south' else f'baked/B_north_{i}.png','duration_ms':80} for i in range(4)]})
    dependencies=['build_run_diagnostics.py','test_diagnostics.py','candidate.json','run-garments.json','parts-manifest.json','sources/run-south-b-v2.png','prompts/run-south-b-v2.txt','evidence/garment-quality.json']
    dependencies += [entry['file'] for record in records for entry in record['frames']]
    result={'schema_version':1,'status':'diagnostic_only_not_accepted','candidate_manifest_sha256':sha(ROOT/'candidate.json'),'run_garments_sha256':sha(ROOT/'run-garments.json'),'canvas_px':[512,768],'root_anchor_px':[256,708],'registration':'south: exact complete-cell crop plus whole-frame+11y; north: existing unmodified layered bake','records':records,'inputs':{path:sha(ROOT/path) for path in sorted(set(dependencies))},'user_accepted':False}
    (ROOT/'run-diagnostics.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('Diagnostic manifest:',sha(ROOT/'run-diagnostics.json'))
if __name__=='__main__':build()
