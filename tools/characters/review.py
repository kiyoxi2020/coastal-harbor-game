"""Single development review launcher; independent of shell working directory."""
from pathlib import Path
import argparse,json,subprocess
REPO=Path(__file__).resolve().parents[2]
def main():
 p=argparse.ArgumentParser();p.add_argument('suite',choices=['locomotion','farming','wardrobe','headwear','static-candidates'],nargs='?',default='headwear');p.add_argument('--dry-run',action='store_true');a=p.parse_args();lib=REPO/'art/characters'
 config=json.loads((lib/'reviews'/a.suite/'review.json').read_text())
 if 'html' in config:cmd=['open',str(lib/config['html'])]
 else:cmd=['/Applications/Godot.app/Contents/MacOS/Godot','--path',str(REPO/'godot2d'),'--log-file','/private/tmp/coastal-character-'+a.suite+'-review.log',config['scene'],'--']+[s.replace('{library}',str(lib)) for s in config.get('args',[])]
 if a.dry_run:print(json.dumps(cmd,ensure_ascii=False))
 else:raise SystemExit(subprocess.call(cmd,cwd=REPO))
if __name__=='__main__':main()
