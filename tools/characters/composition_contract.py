"""Fixed-head target-canvas composition over one validated schema-one recipe.

This does not re-execute opaque historical source extraction or create releases.
Registered views retain separately bound source, ownership and registration data.
"""
from pathlib import Path, PurePosixPath
import re
from PIL import Image, ImageChops

from build_contract import (KIND, MODEL, Validated, digest, identifier, keys,
                            read_json, require, safe_file, validate)

RULES = {
    'bare': ('none', {}, ['base']),
    'hair': ('binary-rgba-replace', {'hair': 'hair'}, ['base', 'hair']),
    'hat': ('supported-alpha-stack', {'far_hat': 'hat', 'near_hat': 'hat'}, ['far_hat', 'base', 'near_hat']),
    'hair_hat': ('supported-alpha-stack', {'far_hat': 'hat', 'under_hat_hair': 'hair', 'near_hat': 'hat'}, ['far_hat', 'base', 'under_hat_hair', 'near_hat']),
}
SPACES = {'source_crop_local', 'source_full_frame', 'returned_source_full_frame', 'target_pose_full_frame'}


def support(image):
    return image.getchannel('A').point(lambda a: 255 if a else 0)


def compose(base, frame, image):
    """Use exact RGBA replacement or preserve base RGBA outside head support."""
    if frame['operation'] == 'none':
        return base
    layers = {layer['id']: image(layer['texture']) for layer in frame['layers']}
    if frame['operation'] == 'binary-rgba-replace':
        return Image.composite(layers['hair'], base, support(layers['hair']))
    result = Image.new('RGBA', base.size)
    selected = Image.new('L', base.size)
    for layer_id in frame['layer_order']:
        texture = base if layer_id == 'base' else layers[layer_id]
        result = Image.alpha_composite(result, texture)
        if layer_id != 'base':
            selected = ImageChops.lighter(selected, support(texture))
    return Image.composite(result, base, selected)


