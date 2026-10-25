"""Bind the optional A/B authoring bakes to the accepted complete-frame proof."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    # Refuse runtime activation when the actual garment interface still fails.
    subprocess.run([sys.executable, str(ROOT / "test_parts.py")], check=True)
    parts = json.loads((ROOT / 'parts-manifest.json').read_text())
    inputs = dict(parts['inputs'])
    for reference, expected in inputs.items():
        path = Path(reference)
        if path.is_absolute() or '..' in path.parts or digest(ROOT / path) != expected:
            raise ValueError(f'Stale or invalid parts dependency: {reference}')
    recipes = {g: [f'baked/{g}_{i}.png' for i in range(4)] for g in ('A', 'B')}
    for g, files in recipes.items():
        for i, reference in enumerate(files):
            picture = Image.open(ROOT / reference).convert('RGBA')
            if picture.size != (512, 768):
                raise ValueError(f'Invalid canvas: {reference}')
            if g == 'A':
                approved = Image.open(ROOT / f'registered/run_west_{i}.png').convert('RGBA')
                if ImageChops.difference(picture, approved).getbbox(alpha_only=False):
                    raise ValueError(f'A no longer restores accepted frame {i}; visual review required')
            inputs[reference] = digest(ROOT / reference)
    for reference in ('candidate.json', 'parts-manifest.json', 'build_garment_candidate.py'):
        inputs[reference] = digest(ROOT / reference)
    result = {
        'candidate_manifest_sha256': digest(ROOT / 'candidate.json'),
        'scope': 'west run A/B garment authoring proof; not a release or visual acceptance',
        'inputs': dict(sorted(inputs.items())),
        'recipes': recipes,
    }
    (ROOT / 'run-garments.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Garment candidate:', digest(ROOT / 'run-garments.json'))


if __name__ == '__main__':
    build()
