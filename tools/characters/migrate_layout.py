"""Import selected character artifacts into the semantic library, from a fixed Git baseline.

No image resampling/painting is performed. Historical JSON retained as source records
is opaque provenance; current manifests and view indexes contain resolved library paths.
"""
from pathlib import Path, PurePosixPath
from collections import defaultdict
import argparse, copy, hashlib, json, re, subprocess
from PIL import Image, ImageChops

REPO=Path(__file__).resolve().parents[2]
LIB='art/characters'
BASELINE='379a9bc'
M='art/design/character-motion/adult-standard-v1'
SKIP_SUFFIX={'.py','.pyc','.gd','.uid','.command','.html','.log','.zip','.xz','.mp4','.gif','.DS_Store'}
META_SKIP={'inputs','sha256','hashes','counts','audit','validation','output_hashes','rejected_attempts','failed_attempts','rejected_sources','failed_sources'}

def relative(value):
    if not isinstance(value,str) or not value or value.startswith('/') or '\\' in value or ':' in value or '..' in value.split('/'):
        raise ValueError('Unsafe library-relative path: '+str(value))
    return value

def digest(data):return hashlib.sha256(data).hexdigest()
def serialized(data):return (json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode()
def slug(value):return re.sub(r'[^a-zA-Z0-9_-]+','-',value).strip('-').lower()

def compose_head(body,hair,near,far):
    rendered=Image.alpha_composite(far,body)
    if hair is not None:rendered=Image.alpha_composite(rendered,hair)
    rendered=Image.alpha_composite(rendered,near)
    support=ImageChops.lighter(near.getchannel('A'),far.getchannel('A'))
    if hair is not None:support=ImageChops.lighter(support,hair.getchannel('A'))
    support=support.point(lambda a:255 if a else 0)
    result=body.copy();result.paste(rendered,(0,0),support);return result

class AssetStore:
    def __init__(self,root):self.root=Path(root);self.records={};self.by_digest={};self.destinations={}
    def add(self,origin,data,destination):
        destination=relative(destination);sha=digest(data)
        if destination in self.destinations and self.destinations[destination]!=sha:raise ValueError('Conflicting destination: '+destination)
        destination=self.by_digest.get(sha,destination)
        path=self.root/destination;path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists() and digest(path.read_bytes())!=sha:raise ValueError('Refuse to replace different content: '+str(path))
        path.write_bytes(data);self.by_digest.setdefault(sha,destination);self.destinations[destination]=sha
        self.records[origin]={'old_path':origin,'new_path':LIB+'/'+destination,'old_sha256':sha,'new_sha256':sha,'bytes':len(data),'type':'unchanged-asset'}
        return destination

class GitReader:
    def __init__(self,repo,ref):
        self.objects={};self.repo=Path(repo);self.ref=subprocess.check_output(['git','rev-parse',ref],cwd=repo,text=True).strip();self.cache={}
        self.blobs={}
        for record in subprocess.check_output(['git','ls-tree','-rz','--full-tree','-r',self.ref],cwd=repo).split(b'\0'):
            if record:
                meta,path=record.split(b'\t',1);self.blobs[path.decode()]=meta.split()[2].decode()
    def read(self,path):
        path=relative(str(path))
        if path not in self.blobs:raise ValueError('Missing baseline resource: '+path)
        if path not in self.cache:self.cache[path]=subprocess.check_output(['git','cat-file','blob',self.blobs[path]],cwd=self.repo)
        return self.cache[path]
    def obj(self,path):
        if path not in self.objects:self.objects[path]=json.loads(self.read(path))
        return self.objects[path]

class Migration:
    def __init__(self,repo=REPO,ref=BASELINE,destination=None):
        self.repo=Path(repo);self.root=Path(destination) if destination else self.repo/LIB;self.reader=GitReader(repo,ref);self.store=AssetStore(self.root)
        self.core={};self.deps={};self.discovering=set();self.equivalence=[];self.sources=defaultdict(set);self.part_views=defaultdict(list);self.actions=[];self.recipes=[]
    def write(self,path,data):
        relative(path);out=self.root/path;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(serialized(data));return path
    def source_id(self,old):
        parts=PurePosixPath(old).parts
        unit=parts[4] if old.startswith(M+'/') and len(parts)>4 else PurePosixPath(old).parent.name
        # Human-readable generation context plus stable path disambiguator, never a blob-only namespace.
        return 'motion-'+slug(unit)+'-'+hashlib.sha256(str(PurePosixPath(old).parent).encode()).hexdigest()[:8]
    def resolve(self,value,origin):
        if not isinstance(value,str) or not value or '\n' in value or len(value)>550:return None
        candidates=[value,str(PurePosixPath(origin).parent/value)]
        if origin.endswith('/baked/export-manifest.json'):
            import posixpath
            data=self.reader.obj(origin)
            candidates.append(posixpath.normpath(str(PurePosixPath(origin).parent/data.get('source_root','..')/value)))
        for candidate in candidates:
            if candidate in self.reader.blobs:return candidate
        return None
    def import_asset(self,old,preferred=None):
        if old in self.core:return self.core[old]
        if old in self.store.records:return self.store.records[old]['new_path'][len(LIB)+1:]
        suffix=PurePosixPath(old).suffix
        if suffix in SKIP_SUFFIX or PurePosixPath(old).name=='.DS_Store':return None
        sid=self.source_id(old);name=PurePosixPath(old).name
        if preferred is None:
            folder='metadata' if suffix=='.json' else 'prompts' if suffix in {'.txt','.md'} else 'originals'
            stem=PurePosixPath(name).stem+'-'+hashlib.sha256(old.encode()).hexdigest()[:8]+suffix
            preferred=f'sources/{sid}/{folder}/{stem}'
        new=self.store.add(old,self.reader.read(old),preferred);self.sources[sid].add(old)
        if suffix=='.json' and old not in self.discovering:
            self.discovering.add(old)
            try:
                self.discover(self.reader.obj(old),old)
            finally:self.discovering.remove(old)
        if suffix=='.png':self.keep_prompt_reference(old,old)
        return new
    def keep_prompt_reference(self,value,origin):
        source=self.resolve(value,origin) or str(PurePosixPath(origin).parent/value)
        parent=str(PurePosixPath(source).parent);stem=PurePosixPath(source).stem
        def prompt_name(name):
            name=re.sub(r'-v[0-9]+$','',name.removesuffix('-prompt'))
            return name.removeprefix('raw-').removeprefix('gpt-').replace('-color-','-')
        folders={parent,parent+'/prompts',str(PurePosixPath(parent).parent/'prompts'),str(PurePosixPath(origin).parent/'prompts')}
        for path in self.reader.blobs:
            if PurePosixPath(path).suffix!='.txt' or str(PurePosixPath(path).parent) not in folders:continue
            candidate=PurePosixPath(path).stem
            if prompt_name(candidate)==prompt_name(stem) or candidate in {'prompt','generation-prompt'}:self.import_asset(path)
    def discover(self,value,origin,key=''):
        """Keep source-generation and hand-authored interfaces, omit old review outputs."""
        if isinstance(value,dict):
            for k,v in value.items():
                if k in META_SKIP or str(k).startswith('visual') or k in {'hair_hat_composite','composite','hair_hat_composite_file'}:continue
                self.discover(v,origin,str(k))
        elif isinstance(value,list):
            for v in value:self.discover(v,origin,key)
        elif isinstance(value,str):
            old=self.resolve(value,origin)
            if old and PurePosixPath(old).suffix not in SKIP_SUFFIX:self.import_asset(old)
            elif key in {'original_attempt','selected_raw','raw_file'} and PurePosixPath(value).suffix=='.png':self.keep_prompt_reference(value,origin)
    def convert(self,value,origin,dependencies,key='',context=None):
        if isinstance(value,dict):
            if context and value.get('pose_id'):context=dict(context,pose=value['pose_id'])
            if context and value.get('id') and value.get('file') and (value.get('placement_mode') or value.get('slot') or 'offset_px' in value):
                part=value['id'];slot=value.get('slot',part)
                design=value.get('design_id',context.get('slots',{}).get(slot,'__body_interface__'))
                context=dict(context,part=part,design=design)
            out={}
            for k,v in value.items():
                if k in {'inputs','artifact_digest','source_contract'}:continue
                if k in {'build_script','builder_script','compose_script'}:continue
                nk=k
                resolved=self.resolve(str(k),origin) or (self.resolve(str(k),context['secondary_origin']) if context and context.get('secondary_origin') else None)
                if resolved:
                    mapped=self.import_asset(resolved)
                    if mapped:nk=mapped;dependencies.add(mapped)
                if resolved and nk!=k and isinstance(v,str) and re.fullmatch(r'[0-9a-f]{64}',v):
                    out[nk]=digest((self.root/nk).read_bytes())
                else:out[nk]=self.convert(v,origin,dependencies,str(k),context)
            return out
        if isinstance(value,list):return [self.convert(v,origin,dependencies,key,context) for v in value]
        if isinstance(value,str):
            old=self.resolve(value,origin) or (self.resolve(value,context['secondary_origin']) if context and context.get('secondary_origin') else None)
            if old:
                preferred=None
                if context and PurePosixPath(old).suffix=='.png' and key in {'file','registered_file','near_file','far_file','complete_source','coverage','source_ownership','semantic_region','edit_mask','occlusion_mask','hair_under_hat_visible','cap_volume_mask','visible_file','coverage_mask','near_ownership','far_ownership','authored_contact'}:
                    role=context.get('part')
                    if role:
                        sub='views' if key in {'registered_file','near_file','far_file','complete_source'} else 'masks'
                        prefix=f"templates/adult-standard-v1/motions/review-motion-v1/body-views" if context['design']=='__body_interface__' else f"parts/{context['design']}/adaptations/adult-standard-v1/review-motion-v1/r001/{sub}"
                        preferred=f"{prefix}/{context['recipe']}/{context['pose']}-{context['part']}-{key}-{hashlib.sha256(old.encode()).hexdigest()[:8]}.png"
                    elif key=='file':preferred=f"builds/{context['build']}/frames/{context['pose']}-{context.get('state','frame')}.png"
                mapped=self.import_asset(old,preferred)
                if mapped:dependencies.add(mapped);return mapped
            return value
        return value
    def keep_inputs_metadata(self,old,data,deps):
        for name in ['provenance.json','source-manifest.json','generation.json']:
            adjacent=str(PurePosixPath(old).parent/name)
            if adjacent in self.reader.blobs:
                mapped=self.import_asset(adjacent)
                if mapped:deps.add(mapped)
        # Small authored metadata/prompt inputs are retained; executable copies and
        # old native evidence/contact sheets are reconstructed from the Git baseline.
        for ref in data.get('inputs',{}):
            target=self.resolve(ref,old)
            if not target:continue
            low=target.lower();suffix=PurePosixPath(target).suffix
            if suffix=='.json' and not any(t in low for t in ['/evidence/','audit','validation','receipt','test_','baseline-defects','generation-summary']):
                mapped=self.import_asset(target)
                if mapped:deps.add(mapped)
    def inputs(self,deps):
        # Include imported metadata's original source dependencies for complete provenance.
        return {p:digest((self.root/p).read_bytes()) for p in sorted(deps)}
    def record_core(self,old,new,data,deps):
        data['resource_root']=LIB;data['inputs']=self.inputs(deps)
        if data.get('artifact_digest'):data['legacy_artifact_digest']=data.pop('artifact_digest')
        if 'legacy_artifact_digest' in data:data['artifact_digest']=digest(serialized(data))
        self.write(new,data);self.core[old]=new;self.deps[old]=set(deps)
        self.store.records[old]={'old_path':old,'new_path':LIB+'/'+new,'old_sha256':digest(self.reader.read(old)),'new_sha256':digest((self.root/new).read_bytes()),'bytes':len(self.reader.read(old)),'type':'new-path-manifest'}
        return new
    def import_sample(self,old,group,sample_id):
        if old in self.core:return self.core[old]
        data=self.reader.obj(old);deps=set();build=f'{group}-{sample_id}-r001';new=f'builds/{build}/sample.json'
        parent_old=data.get('parent_sample')
        if parent_old:
            parent=self.import_sample(parent_old,'wardrobe',sample_id);data=copy.deepcopy(data);data['parent_sample']=LIB+'/'+parent;data['parent_sha256']=digest((self.root/parent).read_bytes())
        result={k:self.convert(v,old,deps,k) for k,v in data.items() if k not in {'inputs','frames','idle'}}
        converted=[]
        for frame in data['frames']+[data['idle']]:
            ctx={'recipe':f'{group}-{sample_id}','build':build,'pose':frame['pose_id'],'slots':data.get('recipe',{}).get('slots',{})}
            target={k:self.convert(v,old,deps,k,ctx) for k,v in frame.items() if k not in {'states','parts','file'}}
            if 'file' in frame:target['file']=self.convert(frame['file'],old,deps,'file',ctx)
            if 'states' in frame:
                target['states']={state:self.convert(rec,old,deps,'states',dict(ctx,state=state)) for state,rec in frame['states'].items()}
            if 'parts' in frame:
                target['parts']={}
                for part,record in frame['parts'].items():
                    design='hair-chestnut-short-v1' if part.startswith('hair') else 'hat-straw-navy-band-v1' if part=='hat' else data.get('recipe',{}).get('slots',{}).get(part,part)
                    part_context=dict(ctx,part=part,design=design)
                    extraction=self.resolve(record.get('extraction_manifest'),old)
                    if extraction:part_context['secondary_origin']=extraction
                    converted_part=self.convert(record,old,deps,part,part_context);target['parts'][part]=converted_part
                    self.part_views[design].append({'recipe_id':ctx['recipe'],'pose_id':frame['pose_id'],'part_id':part,'view':converted_part,'scope':'Exact imported sample only; no compatibility beyond declared pose and recipe.'})
            converted.append(target)
        result['frames']=converted[:-1];result['idle']=converted[-1]
        self.keep_inputs_metadata(old,data,deps)
        result['migration_origin']={'commit':self.reader.ref,'path':old,'sha256':digest(self.reader.read(old))}
        self.record_core(old,new,result,deps)
        self.recipes.append({'recipe_id':f'{group}-{sample_id}','recipe':data.get('recipe',{}),'template_id':data['template_id'],'action_id':data['action_id'],'direction':data['direction'],'build':new,'scope':group+' sampled-not-exhaustive'})
        self.compare_frames(old,new,'sample')
        return new
    def compare_semantics(self,old,a,b):
        ignored={'resource_root','inputs','source_contract','artifact_digest','legacy_artifact_digest','migration_origin','source_root','build_script','builder_script','compose_script'}
        reverse={record['new_path'][len(LIB)+1:]:record['old_sha256'] for record in self.store.records.values()}
        sha_map={record['new_sha256']:record['old_sha256'] for record in self.store.records.values()}
        loc=self.core.get(M+'/locomotion-v1/baked/export-manifest.json')
        if loc:
            l=json.loads((self.root/loc).read_bytes());original=self.reader.obj(M+'/locomotion-v1/baked/export-manifest.json')
            sha_map[l['artifact_digest']]=original['artifact_digest']
        def canonical(value,is_new,secondary=None):
            if isinstance(value,dict):
                if not is_new and value.get('extraction_manifest'):secondary=self.resolve(value['extraction_manifest'],old)
                result={}
                for key,item in value.items():
                    if key in ignored:continue
                    newkey=canonical(key,is_new,secondary)
                    result[newkey]=canonical(item,is_new,secondary)
                return result
            if isinstance(value,list):return [canonical(x,is_new,secondary) for x in value]
            if isinstance(value,str):
                if is_new:
                    local=value[len(LIB)+1:] if value.startswith(LIB+'/') else value
                    if local in reverse:return 'resource:'+reverse[local]
                    if '/' in local and (self.root/local).is_file():return 'resource:'+digest((self.root/local).read_bytes())
                    return sha_map.get(value,value)
                path=self.resolve(value,old) or (self.resolve(value,secondary) if secondary else None)
                if path in self.store.records:return 'resource:'+self.store.records[path]['old_sha256']
            return value
        left=canonical(a,False);right=canonical(b,True)
        if left!=right:
            def first(x,y,path='root'):
                if type(x)!=type(y):return path+' type'
                if isinstance(x,dict):
                    if set(x)!=set(y):return path+' keys '+str(set(x)^set(y))
                    for key in x:
                        if x[key]!=y[key]:return first(x[key],y[key],path+'.'+str(key))
                elif isinstance(x,list):
                    if len(x)!=len(y):return path+' count'
                    for i,(one,two) in enumerate(zip(x,y)):
                        if one!=two:return first(one,two,path+'['+str(i)+']')
                return path+' values '+str(x)[:90]+' != '+str(y)[:90]
            raise ValueError('Semantic configuration changed in '+old+': '+first(left,right))
        return True
    def compare_frames(self,old,new,kind):
        a=self.reader.obj(old);b=json.loads((self.root/new).read_bytes());records=[]
        if ('idle' in a)!=('idle' in b):raise ValueError('Idle presence changed: '+old)
        if len(a.get('frames',[]))!=len(b.get('frames',[])):raise ValueError('Pose count changed: '+old)
        self.compare_semantics(old,a,b)
        before=a.get('frames',[])+([a['idle']] if 'idle' in a else [])
        after=b.get('frames',[])+([b['idle']] if 'idle' in b else [])
        for x,y in zip(before,after):
            for field in ['pose_id','duration_ms','canvas_px','root_anchor_px','display_scale']:
                if x.get(field)!=y.get(field):raise ValueError('Changed '+field+' in '+old)
            states=x.get('states',{'frame':x});newstates=y.get('states',{'frame':y})
            for state,entry in states.items():
                if 'file' not in entry:continue
                src=self.resolve(entry['file'],old)
                if src is None:raise ValueError('Unresolved old frame '+entry['file'])
                actual=digest((self.root/newstates[state]['file']).read_bytes());expected=digest(self.reader.read(src))
                if actual!=expected:raise ValueError('Changed image '+src)
                records.append({'pose_id':x.get('pose_id'),'state':state,'sha256':actual})
        for field in ['canvas_px','root_anchor_px','display_scale','action_id','direction']:
            if a.get(field)!=b.get(field):raise ValueError('Changed '+field+' in '+old)
        self.equivalence.append({'old_path':old,'new_path':LIB+'/'+new,'kind':kind,'frame_count':len(records),'geometry_timing_preserved':True,'frames':records})
    def import_catalog(self,old,name):
        data=self.reader.obj(old);new=copy.deepcopy(data)
        if 'samples' in data:
            for before,entry in zip(data['samples'],new['samples']):
                sample=self.import_sample(before['sample'],name,before['id']);entry['sample']=LIB+'/'+sample;entry['sha256']=digest((self.root/sample).read_bytes())
        else:
            for index,before in enumerate(data['clips']):
                key='-'.join(str(before[k]) for k in ['action_id','direction','garment'])
                entry=new['clips'][index];sample=self.import_farming(before['candidate'],key);entry['candidate']=LIB+'/'+sample;entry['sha256']=digest((self.root/sample).read_bytes())
        target=f'reviews/{name}/catalog.json';self.record_core(old,target,new,set());self.compare_semantics(old,data,new)
        return target
    def import_farming(self,old,key):
        if old in self.core:return self.core[old]
        data=self.reader.obj(old);deps=set();name=slug(key);new=f'builds/farming-{name}-r001/candidate.json'
        ctx={'recipe':f'farming-{name}','build':f'farming-{name}-r001','pose':'full-frame'}
        result=self.convert(data,old,deps,context=ctx)
        for x,y in zip(data['frames'],result['frames']):
            # Give complete-frame outputs an action/pose-specific build location.
            ctx['pose']=x['pose_id'];y['file']=self.convert(x['file'],old,deps,'file',ctx)
        self.keep_inputs_metadata(old,data,deps);result['migration_origin']={'commit':self.reader.ref,'path':old,'sha256':digest(self.reader.read(old))}
        self.record_core(old,new,result,deps);self.compare_frames(old,new,'farming')
        self.actions.append({'action_id':data['action_id'],'direction':data['direction'],'garment':data.get('garment'),'poses':[{'pose_id':f['pose_id'],'duration_ms':f['duration_ms'],'phase':f.get('phase')} for f in data['frames']],'canvas_px':data['canvas_px'],'root_anchor_px':data['root_anchor_px'],'display_scale':data['display_scale'],'reference_build':new,'body_views_available':False,'scope':'Complete clothed reference, not a hidden-body template.'})
        return new
    def import_motion(self):
        old=M+'/locomotion-v1/baked/export-manifest.json';data=self.reader.obj(old);deps=set();root=str(PurePosixPath(old).parent)
        sourcebase=str((PurePosixPath(root)/data.get('source_root','..')))
        # normalize only lexical .. from the historical trusted manifest
        import posixpath
        sourcebase=posixpath.normpath(sourcebase)
        for recipe,rec in data['recipes'].items():
            for i,frame in enumerate(rec['frames']):
                self.import_asset(root+'/'+frame['file'],f'builds/locomotion-r001/frames/{recipe}_{i}.png')
        result=self.convert(data,old,deps);result['source_root']='.';result['legacy_artifact_digest']=data['artifact_digest']
        for ref in data['source_contract']:
            target=sourcebase+'/'+ref
            if target in self.reader.blobs:
                mapped=self.import_asset(target)
                if mapped:deps.add(mapped)
        result['source_contract']=self.inputs(deps)
        result['migration_origin']={'commit':self.reader.ref,'path':old,'sha256':digest(self.reader.read(old))}
        new='builds/locomotion-r001/manifest.json';self.record_core(old,new,result,deps);self.compare_semantics(old,data,result)
        count=0
        for recipe in data['recipes']:
            for a,b in zip(data['recipes'][recipe]['frames'],result['recipes'][recipe]['frames']):
                if digest(self.reader.read(root+'/'+a['file']))!=digest((self.root/b['file']).read_bytes()):raise ValueError('Locomotion frame changed')
                count+=1
        self.equivalence.append({'old_path':old,'new_path':LIB+'/'+new,'kind':'locomotion','frame_count':count,'geometry_timing_preserved':data['frames']==result['frames'] and data['actions']==result['actions']})
        runold=M+'/run-four-directions-v1/candidate.json';run=self.reader.obj(runold);deps=set()
        for frame in run['frames']:
            src=self.resolve(frame['file'],runold);self.import_asset(src,f"builds/run-r001/frames/{frame['pose_id']}-A.png")
        out=self.convert(run,runold,deps);out['walk_artifact_digest']=json.loads((self.root/'builds/locomotion-r001/manifest.json').read_bytes())['artifact_digest'];self.keep_inputs_metadata(runold,run,deps)
        self.record_core(runold,'builds/run-r001/candidate.json',out,deps);self.compare_frames(runold,'builds/run-r001/candidate.json','run')
        garmentold=M+'/run-four-directions-v1/run-garments.json';g=self.reader.obj(garmentold);deps=set()
        for recipe,directions in g['recipes'].items():
            for direction,files in directions.items():
                for i,ref in enumerate(files):
                    self.import_asset(self.resolve(ref,garmentold),f'builds/run-r001/frames/run_{direction}_{i}-{recipe}.png')
        out=self.convert(g,garmentold,deps);self.keep_inputs_metadata(garmentold,g,deps);out['candidate_manifest_sha256']=digest((self.root/'builds/run-r001/candidate.json').read_bytes())
        self.record_core(garmentold,'builds/run-r001/run-garments.json',out,deps);self.compare_semantics(garmentold,g,out)
        diagold=M+'/run-four-directions-v1/run-diagnostics.json';d=self.reader.obj(diagold);deps=set();out=self.convert(d,diagold,deps);self.keep_inputs_metadata(diagold,d,deps);out['candidate_manifest_sha256']=digest((self.root/'builds/run-r001/candidate.json').read_bytes());out['run_garments_sha256']=digest((self.root/'builds/run-r001/run-garments.json').read_bytes())
        self.record_core(diagold,'builds/run-r001/run-diagnostics.json',out,deps);self.compare_semantics(diagold,d,out)
    def indexes(self):
        for sid,origins in self.sources.items():
            assets=[self.store.records[o] for o in sorted(origins)]
            self.write(f'sources/{sid}/source.json',{'source_id':sid,'origin_commit':self.reader.ref,'assets':assets,'scope':'Necessary source/registration records imported unchanged. Legacy JSON is opaque provenance; use current view and build indexes for resolved paths.'})
        for design,views in self.part_views.items():
            self.write(f'parts/{design}/adaptations/adult-standard-v1/review-motion-v1/r001/views.json',{'design_id':design,'template_id':'adult-standard-v1','views':views,'scope':'Exact imported recipe/pose view mappings only'})
            if not (self.root/f'parts/{design}/design.json').exists():self.write(f'parts/{design}/design.json',{'design_id':design,'adaptations':['adaptations/adult-standard-v1/review-motion-v1/r001/views.json'],'status':'sampled-motion-adaptations','do_not_infer_full_compatibility':True})
        for recipe in self.recipes:self.write(f"recipes/{recipe['recipe_id']}/r001.json",recipe)
        self.write('templates/adult-standard-v1/motions/review-motion-v1/motion-set.json',{'template_id':'adult-standard-v1','motion_set_id':'review-motion-v1','locomotion':'builds/locomotion-r001/manifest.json','run':'builds/run-r001/candidate.json','farming_reference_clips':self.actions,'scope':'Current approved complete-frame and sampled component material; hidden bodies and strict contact remain incomplete.'})
        self.write('definitions/actions.json',{'actions':['idle','walk','run','hoe','water','harvest'],'scope':'Existing semantic actions only; extra actions require explicit motion data and applicable gameplay handler.'})
        self.write('definitions/slots.json',{'slots':['hair','top','pants','shoes','hat','tool'],'source_ownership_coverage_occlusion_separate':True})
    def run(self,pilot=False):
        if pilot:self.import_sample(M+'/headwear-sampling-v1/revisions/hoe-west-ear-v3/sample-build/sample.json','headwear','hoe-west')
        else:
            self.import_motion();self.import_catalog(M+'/farming-four-directions-v1/catalog-color-v2.json','farming');self.import_catalog(M+'/wardrobe-sampling-v1/catalog.json','wardrobe');self.import_catalog(M+'/headwear-sampling-v1/catalog.json','headwear')
        self.indexes();records=list(self.store.records.values())
        self.write('migrations/2026-10-resource-layout/dynamic-path-map.json',{'baseline_commit':self.reader.ref,'resource_root':LIB,'files':records,'core':{k:LIB+'/'+v for k,v in self.core.items()},'equivalence':self.equivalence})
        print(json.dumps({'pilot':pilot,'resources':len(records),'equivalent_artifacts':len(self.equivalence),'new_root':str(self.root)}))

def validate_manifest_references(root,obj):
    """Check executable asset references, excluding explicitly historical provenance."""
    root=Path(root)
    path_keys={'file','registered_file','source_ownership','registered_ownership','coverage','ownership','complete_source','near_file','far_file','extraction_manifest','semantic_region','edit_mask','occlusion_mask','hair_under_hat_visible','cap_volume_mask','visible_file','coverage_mask','near_ownership','far_ownership','authored_contact','shared_body','frame_alpha','changed_clothing_mask','visible_mask','ownership_alpha','hide_mask','hidden_mask','hidden_source'}
    for group in ['inputs','external_inputs','source_contract']:
        for rel,expected in obj.get(group,{}).items():
            relative(rel)
            if not (root/rel).is_file():raise ValueError('Missing '+group+' reference: '+rel)
            sha=expected.get('sha256') if isinstance(expected,dict) else expected
            if isinstance(sha,str) and re.fullmatch(r'[0-9a-f]{64}',sha) and digest((root/rel).read_bytes())!=sha:raise ValueError('Stale '+group+' hash: '+rel)
    def walk(value,key=''):
        if isinstance(value,dict):
            for k,v in value.items():
                if k in {'historical_provenance','migration_origin','provenance'}:continue
                walk(v,k)
        elif isinstance(value,list):
            for v in value:walk(v,key)
        elif isinstance(value,str) and key in path_keys and value:
            relative(value)
            if not (root/value).is_file():raise ValueError('Missing '+key+' asset: '+value)
    walk(obj)
    for entry in obj.get('samples',[]) if isinstance(obj.get('samples'),list) else []:
        if not entry['sample'].startswith(LIB+'/'):raise ValueError('Catalog sample outside current library')
        target=root/relative(entry['sample'][len(LIB)+1:])
        if digest(target.read_bytes())!=entry['sha256']:raise ValueError('Catalog sample SHA mismatch')
    for entry in obj.get('clips',[]) if isinstance(obj.get('clips'),list) else []:
        if not entry['candidate'].startswith(LIB+'/'):raise ValueError('Catalog candidate outside current library')
        target=root/relative(entry['candidate'][len(LIB)+1:])
        if digest(target.read_bytes())!=entry['sha256']:raise ValueError('Catalog candidate SHA mismatch')
    return True

def verify(repo=REPO,destination=None):
    root=Path(destination) if destination else Path(repo)/LIB;data=json.loads((root/'migrations/2026-10-resource-layout/dynamic-path-map.json').read_bytes());count=0
    for entry in data['files']:
        p=root/entry['new_path'][len(LIB)+1:]
        if digest(p.read_bytes())!=entry['new_sha256']:raise ValueError('Migrated resource changed: '+str(p))
        count+=1
    for path in data['core'].values():
        obj=json.loads((root/path[len(LIB)+1:]).read_bytes())
        if obj.get('resource_root')==LIB:validate_manifest_references(root,obj)
        for rel,sha in obj.get('inputs',{}).items():
            relative(rel)
            if digest((root/rel).read_bytes())!=sha:raise ValueError('Current input differs: '+rel)
    if not all(x['geometry_timing_preserved'] for x in data['equivalence']):raise ValueError('Geometry/timing changed')
    result={'passed':True,'mapped_files':count,'equivalent_artifacts':len(data['equivalence']),'equivalent_frames':sum(x['frame_count'] for x in data['equivalence'])}
    print(json.dumps(result));return result

def publish(stage,repo=REPO):
    import shutil
    stage=Path(stage).resolve();root=(Path(repo)/LIB).resolve()
    if (root/'evidence/layout-native/receipt.json').exists():raise ValueError('Validated library is immutable; create a new revision instead of republishing migration data')
    if stage==root or not str(stage).startswith('/private/tmp/coastal-'):raise ValueError('Publish requires an isolated coastal staging directory')
    verify(repo,destination=stage)
    for suite,count,key in [('farming',24,'clips'),('wardrobe',5,'samples'),('headwear',4,'samples')]:
        data=json.loads((stage/f'reviews/{suite}/catalog.json').read_bytes())
        if len(data[key])!=count:raise ValueError('Incomplete staged '+suite)
    if not (root/'migrations/2026-10-resource-layout/static-inventory.json').is_file():raise ValueError('Static migration must exist before publishing the full library')
    # These namespaces were newly generated by this migration, never old source roots.
    owned=list((root/'sources').glob('motion-*'))+list((root/'parts').glob('*/adaptations/adult-standard-v1/review-motion-v1'))
    for name in ['locomotion-r001','run-r001']:
        if (root/'builds'/name).exists():owned.append(root/'builds'/name)
    for prefix in ['farming-','wardrobe-','headwear-']:owned.extend((root/'builds').glob(prefix+'*'))
    for folder in owned:
        if folder.is_symlink():raise ValueError('Refuse to replace symlink namespace')
        shutil.rmtree(folder)
    for path in stage.rglob('*'):
        if not path.is_file():continue
        rel=path.relative_to(stage);target=root/rel
        # Static definitions are immutable inputs; the top index joins their dynamic adaptations.
        if len(rel.parts)==3 and rel.parts[0]=='parts' and rel.name=='design.json' and target.exists():continue
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
    verify(repo)
    print('Published complete rooted dynamic library; old art roots were not changed.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['pilot','import','verify','publish']);parser.add_argument('--destination',type=Path);args=parser.parse_args()
    if args.command=='verify':verify(destination=args.destination)
    elif args.command=='publish':publish(args.destination)
    else:Migration(destination=args.destination).run(pilot=args.command=='pilot')
