"""Read-only four-pose source, ownership, same-hat and composite audit entry."""
from pathlib import Path
import json,hashlib,subprocess,sys
P=Path(__file__).resolve().parent;V=P.parent;ROOT=V.parents[6]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
m=json.loads((P/'manifest.json').read_text())
for rel,digest in m['sha256'].items():assert sha(P/rel)==digest,('validation tool/note changed',rel)
for rel,digest in m['external_validation_tools'].items():assert sha(ROOT/rel)==digest,('called external validation tool changed',rel)
results=[]
for record in m['frames']:
 pose=record['pose_id'];path=P/record['manifest'];assert sha(path)==record['sha256'];data=json.loads(path.read_text());assert data['pose_id']==pose and data['runtime_candidate_allowed'] is True;assert data['runtime_full_frame_placement_px']==[0,0] and data['source_to_target_integer_translation_px']==[0,0]
 assert data['compatible_hat_manifest_sha256']==sha(V/f'extraction/{pose}/manifest.json')
 for rel,digest in data['sha256'].items():assert sha(path.parent/rel)==digest,(pose,rel)
 command=[sys.executable,'-B',str(P/('audit_idle.py' if pose=='idle_west_0' else 'audit_motion.py'))]
 if pose!='idle_west_0':command.append(pose.rsplit('_',1)[1])
 r=subprocess.run(command,capture_output=True,text=True)
 if r.returncode:print(r.stdout);print(r.stderr,file=sys.stderr);raise SystemExit(r.returncode)
 result=json.loads(r.stdout);assert result['runtime_candidate_allowed'] is True and all(v is True for v in result['checks'].values());results.append({'pose_id':pose,'checks':len(result['checks']),'owned_source_pixels':result['counts']['owned_source_pixels'],'crown_or_band_protrusions':result['counts']['crown_or_band_protrusions'],'outside_hair_rgba_differences':result['counts']['outside_new_hair_support_rgba_differences'],'compatible_hat_manifest_sha256':result['compatible_hat_manifest_sha256']})
print(json.dumps({'status':'PASS','scope':'four exact-hat-compatible compact visible hair views; native and user acceptance pending','summary':results},indent=2))
