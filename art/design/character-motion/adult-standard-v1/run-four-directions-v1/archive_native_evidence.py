"""Validate and archive native evidence, preserving actual capture timestamps."""
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile
from PIL import Image

ROOT = Path(__file__).resolve().parent
SOURCE = Path('/private/tmp/coastal-run-directions-native')
OUTPUT = ROOT / 'evidence/native'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def required_checks(directions, combinations):
    names = {'native_renderer', 'candidate_loads'}
    for direction in directions:
        names.update(direction + suffix for suffix in ('_actual_run', '_actual_displacement', '_keyboard_short_sleeve', '_return_walk', '_stop_idle'))
        names.add('capture_' + direction + '-running-harbor')
        names.add(direction + ('_keyboard_long_sleeve' if (direction, 'B') in combinations else '_missing_long_sleeve_rejected'))
    for direction, garment in combinations:
        names.update((direction + garment + '_select', direction + '-' + garment + '_ten_cycles'))
    return names


def capture_path(name):
    path = Path(name)
    if path.is_absolute() or '..' in path.parts or not (SOURCE / path).is_file():
        raise ValueError('Missing or unsafe capture: ' + str(name))
    return SOURCE / path


def validate_inputs():
    candidate = json.loads((ROOT / 'candidate.json').read_text())
    garments = json.loads((ROOT / 'run-garments.json').read_text())
    candidate_hash, garment_hash = digest(ROOT / 'candidate.json'), digest(ROOT / 'run-garments.json')
    expected = {(direction, garment) for garment, directions in garments['recipes'].items() for direction in directions}
    if not expected:
        raise ValueError('Empty expected combinations')
    checks = json.loads((SOURCE / 'checks.json').read_text())
    if not required_checks(candidate['directions'], expected).issubset(checks) or not all(value is True for value in checks.values()):
        raise ValueError('Missing or failed native checks')
    records = [json.loads(path.read_text()) for path in sorted(SOURCE.glob('metadata-*.json'))]
    keys = [(data['direction'], data['garment']) for data in records]
    if len(keys) != len(set(keys)) or set(keys) != expected:
        raise ValueError('Incomplete or duplicate native metadata combinations')
    project = ROOT.parents[4]
    boards = json.loads((SOURCE / 'boards.json').read_text())
    board_keys = [(data['direction'], data['garment']) for data in boards['boards']]
    if len(board_keys) != len(set(board_keys)) or set(board_keys) != expected:
        raise ValueError('Incomplete or duplicate native board combinations')
    if boards.get('script_sha256') != digest(project / 'godot2d/tests/capture_character_run_direction_boards.gd'):
        raise ValueError('Stale board script')
    if not boards.get('renderer') or boards['renderer'] == 'headless' or boards.get('output_px') != [2560,1440] or boards.get('magnifications') != [1,2] or not math.isclose(boards.get('scale',0),138/582):
        raise ValueError('Invalid native board renderer or display scale')
    if boards.get('candidate_manifest_sha256') != candidate_hash or boards.get('run_garments_sha256') != garment_hash or boards.get('walk_artifact_digest') != candidate.get('walk_artifact_digest'):
        raise ValueError('Stale native board dependencies')
    for board in boards['boards']:
        path = capture_path(board['file'])
        with Image.open(path) as picture:
            size = picture.size
        if digest(path) != board['sha256'] or size != (2560,1440):
            raise ValueError('Changed native board: ' + board['file'])
    for data in records:
        direction = data['direction']
        if data['candidate_manifest_sha256'] != candidate_hash or data['run_garments_sha256'] != garment_hash:
            raise ValueError('Stale native candidate or garment')
        for key, name in [('trial_script_sha256','dev/character_walk_trial.gd'), ('test_script_sha256','tests/test_character_run_directions_native.gd')]:
            if data[key] != digest(project / 'godot2d' / name):
                raise ValueError('Stale native script: ' + name)
        expected_frames = [frame for frame in candidate['frames'] if frame.get('direction','west') == direction]
        samples = data['samples']
        times = [sample['wall_ms'] for sample in samples]
        poses = {frame['pose_id'] for frame in expected_frames}
        if len(samples) <= 100 or {sample['pose_id'] for sample in samples} != poses or any(b <= a for a,b in zip(times,times[1:])):
            raise ValueError('Invalid native poses or sample timing')
        if times[-1] - times[0] < sum(frame['duration_ms'] for frame in expected_frames) / candidate['playback_rate'] * 10:
            raise ValueError('Native sequence shorter than ten cycles')
        captures = [sample for sample in samples if 'capture_file' in sample]
        if len(captures) < 40 or {sample['pose_id'] for sample in captures} != poses:
            raise ValueError('Incomplete native captured poses')
        for sample in captures:
            capture_path(sample['capture_file'])
    return candidate_hash, garment_hash, checks, records, boards


