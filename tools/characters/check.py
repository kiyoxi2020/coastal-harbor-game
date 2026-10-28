"""Repository gate for character construction and current production isolation.

The baseline is deliberately explicit and has no auto-refresh CLI. Updating
production character bindings or granting a release requires a separate review.
This scanner is a regression guard, not a proof of arbitrary script semantics.
"""
import argparse
import json
import os
from pathlib import Path
import re
from build_contract import KIND, MODEL, digest, read_json, require, validate
from build import verify

REPO = Path(__file__).resolve().parents[2]
BASELINE = Path(__file__).with_name('runtime-baseline.json')
RETIRED = [
    'art/design/character-motion', 'art/design/character-bodies',
    'art/design/character-candidates-v2', 'art/design/character-head-proof-v1',
    'art/design/character-clothing-proof-v1', 'art/design/character-library-v1',
    'godot2d/assets/characters/adult-standard-v1/head-proof',
    'godot2d/scenes/reviews/character_head_proof.tscn',
]
TEXT = {'.gd', '.tscn', '.tres', '.godot', '.cfg'}
REFERENCE = re.compile(r'''["']([^"'\r\n]*(?:assets/(?:player[^/"']*|characters)/|resources/player[^/"']*\.|art/characters/|art/design/character-|res://dev/characters/)[^"'\r\n]*)["']''')


def file_hashes(repo, paths):
    result = {}
    for root in paths:
        folder = repo / root
        if not folder.exists():
            continue
        candidates = [folder] if folder.is_file() else folder.rglob('*')
        for path in candidates:
            if path.is_file() and path.suffix != '.import' and path.name != '.DS_Store':
                require(not path.is_symlink(), 'Production symlink forbidden')
                result[path.relative_to(repo).as_posix()] = digest(path)
    return dict(sorted(result.items()))


def production_scan(repo):
    references, bodies = {}, {}
    project = repo / 'godot2d'
    if not project.exists():
        return references, bodies
    candidates = []
    for folder, directories, filenames in os.walk(project):
        directories[:] = [name for name in directories if not name.startswith('.')
                          and not (Path(folder) == project and name in {'dev', 'tests'})]
        candidates.extend(Path(folder)/name for name in filenames if Path(name).suffix in TEXT)
    for path in candidates:
        require(not path.is_symlink(), 'Production text symlink forbidden')
        text = path.read_text()
        matches = sorted(set(REFERENCE.findall(text)))
        key = path.relative_to(repo).as_posix()
        if matches:
            references[key] = matches
        if re.search(r'extends\s+CharacterBody2D\b|type="CharacterBody2D"', text):
            bodies[key] = True
    return dict(sorted(references.items())), dict(sorted(bodies.items()))


def capture_baseline(repo):
    """Explicit baseline authoring helper; not called by normal checks."""
    repo = Path(repo)
    production_roots = ['godot2d/assets/player-unified-v4', 'godot2d/assets/characters']
    protected = ['godot2d/scripts/player.gd', 'godot2d/scripts/player_tool_action.gd',
                 'godot2d/scenes/actors/player.tscn', 'godot2d/scenes/actors/player_tool_action.tscn']
    protected += [p.relative_to(repo).as_posix() for p in (repo/'godot2d/resources').glob('player*.tres')]
    refs, bodies = production_scan(repo)
    lib = repo / 'art/characters'
    legacy_recipes = {}
    for path in (lib/'recipes').glob('*/*.json'):
        if read_json(path).get('kind') != KIND:
            legacy_recipes[path.relative_to(repo).as_posix()] = digest(path)
    legacy_dirs = []
    for path in (lib/'builds').glob('*'):
        if path.is_dir():
            manifest = path/'manifest.json'
            if not manifest.exists() or read_json(manifest).get('kind') != 'coastal-character-review-build-v1':
                legacy_dirs.append(path.relative_to(repo).as_posix())
    return {'schema_version': 1, 'production_character_roots': production_roots,
            'protected_character_code': protected,
            'production_files': file_hashes(repo, production_roots + protected),
            'production_references': refs, 'character_body_entries': bodies,
            'legacy_recipes': legacy_recipes, 'legacy_build_directories': sorted(legacy_dirs),
            'legacy_build_files': file_hashes(repo, legacy_dirs)}


def check_repository(repo, policy=None):
    repo = Path(repo).resolve()
    policy = read_json(BASELINE) if policy is None else policy
    require(policy['schema_version'] == 1, 'Unsupported gate baseline')
    for root in RETIRED:
        require(not (repo/root).exists(), 'Recreated retired character root: ' + root)
    for path in (repo/'art/characters').rglob('*'):
        if path.is_file() and path.suffix in {'.py', '.gd', '.tscn', '.command', '.sh'}:
            raise ValueError('Per-batch authoring code in resource library: ' + str(path))
    for path in (repo/'godot2d/dev').rglob('*'):
        if path.is_file() and path.suffix in TEXT:
            text = path.read_text()
            require(not any(old in text for old in RETIRED), 'Review references retired character path: ' + str(path))
    current = file_hashes(repo, policy['production_character_roots'] + policy['protected_character_code'])
    require(current == policy['production_files'], 'Unreviewed production character assets/code change; production release gate remains closed')
    refs, bodies = production_scan(repo)
    require(refs == policy['production_references'], 'Unreviewed production character reference change')
    require(bodies == policy['character_body_entries'], 'Unregistered production character body entry')
    require(file_hashes(repo, policy['legacy_build_directories']) == policy['legacy_build_files'], 'Legacy build changed or contains unregistered files')
    for name, expected in policy['legacy_recipes'].items():
        path = repo/name
        require(path.is_file() and not path.is_symlink() and digest(path) == expected, 'Frozen legacy recipe changed: ' + name)
    lib = repo/'art/characters'
    catalog = lib/'catalog.json'
    if catalog.exists():
        data = read_json(catalog)
        require(data.get('character_model_id') == MODEL and data.get('resource_root') == 'art/characters' and data.get('production_release') is None, 'Unreviewed model or production release change')
    recipes = 0
    # rglob catches recipes placed at the wrong nesting depth as well.
    for path in (lib/'recipes').rglob('*.json'):
        relative = path.relative_to(repo).as_posix()
        if relative in policy['legacy_recipes']:
            continue
        require(read_json(path).get('kind') == KIND, 'Unregistered legacy/unknown recipe: ' + relative)
        validate(repo, path)
        recipes += 1
    builds = 0
    legacy_dirs = set(policy['legacy_build_directories'])
    for path in (lib/'builds').glob('*'):
        if path.relative_to(repo).as_posix() in legacy_dirs:
            continue
        require(path.is_dir() and not path.is_symlink() and (path/'manifest.json').is_file(), 'Unmanaged character build: ' + str(path))
        verify(repo, path)
        builds += 1
    return {'passed': True, 'strict_recipes': recipes, 'strict_builds': builds,
            'frozen_legacy_recipes': len(policy['legacy_recipes']),
            'production_release': 'closed; current player-unified-v4 preserved'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        print(json.dumps(check_repository(REPO)))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(1, str(exc) + '\n')

if __name__ == '__main__':
    main()
