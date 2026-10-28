"""Prepare diagnostic API inputs only. Does not generate or adopt art."""
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
MISSING = [(x, 208) for x in range(372, 377)] + [(x, 209) for x in range(371, 374)]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    contract_path = ROOT / 'contracts/idle-contract.json'
    contract = json.loads(contract_path.read_text())
    masks = {}
    for name in ('allowed_edit', 'frozen_hat'):
        record = contract['masks'][name]
        path = ROOT / 'contracts' / record['file']
        assert sha(path) == record['sha256'], name
        masks[name] = Image.open(path).convert('L')
    source_path = ROOT / 'sources/idle-contact-v2-normalized.png'
    assert sha(source_path) == 'be09d50495f16340b7936b0376391d2a5be9a23461ac91e5bbd04198291cedbb'
    source = Image.open(source_path).convert('RGBA').crop((0, 0, 512, 512))
    # An opaque neutral backing is context, never an adopted hat pixel.
    target = Image.new('RGBA', source.size, (225, 230, 232, 255))
    target.alpha_composite(source)
    mask = Image.new('RGBA', source.size, (0, 0, 0, 255))
    edited = []
    # Astra's inclusive native repair window, intersected with frozen authority.
    for y in range(199, 213):
        for x in range(366, 382):
            if masks['allowed_edit'].getpixel((x, y)) and not masks['frozen_hat'].getpixel((x, y)):
                mask.putpixel((x, y), (0, 0, 0, 0))
                edited.append((x, y))
    assert set(MISSING).issubset(edited)
    assert edited
    out = ROOT / 'masked-edit-preflight'
    out.mkdir(exist_ok=True)
    target.resize((1024, 1024), Image.Resampling.NEAREST).save(out / 'target-1024.png')
    mask.resize((1024, 1024), Image.Resampling.NEAREST).save(out / 'mask-1024.png')
    for x, y in edited:
        assert masks['allowed_edit'].getpixel((x, y))
        assert not masks['frozen_hat'].getpixel((x, y))
    prompt = '''Use case: precise-object-edit
Edit image 1, a straw hat on an opaque neutral inspection backing. Image 2 is the original character head, for fit context only. Image 3 is a diagnostic contact guide; its colored lines are not art.
Repair only the masked forehead-end inner brim. Retain the existing crown, navy band, golden outer brim, silhouette, framing and hat position. Do not draw a person, skin, face outline, hair or guide marks. Keep the neutral backing outside the hat.
At the full native 512 square coordinates, the contact line ends at (376,208), approached from (340,216). The displayed 1024 square is exactly 2x these coordinates. Create one continuous dark brown/black inner lip with real thickness connecting the current inner edge and far-side brim underside, not isolated dots or a bright golden cap surface.
The native points (372..376,208) and (371..373,209), corresponding to their exact 2x2 blocks on this image, must be inside the solid dark lip. Keep the original head opening below the approved contact line clear; do not extend a hanging strip into the face. Preserve all other geometry and all unmasked detail. Return the same 1024x1024 framing without translation or rescaling.
'''
    (out / 'prompt.txt').write_text(prompt)
    args = ['edit', '--model', 'gpt-image-2', '--image', str(out / 'target-1024.png'),
            '--image', str(ROOT / 'references/original-head-window-1024.png'),
            '--image', str(ROOT / 'references/contact-guide-1024.png'),
            '--mask', str(out / 'mask-1024.png'), '--prompt-file', str(out / 'prompt.txt'),
            '--no-augment', '--size', '1024x1024', '--quality', 'high',
            '--background', 'opaque', '--output-format', 'png',
            '--out', str(out / 'candidate-unreviewed.png')]
    report = {
        'status': 'prepared-only-api-not-called',
        'api_called': False, 'art_accepted': False, 'active_catalog_changed': False,
        'contract_sha256': sha(contract_path), 'source_sha256': sha(source_path),
        'native_window_inclusive': [366, 199, 381, 212],
        'native_edit_pixel_count': len(edited), 'api_edit_pixel_count': len(edited) * 4,
        'uncovered_contact_points': MISSING, 'missing_points_inside_mask': True,
        'edit_outside_allowed': 0, 'edit_on_frozen_hat': 0,
        'coordinate_mapping': 'whole 512-square window -> nearest 1024-square; zero placement',
        'mask_semantics': 'alpha zero permits editing; opaque protects; guidance, not a hard guarantee',
        'cli_script': '/Users/wyq/.codex/skills/.system/imagegen/scripts/image_gen.py',
        'argv_after_script': args,
        'files_sha256': {p.name: sha(p) for p in (out / 'target-1024.png', out / 'mask-1024.png', out / 'prompt.txt')},
        'adoption_gate': 'Review actual new hat surface ownership; extract only approved region at original coordinates; never adopt backing/body/guide pixels. Run unchanged source, opening, contact, frozen-art contracts and native visual checks before activation.',
        'official_docs': 'https://developers.openai.com/api/docs/guides/image-generation',
    }
    (out / 'preflight.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('status', 'native_edit_pixel_count', 'missing_points_inside_mask', 'edit_outside_allowed', 'edit_on_frozen_hat')}))


if __name__ == '__main__':
    main()
