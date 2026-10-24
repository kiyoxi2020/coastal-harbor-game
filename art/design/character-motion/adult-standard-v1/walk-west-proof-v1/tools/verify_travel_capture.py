#!/usr/bin/env python3
"""Verify travel evidence and optional native fixture pixels, never judge gait art."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from PIL import Image, ImageChops


def check_display_scale(recorded, declared):
    # Godot JSON rounds scalar decimals; tolerate serialization noise only.
    assert math.isclose(recorded, declared, rel_tol=1e-12, abs_tol=1e-12), 'display scale changed'


def verify(directory, fixture=False):
    root = Path(directory)
    evidence = json.loads((root / 'travel-capture.json').read_text())
    manifest_path = Path(evidence['manifest_path'])
    assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == evidence['manifest_sha256']
    manifest = json.loads(manifest_path.read_text())
    assert evidence['world_speed_per_s'] == 72 and evidence['camera_zoom'] == 4
    assert evidence['screen_velocity_px_s'] == -288
    check_display_scale(evidence['display_scale'], manifest['display_scale'])
    assert evidence['requested_loops'] == 10 and evidence['root_start_x'] == 1100
    cycle = sum(frame['duration_ms'] for frame in manifest['frames'])
    assert cycle == evidence['cycle_ms']
    pass_loops = max(1, math.floor((1100 - 128) / (288 * cycle / 1000)))
    assert evidence['loops_per_pass'] == pass_loops
    records = [record for record in evidence['captures'] if record['kind'] == 'continuous']
    assert records[-1]['elapsed_ms'] >= cycle * 10
    assert len(records) >= 30
    fixed_tick = None
    for record in evidence['captures']:
        elapsed = record['elapsed_ms']
        loop = math.floor(elapsed / cycle)
        pass_index = loop // pass_loops
        expected_x = 1100 - 288 * (elapsed - pass_index * pass_loops * cycle) / 1000
        assert abs(record['root_screen_x'] - expected_x) < .001
        assert record['pass'] == pass_index and record['loop'] == loop
        assert record['root_positions_px'] == [[record['root_screen_x'], 350], [record['root_screen_x'], 730]]
        phase = elapsed % cycle
        frame_index = 0
        while phase >= manifest['frames'][frame_index]['duration_ms']:
            phase -= manifest['frames'][frame_index]['duration_ms']
            frame_index += 1
        assert record['frame'] == frame_index
        assert record['displayed_indices'] == [frame_index, frame_index]
        assert record['pose_id'] == manifest['frames'][frame_index]['pose_id']
        assert record['png_error'] == 0
        with Image.open(root / record['file']) as opened:
            assert opened.size == (1280, 900)
            image = opened.convert('RGB')
            tick = image.getpixel((1224, 342))
            if fixed_tick is None:
                fixed_tick = tick
            assert tick == fixed_tick, 'fixed ground mark moved'
            if fixture:
                for recipe, color, y in [('A', (30, 110, 220), 350), ('B', (180, 70, 130), 730)]:
                    # Distinct diagnostic garment rectangle; measure actual PNG pixels.
                    band = image.crop((0, y - 180, 1280, y))
                    difference = ImageChops.difference(band, Image.new('RGB', band.size, color))
                    channels = difference.split()
                    maximum = ImageChops.lighter(ImageChops.lighter(channels[0], channels[1]), channels[2])
                    mask = maximum.point(lambda value: 255 if value == 0 else 0)
                    bounds = mask.getbbox()
                    assert bounds is not None, 'fixture garment absent from native PNG'
                    layer = manifest['recipes'][recipe]['frames'][frame_index]['layers'][1]
                    expected_left = expected_x + (layer['offset_px'][0] - manifest['root_anchor_px'][0]) * manifest['display_scale']
                    assert abs(bounds[0] - expected_left) <= 1.1, (record['file'], recipe, bounds[0], expected_left)
    for previous, current in zip(records, records[1:]):
        assert current['wall_usec'] > previous['wall_usec']
        actual_delta = (current['wall_usec'] - previous['wall_usec']) / 1000
        assert abs(actual_delta - (current['elapsed_ms'] - previous['elapsed_ms'])) < .002
        if current['pass'] == previous['pass']:
            measured_speed = (current['root_screen_x'] - previous['root_screen_x']) / actual_delta * 1000
            assert abs(measured_speed + 288) < .05
    expected_boundaries = range(1, records[-1]['pass'] + 1)
    assert len(evidence['resets']) == len(expected_boundaries)
    for index, event in zip(expected_boundaries, evidence['resets']):
        assert event['at_elapsed_ms'] == index * pass_loops * cycle
        assert event['loop'] == index * pass_loops
        assert event['to_root_x'] == 1100
        assert event['observed_elapsed_ms'] >= event['at_elapsed_ms']
    assert {r['frame'] for r in records} == {0, 1, 2, 3}
    maximum_gap = max(b['elapsed_ms'] - a['elapsed_ms'] for a, b in zip(records, records[1:]))
    print(f"PASS native travel: {len(records)} samples, {records[-1]['elapsed_ms']:.3f} ms, {len(evidence['resets'])} declared boundary resets, max gap {maximum_gap:.3f} ms; 288px/s; fixture pixels checked={fixture}; foot contact art unassessed")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory')
    parser.add_argument('--fixture', action='store_true')
    options = parser.parse_args()
    verify(options.directory, options.fixture)
