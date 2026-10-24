"""Audit sampled ground-relative support drift; never edits or approves art."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def assess(samples, required=None):
    required = required if required is not None else {(d,s) for d in ('south','west','east','north') for s in ('left','right')}
    groups=[]
    previous=None
    for item in samples:
        t=item['elapsed_ms']
        if not math.isfinite(t) or previous and t<=previous['elapsed_ms']:
            raise ValueError('sample times must be finite and strictly increasing')
        key=(item['direction'],item['pose_id'],item['support'])
        same=previous and key==(previous['direction'],previous['pose_id'],previous['support']) and t-previous['elapsed_ms']<=100
        if not same: groups.append([])
        groups[-1].append(item)
        previous=item
    intervals=[]
    covered=set()
    for group in groups:
        first,last=group[0],group[-1]
        if first['support'] not in ('left','right') or last['elapsed_ms']-first['elapsed_ms']<40:
            continue
        points=[tuple(a-b for a,b in zip(row['foot_screen_px'],row['ground_screen_px'])) for row in group]
        if any(len(p)!=2 or not all(math.isfinite(v) for v in p) for p in points):
            raise ValueError('invalid screen point')
        distance=max(math.dist(a,b) for a in points for b in points)
        covered.add((first['direction'],first['support']))
        intervals.append({'direction':first['direction'],'pose_id':first['pose_id'],'support':first['support'],'sample_count':len(group),'span_ms':last['elapsed_ms']-first['elapsed_ms'],'drift_px':distance,'first_file':first.get('file'),'last_file':last.get('file')})
    maximum=max((row['drift_px'] for row in intervals),default=0)
    missing=sorted(required-covered)
    return {'passed':not missing and maximum<=1,'threshold_px':1,'missing_supports':missing,'max_observed_drift_px':maximum,'intervals':intervals,'scope':'sampled within-pose support drift lower bound; absolute anchors and inter-pose foot trajectory remain unverified'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    data=json.loads(args.capture.read_text())
    for row in data['samples']:
        path=args.capture.parent/row['file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=row['png_sha256']:
            raise ValueError('capture PNG hash mismatch: '+str(path))
    result=assess(data['samples'])
    result.update(artifact_digest=data['artifact_digest'],capture_sha256=hashlib.sha256(args.capture.read_bytes()).hexdigest(),checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='intervals'},ensure_ascii=False))
    return 0 if result['passed'] else 2

if __name__=='__main__':raise SystemExit(main())