def validate_composition(repo, recipe_path, recipe):
    library = Path(repo) / 'art/characters'
    keys(recipe, 'kind schema_version resource_root character_model_id recipe_id revision base_recipe head_state slots clips authoring_inputs', 'schema2 recipe')
    require(recipe['kind'] == KIND and type(recipe['schema_version']) is int and recipe['schema_version'] == 2, 'Unsupported schema2')
    require(recipe['resource_root'] == 'art/characters' and recipe['character_model_id'] == MODEL, 'Wrong schema2 model/root')
    identifier(recipe['recipe_id']); identifier(recipe['revision'])
    relative = recipe_path.relative_to(library).as_posix()
    require(relative == f"recipes/{recipe['recipe_id']}/{recipe['revision']}.json", 'Recipe identity/path mismatch')
    dependencies = {relative: digest(recipe_path)}
    documents = {}

    def reference(ref, namespace=None, canvas=None, mask=False, binary=False):
        keys(ref, 'file sha256', 'reference')
        require(isinstance(ref['sha256'], str) and re.fullmatch('[0-9a-f]{64}', ref['sha256']), 'Invalid SHA256')
        path = safe_file(library, ref['file'], namespace)
        if ref['file'] in dependencies:
            require(dependencies[ref['file']] == ref['sha256'], 'Conflicting dependency SHA')
        else:
            require(digest(path) == ref['sha256'], 'SHA mismatch: ' + ref['file'])
            dependencies[ref['file']] = ref['sha256']
        if canvas is not None or mask:
            with Image.open(path) as image:
                require(image.format == 'PNG', 'Expected PNG: ' + ref['file'])
                if canvas is not None:
                    require(image.size == tuple(canvas), 'Image canvas mismatch: ' + ref['file'])
                if mask:
                    require(image.mode in {'L', 'RGBA'}, 'Invalid ownership mask')
                if binary:
                    require(image.mode == 'L' and set(image.get_flattened_data()) <= {0, 255}, 'Selection must be binary L mask')
        return path

    def record(ref, namespace=None):
        path = reference(ref, namespace)
        if ref['file'] not in documents:
            documents[ref['file']] = read_json(path)
        return documents[ref['file']]

    def image(ref):
        with Image.open(reference(ref)) as im:
            require(im.format == 'PNG', 'Expected PNG')
            return im.convert('RGBA')

    def merged(deps):
        for name, value in deps.items():
            require(name not in dependencies or dependencies[name] == value, 'Conflicting dependency SHA')
            dependencies[name] = value

    base_path = reference(recipe['base_recipe'], 'recipes')
    require(base_path != recipe_path, 'Self-referencing base recipe')
    base_record = record(recipe['base_recipe'], 'recipes')
    require(type(base_record.get('schema_version')) is int and base_record['schema_version'] == 1, 'Base must use schema1; nested composition forbidden')
    base = validate(repo, base_path)
    merged(base.dependencies)
    template = record(base.recipe['template'])
    motion = record(base.recipe['motion_set'])
    state = recipe['head_state']
    require(isinstance(state, str) and state in RULES, 'Unknown head state')
    operation, expected_layers, order = RULES[state]
    slots = recipe['slots']
    require(isinstance(slots, dict) and set(slots) == set(expected_layers.values()), 'Head state/slots mismatch')
    namespaces = {}
    registered_views = {}
    for slot, ref in slots.items():
        design = record(ref, 'parts')
        require(design.get('category', slot) == slot and ref['file'] == f"parts/{identifier(design['design_id'])}/design.json", 'Head design/category mismatch')
        namespaces[slot] = str(PurePosixPath(ref['file']).parent) + f"/adaptations/{template['template_id']}/{motion['motion_set_id']}"
        adaptations = design.get('adaptations')
        require(isinstance(adaptations, list) and adaptations, 'Head design adaptations missing')
        registered_views[slot] = []
        for path in adaptations:
            require(isinstance(path, str) and path.startswith('adaptations/'), 'Invalid head adaptation path')
            path = str(PurePosixPath(ref['file']).parent / path)
            data = record({'file': path, 'sha256': digest(safe_file(library, path, namespaces[slot]))})
            require(data.get('design_id') == design['design_id'] and data.get('template_id') == template['template_id'], 'Head adaptation identity mismatch')
            require(isinstance(data.get('views'), list) and all(v.get('slot') in ({'hair', 'hair_under_hat'} if slot == 'hair' else {'hat'}) for v in data['views']), 'Head adaptation slot mismatch')
            registered_views[slot].extend(data['views'])
    require(isinstance(recipe['authoring_inputs'], list), 'Invalid authoring inputs')
    for ref in recipe['authoring_inputs']:
        require(isinstance(ref, dict) and isinstance(ref.get('file'), str) and ref['file'].split('/')[0] in {'sources','templates','parts','builds'}, 'Wrong authoring namespace')
        reference(ref)

    def bundle_for(ref):
        path = ref['file']
        require(path.startswith('sources/'), 'Wrong source bundle namespace')
        bundle = record(ref, 'sources')
        source_id = identifier(bundle.get('source_id'))
        require(path == f'sources/{source_id}/source.json', 'Noncanonical source bundle')
        require(isinstance(bundle.get('assets'), list), 'Source bundle assets missing')
        return bundle

    def source_bound(source, bundle):
        require(any((x.get('new_path') == 'art/characters/' + source['file'] and x.get('new_sha256') == source['sha256']) or
                    (x.get('file') == source['file'] and x.get('sha256') == source['sha256']) for x in bundle['assets']), 'Source not bound by source bundle')

    def legacy_asset(extraction_ref, extraction, bundle, role):
        """Resolve one exact old relative name via this bundle's manifest alias."""
        assets = bundle['assets']
        manifest_aliases = [x for x in assets if x.get('new_path') == 'art/characters/' + extraction_ref['file'] and x.get('new_sha256') == extraction_ref['sha256']]
        require(len(manifest_aliases) == 1, 'Extraction not bound by source bundle')
        alias = extraction.get('files', {}).get(role)
        require(isinstance(alias, str), 'Extraction role missing: ' + role)
        old_manifest = PurePosixPath(manifest_aliases[0]['old_path'])
        # Absolute repository aliases and manifest-local filenames are distinct.
        old = str(PurePosixPath(alias)) if alias.startswith('art/') else str(old_manifest.parent / alias)
        matches = [x for x in assets if x.get('old_path') == old]
        require(matches and len({(x.get('new_path'), x.get('new_sha256')) for x in matches}) == 1, 'Missing exact extraction alias: ' + role)
        asset = matches[0]
        require(asset['new_path'].startswith('art/characters/'), 'Extraction alias outside library')
        expected_sha = extraction.get('sha256', {}).get(alias)
        require(expected_sha == asset['new_sha256'], 'Extraction alias SHA mismatch')
        return {'file': asset['new_path'][len('art/characters/'):], 'sha256': expected_sha}

    def extraction_binds(extraction_ref, extraction, value):
        """Bind a migrated texture/mask through its exact old-path alias and SHA."""
        bundle_path = str(PurePosixPath(extraction_ref['file']).parents[1] / 'source.json')
        bundle = bundle_for({'file': bundle_path, 'sha256': digest(safe_file(library, bundle_path, 'sources'))})
        manifests = [x for x in bundle['assets'] if x.get('new_path') == 'art/characters/' + extraction_ref['file'] and x.get('new_sha256') == extraction_ref['sha256']]
        require(len(manifests) == 1, 'Extraction not bound by source bundle')
        parent = PurePosixPath(manifests[0]['old_path']).parent
        for asset in bundle['assets']:
            if asset.get('new_path') != 'art/characters/' + value['file'] or asset.get('new_sha256') != value['sha256']:
                continue
            old = PurePosixPath(asset['old_path'])
            if not old.is_relative_to(parent):
                continue
            alias = old.relative_to(parent).as_posix()
            expected = extraction.get('sha256', {}).get(alias, extraction.get('files', {}).get(alias))
            if expected == value['sha256']:
                return
        raise ValueError('Asset not bound by exact extraction alias/SHA: ' + value['file'])

    def registered_inputs(reg, refs, explicit_extraction_sources=()):
        doc = record(reg['document'], 'builds')
        inputs = doc.get('inputs')
        require(isinstance(inputs, dict) and inputs, 'Missing or invalid registered inputs')
        for ref in refs:
            keys(ref, 'file sha256', 'registered input reference')
            if ref['file'] not in inputs:
                # Only an existing original_manifest source-view record can
                # delegate its returned source/ownership to that exact bound
                # extraction. Its view, selection and extraction stay direct.
                require(ref['file'] in explicit_extraction_sources, 'Registered input missing: ' + ref['file'])
            else:
                require(inputs[ref['file']] == ref['sha256'], 'Registered input SHA mismatch: ' + ref['file'])

    def registration(reg, texture, clip, old_frame):
        keys(reg, 'document record texture_field extraction', 'head registration')
        doc = record(reg['document'], 'builds')
        registered_inputs(reg, [texture] + ([reg['extraction']] if reg['extraction'] is not None else []))
        require(doc.get('template_id') == template['template_id'], 'Registration template mismatch')
        # The same head sample includes its matching idle frame under /idle.
        require(doc.get('direction') == clip['direction'], 'Registration direction mismatch')
        require(clip['action_id'] == 'idle' or doc.get('action_id') == clip['action_id'], 'Registration action mismatch')
        parent_name = doc.get('parent_sample')
        require(isinstance(parent_name, str) and parent_name.startswith('art/characters/'), 'Missing registration parent')
        parent_name = parent_name[len('art/characters/'):]
        require(parent_name in base.dependencies and base.dependencies[parent_name] == doc.get('parent_sha256'), 'Registration parent SHA not bound by base')
        parent = record({'file': parent_name, 'sha256': doc['parent_sha256']})
        require(doc.get('action_id') == parent.get('action_id') and any(c['action_id'] == doc.get('action_id') and c['direction'] == clip['direction'] for c in base.recipe['clips']), 'Registration parent action mismatch')
        require(parent.get('template_id') == template['template_id'] and parent.get('direction') == clip['direction'], 'Registration parent identity mismatch')
        parent_slots = parent.get('recipe', {}).get('slots')
        expected_slots = {s: PurePosixPath(r['file']).parent.name for s, r in base.recipe['slots'].items() if s != 'body'}
        require(parent_slots == expected_slots, 'Registration parent wardrobe mismatch')
        pointer = reg['record']
        match = re.fullmatch(r'/(frames/([0-9]+)|idle)/parts/([a-z][a-z0-9_]*)(/source_views/([0-9]+))?', pointer) if isinstance(pointer, str) else None
        require(match is not None, 'Invalid head registration record')
        if match.group(1) == 'idle':
            require(clip['action_id'] == 'idle', 'Registration action/idle mismatch')
            frame = doc.get('idle', {})
            parent_frame = parent.get('idle', {})
        else:
            require(clip['action_id'] == doc.get('action_id'), 'Registration action mismatch')
            index = int(match.group(2))
            require(index < len(doc.get('frames', [])) and index < len(parent.get('frames', [])), 'Registration frame missing')
            frame = doc['frames'][index]; parent_frame = parent['frames'][index]
        require(frame.get('pose_id') == old_frame['pose_id'] and frame.get('duration_ms') == old_frame['duration_ms'], 'Registration pose/timing mismatch')
        require(parent_frame.get('pose_id') == old_frame['pose_id'] and parent_frame.get('duration_ms') == old_frame['duration_ms'], 'Registration parent pose/timing mismatch')
        require(frame.get('canvas_px', doc.get('canvas_px')) == clip['canvas_px'] and frame.get('root_anchor_px', doc.get('root_anchor_px')) == clip['root_anchor_px'] and frame.get('display_scale', doc.get('display_scale')) == clip['display_scale'], 'Registration geometry mismatch')
        base_reg = old_frame['registration']
        if base_reg is not None:
            require(base_reg['document'] == {'file':parent_name, 'sha256':doc['parent_sha256']}, 'Registration parent differs from base pose')
        part = frame.get('parts', {}).get(match.group(3))
        require(isinstance(part, dict), 'Registration part missing')
        require(part.get('placement_mode') == 'full_frame' and part.get('offset_px') == [0,0] and part.get('local_scale') == [1,1], 'Unsupported head registration transform')
        leaf = part
        if match.group(4):
            i = int(match.group(5)); sources = part.get('source_views', [])
            require(i < len(sources), 'Registration source view missing')
            leaf = sources[i]
        field = reg['texture_field']
        require(field in {'registered_file','near_file','far_file'} and leaf.get(field) == texture['file'], 'Registered texture does not match record')
        require('sha256' not in leaf or leaf['sha256'] == texture['sha256'], 'Registered texture SHA mismatch')
        expected_extraction = leaf.get('extraction_manifest', leaf.get('original_manifest'))
        require((reg['extraction'] is None) == (expected_extraction is None), 'Missing or extra extraction registration')
        extraction = None
        if reg['extraction'] is not None:
            require(reg['extraction']['file'] == expected_extraction, 'Extraction registration mismatch')
            extraction = record(reg['extraction'], 'sources')
            require(extraction.get('pose_id') == old_frame['pose_id'] and extraction.get('canvas_px') == clip['canvas_px'], 'Extraction pose/canvas mismatch')
            for field in ('runtime_placement_px','runtime_full_frame_placement_px'):
                require(field not in extraction or extraction[field] == [0,0], 'Unsupported extraction runtime transform')
            require(extraction.get('local_scale') == [1,1], 'Unsupported extraction scale')
        return leaf, extraction

    def validate_layer(layer, clip, old_frame):
        keys(layer, 'id slot texture registration provenance', 'head layer')
        identifier(layer['id'])
        slot = layer['slot']
        require(slot in namespaces, 'Unknown head layer slot')
        reference(layer['texture'], namespaces[slot], clip['canvas_px'])
        keys(layer['registration'], 'document record texture_field extraction', 'head registration')
        expected_field = {'far_hat':'far_file', 'near_hat':'near_file'}.get(layer['id'], 'registered_file')
        require(layer['registration']['texture_field'] == expected_field, 'Head layer registration role mismatch')
        leaf, layer_extraction = registration(layer['registration'], layer['texture'], clip, old_frame)
        compatibility = [data['compatible_hat_manifest_sha256'] for data in (leaf, layer_extraction) if isinstance(data, dict) and 'compatible_hat_manifest_sha256' in data]
        pointer = layer['registration']['record']
        head_doc = record(layer['registration']['document'])
        prefix = pointer.split('/parts/')[0]
        registered_frame = head_doc['idle'] if prefix == '/idle' else head_doc['frames'][int(prefix.split('/')[2])]
        role = 'hat' if slot == 'hat' else 'hair'
        if layer['id'] == 'under_hat_hair' and 'hair_under_hat' in registered_frame['parts']:
            role = 'hair_under_hat'
            require('compatible_hat_manifest_sha256' in leaf, 'Missing under-hat compatibility claim')
        require(pointer == prefix + '/parts/' + role, 'Head layer registered role mismatch')
        if layer_extraction is not None:
            extraction_binds(layer['registration']['extraction'], layer_extraction, layer['texture'])
        require(any(v.get('pose_id') == old_frame['pose_id'] and v.get('view') == leaf for v in registered_views[slot]), 'Head view not registered by design adaptation')
        provenance = layer['provenance']
        keys(provenance, 'kind source_views', 'head provenance')
        sources = provenance['source_views']; kind = provenance['kind']
        require(isinstance(sources, list), 'Missing source views')
        require((kind == 'registered-source-view' and len(sources) == 1) or (kind == 'binary-source-selection' and len(sources) >= 2), 'Invalid source selection kind/count')
        combined = Image.new('RGBA', tuple(clip['canvas_px']))
        selected = Image.new('L', combined.size)
        expected_sources = leaf.get('source_views')
        if kind == 'binary-source-selection':
            require(isinstance(expected_sources, list) and len(expected_sources) == len(sources), 'Multi-source registration missing')
        for index, source in enumerate(sources):
            keys(source, 'view selection source source_bundle source_ownership source_ownership_space registration', 'head source view')
            reference(source['view'], namespaces[slot], clip['canvas_px'])
            record_view, extraction = registration(source['registration'], source['view'], clip, old_frame)
            compatibility.extend(data['compatible_hat_manifest_sha256'] for data in (record_view, extraction) if isinstance(data, dict) and 'compatible_hat_manifest_sha256' in data)
            delegated = (source['source']['file'], source['source_ownership']['file']) if 'original_manifest' in record_view and extraction is not None else ()
            registered_inputs(source['registration'], [source['source'], source['source_ownership']] + ([source['selection']] if source['selection'] is not None else []), delegated)
            reference(source['source'], 'sources')
            with Image.open(reference(source['source'])) as original:
                require(original.format == 'PNG', 'Source must be PNG')
                original.verify()
            bundle = bundle_for(source['source_bundle'])
            require(str(PurePosixPath(source['source']['file']).parents[1] / 'source.json') == source['source_bundle']['file'], 'Noncanonical source bundle')
            source_bound(source['source'], bundle)
            reference(source['source_ownership'], mask=True)
            space = source['source_ownership_space']
            require(space in SPACES, 'Unknown source ownership space')
            if 'source' in record_view:
                require(source['source']['file'] == record_view['source'] and source['source_ownership']['file'] == record_view.get('source_ownership'), 'Source/ownership differs from registered provenance')
                coordinates = record_view.get('source_ownership_coordinates', {})
                require(space == coordinates.get('space') and coordinates.get('pose_id') == old_frame['pose_id'], 'Source ownership coordinates mismatch')
                reference(source['source_ownership'], canvas=coordinates.get('canvas_px'), mask=True)
                if extraction is not None:
                    require(legacy_asset(source['registration']['extraction'], extraction, bundle, 'source_full_frame') == source['source'], 'Extraction source mismatch')
                    require(legacy_asset(source['registration']['extraction'], extraction, bundle, 'source_ownership') == source['source_ownership'], 'Extraction ownership mismatch')
            else:
                # Existing multi-source entries can reference their complete
                # returned-source extraction rather than repeat its source path.
                require(extraction is not None and 'original_manifest' in record_view, 'Missing explicit source provenance')
                require(legacy_asset(source['registration']['extraction'], extraction, bundle, 'source_full_frame') == source['source'], 'Extraction source mismatch')
                require(legacy_asset(source['registration']['extraction'], extraction, bundle, 'source_ownership') == source['source_ownership'], 'Extraction ownership mismatch')
                coordinates = extraction.get('source_ownership_coordinates', {})
                require(space == coordinates.get('space') and coordinates.get('pose_id') == old_frame['pose_id'], 'Source ownership coordinates mismatch')
                reference(source['source_ownership'], canvas=coordinates.get('canvas_px'), mask=True)
            if kind == 'registered-source-view':
                require(source['view'] == layer['texture'] and source['selection'] is None and source['registration'] == layer['registration'], 'Invalid direct registered view')
            else:
                expected = expected_sources[index]
                require(isinstance(source['selection'], dict), 'Missing binary source selection')
                require(expected.get('registered_file') == source['view']['file'] and expected.get('sha256') == source['view']['sha256'] and expected.get('ownership') == source['selection']['file'], 'Source selection differs from registered sources')
                reference(source['selection'], canvas=clip['canvas_px'], mask=True, binary=True)
                require(layer_extraction is not None, 'Missing source selection extraction')
                extraction_binds(layer['registration']['extraction'], layer_extraction, source['selection'])
                with Image.open(reference(source['selection'])) as mask:
                    require(ImageChops.multiply(selected, mask).getbbox() is None, 'Overlapping binary source selection')
                    combined = Image.composite(image(source['view']), combined, mask)
                    selected = ImageChops.lighter(selected, mask)
        if kind == 'binary-source-selection':
            require(combined.tobytes() == image(layer['texture']).tobytes(), 'Binary source selection RGBA mismatch')
        return compatibility

    require(isinstance(recipe['clips'], list) and len(recipe['clips']) == len(base.recipe['clips']), 'Wrong composition clips')
    for clip, original in zip(recipe['clips'], base.recipe['clips']):
        keys(clip, 'action_id direction frames', 'composition clip')
        require((clip['action_id'], clip['direction']) == (original['action_id'], original['direction']), 'Wrong composition capability/order')
        require(isinstance(clip['frames'], list) and len(clip['frames']) == len(original['frames']), 'Missing or extra composition pose')
        for frame, old in zip(clip['frames'], original['frames']):
            keys(frame, 'pose_id operation layers layer_order', 'composition frame')
            require(frame['pose_id'] == old['pose_id'], 'Wrong composition pose/order')
            require(frame['operation'] == operation and frame['layer_order'] == order, 'Head state operation/order mismatch')
            require(isinstance(frame['layers'], list) and all(isinstance(layer, dict) for layer in frame['layers']), 'Invalid head layers')
            ids = [layer.get('id') for layer in frame['layers']]
            require(len(ids) == len(set(ids)) and set(ids) == set(expected_layers), 'Missing/duplicate head layers')
            compatibility = {}
            for layer in frame['layers']:
                require(layer.get('slot') == expected_layers[layer['id']], 'Head layer slot mismatch')
                compatibility[layer['id']] = validate_layer(layer, original, old)
            if state in {'hat', 'hair_hat'}:
                by_id = {layer['id']: layer for layer in frame['layers']}
                near = by_id['near_hat']['registration']
                far = by_id['far_hat']['registration']
                require(near['extraction'] is not None and all(near[k] == far[k] for k in ('document', 'record', 'extraction')), 'Near/far must use the same hat registration/extraction')
                if state == 'hair_hat':
                    require(all(claim == near['extraction']['sha256'] for claim in compatibility['under_hat_hair']), 'Under-hat compatibility does not match selected hat extraction')
    return Validated(Path(repo), library, recipe_path, recipe, dict(sorted(dependencies.items())), {}, base)


def render_composition(validated, render_base):
    frames = [f for clip in validated.recipe['clips'] for f in clip['frames']]
    for (name, base), frame in zip(render_base(validated.base), frames):
        yield name, compose(base, frame, validated.image)
