import copy
import hashlib
import importlib.util
import json
import math
import struct
from pathlib import Path
import tempfile
import unittest

from PIL import Image

MODULE = Path(__file__).parents[1] / 'native_contract.py'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True))


class NativeContractTests(unittest.TestCase):
    def module(self):
        self.assertTrue(MODULE.exists(), 'Native snapshot/validation module is not implemented')
        spec = importlib.util.spec_from_file_location('layout_native_contract', MODULE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def fixture(self, m, root):
        library = root / 'art/characters'
        def save(relative, value):
            write_json(library / relative, value)
            return 'art/characters/' + relative
        loco = {'resource_root': 'art/characters', 'frames': [], 'actions': {}, 'move_policy': {'walk': {'playback_rate': 0.75}}}
        for action in ['idle', 'walk']:
            loco['actions'][action] = {'directions': {}}
            for direction in m.DIRECTIONS:
                poses = []
                for i in range(1 if action == 'idle' else 4):
                    pose = f'{action}_{direction}_{i}'
                    poses.append(pose)
                    loco['frames'].append({'pose_id': pose, 'duration_ms': 80})
                loco['actions'][action]['directions'][direction] = poses
        save('builds/locomotion-r001/manifest.json', loco)
        save('builds/run-r001/candidate.json', {'resource_root': 'art/characters', 'frames': [
            {'pose_id': f'run_{d}_{i}', 'direction': d, 'duration_ms': 80} for d in m.DIRECTIONS for i in range(4)]})
        for name in ['run-garments', 'run-diagnostics']:
            save('builds/run-r001/' + name + '.json', {'resource_root': 'art/characters'})
        farming = {'clips': []}
        for action in ['hoe', 'water', 'harvest']:
            for direction in m.DIRECTIONS:
                for garment in ['A', 'B']:
                    candidate = save(f'builds/farm-{action}-{direction}-{garment}/candidate.json', {
                        'resource_root': 'art/characters', 'frames': [{'duration_ms': 200} for _ in range(4)]})
                    farming['clips'].append({'action_id': action, 'direction': direction, 'garment': garment, 'candidate': candidate})
        save('reviews/farming/catalog.json', farming)
        wardrobe = {'samples': []}
        parents = {}
        for identity in m.WARDROBE_IDS:
            path = save(f'builds/wardrobe-{identity}/sample.json', {'resource_root': 'art/characters', 'frames': [{'duration_ms': 100} for _ in range(4)]})
            parents[identity] = path
            wardrobe['samples'].append({'id': identity, 'sample': path})
        save('reviews/wardrobe/catalog.json', wardrobe)
        heads = {'samples': []}
        for identity in m.HEADWEAR_IDS:
            path = save(f'builds/headwear-{identity}/sample.json', {'resource_root': 'art/characters', 'parent_sample': parents[identity], 'frames': [{'duration_ms': 100} for _ in range(4)]})
            heads['samples'].append({'id': identity, 'sample': path})
        save('reviews/headwear/catalog.json', heads)
        save('reviews/static-candidates/catalog.json', {'categories': {}})
        save('static-index.json', {'candidate_count': 60})
        asset = library / 'sources/fixture.png'; asset.parent.mkdir(parents=True); asset.write_bytes(b'bound source')
        save('migrations/2026-10-resource-layout/dynamic-path-map.json', {
            'resource_root': 'art/characters', 'files': [{'new_path': 'art/characters/sources/fixture.png', 'new_sha256': sha(asset)}],
            'core': {'old/manifest.json': 'art/characters/builds/locomotion-r001/manifest.json'}})
        for relative in m.SUBJECT_SCRIPTS:
            path = root / relative; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('extends RefCounted\n')
        dev = root / 'godot2d/dev/characters'
        (dev / 'character_motion_review.tscn').write_text('[node name="Slot" type="Control" parent="Margin/Rows/Views/Reference"]\ncustom_minimum_size = Vector2(224, 240)\n[node name="Slot" type="Control" parent="Margin/Rows/Views/Motion"]\ncustom_minimum_size = Vector2(224, 240)\n')
        (dev / 'character_walk_trial.tscn').write_text('[node name="TrialUI" type="CanvasLayer" parent="."]\ntransform = Transform2D(2, 0, 0, 2, 0, 0)\n')
        support = root / 'godot2d/tests/life_test_support.gd'; support.write_text('extends RefCounted\n')
        native = root / m.SUBJECT_SCRIPTS[0]
        native.write_text('extends SceneTree\nconst S=preload("res://tests/life_test_support.gd")\n')
        write_json(root / 'godot2d/project.godot', {})

    def evidence(self, m, directory):
        repo = directory / 'repo'; repo.mkdir()
        self.fixture(m, repo)
        evidence = directory / 'evidence'; evidence.mkdir()
        contract_path = evidence / 'input-contract.json'
        contract = m.snapshot(repo, contract_path)
        subjects = {('res://' + path[len('godot2d/'):] if path.startswith('godot2d/') else str(repo / path)): digest
                    for path, digest in contract['expected_subjects'].items()}
        checks = dict.fromkeys(m.required_checks(contract, subjects), True)
        timing = []; wall = 1000
        for group, spec in contract['groups'].items():
            durations = spec['durations_ms']; total = sum(durations); cumulative = 0
            phases = []
            for duration in durations:
                phases.append(cumulative + duration / 2); cumulative += duration
            if spec['kind'] == 'panel': phases.append(0)
            elapsed = 0; last = 0
            for phase in phases:
                elapsed += (phase - last) % total; last = phase; wall += 100
                pose = next(i for i in range(4) if phase < sum(durations[:i+1]))
                row = {'clip': group, 'wall_ms': wall, 'phase_ms': phase, 'phase_f64_le': struct.pack('<d', phase).hex(), 'pose': pose}
                if spec['kind'] == 'panel':
                    row['unwrapped_ms'] = elapsed
                    row['unwrapped_f64_le'] = struct.pack('<d', elapsed).hex()
                timing.append(row)
            wall += 100
        outputs = {}
        for name, size in contract['outputs'].items():
            path = evidence / name; path.parent.mkdir(exist_ok=True)
            Image.new('RGBA', tuple(size), (70, 90, 110, 255)).save(path)
            outputs[name] = sha(path)
        report = {'timing_precision': 'ieee754-f64-le', 'input_contract_sha256': sha(contract_path), 'started_utc': contract['created_utc'], 'finished_utc': contract['created_utc'],
                  'renderer': 'Metal', 'subjects': subjects, 'checks': checks, 'timing': timing, 'output_hashes': outputs}
        report_path = evidence / 'report.json'; write_json(report_path, report)
        return repo, contract_path, report_path, evidence / 'receipt.json', report

    def test_raw_double_boundaries_are_authoritative(self):
        m = self.module()
        for durations in ([200, 200, 200, 200], [200, 500, 50, 250]):
            group = {'kind': 'world', 'durations_ms': durations, 'loop': False}
            contract = {'groups': {'world-water-south-bare': group}}
            for target in range(4):
                rows = []; previous = 0
                for i, duration in enumerate(durations):
                    boundary = previous + duration
                    phase = math.nextafter(float(boundary), 0) if i == target else previous + duration/2
                    rows.append({'clip': 'world-water-south-bare', 'wall_ms': 1000+i*100,
                                 'phase_ms': float(boundary) if i == target else phase,
                                 'phase_f64_le': struct.pack('<d', phase).hex(), 'pose': i})
                    previous = boundary
                with self.subTest(durations=durations, target=target):
                    m.validate_timing(contract, rows)
                    # Both internal boundaries (including 200/700/750) and the
                    # final half-open upper bound use actual bits, never rounding.
                    rows[target]['phase_f64_le'] = struct.pack('<d', float(sum(durations[:target+1]))).hex()
                    with self.assertRaises(ValueError): m.validate_timing(contract, rows)

    def test_exact_bits_are_required_and_finite(self):
        m = self.module()
        groups = {'panel': {'kind': 'panel', 'durations_ms': [100]*4, 'loop': True}}
        rows = []
        for i, (phase, elapsed, pose) in enumerate([(50,50,0), (150,150,1), (250,250,2), (350,350,3), (0,400,0)]):
            rows.append({'clip': 'panel', 'wall_ms': i*100, 'phase_ms': phase, 'unwrapped_ms': elapsed,
                         'phase_f64_le': struct.pack('<d', phase).hex(),
                         'unwrapped_f64_le': struct.pack('<d', elapsed).hex(), 'pose': pose})
        m.validate_timing({'groups': groups}, rows)
        # A pre-final raw value just below total remains mid-cycle even when
        # BOTH JSON summaries round up to total; the following wrap completes it.
        mid_loop = copy.deepcopy(rows)
        below_total = math.nextafter(400.0, 0)
        mid_loop[3].update(phase_ms=400., unwrapped_ms=400.,
                           phase_f64_le=struct.pack('<d', below_total).hex(),
                           unwrapped_f64_le=struct.pack('<d', below_total).hex())
        m.validate_timing({'groups': groups}, mid_loop)
        for field in ['phase_f64_le', 'unwrapped_f64_le']:
            for value in [None, '', '00', 'g'*16, '00 '*8, struct.pack('<d', math.inf).hex(), struct.pack('<d', math.nan).hex()]:
                with self.subTest(field=field, value=value):
                    damaged = copy.deepcopy(rows)
                    if value is None: damaged[0].pop(field)
                    else: damaged[0][field] = value
                    with self.assertRaises(ValueError): m.validate_timing({'groups': groups}, damaged)
        # Rounded summaries must never promote an incomplete raw cycle to complete.
        damaged = copy.deepcopy(rows)
        final = math.nextafter(400.0, 0)
        damaged[-1].update(phase_ms=400.0, phase_f64_le=struct.pack('<d', final).hex(),
                           unwrapped_ms=400.0, unwrapped_f64_le=struct.pack('<d', final).hex(), pose=3)
        with self.assertRaises(ValueError): m.validate_timing({'groups': groups}, damaged)

    def test_raw_monotonicity_and_one_ulp_accumulation_are_not_rounded_away(self):
        m = self.module()
        world = {'kind': 'world', 'durations_ms': [200]*4, 'loop': False}
        rows = []
        for i, phase in enumerate([100., 300., math.nextafter(300., 0), 500., 700.]):
            rows.append({'clip': 'world', 'wall_ms': i*100, 'phase_ms': round(phase),
                         'phase_f64_le': struct.pack('<d', phase).hex(),
                         'pose': next(j for j in range(4) if phase < (j+1)*200)})
        with self.assertRaisesRegex(ValueError, 'backwards'): m.validate_timing({'groups': {'world': world}}, rows)
        group = {'kind': 'panel', 'durations_ms': [100]*4, 'loop': True}
        rows = []
        for i, (phase, elapsed, pose) in enumerate([(50.,50.,0), (150.,150.,1), (250.,250.,2), (350.,350.,3), (0.,400.,0)]):
            rows.append({'clip': 'panel', 'wall_ms': i*100, 'phase_ms': phase, 'unwrapped_ms': elapsed,
                         'phase_f64_le': struct.pack('<d', phase).hex(),
                         'unwrapped_f64_le': struct.pack('<d', elapsed).hex(), 'pose': pose})
        rows[1]['unwrapped_f64_le'] = struct.pack('<d', math.nextafter(150., 0)).hex()
        with self.assertRaisesRegex(ValueError, 'accumulated|unwrapped'): m.validate_timing({'groups': {'panel': group}}, rows)
        rows[1]['unwrapped_f64_le'] = struct.pack('<d', 150.).hex()
        rows[0].update(phase_ms=0., phase_f64_le=struct.pack('<d', 0.).hex(),
                       unwrapped_ms=0., unwrapped_f64_le=struct.pack('<d', -0.).hex())
        # Even a sign-bit change of zero is not the producer's recorded sum.
        with self.assertRaisesRegex(ValueError, 'unwrapped'): m.validate_timing({'groups': {'panel': group}}, rows)

    def test_v1_contract_is_rejected(self):
        m = self.module()
        with tempfile.TemporaryDirectory(prefix='coastal-native-contract-', dir='/private/tmp') as tmp:
            _, contract, report, receipt, _ = self.evidence(m, Path(tmp))
            old = json.loads(contract.read_text()); old['schema_version'] = 1
            old['kind'] = 'coastal-character-layout-native-input-v1'; write_json(contract, old)
            with self.assertRaisesRegex(ValueError, 'Unknown native contract'): m.validate(contract, report, receipt)
            self.assertFalse(receipt.exists())

    def test_static_closure_binds_resources_and_ignores_declared_output_paths(self):
        m = self.module()
        with tempfile.TemporaryDirectory(prefix='coastal-native-contract-', dir='/private/tmp') as tmp:
            repo = Path(tmp); self.fixture(m, repo)
            asset = repo / 'godot2d/assets/input.tres'; asset.parent.mkdir()
            asset.write_text('[gd_resource type="Resource" format=3]\n')
            fixture = repo / m.SUBJECT_SCRIPTS[0]
            fixture.write_text(fixture.read_text() + 'const Bound=preload("res://assets/input.tres")\nvar output="res://verification-v2"\nvar f=FileAccess.open("res://verification-v2/output.json", FileAccess.WRITE)\n')
            contract = m.build_contract(repo)
            self.assertIn('godot2d/assets/input.tres', contract['files'])
            self.assertFalse(any('verification-v2' in key for key in contract['files']))
            asset.unlink()
            with self.assertRaises(ValueError): m.build_contract(repo)

    def test_complete_contract_and_report_validate(self):
        m = self.module()
        with tempfile.TemporaryDirectory(prefix='coastal-native-contract-', dir='/private/tmp') as tmp:
            repo, contract, report, receipt, data = self.evidence(m, Path(tmp))
            result = m.validate(contract, report, receipt)
            self.assertEqual(result['output_count'], 129)
            self.assertIs(result['archive_allowed'], True)
            self.assertEqual(result['input_contract_sha256'], sha(contract))
            self.assertEqual(result['native_report_sha256'], sha(report))
            self.assertEqual(result['panel_cycle_count'], 65)
            self.assertEqual(result['world_clip_count'], 16)
            self.assertEqual(len(data['subjects']), 46)
            self.assertIn('godot2d/tests/life_test_support.gd', json.loads(contract.read_text())['files'])

    def test_reject_missing_extra_or_truncated_png_without_writing_receipt(self):
        m = self.module()
        for defect in ['missing', 'extra', 'truncated', 'size']:
            with self.subTest(defect=defect), tempfile.TemporaryDirectory(prefix='coastal-native-contract-', dir='/private/tmp') as tmp:
                _, contract, report, receipt, data = self.evidence(m, Path(tmp))
                name = next(iter(data['output_hashes'])); image = report.parent / name
                if defect == 'missing': image.unlink()
                elif defect == 'extra': (report.parent / 'boards/extra.png').write_bytes(image.read_bytes())
                elif defect == 'truncated': image.write_bytes(image.read_bytes()[:-16]); data['output_hashes'][name] = sha(image)
                else: Image.new('RGBA', (1,1)).save(image); data['output_hashes'][name] = sha(image)
                write_json(report, data)
                with self.assertRaises(ValueError): m.validate(contract, report, receipt)
                self.assertFalse(receipt.exists())

    def test_reject_bad_timing_subjects_checks_and_changed_snapshot_inputs(self):
        m = self.module()
        for defect in ['timing_missing', 'timing_pose', 'timing_wall', 'cycle_short', 'subject_extra', 'subject_missing', 'check_missing', 'check_false', 'input_changed', 'digest_changed', 'utc', 'precision']:
            with self.subTest(defect=defect), tempfile.TemporaryDirectory(prefix='coastal-native-contract-', dir='/private/tmp') as tmp:
                repo, contract, report, receipt, data = self.evidence(m, Path(tmp))
                if defect == 'timing_missing': data['timing'] = [r for r in data['timing'] if r['pose'] != 3]
                elif defect == 'timing_pose': data['timing'][0]['pose'] = 3
                elif defect == 'timing_wall': data['timing'][1]['wall_ms'] = data['timing'][0]['wall_ms'] - 1
                elif defect == 'cycle_short':
                    data['timing'][4]['unwrapped_ms'] = 319
                    data['timing'][4]['unwrapped_f64_le'] = struct.pack('<d', 319).hex()
                elif defect == 'subject_extra': data['subjects'][str(repo/'extra')] = '0'*64
                elif defect == 'subject_missing': data['subjects'].pop(next(iter(data['subjects'])))
                elif defect == 'check_missing': data['checks'].pop('real_gpu')
                elif defect == 'check_false': data['checks']['real_gpu'] = False
                elif defect == 'input_changed': (repo/'art/characters/sources/fixture.png').write_bytes(b'changed')
                elif defect == 'digest_changed':
                    changed = json.loads(contract.read_text()); changed['created_utc'] = '2000-01-01T00:00:00Z'; write_json(contract, changed)
                    data['input_contract_sha256'] = sha(contract)
                elif defect == 'precision': data.pop('timing_precision')
                else: data['started_utc'] = '2000-01-01T00:00:00Z'
                write_json(report, data)
                with self.assertRaises(ValueError): m.validate(contract, report, receipt)
                self.assertFalse(receipt.exists())

    def test_receipt_aliases_never_overwrite_evidence(self):
        m = self.module()
        with tempfile.TemporaryDirectory(prefix='coastal-native-contract-', dir='/private/tmp') as tmp:
            _, contract, report, receipt, data = self.evidence(m, Path(tmp))
            for protected in [contract, report, report.parent / next(iter(data['output_hashes']))]:
                before = protected.read_bytes()
                for kind in ['direct', 'symlink', 'hardlink']:
                    with self.subTest(target=protected.name, kind=kind):
                        destination = protected if kind == 'direct' else receipt
                        if kind == 'symlink': destination.symlink_to(protected)
                        if kind == 'hardlink': destination.hardlink_to(protected)
                        with self.assertRaises(ValueError): m.validate(contract, report, destination)
                        self.assertEqual(protected.read_bytes(), before)
                        if destination == receipt: destination.unlink()


if __name__ == '__main__': unittest.main()
