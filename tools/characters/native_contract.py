#!/usr/bin/env python3
"""Freeze and validate the bounded character-layout GPU capture contract.

This validates evidence consistency, not OS input, visual approval, or an
independent measurement of movement: the fixture records those as assertions.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import sys
import struct

from PIL import Image

LIBRARY = 'art/characters'
DIRECTIONS = ('south', 'west', 'east', 'north')
WARDROBE_IDS = ('walk-west', 'run-east', 'hoe-west', 'water-south', 'harvest-north')
HEADWEAR_IDS = WARDROBE_IDS[1:]
STATES = ('bare', 'hair', 'hat', 'hair_hat')
ENTRIES = (
    'builds/locomotion-r001/manifest.json', 'builds/run-r001/candidate.json',
    'builds/run-r001/run-garments.json', 'builds/run-r001/run-diagnostics.json',
    'reviews/farming/catalog.json', 'reviews/wardrobe/catalog.json', 'reviews/headwear/catalog.json',
)
SUBJECT_SCRIPTS = (
    'godot2d/tests/characters/test_character_layout_native.gd',
    'godot2d/dev/characters/character_resource_paths.gd',
    'godot2d/dev/characters/character_walk_trial.gd',
    'godot2d/dev/characters/character_farming_review.gd',
    'godot2d/dev/characters/character_wardrobe_samples.gd',
    'godot2d/dev/characters/character_headwear_samples.gd',
)
KIND = 'coastal-character-layout-native-input-v2'
SHA = re.compile(r'^[a-f0-9]{64}$')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key: ' + key)
        result[key] = value
    return result


def read_json(path):
    return json.loads(Path(path).read_bytes(), object_pairs_hook=_unique_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Non-finite JSON: ' + value)))


def relative(value):
    require(isinstance(value, str) and value and not any(c in value for c in ('\\', ':')),
            'Invalid relative path: ' + str(value))
    require(not value.startswith('/') and all(part not in ('', '.', '..') for part in value.split('/')),
            'Invalid relative path: ' + value)
    return value


def normalize_subject(repo, value):
    require(isinstance(value, str), 'Subject path must be a string')
    if value.startswith('res://'):
        path = repo / 'godot2d' / relative(value[6:])
    elif Path(value).is_absolute():
        path = Path(value)
    else:
        path = repo / relative(value)
    try:
        return path.resolve().relative_to(repo).as_posix()
    except ValueError as error:
        raise ValueError('Subject leaves repository: ' + value) from error


def _repo_file(repo, value):
    relative(value)
    normalized = normalize_subject(repo, value)
    require('.godot' not in PurePosixPath(normalized).parts, 'Godot cache is not an input')
    path = repo / normalized
    require(path.is_file(), 'Missing input: ' + value)
    return normalized, path


def _frames(document):
    frames = document.get('frames')
    require(isinstance(frames, list) and len(frames) == 4, 'Expected four ordered poses')
    values = [frame.get('duration_ms') for frame in frames]
    require(all(type(value) in (int, float) and math.isfinite(value) and value > 0 and value == int(value)
                for value in values), 'Invalid pose durations')
    return values


def _slot_dimensions(repo):
    panel = (repo / 'godot2d/dev/characters/character_motion_review.tscn').read_text()
    slots = []
    for block in re.split(r'(?=\[node )', panel):
        if block.startswith('[node name="Slot" type="Control" parent="Margin/Rows/Views/'):
            match = re.search(r'custom_minimum_size = Vector2\((\d+), (\d+)\)', block)
            require(match is not None, 'Cannot derive panel capture dimensions')
            slots.append(tuple(map(int, match.groups())))
    require(len(slots) == 2 and slots[0] == slots[1], 'Reference/motion slots must match')
    scene = (repo / 'godot2d/dev/characters/character_walk_trial.tscn').read_text()
    block = next((part for part in re.split(r'(?=\[node )', scene)
                  if part.startswith('[node name="TrialUI" type="CanvasLayer"')), '')
    matrix = re.search(r'transform = Transform2D\(([^)]+)\)', block)
    require(matrix is not None, 'Missing native UI transform')
    values = [float(value.strip()) for value in matrix.group(1).split(',')]
    require(len(values) == 6 and values[1:3] == [0, 0] and values[0] == values[3]
            and values[0] > 0 and values[0].is_integer(), 'Unsupported native UI transform')
    return tuple(int(value * values[0]) for value in slots[0])


def layout(repo):
    """Derive exact fixture subjects, pose timing, and capture names from new inputs."""
    subjects = {LIBRARY + '/' + path for path in ENTRIES} | set(SUBJECT_SCRIPTS)
    groups = {}
    library = repo / LIBRARY
    def document(path):
        _, actual = _repo_file(repo, path)
        return read_json(actual)
    def group(identity, durations, kind='panel', rate=1.0, loop=True):
        require(len(durations) == 4 and all(value > 0 for value in durations), 'Invalid group durations')
        groups[identity] = {'kind': kind, 'durations_ms': durations, 'rate': rate, 'loop': loop}
    loco = document(LIBRARY + '/' + ENTRIES[0])
    durations_by_pose = {frame['pose_id']: frame['duration_ms'] for frame in loco['frames']}
    walk_rate = loco['move_policy']['walk']['playback_rate']
    require(_number(walk_rate) and 0 < walk_rate <= 1, 'Invalid walk playback rate')
    walk_rate = max(0.5, min(1.0, walk_rate))
    run = document(LIBRARY + '/' + ENTRIES[1])
    for direction in DIRECTIONS:
        poses = loco['actions']['walk']['directions'][direction]
        walk_ms = _frames({'frames': [{'duration_ms': durations_by_pose[pose]} for pose in poses]})
        run_ms = _frames({'frames': [frame for frame in run['frames'] if frame.get('direction') == direction]})
        for garment in ('A', 'B'):
            group(f'baseline-walk-{direction}-{garment}', walk_ms, rate=walk_rate)
            group(f'baseline-run-{direction}-{garment}', run_ms, rate=walk_rate)
    farming = document(LIBRARY + '/reviews/farming/catalog.json')['clips']
    seen = set()
    for entry in farming:
        key = (entry['action_id'], entry['direction'], entry['garment'])
        require(key not in seen and key[0] in ('hoe', 'water', 'harvest') and key[1] in DIRECTIONS
                and key[2] in ('A', 'B'), 'Invalid farming combination')
        seen.add(key); subjects.add(entry['candidate'])
        group('baseline-' + '-'.join(key), _frames(document(entry['candidate'])))
    require(len(seen) == 24, 'Farming catalog must contain 24 combinations')
    parents = set()
    for suite, expected in [('wardrobe', WARDROBE_IDS), ('headwear', HEADWEAR_IDS)]:
        entries = document(f'{LIBRARY}/reviews/{suite}/catalog.json')['samples']
        require(len(entries) == len(expected) and {entry['id'] for entry in entries} == set(expected),
                'Invalid ' + suite + ' sample set')
        for entry in entries:
            path = relative(entry['sample']); subjects.add(path)
            sample = document(path); durations = _frames(sample)
            rate = walk_rate if entry['id'].split('-')[0] in ('walk', 'run') else 1.0
            if suite == 'wardrobe':
                parents.add(path); group('wardrobe-' + entry['id'], durations, rate=rate)
            else:
                require(sample['parent_sample'] in parents, 'Headwear parent is not a wardrobe sample')
                subjects.add(sample['parent_sample'])
                for state in STATES:
                    group('headwear-' + entry['id'] + '-' + state, durations, rate=rate)
                    group('world-' + entry['id'] + '-' + state, durations, 'world', rate,
                          entry['id'].startswith('run-'))
                    if entry['id'] == 'hoe-west':
                        group('headwear-' + entry['id'] + '-' + state + '-light', durations, rate=rate)
    width, height = _slot_dimensions(repo)
    outputs = {}
    for identity, spec in groups.items():
        if spec['kind'] == 'panel':
            outputs['boards/' + identity + '.png'] = [width * (4 if identity.startswith('baseline-') else 5), height]
        else:
            for pose in range(4): outputs[f'boards/{identity}-pose-{pose}.png'] = [300, 320]
    require(len(subjects) == 46 and len(outputs) == 129, 'Unexpected fixture subject/output count')
    return subjects, groups, outputs


def build_contract(repo_root):
    repo = Path(repo_root).resolve(strict=True)
    require(repo.is_dir(), 'Invalid repository root')
    files = {}
    def bind(value, expected=None):
        normalized, path = _repo_file(repo, value)
        actual = digest(path)
        require(expected is None or actual == expected, 'Mapped input SHA mismatch: ' + value)
        require(normalized not in files or files[normalized] == actual, 'Conflicting input SHA')
        files[normalized] = actual
    dynamic = LIBRARY + '/migrations/2026-10-resource-layout/dynamic-path-map.json'
    maps = [dynamic]
    static = LIBRARY + '/migrations/2026-10-resource-layout/static-inventory.json'
    if (repo / static).exists(): maps.append(static)
    for value in maps:
        bind(value)
        manifest = read_json(repo / value)
        require(manifest.get('resource_root') == LIBRARY, 'Invalid migration resource root')
        for entry in manifest['files']: bind(entry['new_path'], entry['new_sha256'])
        core = manifest.get('core', {})
        for path in core.values(): bind(path)
    for path in (repo / LIBRARY).rglob('*.json'): bind(path.relative_to(repo).as_posix())
    for value in ('reviews/static-candidates/catalog.json', 'static-index.json'): bind(LIBRARY + '/' + value)
    seeds = [repo / path for path in SUBJECT_SCRIPTS]
    seeds += list((repo / 'godot2d/dev/characters').glob('*.gd'))
    seeds += list((repo / 'godot2d/dev/characters').glob('*.tscn'))
    seeds += [repo / 'godot2d/project.godot', repo / 'godot2d/tests/life_test_support.gd']
    visited = set()
    while seeds:
        path = seeds.pop()
        value = normalize_subject(repo, str(path))
        if value in visited: continue
        visited.add(value); bind(value)
        if path.suffix in ('.gd', '.tscn', '.tres', '.godot', '.cfg'):
            text = path.read_text()
            for match in re.finditer(r'["\'](res://[^"\'\n]+)["\']', text):
                resource = match.group(1)
                if resource in ('res://', 'res://.', 'res://..'): continue
                relative(resource[6:])
                target = repo / 'godot2d' / resource[6:]
                # Literal output directories/files are not dependencies. Resource
                # declarations and load/preload/extends targets must exist.
                mandatory = path.suffix != '.gd' or re.search(r'(?:\b(?:preload|load)\(\s*|\bextends\s*)$', text[max(0, match.start()-80):match.start()])
                if target.is_file() or mandatory: seeds.append(target)
            uid = Path(str(path) + '.uid')
            if uid.exists(): seeds.append(uid)
    subjects, groups, outputs = layout(repo)
    expected = {}
    for value in subjects:
        bind(value); normalized = normalize_subject(repo, value); expected[normalized] = files[normalized]
    contract = {'schema_version': 2, 'kind': KIND, 'repo_root': str(repo),
                'timing_precision': 'ieee754-f64-le',
                'created_utc': datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
                'validator_sha256': digest(__file__), 'files': dict(sorted(files.items())),
                'expected_subjects': dict(sorted(expected.items())), 'groups': dict(sorted(groups.items())),
                'outputs': dict(sorted(outputs.items()))}
    contract['contract_digest'] = hashlib.sha256(canonical(contract)).hexdigest()
    return contract


def _write_new(path, document):
    path = Path(path)
    require(not path.exists() and not path.is_symlink(), 'Refusing to overwrite existing evidence: ' + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open('xb') as output:
            output.write(canonical(document) + b'\n')
    except FileExistsError as error:
        raise ValueError('Evidence destination already exists: ' + str(path)) from error


def snapshot(repo_root, output):
    contract = build_contract(repo_root)
    _write_new(output, contract)
    return contract


def required_checks(contract, subjects):
    checks = {'real_gpu', 'locomotion_run_loaded', 'farming_24_loaded', 'wardrobe_five_loaded',
              'headwear_four_loaded', 'input_contract_unchanged'}
    for identity in WARDROBE_IDS: checks.add('loaded_sha_' + identity)
    for raw in subjects:
        checks.update(('subject_exists_' + raw, 'subject_unchanged_' + raw))
    for output in contract['outputs']:
        checks.add('capture_' + PurePosixPath(output).stem)
    for identity, group in contract['groups'].items():
        if group['kind'] == 'panel':
            checks.add(identity + '_native_cycle')
            checks.update(identity + '_pose_' + str(pose) for pose in range(4))
        else:
            checks.update(identity + suffix for suffix in ('_all_four_poses', '_motion_policy', '_matching_idle', '_switch_keeps_clock'))
            checks.update(identity + '_texture_' + str(pose) for pose in range(4))
            if not group['loop']: checks.add(identity + '_starts')
    for identity in HEADWEAR_IDS:
        for state in STATES: checks.add('head_control_' + identity + '-' + state)
    return checks


def _number(value):
    return type(value) in (int, float) and math.isfinite(value)


def exact_double(row, field):
    value = row.get(field)
    require(isinstance(value, str) and re.fullmatch(r'[0-9a-fA-F]{16}', value),
            'Missing or malformed raw double: ' + field)
    decoded = struct.unpack('<d', bytes.fromhex(value))[0]
    require(math.isfinite(decoded), 'Non-finite raw double: ' + field)
    return decoded


def _fposmod(value, total):
    # Match Godot's positive floating-point modulo, preserving the producer's
    # binary64 operations instead of interpreting rounded JSON summaries.
    result = math.fmod(value, total)
    return result + total if result < 0 else result


def validate_timing(contract, timing):
    require(isinstance(timing, list) and timing, 'Missing timing rows')
    rows = defaultdict(list)
    previous_wall = -1
    previous_group = None
    completed = set()
    for row in timing:
        require(isinstance(row, dict) and row.get('clip') in contract['groups'], 'Unknown timing group')
        wall = row.get('wall_ms')
        require(_number(wall) and wall >= 0 and wall == int(wall) and wall >= previous_wall, 'Non-monotone wall timing')
        previous_wall = wall
        identity = row['clip']
        if identity != previous_group:
            require(identity not in completed, 'Timing group appears in disjoint segments')
            if previous_group is not None: completed.add(previous_group)
            previous_group = identity
        rows[identity].append(row)
    require(set(rows) == set(contract['groups']), 'Missing timing groups')
    for identity, group in contract['groups'].items():
        durations = group['durations_ms']; total = sum(durations)
        seen = set(); last_phase = 0.0; last_unwrapped = 0.0
        for index, row in enumerate(rows[identity]):
            phase = exact_double(row, 'phase_f64_le'); pose = row.get('pose')
            require(_number(row.get('phase_ms')), 'Missing human-readable phase summary')
            require(_number(phase) and 0 <= phase < total, 'Invalid timing phase: ' + identity)
            require(type(pose) is int and 0 <= pose < 4, 'Invalid timing pose: ' + identity)
            require(pose == next(i for i in range(4) if phase < sum(durations[:i+1])), 'Pose does not match source timing: ' + identity)
            seen.add(pose)
            if group['kind'] == 'panel':
                elapsed = exact_double(row, 'unwrapped_f64_le')
                require(_number(row.get('unwrapped_ms')), 'Missing human-readable unwrapped summary')
                predicted = last_unwrapped + _fposmod(phase - last_phase, total)
                require(elapsed >= last_unwrapped and
                        struct.pack('<d', elapsed) == struct.pack('<d', predicted), 'Inconsistent unwrapped timing: ' + identity)
                if index < len(rows[identity]) - 1: require(elapsed < total, 'Panel continued after fixture cycle completed')
                last_unwrapped = elapsed
            elif not group['loop'] and index:
                require(phase >= last_phase, 'Tool timing moves backwards: ' + identity)
            last_phase = phase
        require(seen == {0, 1, 2, 3} and rows[identity][-1]['wall_ms'] > rows[identity][0]['wall_ms'], 'Incomplete timed pose coverage: ' + identity)
        if group['kind'] == 'panel': require(last_unwrapped >= total, 'Native preview cycle is incomplete: ' + identity)


def _utc(value):
    require(isinstance(value, str), 'Missing UTC timestamp')
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as error:
        raise ValueError('Invalid UTC timestamp') from error
    # Godot Time.get_datetime_string_from_system(true) omits the UTC suffix.
    if parsed.tzinfo is None: parsed = parsed.replace(tzinfo=timezone.utc)
    require(parsed.utcoffset().total_seconds() == 0, 'Timestamp must be UTC')
    return parsed


def _protect_receipt(receipt, paths):
    receipt = Path(receipt)
    for path in paths:
        path = Path(path)
        same_inode = receipt.exists() and path.exists() and os.path.samefile(receipt, path)
        require(receipt.resolve() != path.resolve() and not same_inode, 'Receipt aliases protected evidence: ' + str(path))
    require(not receipt.exists() and not receipt.is_symlink(), 'Receipt destination must be new')


def _png(path, size):
    require(not path.is_symlink(), 'Output cannot be a symbolic link')
    require(path.read_bytes()[-12:] == b'\x00\x00\x00\x00IEND\xaeB`\x82', 'Truncated/non-canonical PNG ending: ' + str(path))
    try:
        with Image.open(path) as image:
            require(image.format == 'PNG' and list(image.size) == size, 'Unexpected capture format/dimensions: ' + str(path))
            image.verify()
        with Image.open(path) as image: image.load()
    except (OSError, SyntaxError) as error:
        raise ValueError('Invalid PNG: ' + str(path)) from error


def validate(contract_path, report_path, receipt_path):
    contract_path, report_path, receipt_path = map(Path, (contract_path, report_path, receipt_path))
    contract, report = read_json(contract_path), read_json(report_path)
    require(contract.get('schema_version') == 2 and contract.get('kind') == KIND
            and contract.get('timing_precision') == 'ieee754-f64-le', 'Unknown native contract')
    payload = {key: value for key, value in contract.items() if key != 'contract_digest'}
    require(contract.get('contract_digest') == hashlib.sha256(canonical(payload)).hexdigest(), 'Contract canonical digest mismatch')
    require(contract.get('validator_sha256') == digest(__file__), 'Validator changed since snapshot')
    evidence = report_path.parent.resolve()
    output_paths = [evidence / relative(name) for name in contract['outputs']]
    _protect_receipt(receipt_path, [contract_path, report_path, *output_paths])
    require(report.get('input_contract_sha256') == digest(contract_path), 'Report binds another contract')
    now = datetime.now(timezone.utc)
    require(_utc(contract['created_utc']) <= _utc(report.get('started_utc')) <= _utc(report.get('finished_utc')) <= now, 'Invalid capture UTC ordering')
    repo = Path(contract['repo_root']).resolve(strict=True)
    for value, expected in contract['files'].items():
        _, path = _repo_file(repo, value)
        require(SHA.fullmatch(expected) and digest(path) == expected, 'Snapshot input changed: ' + value)
    expected = contract['expected_subjects']
    require(all(contract['files'].get(path) == value for path, value in expected.items()), 'Subjects must be a snapshot subset')
    raw_subjects = report.get('subjects')
    require(isinstance(raw_subjects, dict), 'Missing report subjects')
    normalized = {}
    for raw, value in raw_subjects.items():
        path = normalize_subject(repo, raw)
        require(path not in normalized, 'Duplicate normalized subject')
        normalized[path] = value
    require(normalized == expected, 'Report subject set/SHA mismatch')
    checks = report.get('checks')
    require(isinstance(checks, dict) and checks and all(value is True for value in checks.values()), 'Native checks are not all true')
    require(required_checks(contract, raw_subjects).issubset(checks), 'Missing required native checks')
    require(isinstance(report.get('renderer'), str) and report['renderer'].strip()
            and report['renderer'].lower() not in ('headless', 'dummy'), 'No native GPU renderer claim')
    require(report.get('timing_precision') == 'ieee754-f64-le', 'Missing original binary64 timing precision')
    validate_timing(contract, report.get('timing'))
    hashes = report.get('output_hashes')
    require(isinstance(hashes, dict) and set(hashes) == set(contract['outputs']), 'Output manifest must contain exactly 129 expected captures')
    actual_pngs = {path.relative_to(evidence).as_posix() for path in evidence.rglob('*') if path.is_file() and path.suffix.lower() == '.png'}
    require(actual_pngs == set(contract['outputs']), 'Missing or extra PNG files')
    for name, size in contract['outputs'].items():
        path = evidence / name
        require(path.resolve().is_relative_to(evidence), 'Output escapes evidence directory')
        require(isinstance(hashes[name], str) and SHA.fullmatch(hashes[name]) and digest(path) == hashes[name], 'Output SHA mismatch: ' + name)
        _png(path, size)
    receipt = {'schema_version': 2, 'kind': 'coastal-character-layout-native-validation-v2',
               'validated_utc': now.isoformat().replace('+00:00', 'Z'), 'contract_digest': contract['contract_digest'],
               'contract_sha256': digest(contract_path), 'report_sha256': digest(report_path),
               'input_contract_sha256': digest(contract_path), 'native_report_sha256': digest(report_path),
               'archive_allowed': True,
               'validator_sha256': digest(__file__), 'timing_precision': 'ieee754-f64-le', 'output_count': len(hashes), 'panel_cycle_count': 65, 'world_clip_count': 16,
               'scope': '129 native PNGs, 65 one-cycle previews, 16 world action/state-switch reports; inputs, subjects, checks and reported timing are consistent. No ten-cycle, OS input, export or visual acceptance claim.',
               'timing_limits': 'Checks original binary64 phase/unwrapped values against pose/source durations, exact modulo accumulation, ordered wall timestamps and full reported cycle coverage; JSON decimal summaries are human-readable only. Engine frame delta and world positions are not recorded, so wall-speed accuracy and movement/state-switch outcomes remain fixture assertions.'}
    # Recheck inputs/evidence before the only mutation; failed validation never writes evidence.
    for value, expected in contract['files'].items(): require(digest(repo / value) == expected, 'Input changed during validation')
    require(report.get('input_contract_sha256') == digest(contract_path) and receipt['report_sha256'] == digest(report_path), 'Evidence changed during validation')
    for name, expected_sha in hashes.items(): require(digest(evidence / name) == expected_sha, 'Output changed during validation')
    _protect_receipt(receipt_path, [contract_path, report_path, *output_paths])
    _write_new(receipt_path, receipt)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='command', required=True)
    capture = subparsers.add_parser('snapshot')
    capture.add_argument('--repo-root', type=Path, default=Path(__file__).resolve().parents[2])
    capture.add_argument('--output', type=Path, required=True)
    check = subparsers.add_parser('validate')
    for option in ('contract', 'report', 'receipt'): check.add_argument('--' + option, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = snapshot(args.repo_root, args.output) if args.command == 'snapshot' else validate(args.contract, args.report, args.receipt)
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        print('Native contract rejected: ' + str(error), file=sys.stderr)
        return 1
    print(json.dumps({'command': args.command, 'files': len(result.get('files', {})),
                      'outputs': result.get('output_count', len(result.get('outputs', {}))),
                      'contract_digest': result.get('contract_digest')}, sort_keys=True))
    return 0


if __name__ == '__main__': raise SystemExit(main())
