#!/usr/bin/env python3
"""Verify native capture evidence completeness; never judge artwork."""
import argparse
import json
from pathlib import Path
from PIL import Image


def verify(directory):
    root = Path(directory)
    evidence = json.loads((root / 'capture.json').read_text())
    records = evidence['captures']
    stills = [r for r in records if r['kind'] == 'still']
    assert {(r['background'], r['frame']) for r in stills} == {(b, i) for b in ('light', 'dark') for i in range(4)}
    continuous = [r for r in records if r['kind'] == 'continuous']
    assert continuous[-1]['elapsed_ms'] >= 10 * evidence['cycle_ms']
    assert continuous[-1]['wall_usec'] > continuous[0]['wall_usec']
    assert len(continuous) >= 40, 'insufficient continuous samples'
    assert {r['frame'] for r in continuous} == {0, 1, 2, 3}, 'continuous sequence must cover all four poses'
    intervals = [b['elapsed_ms'] - a['elapsed_ms'] for a, b in zip(continuous, continuous[1:])]
    assert min(intervals) > 0
    actual_fps = (len(continuous) - 1) * 1000 / (continuous[-1]['elapsed_ms'] - continuous[0]['elapsed_ms'])
    if 'capture_actual_fps' in evidence:
        assert abs(actual_fps - evidence['capture_actual_fps']) < 1e-5
        stats = evidence['capture_interval_stats_ms']
        assert abs(stats['min'] - min(intervals)) < 1e-5
        assert abs(stats['max'] - max(intervals)) < 1e-5
        assert abs(stats['mean'] - sum(intervals) / len(intervals)) < 1e-5
    for r in records:
        assert r['displayed_indices'] == [r['frame']] * 4
        assert r['pose_id'] == f"walk_w_{r['frame']}"
        assert r['png_error'] == 0
        with Image.open(root / r['file']) as image:
            assert image.size == (1280, 900)
    inspections = [r for r in records if r['kind'] == 'inspection']
    assert {r['source_mode'] for r in inspections} == {'original', 'mask'}
    assert evidence['artifact_digest'] and evidence['manifest_sha256']
    print(f"PASS native evidence: {len(stills)} stills, {len(continuous)} continuous samples, {continuous[-1]['elapsed_ms']:.1f} ms, >=10 loops, actual {actual_fps:.2f} fps, max gap {max(intervals):.2f} ms; artwork unassessed")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory')
    verify(parser.parse_args().directory)
