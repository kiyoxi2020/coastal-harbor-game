#!/usr/bin/env python3
"""Read-only candidate inventory validation; never grants visual or user approval."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

CATEGORIES = ('body', 'hair', 'top', 'pants', 'shoes', 'hat')
DIRECTIONS = ('south', 'west', 'east', 'north')
STATUSES = {'candidate', 'rejected', 'user_accepted'}
REVIEW_STATES = {'selected', 'registered', 'geometry_checked', 'swap_checked',
                 'native_checked', 'user_accepted', 'unverified', 'rework_required', 'rejected'}
SHA256 = re.compile(r'^[0-9a-f]{64}$')


def relative_file(root: Path, value: str) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise ValueError('expected a nonempty project-relative path')
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()) or '..' in Path(value).parts:
        raise ValueError('path escapes project root')
    if not path.is_file():
        raise ValueError('file missing')
    if path.stat().st_size == 0:
        raise ValueError('file empty')
    return path


def digest_file(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def referenced_files(item: dict) -> set[str]:
    """All path fields and extra declared hashes, including masks/config/evidence."""
    result = {item[k] for k in ('source', 'prompt', 'metadata', 'body_template',
                               'semantic_masks', 'recipe', 'native_config')
              if isinstance(item.get(k), str) and item[k]}
    for key in ('previews', 'components'):
        value = item.get(key, {})
        if isinstance(value, dict):
            for part in value.values():
                if isinstance(part, str) and part:
                    result.add(part)
                elif isinstance(part, list):
                    result.update(p for p in part if isinstance(p, str) and p)
    hashes = item.get('hashes', {})
    if isinstance(hashes, dict):
        result.update(k for k in hashes if isinstance(k, str))
    return result


def artifact_digest(item: dict, category: str, root: Path) -> str:
    """Bind complete candidate config plus CURRENT input bytes; no state is written."""
    config = {key: value for key, value in item.items() if key not in ('review', 'status')}
    actual = {p: digest_file(relative_file(root, p)) for p in sorted(referenced_files(item))}
    payload = {'category': category, 'candidate': config, 'actual_hashes': actual}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


def verify(catalog: dict, root: Path, expected: int = 10) -> dict:
    report = {'schema_version': 1, 'errors': [], 'warnings': [], 'categories': {},
              'scope': 'File/config/count checks only; no aesthetic, semantic-mask, swap or user approval.'}
    errors, warnings = report['errors'], report['warnings']
    if not isinstance(catalog, dict) or catalog.get('schema_version') != 1:
        errors.append('catalog: schema_version must be 1')
        return report
    categories = catalog.get('categories')
    if not isinstance(categories, dict):
        errors.append('catalog: categories must be an object')
        return report
    for extra in sorted(set(categories) - set(CATEGORIES)):
        errors.append(f'catalog: unknown category {extra}')
    bodies = {b.get('id'): b for b in categories.get('body', []) if isinstance(b, dict) and isinstance(b.get('id'), str)} if isinstance(categories.get('body'), list) else {}
    global_ids = set()
    for category in CATEGORIES:
        entries = categories.get(category)
        if not isinstance(entries, list):
            errors.append(f'{category}: expected an array')
            entries = []
        unique, complete, statuses, reviews = set(), set(), Counter(), Counter()
        for index, item in enumerate(entries):
            tag = f'{category}[{index}]'
            if not isinstance(item, dict):
                errors.append(f'{tag}: expected an object')
                continue
            item_id = item.get('id')
            tag = f'{category}/{item_id or index}'
            before = len(errors)
            if not isinstance(item_id, str) or not item_id:
                errors.append(f'{tag}: missing id')
            elif item_id in global_ids:
                errors.append(f'{tag}: duplicate id')
            else:
                global_ids.add(item_id)
            design = item.get('design_id', item_id)
            if not isinstance(design, str) or not design:
                errors.append(f'{tag}: missing design_id')
            else:
                unique.add(design)
            status = item.get('status')
            statuses[str(status)] += 1
            if not isinstance(status, str) or status not in STATUSES:
                errors.append(f'{tag}: status must be candidate/rejected/user_accepted')
            template = item.get('template_id')
            if not isinstance(template, str) or not template:
                errors.append(f'{tag}: missing template_id')
            template_hash = item.get('template_hash')
            if not isinstance(template_hash, str) or not SHA256.fullmatch(template_hash):
                errors.append(f'{tag}: missing/invalid template_hash')
            for key in ('source', 'prompt'):
                if not isinstance(item.get(key), str) or not item[key]:
                    errors.append(f'{tag}: missing {key}')
            for key in ('previews', 'components'):
                paths = item.get(key)
                if not isinstance(paths, dict):
                    errors.append(f'{tag}: incomplete {key}; four directions required')
                    continue
                for direction in DIRECTIONS:
                    value = paths.get(direction)
                    if key == 'components' and isinstance(value, list):
                        valid = bool(value) and all(isinstance(p, str) and p for p in value)
                    else:
                        valid = isinstance(value, str) and bool(value)
                    if not valid:
                        errors.append(f'{tag}: incomplete {key}.{direction}')
            hashes = item.get('hashes')
            if not isinstance(hashes, dict):
                errors.append(f'{tag}: hashes must be an object')
                hashes = {}
            for path in sorted(referenced_files(item)):
                expected_hash = hashes.get(path)
                if not isinstance(expected_hash, str) or not SHA256.fullmatch(expected_hash):
                    errors.append(f'{tag}: missing/invalid sha256: {path}')
                try:
                    current_hash = digest_file(relative_file(root, path))
                    if current_hash != expected_hash:
                        errors.append(f'{tag}: sha256 mismatch: {path}')
                except (ValueError, OSError) as exc:
                    errors.append(f'{tag}: {path}: {exc}')
            compatibility = item.get('compatibility')
            if not isinstance(compatibility, dict):
                errors.append(f'{tag}: compatibility must be separate from status')
                compatibility = {}
            body_ids = compatibility.get('body_ids')
            if not isinstance(body_ids, list) or not body_ids or not all(isinstance(b, str) for b in body_ids):
                errors.append(f'{tag}: compatibility.body_ids must be a nonempty id array')
            else:
                for body_id in body_ids:
                    body = bodies.get(body_id)
                    if not body:
                        errors.append(f'{tag}: unknown compatible body {body_id}')
                    elif body.get('template_id') != template:
                        errors.append(f'{tag}: incompatible template for {body_id}; explicit separately fitted variant required')
                    else:
                        try:
                            if digest_file(relative_file(root, body.get('source'))) != template_hash:
                                errors.append(f'{tag}: stale template_hash for {body_id}')
                        except (ValueError, OSError):
                            errors.append(f'{tag}: template_hash cannot bind {body_id} source')
            if not isinstance(compatibility.get('pose'), str) or not compatibility['pose']:
                errors.append(f'{tag}: missing compatibility.pose')
            artifact_errors = len(errors) != before
            review = item.get('review')
            if review is None:
                reviews['missing'] += 1
                warnings.append(f'{tag}: review missing; appearance/swap/native/user acceptance unverified')
            elif not isinstance(review, dict) or not isinstance(review.get('status'), str) or review.get('status') not in REVIEW_STATES:
                reviews['invalid'] += 1
                errors.append(f'{tag}: invalid review.status')
            else:
                reviews[review['status']] += 1
                try:
                    if review.get('artifact_digest') != artifact_digest(item, category, root):
                        errors.append(f'{tag}: stale/missing review artifact_digest')
                except (ValueError, OSError):
                    errors.append(f'{tag}: review cannot bind missing files')
                evidence = review.get('evidence', {})
                if not isinstance(evidence, dict):
                    errors.append(f'{tag}: review.evidence must map project paths to sha256')
                else:
                    for path, expected_hash in evidence.items():
                        try:
                            if digest_file(relative_file(root, path)) != expected_hash:
                                errors.append(f'{tag}: review evidence hash mismatch: {path}')
                        except (ValueError, OSError) as exc:
                            errors.append(f'{tag}: review evidence {path}: {exc}')
                if status == 'user_accepted' and (review['status'] != 'user_accepted' or not review.get('user_evidence')):
                    errors.append(f'{tag}: user_accepted requires review.user_evidence and matching review status')
            if status == 'user_accepted' and not isinstance(review, dict):
                errors.append(f'{tag}: user_accepted requires bound review and user evidence')
            if not artifact_errors and isinstance(status, str) and status in ('candidate', 'user_accepted') and isinstance(design, str):
                complete.add(design)
        report['categories'][category] = {'entries': len(entries), 'unique_designs': len(unique),
            'complete_designs': len(complete), 'statuses': dict(statuses), 'review_states': dict(reviews)}
        if len(unique) != expected:
            errors.append(f'{category}: {len(unique)} unique designs; expected {expected}; directions/colors/adaptations do not add designs')
        if len(complete) != expected:
            errors.append(f'{category}: incomplete usable candidate inventory {len(complete)}/{expected}; rejected/missing artifacts excluded')
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('catalog', nargs='?', type=Path, default=Path(__file__).with_name('catalog.json'))
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--expected', type=int, default=10)
    parser.add_argument('--json', action='store_true', help='print report JSON to stdout; writes no files')
    parser.add_argument('--digests', action='store_true', help='print current item digest map only; grants no review status')
    args = parser.parse_args()
    try:
        catalog = json.loads(args.catalog.read_text(encoding='utf-8'))
        if args.digests:
            value = {category: {item['id']: artifact_digest(item, category, args.root)
                     for item in entries} for category, entries in catalog['categories'].items()}
            print(json.dumps(value, ensure_ascii=False, indent=2))
            return 0
        report = verify(catalog, args.root, args.expected)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'catalog error: {exc}', file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for category, values in report['categories'].items():
            print(f'{category}: {values["complete_designs"]}/{args.expected} complete unique designs; statuses={values["statuses"]}; reviews={values["review_states"]}')
        print(f'{len(report["errors"])} errors; {len(report["warnings"])} pending-review warnings')
        for error in report['errors']:
            print(f'ERROR: {error}')
        print(report['scope'])
    return 1 if report['errors'] else 0

if __name__ == '__main__':
    sys.exit(main())
