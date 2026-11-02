"""Tiny procedural schema2 registration graph; no archived art or provenance.

Names model the historical interface exercised by composition_contract, while all
pixels, selections and extraction aliases are generated in a temporary library.
"""
import copy
import json
from PIL import Image
from test_build_contract import ConstructionTests, sha


class CompositionFixture:
    def __init__(self):
        self.base = ConstructionTests('test_three_frame_action_and_matching_idle')
        self.base.fixed_profile = True
        self.base.setUp()
        self.repo, self.lib, self.write = self.base.repo, self.base.lib, self.base.write
        recipe = self.base.recipe
        # Keep the action-first ordering and pose IDs used by the negative cases.
        idle, action = recipe['clips']
        action['action_id'] = 'hoe'
        for i, frame in enumerate(action['frames']):
            frame['pose_id'] = f'hoe_west_key_{i}'
            for layer in frame['layers']: layer['pose_id'] = frame['pose_id']
        recipe['clips'] = [action, idle]
        recipe['required_capabilities'] = [{'action_id': a, 'direction': 'west'} for a in ['hoe', 'idle']]
        poses = json.loads((self.lib/action['poses']['file']).read_text())
        poses['action_id'] = 'hoe'
        for i, frame in enumerate(poses['variants']['A']['frames']): frame['pose_id'] = f'hoe_west_key_{i}'
        action['poses'] = self.write('templates/adult-standard-v1/motions/review-motion-v1/actions/hoe/r001/west/poses.json', poses)
        act = {'action_id': 'hoe', 'revision': 'r001', 'loop': True, 'directions': {'west': action['poses']['file']}}
        action['action'] = self.write('templates/adult-standard-v1/motions/review-motion-v1/actions/hoe/r001/action.json', act)
        motion = json.loads((self.lib/recipe['motion_set']['file']).read_text())
        motion['actions'] = {'hoe': action['action']['file'], 'idle': idle['action']['file']}
        recipe['motion_set'] = self.write(recipe['motion_set']['file'], motion)
        parent = {'template_id': 'adult-standard-v1', 'action_id': 'hoe', 'direction': 'west',
                  'recipe': {'slots': {'top': 'top03'}},
                  'frames': [{'pose_id': f['pose_id'], 'duration_ms': f['duration_ms']} for f in action['frames']],
                  'idle': {'pose_id': idle['frames'][0]['pose_id'], 'duration_ms': 100}}
        parent_ref = self.write('builds/procedural-parent/sample.json', parent)
        recipe['authoring_inputs'].append(parent_ref)
        self.base.save()
        self.parent = parent_ref
        self.definitions = {}
        self.views = {'hair': [], 'hat': []}
        self.namespaces = {slot: f'parts/{slot}/{name}/adult-standard-v1/review-motion-v1/r001'
                           for slot, name in [('hair', 'hair-chestnut-short-v1'), ('hat', 'hat-straw-navy-band-v1')]}
        records = []
        for clip in recipe['clips']:
            for i, frame in enumerate(clip['frames']):
                records.append((clip['action_id'], i, frame))
        # One sample binds all sources, masks, texture and extraction inputs.
        sample = {**parent, 'parent_sample': 'art/characters/'+parent_ref['file'],
                  'parent_sha256': parent_ref['sha256'], 'canvas_px': [2, 2],
                  'root_anchor_px': [1, 1], 'display_scale': 1, 'inputs': {}}
        sample['frames'] = []; sample['idle'] = None
        self.layer_data = {}
        for action_id, i, frame in records:
            pose = frame['pose_id']
            parts = {}
            # Soft alpha and transparent RGB make replacement/stack errors visible.
            hair_im = Image.new('RGBA', (2, 2), (41, 42, 43, 0)); hair_im.putpixel((0, 0), (190, 40+i, 60, 128))
            hat_im = Image.new('RGBA', (2, 2)); hat_im.putpixel((1, 0), (60, 180, 70+i, 210))
            far_im = Image.new('RGBA', (2, 2)); far_im.putpixel((0, 1), (80, 100, 220, 255))
            hat_extraction = self.extraction(pose, 'hat', {'near': hat_im, 'far': far_im})
            for ref in hat_extraction['images'].values(): sample['inputs'][ref['file']] = ref['sha256']
            for role, slot, image in [('hair', 'hair', hair_im), ('hat', 'hat', hat_im), ('hair_under_hat', 'hair', hair_im)]:
                namespace = self.namespaces[slot]
                texture = self.write(f'{namespace}/{pose}-{role}.png', image)
                source = self.write(f'sources/{pose}-{role}/originals/source.png', image)
                owner = self.write(f'sources/{pose}-{role}/originals/owner.png', Image.new('L', (2, 2), 255))
                bundle = self.write(f'sources/{pose}-{role}/source.json', {'source_id': pose+'-'+role,
                    'assets': [{'new_path': 'art/characters/'+r['file'], 'new_sha256': r['sha256']} for r in [source, owner]]})
                leaf = {'placement_mode': 'full_frame', 'offset_px': [0, 0], 'local_scale': [1, 1],
                        'registered_file': texture['file'], 'source': source['file'], 'source_ownership': owner['file'],
                        'source_ownership_coordinates': {'space': 'source_full_frame', 'pose_id': pose, 'canvas_px': [2, 2]}}
                sources = [{'view': texture, 'selection': None, 'source': source, 'source_bundle': bundle,
                            'source_ownership': owner, 'source_ownership_space': 'source_full_frame'}]
                extraction = None
                if role == 'hat':
                    near, far = hat_extraction['images']['near'], hat_extraction['images']['far']
                    leaf.update(near_file=near['file'], far_file=far['file'], extraction_manifest=hat_extraction['ref']['file'])
                    leaf.update(source=hat_extraction['source']['file'], source_ownership=hat_extraction['owner']['file'])
                    sources[0].update(view=near, source=hat_extraction['source'], source_bundle=hat_extraction['bundle'], source_ownership=hat_extraction['owner'])
                    extraction = hat_extraction['ref']; texture = near
                if role == 'hair_under_hat':
                    leaf['compatible_hat_manifest_sha256'] = hat_extraction['ref']['sha256']
                if role == 'hair_under_hat' and action_id == 'hoe' and i == 2:
                    # Two explicit, disjoint selections reconstruct the exact RGBA.
                    e = self.extraction(pose, role, {'registered': image}, selections=True)
                    texture = e['images']['registered']; extraction = e['ref']
                    leaf.update(registered_file=texture['file'], extraction_manifest=extraction['file'])
                    leaf.pop('source'); leaf.pop('source_ownership'); leaf.pop('source_ownership_coordinates')
                    leaf['source_views'] = []; sources = []
                    for j in range(2):
                        sub = self.extraction(pose, role+str(j), {'registered': image})
                        selection = e['selections'][j]
                        subleaf = {'registered_file': sub['images']['registered']['file'], 'sha256': sub['images']['registered']['sha256'],
                                   'original_manifest': sub['ref']['file'], 'ownership': selection['file']}
                        leaf['source_views'].append(subleaf)
                        sources.append({'view': sub['images']['registered'], 'selection': selection,
                                        'source': sub['source'], 'source_bundle': sub['bundle'],
                                        'source_ownership': sub['owner'], 'source_ownership_space': 'source_full_frame',
                                        '_extraction': sub['ref']})
                parts[role] = leaf
                self.layer_data[(pose, role)] = (texture, extraction, sources)
                for r in [texture, source, owner] + ([extraction] if extraction else []): sample['inputs'][r['file']] = r['sha256']
                for s in sources:
                    for key in ['view', 'source', 'source_ownership', 'selection', '_extraction']:
                        r = s.get(key)
                        if r: sample['inputs'][r['file']] = r['sha256']
                self.views[slot].append({'recipe_id': 'headwear-hoe-west', 'pose_id': pose, 'slot': role, 'part_id': role, 'view': leaf})
            row = {'pose_id': pose, 'duration_ms': frame['duration_ms'], 'parts': parts}
            if action_id == 'idle': sample['idle'] = row
            else: sample['frames'].append(row)
        document = self.write('builds/procedural-head/sample.json', sample)
        for slot, namespace in self.namespaces.items():
            name = namespace.split('/')[2]
            self.write(namespace+'/views.json', {'design_id': name, 'template_id': 'adult-standard-v1', 'views': self.views[slot]})
            self.definitions[slot] = self.write(f'parts/{slot}/{name}/design.json', {'design_id': name, 'category': slot, 'adaptations': ['adult-standard-v1/review-motion-v1/r001/views.json']})
        from composition_contract import RULES
        self.recipes = {}
        for state, slug in [('bare','bare'), ('hair','hair'), ('hat','hat'), ('hair_hat','hair-hat')]:
            operation, roles, order = RULES[state]
            head = {'kind': 'coastal-character-construction-v1', 'schema_version': 2,
                    'resource_root': 'art/characters', 'character_model_id': 'unified-composable-character-v1',
                    'recipe_id': 'headwear-hoe-west-'+slug, 'revision': 'r001', 'base_recipe': {'file': 'recipes/test/r001.json', 'sha256': sha(self.base.path)},
                    'head_state': state, 'slots': {s: self.definitions[s] for s in set(roles.values())}, 'clips': [], 'authoring_inputs': []}
            for clip in recipe['clips']:
                frames = []
                for i, frame in enumerate(clip['frames']):
                    pose = frame['pose_id']; prefix = '/idle' if clip['action_id'] == 'idle' else '/frames/'+str(i)
                    layers = []
                    for role, slot in roles.items():
                        part = 'hat' if slot == 'hat' else ('hair_under_hat' if role == 'under_hat_hair' else 'hair')
                        texture, extraction, sources = copy.deepcopy(self.layer_data[(pose, part)])
                        field = {'far_hat': 'far_file', 'near_hat': 'near_file'}.get(role, 'registered_file')
                        if role == 'far_hat':
                            registered_frame = sample['idle'] if clip['action_id'] == 'idle' else sample['frames'][i]
                            texture = self.ref(registered_frame['parts']['hat']['far_file'])
                        reg = {'document': document, 'record': prefix+'/parts/'+part, 'texture_field': field, 'extraction': extraction}
                        for j, s in enumerate(sources):
                            sub = s.pop('_extraction', None)
                            s['registration'] = {**reg, 'record': reg['record']+('/source_views/'+str(j) if len(sources)>1 else ''), 'texture_field': 'registered_file' if len(sources)>1 else field, 'extraction': sub if len(sources)>1 else extraction}
                            if role == 'far_hat': s['view'] = texture
                        layers.append({'id': role, 'slot': slot, 'texture': texture, 'registration': reg,
                                       'provenance': {'kind': 'binary-source-selection' if len(sources)>1 else 'registered-source-view', 'source_views': sources}})
                    frames.append({'pose_id': pose, 'operation': operation, 'layers': layers, 'layer_order': order})
                head['clips'].append({'action_id': clip['action_id'], 'direction': clip['direction'], 'frames': frames})
            path = 'recipes/'+head['recipe_id']+'/r001.json'; self.write(path, head); self.recipes[state] = self.lib/path

    def ref(self, path): return {'file': path, 'sha256': sha(self.lib/path)}

    def extraction(self, pose, role, images, selections=False):
        base = f'sources/{pose}-{role}-extraction'
        namespace = self.namespaces['hat' if role=='hat' else 'hair']
        source = self.write(base+'/originals/source-full-frame.png', next(iter(images.values())))
        owner = self.write(base+'/originals/source-ownership.png', Image.new('L', (2,2),255))
        textures = {k: self.write(f'{namespace}/{pose}-{role}-{k}.png', im) for k,im in images.items()}
        refs = [source, owner] + list(textures.values()); masks=[]
        if selections:
            for j in range(2):
                mask = Image.new('L',(2,2)); mask.paste(255,(j,0,j+1,2))
                masks.append(self.write(f'{namespace}/{pose}-{role}-selection{j}.png',mask))
            refs += masks
        aliases = {source['file']: 'source-full-frame.png', owner['file']: 'source-ownership.png'}
        for r in refs: aliases.setdefault(r['file'],r['file'].split('/')[-1])
        data = {'pose_id':pose,'canvas_px':[2,2],'local_scale':[1,1],
                'source_ownership_coordinates': {'space':'source_full_frame','pose_id':pose,'canvas_px':[2,2]},
                'files': {'source_full_frame':'source-full-frame.png','source_ownership':'source-ownership.png'},
                'sha256':{aliases[r['file']]:r['sha256'] for r in refs}}
        extraction = self.write(base+'/originals/manifest.json',data)
        bundle = self.write(base+'/source.json',{'source_id':pose+'-'+role+'-extraction','assets':[
            {'old_path':'procedural/'+pose+'/'+role+'/'+aliases[r['file']], 'new_path':'art/characters/'+r['file'],'new_sha256':r['sha256']} for r in refs]+[
            {'old_path':'procedural/'+pose+'/'+role+'/manifest.json','new_path':'art/characters/'+extraction['file'],'new_sha256':extraction['sha256']}]})
        return {'ref':extraction,'source':source,'owner':owner,'bundle':bundle,'images':textures,'selections':masks}

    def cleanup(self): self.base.tearDown()
