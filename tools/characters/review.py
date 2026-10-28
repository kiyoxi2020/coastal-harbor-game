"""Single development review launcher; independent of shell working directory."""
from pathlib import Path
import argparse
import json
import subprocess
from build_contract import digest, keys, read_json, require, safe_file
from build import verify

REPO = Path(__file__).resolve().parents[2]
STATES = ['bare', 'hair', 'hat', 'hair_hat']


def construction_preflight(repo, suite_path):
    repo=Path(repo).resolve(); suite_path=Path(suite_path).absolute()
    require(suite_path.is_relative_to(repo/'art/characters/reviews'), 'Suite outside reviews')
    suite=read_json(safe_file(repo,suite_path.relative_to(repo).as_posix(),'art/characters/reviews'))
    keys(suite,'kind schema_version resource_root scope sample_id states','construction review suite')
    require(suite['kind']=='coastal-character-construction-review-v1' and type(suite['schema_version']) is int and suite['schema_version']==1
            and suite['resource_root']=='art/characters' and suite['scope']=='review-only'
            and suite['sample_id']=='hoe-west' and isinstance(suite['states'],dict) and set(suite['states'])==set(STATES),'Invalid construction review scope')
    base=None
    for state in STATES:
        ref=suite['states'][state];keys(ref,'manifest sha256','review state')
        path=safe_file(repo,ref['manifest'],'art/characters/builds')
        require(path.name=='manifest.json' and digest(path)==ref['sha256'],'Review manifest SHA mismatch')
        manifest=verify(repo,path.parent)
        recipe=read_json(safe_file(repo/'art/characters',manifest['recipe'],'recipes'))
        require(recipe.get('schema_version')==2 and recipe.get('head_state')==state,'Review state recipe mismatch')
        if base is None:base=recipe['base_recipe']
        require(recipe['base_recipe']==base,'Review states must share one base recipe')
    return suite


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('suite',choices=['locomotion','farming','wardrobe','headwear','static-candidates','headwear-construction'],nargs='?',default='headwear')
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args();lib=REPO/'art/characters'
    path=lib/'reviews'/args.suite/'review.json'
    try:
        if args.suite=='headwear-construction':
            construction_preflight(REPO,path)
            config={'scene':'res://dev/characters/character_headwear_hoe_review.tscn','args':['--construction-suite='+str(path)]}
        else:config=read_json(path)
        if 'html' in config:cmd=['open',str(lib/config['html'])]
        else:
            cmd=['/Applications/Godot.app/Contents/MacOS/Godot','--path',str(REPO/'godot2d'),'--log-file','/private/tmp/coastal-character-'+args.suite+'-review.log',config['scene'],'--']+[s.replace('{library}',str(lib)) for s in config.get('args',[])]
        if args.dry_run:print(json.dumps(cmd,ensure_ascii=False))
        else:raise SystemExit(subprocess.call(cmd,cwd=REPO))
    except (ValueError,KeyError,TypeError,OSError) as exc:parser.exit(1,str(exc)+'\n')

if __name__=='__main__':main()