def main():
    candidate_hash, garment_hash, checks, records, boards = validate_inputs()
    # Stage only after every input passes. Existing final evidence survives errors.
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.native-stage-', dir=OUTPUT.parent) as temporary:
        stage = Path(temporary)
        report = {'candidate_manifest_sha256': candidate_hash, 'run_garments_sha256': garment_hash,
                  'archiver_sha256': digest(Path(__file__)), 'user_accepted': False,
                  'scope': 'Real native controls and continuous playback; not approved contact trajectories.', 'checks': checks, 'clips': {}}
        for name in ('checks.json','boards.json'):
            shutil.copy2(SOURCE / name, stage / name)
        with zipfile.ZipFile(stage / 'originals.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(SOURCE.rglob('*')):
                if path.is_file() and path.suffix in ('.png','.json'):
                    archive.write(path, path.relative_to(SOURCE))
        for data in records:
            key = data['direction'] + '-' + data['garment']
            (stage / ('metadata-' + key + '.json')).write_text(json.dumps(data,indent=2)+'\n')
            samples = data['samples']
            frames = [sample for sample in samples if 'capture_file' in sample]
            concat = stage / (key + '.ffconcat')
            lines = ['ffconcat version 1.0']
            for index, frame in enumerate(frames):
                lines += ["file '" + str(SOURCE / frame['capture_file']) + "'", 'option framerate 1000']
                if index+1 < len(frames):
                    lines += ['duration ' + str((frames[index+1]['wall_ms']-frame['wall_ms'])/1000)]
            concat.write_text('\n'.join(lines)+'\n')
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-safe','0','-f','concat','-i',str(concat),'-fps_mode','vfr','-c:v','libx264','-crf','17','-pix_fmt','yuv420p','-video_track_timescale','1000',str(stage/(key+'.mp4'))],check=True)
            concat.unlink()
            report['clips'][key] = {'samples':len(samples),'captures':len(frames),'last_wall_ms':samples[-1]['wall_ms'],
                                    'max_sample_gap_ms':max(b['wall_ms']-a['wall_ms'] for a,b in zip(samples,samples[1:])),
                                    'video':key+'.mp4','trial_script_sha256':data['trial_script_sha256']}
        for path in SOURCE.glob('*-running-harbor.png'):
            shutil.copy2(path,stage/path.name)
        for board in boards['boards']:
            shutil.copy2(SOURCE/board['file'],stage/board['file'])
        project=ROOT.parents[4]
        report['additional_current_dependency_hashes']={name:digest(project/name) for name in ['godot2d/dev/character_walk_trial.tscn','godot2d/scenes/world/harbor_exterior.tscn','godot2d/tests/test_life_farming_native.gd']}
        report['additional_dependency_scope']='Read at final archive; these files were unchanged during native capture, not retroactive process measurements.'
        report['authoring_dependency_hashes']={name:digest(ROOT/name) for name in ['build_parts.py','test_parts.py','parts-manifest.json','build_candidate.py','test_candidate.py']}
        report['authoring_dependency_scope']='Authoring rules independently bound here; the runtime garment manifest binds their actual baked output. No inference of visual acceptance.'
        report['files']={path.name:digest(path) for path in stage.iterdir() if path.is_file()}
        (stage/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        if OUTPUT.exists():
            # Preserve the prior delivery non-destructively, never replace it blindly.
            previous=OUTPUT.with_name('native-previous-'+digest(OUTPUT/'summary.json')[:12])
            if previous.exists(): raise ValueError('Previous archive already exists; choose a new delivery directory')
            OUTPUT.rename(previous)
            try: stage.rename(OUTPUT)
            except OSError:
                previous.rename(OUTPUT)
                raise
        else:
            stage.rename(OUTPUT)
    print(json.dumps(report['clips'],indent=2))


if __name__=='__main__': main()
