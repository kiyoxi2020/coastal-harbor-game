"""Bound frozen source material to native raster samples, never physical contact.

Point ROIs are fixed41x41 in canonical source pixels before any screenshot is
read. No point/ROI/texture/root is fitted or changed. A good offset only proves
bounded near-opaque raster correspondence, not support, flight, sliding, soil,
legal targets, art acceptance or user approval.
"""
import argparse
from functools import lru_cache, wraps
import hashlib
import json
import math
from pathlib import Path
from PIL import Image
from build_contract import digest, read_json, require, safe_file, stable
from native_raster import measure


def contract_errors(fn):
    @wraps(fn)
    def checked(*args,**kwargs):
        try:return fn(*args,**kwargs)
        except (KeyError,TypeError,IndexError,AttributeError,OverflowError) as error:
            raise ValueError('Malformed contact evidence: '+str(error)) from error
    return checked


def integer_pair(value):
    require(isinstance(value,list) and len(value)==2 and all(type(x) is int for x in value),'Invalid integer source coordinate')
    return value


def rgba_hash(image):return hashlib.sha256(image.convert('RGBA').tobytes()).hexdigest()


def finite_vector(value,size):
    require(isinstance(value,list) and len(value)==size and all(type(v) in [int,float] and math.isfinite(v) for v in value),'Invalid actual render transform/vector')
    return value


def classify_raster(result):
    """All optimum offsets, including ties, must establish the same <=1px bound."""
    best=result['equally_good_offsets']
    require(isinstance(best,list) and best,'Missing raster optimum')
    bounded=all(math.hypot(*finite_vector(p,2))<=1 for p in best)
    rgb=result['mean_rgb_error']<=result['mean_rgb_error_limit']
    if bounded and rgb:return 'within-one-pixel',None
    if len(best)>1:return 'unverified','Ambiguous optimum does not prove all offsets within one pixel and RGB bound.'
    return 'mismatch','Unique best raster offset/error does not prove the <=1px bound.'


class BoundContactEvidence:
    """Caller pins both manifest SHA/artifact and independent source report SHA.

    This does not replace strict build.verify or raw observer validation. It
    verifies every consumed file against those frozen inputs and records the
    complete native snapshot file hashes when native samples are supplied.
    """
    @contract_errors
    def __init__(self,repo,manifest,manifest_sha256,artifact_digest,points,points_sha256):
        self.repo=Path(repo).resolve();self.library=self.repo/'art/characters';self.used={}
        self.manifest_path=Path(manifest).absolute();self.points_path=Path(points).absolute()
        require(self.manifest_path.is_relative_to(self.library/'builds'),'Manifest outside character builds')
        self._bind(self.manifest_path,manifest_sha256);self._bind(self.points_path,points_sha256)
        self.manifest=read_json(self.manifest_path);self.points=read_json(self.points_path)
        require(self.manifest['kind']=='coastal-character-review-build-v1' and self.manifest['schema_version']==1,'Wrong review manifest')
        require(self.manifest['artifact_digest']==artifact_digest and artifact_digest==hashlib.sha256(stable({'inputs':self.manifest['inputs'],'engine':self.manifest['engine']})).hexdigest(),'Artifact digest differs')
        require(self.points['kind']=='coastal-independent-actual-farm-contact-source-review-v1' and isinstance(self.points['rows'],list),'Wrong material point report')
        self.outputs={row['file']:row for row in self.manifest['outputs']};require(len(self.outputs)==len(self.manifest['outputs']),'Duplicate manifest output')
        self.head=self._json({'file':self.manifest['recipe'],'sha256':self.manifest['inputs'][self.manifest['recipe']]})
        if self.head.get('schema_version')==3:
            self.base=self.head
            self.reference_kind='schema3-body-only'
            require(self.base.get('kind')=='coastal-character-construction-v1'
                    and self.base.get('slots')=={'body':None},'Direct schema3 contact requires body-only slots')
            require(all(len(f['layers'])==1 and f['layers'][0]['slot']=='body'
                        for c in self.base['clips'] for f in c['frames']),
                    'Direct body reference contains non-body layers')
        else:
            self.base=self._json(self.head['base_recipe'])
            self.reference_kind='registered-head-composite'
            require(self.head['kind']==self.base['kind']=='coastal-character-construction-v1' and self.head['schema_version']==2 and self.base['schema_version']==3,'Contact evidence requires registered head plus schema3 body')
        self.clips={};self.head_clips={}
        for clip in self.base['clips']:
            key=clip['action_id']+'-'+clip['direction'];require(key not in self.clips,'Duplicate body clip');self.clips[key]=clip
        if self.reference_kind=='registered-head-composite':
            for clip in self.head['clips']:
                key=clip['action_id']+'-'+clip['direction'];require(key not in self.head_clips,'Duplicate head clip');self.head_clips[key]=clip
            require(set(self.clips)==set(self.head_clips),'Head/body clip scope differs')

    def _bind(self,path,expected):
        path=Path(path).absolute();require(not any(q.is_symlink() for q in [path,*path.parents]),'Contact evidence symlink forbidden')
        require(isinstance(expected,str) and len(expected)==64 and digest(path)==expected,'Bound input SHA differs: '+str(path))
        require(str(path) not in self.used or self.used[str(path)]==expected,'Conflicting frozen input');self.used[str(path)]=expected
        return path

    def _ref(self,ref):
        path=safe_file(self.library,ref['file']);require(self.manifest['inputs'].get(ref['file'])==ref['sha256'],'Reference absent from frozen manifest inputs')
        return self._bind(path,ref['sha256'])

    def _json(self,ref):return read_json(self._ref(ref))

    @lru_cache(maxsize=12)
    def _image(self,path):
        with Image.open(path) as im:
            require(im.format=='PNG','Actual image is not PNG');return im.convert('RGBA')

    def _output(self,key,pose):
        clip=self.clips[key];name=f'frames/{clip["action_id"]}/{clip["direction"]}/{pose}.png';entry=self.outputs[name]
        path=self._bind(safe_file(self.manifest_path.parent,name,'frames'),entry['sha256']);im=self._image(str(path))
        require(list(im.size)==entry['size'] and rgba_hash(im)==entry['rgba_sha256'],'Actual final PNG/RGBA differs')
        pad=self.head_clips.get(key,{}).get('output_padding_px',[0,0,0,0]);require(isinstance(pad,list) and len(pad)==4 and all(type(x) is int and x>=0 for x in pad),'Invalid whole-frame output padding')
        require(list(im.size)==[clip['canvas_px'][0]+pad[0]+pad[2],clip['canvas_px'][1]+pad[1]+pad[3]],'Whole-frame output geometry differs')
        return im,pad,entry

    @contract_errors
    def static_points(self):
        result=[];seen=set()
        for row in self.points['rows']:
            require(row['target']['kind'] in ['crop','soil-candidate'] and row['target']['source_ground_contact_proven'] is False,'Source target cannot assert unobserved ground proof')
            key=row['action']+'-'+row['direction'];clip=self.clips[key];pose=row['pose_id'];pose_doc=self._json(row['canonical_pose_document'])
            require(clip['poses']==row['canonical_pose_document'] and clip['variant']==row['variant'],'Canonical pose/variant differs from actual base clip')
            variant=pose_doc['variants'][row['variant']];frames=[f for f in variant['frames'] if f['pose_id']==pose]
            require(len(frames)==1 and any(f['pose_id']==pose for f in clip['frames']),'Canonical pose missing')
            original=frames[0];ref=row['canonical_reference'];require({k:original[k] for k in ['file','sha256']}==ref,'Canonical frame identity differs')
            require(all(clip[k]==row[k]==variant[k] for k in ['canvas_px','root_anchor_px','display_scale']),'Canonical geometry differs')
            canonical=self._image(str(self._ref(ref)));raw=self._image(str(self._ref(row['full_original_or_legacy_derived_source'])));translation=integer_pair(row['whole_frame_translation_px'])
            require(list(canonical.size)==clip['canvas_px'],'Canonical frame size differs')
            if 'whole_frame_translation_px' in original:require(original['whole_frame_translation_px']==translation,'Actual source registration differs')
            if 'source' in original:require(original['source']==row['full_original_or_legacy_derived_source']['file'] and original['source_sha256']==row['full_original_or_legacy_derived_source']['sha256'],'Actual historical full source differs')
            rebuilt=Image.new('RGBA',canonical.size);rebuilt.paste(raw,tuple(translation));require(rebuilt.tobytes()==canonical.tobytes(),'Full source translation does not reconstruct canonical reference')
            final,pad,entry=self._output(key,pose)
            for point in row['points']:
                identity=key+'/'+pose+'/'+point['id'];require(identity not in seen,'Duplicate source material point');seen.add(identity)
                item={k:point[k] for k in ['id','material','visible','hidden_mechanical_contact_observable'] if k in point}
                item.update(identity=identity,clip=key,pose_id=pose,target=row['target'],canonical_reference=ref,full_original_or_legacy_derived_source=row['full_original_or_legacy_derived_source'],output=entry,output_padding_px=pad,grip_observation=row.get('grip_observation'),source_status='source-unobservable')
                require(type(point['visible']) is bool,'Invalid source visibility')
                if not point['visible']:result.append(item);continue
                xy=integer_pair(point['canonical_px']);rawxy=integer_pair(point['source_px']);require(rawxy==[xy[i]-translation[i] for i in range(2)],'Source point registration differs')
                require(0<=xy[0]<canonical.width and 0<=xy[1]<canonical.height and 0<=rawxy[0]<raw.width and 0<=rawxy[1]<raw.height,'Source point outside actual frame')
                value=list(canonical.getpixel(tuple(xy)));require(value==point['RGBA']==list(raw.getpixel(tuple(rawxy))) and value[3]>0,'Actual canonical/source point RGBA differs')
                fp=[xy[0]+pad[0],xy[1]+pad[1]];actual=list(final.getpixel(tuple(fp)));box=[xy[0]-20,xy[1]-20,xy[0]+21,xy[1]+21]
                item.update(canonical_px=xy,source_px=rawxy,RGBA=value,final_px=fp,final_RGBA=actual,fixed_source_roi_px=box,fixed_raw_roi_px=[rawxy[0]-20,rawxy[1]-20,rawxy[0]+21,rawxy[1]+21],fixed_final_roi_px=[box[0]+pad[0],box[1]+pad[1],box[2]+pad[0],box[3]+pad[1]],source_status='visible-unchanged' if value==actual else 'changed-unverified')
                if value!=actual and self.reference_kind=='registered-head-composite':
                    hf=next(f for f in self.head_clips[key]['frames'] if f['pose_id']==pose);order=hf['layer_order'];after=order[order.index('base')+1:];cover=[]
                    for layer in hf['layers']:
                        if layer['id'] not in after:continue
                        texture=self._image(str(self._ref(layer['texture'])));p=fp if texture.size==final.size else xy
                        require(texture.size in [final.size,canonical.size],'Head layer geometry differs')
                        if texture.getpixel(tuple(p))[3]:cover.append(layer['id'])
                    if cover:item.update(source_status='occluded-by-selected-head-support',occluding_layers=cover)
                result.append(item)
        return result

    @contract_errors
    def shoe_surfaces(self,actions=('walk','run')):
        require(self.reference_kind!='schema3-body-only','Body-only reference has no shoes coverage; use explicit visible material points')
        result=[]
        for key,clip in self.clips.items():
            if clip['action_id'] not in actions:continue
            for frame in clip['frames']:
                shoes=[l for l in frame['layers'] if l['slot']=='shoes'];require(len(shoes)==1 and shoes[0]['coverage'] is not None,'Missing actual shoes coverage')
                coverage=shoes[0]['coverage'];path=self._ref(coverage)
                with Image.open(path) as image:
                    require(image.mode=='L' and image.size==tuple(clip['canvas_px']),'Actual shoes coverage space/mode differs');mask=image.copy()
                require(not any(n for x,n in enumerate(mask.histogram()) if x not in [0,255]) and mask.getbbox() is not None,'Shoes coverage must be nonempty binary')
                output,pad,entry=self._output(key,frame['pose_id']);shifted=Image.new('L',output.size);shifted.paste(mask,tuple(pad[:2]))
                result.append({'identity':key+'/'+frame['pose_id']+'/shoes','clip':key,'pose_id':frame['pose_id'],'surface':'shoes','source_status':'actual-base-shoes-coverage','coverage':coverage,'output_padding_px':pad,'output':entry,'mask':shifted,'target':{'kind':'raster-only','source_ground_contact_proven':False}})
        return result

    def _native(self,evidence):
        evidence=Path(evidence).absolute();cp=safe_file(evidence,'input-contract.json');rp=safe_file(evidence,'report.json');self._bind(cp,digest(cp));self._bind(rp,digest(rp));contract=read_json(cp);report=read_json(rp)
        body_native=contract['kind']=='coastal-body-source-native-input-v1'
        require(contract['kind'] in ['coastal-all-actions-native-input-v1','coastal-body-source-native-input-v1'] and contract['schema_version']==1 and contract['contract_digest']==hashlib.sha256(stable({k:v for k,v in contract.items() if k!='contract_digest'})).hexdigest(),'Native input contract differs')
        require(body_native==(contract['observer']=='source-poses'),'Body source observer requires its own typed input contract')
        if body_native:
            require(self.reference_kind=='schema3-body-only' and contract['observer']=='source-poses'
                    and contract['source_points']=={'file':self.points_path.relative_to(self.repo).as_posix(),'sha256':digest(self.points_path)},
                    'Body native source points/reference differ')
        require(contract['manifest']=={'manifest':self.manifest_path.relative_to(self.repo).as_posix(),'sha256':digest(self.manifest_path)} and contract['artifact_digest']==self.manifest['artifact_digest'],'Native observes another actual manifest/artifact')
        require(report['input_contract_sha256']==digest(cp) and isinstance(report['renderer'],str) and report['renderer'] not in ['','headless'] and report['checks'] and all(type(v) is bool and v for v in report['checks'].values()),'Native raw input/renderer/checks differ')
        require((contract['observer'],report['kind']) in [('world','coastal-registered-actions-world-observation-v1'),('poses','coastal-registered-native-observation-v1'),('source-poses','coastal-body-source-native-observation-v1')],'Unsupported native screenshot convention')
        for name,expected in contract['files'].items():self._bind(safe_file(self.repo,name),expected)
        expected_files={'art/characters/'+k:v for k,v in self.manifest['inputs'].items()};expected_files.update({self.manifest_path.relative_to(self.repo).as_posix():digest(self.manifest_path)});expected_files.update({(self.manifest_path.parent/o['file']).relative_to(self.repo).as_posix():o['sha256'] for o in self.manifest['outputs']})
        if body_native:expected_files[self.points_path.relative_to(self.repo).as_posix()]=digest(self.points_path)
        require(all(contract['files'].get(k)==v for k,v in expected_files.items()),'Native snapshot omits frozen package inputs/outputs')
        hashes=report['output_hashes'];require(set(hashes)=={p.relative_to(evidence).as_posix() for p in evidence.rglob('*.png')},'Native PNG inventory differs')
        for name,expected in hashes.items():self._bind(safe_file(evidence,name),expected)
        return evidence,contract,report

    @contract_errors
    def native_receipt(self,evidence,include_shoes=False):
        points=self.static_points();surfaces=points+(self.shoe_surfaces() if include_shoes else []);evidence,contract,report=self._native(evidence);by_pose={};required={s['identity'] for s in surfaces};observed=set();measurements=[];seen_captures=set()
        for s in surfaces:by_pose.setdefault((s['clip'],s['pose_id']),[]).append(s)
        for sample in report['samples']:
            if contract['observer']=='source-poses':require(sample.get('mode')=='source-pose','Body material observer is not a motion/contact observation')
            if contract['observer']=='poses' and sample['mode'] not in ['world-continuous','world-idle']:continue
            if not sample.get('capture'):continue
            capture=sample['capture'];require(capture in report['output_hashes'] and capture not in seen_captures,'Missing/duplicate actual native capture');seen_captures.add(capture)
            texture=sample.get('world_texture',sample.get('texture'));require(isinstance(texture,dict),'Missing actual native GPU texture');key=texture['clip'];pose=texture['pose_id'];require(key in self.clips,'Unbound actual native clip')
            _,_,output=self._output(key,pose);require(texture['rgba_sha256']==output['rgba_sha256'],'Actual native texture RGBA differs from final manifest')
            if 'texture' in sample and 'world_texture' in sample:require(sample['texture']==sample['world_texture'],'Actual native GPU identities differ')
            state=sample['world_state'];require(state['action']+'-'+state['direction']==key,'Actual native state/GPU differs')
            for surface in by_pose.get((key,pose),[]):
                item={k:v for k,v in surface.items() if k!='mask'};item.update(capture=capture,capture_sha256=report['output_hashes'][capture],status='unverified');observed.add(surface['identity'])
                if surface['source_status'] not in ['visible-unchanged','actual-base-shoes-coverage']:
                    item['reason']='Source material is hidden, changed or occluded; original source point/ROI retained.';measurements.append(item);continue
                source,_,_=self._output(key,pose)
                if 'mask' in surface:mask=surface['mask']
                else:
                    box=surface['fixed_final_roi_px']
                    if not(0<=box[0]<box[2]<=source.width and 0<=box[1]<box[3]<=source.height):
                        item['reason']='Fixed41x41 source ROI crosses frame; never shrink or move it.';measurements.append(item);continue
                    mask=Image.new('L',source.size);mask.paste(255,tuple(box))
                origin=[0,0] if contract['observer']=='poses' else sample.get('actor_capture_origin_px')
                if origin is None:item['reason']='Missing actual actor capture origin; no inferred fallback.';measurements.append(item);continue
                transform=sample.get('render_source_to_screen');offset=sample.get('sprite_offset')
                if transform is None or offset is None:item['reason']='Missing actual render transform/sprite offset.';measurements.append(item);continue
                if sample.get('texture_size_px')!=list(source.size):item['reason']='Missing/wrong actual GPU texture size.';measurements.append(item);continue
                try:
                    finite_vector(transform,6);finite_vector(offset,2);finite_vector(origin,2)
                    result=measure(source,mask,self._image(str(safe_file(evidence,capture))),transform,offset,origin)
                except ValueError as error:item['reason']=str(error);measurements.append(item);continue
                item.update(measurement=result,render_source_to_screen=transform,sprite_offset=offset,actual_capture_origin_px=origin)
                item['status'],reason=classify_raster(result)
                if reason:item['reason']=reason
                measurements.append(item)
        self.verify_unchanged();missing=sorted(required-observed);bad=[r for r in measurements if r['status']!='within-one-pixel'];shoe_gaps=[]
        if include_shoes:
            for a in ['walk','run']:
                for d in ['south','west','east','north']:
                    key=a+'-'+d
                    if key not in self.clips or len(self.clips[key]['frames'])!=4:shoe_gaps.append(key+' requires4 actual poses')
        return {'kind':'coastal-bounded-contact-raster-correspondence-v1','schema_version':1,'status':'internal-raster-observation-only','reference_kind':self.reference_kind,'raster_scope':'Only the explicitly selected source points/surfaces; not whole bare-foot coverage or physical contact.','manifest':{'file':self.manifest_path.relative_to(self.repo).as_posix(),'sha256':digest(self.manifest_path)},'artifact_digest':self.manifest['artifact_digest'],'source_points_sha256':digest(self.points_path),'native_input_contract_sha256':digest(evidence/'input-contract.json'),'native_report_sha256':digest(evidence/'report.json'),'tool_sha256':digest(__file__),'native_raster_sha256':digest(Path(__file__).with_name('native_raster.py')),'fixed_point_roi_size_px':[41,41],'precision_contract':'All equally best raster offsets must be<=1px and RGB error<=native_raster alpha-blend bound; no unique-best requirement. Nonlocal ambiguity/low samples/missing fields remain unverified.','measurements':measurements,'required_points':len(points),'shoe_pose_count':sum('mask' in s for s in surfaces),'missing_points':missing,'shoe_scope_gaps':shoe_gaps,'raster_matrix_complete':bool(required) and not missing and not bad and not shoe_gaps,'verified_measurements':sum(r['status']=='within-one-pixel' for r in measurements),'unverified_or_mismatched_measurements':len(bad),'bound_files':dict(sorted(self.used.items())),'physical_contact_acceptance':False,'support_flight_slide_acceptance':False,'soil_or_target_acceptance':False,'art_acceptance':False,'user_approval':False,'release_eligible':False,'scope':'Actual source material and near-opaque raster correspondence only. Does not replace strict build or full raw observer validation; no physical support/flight/sliding/soil/target/art/user proof.'}

    def verify_unchanged(self):
        for name,expected in self.used.items():require(digest(name)==expected,'Contact evidence changed during measurement: '+name)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[2]);parser.add_argument('--manifest',type=Path,required=True);parser.add_argument('--manifest-sha256',required=True);parser.add_argument('--artifact',required=True);parser.add_argument('--points',type=Path,required=True);parser.add_argument('--points-sha256',required=True);parser.add_argument('--native',type=Path);parser.add_argument('--shoes',action='store_true');parser.add_argument('--output',type=Path,required=True);args=parser.parse_args(argv)
    try:
        require(not args.output.exists() and not args.output.is_symlink(),'Receipt output must be fresh')
        require(not args.shoes or args.native is not None,'Shoes raster measurement requires native samples')
        tool=BoundContactEvidence(args.repo,args.manifest,args.manifest_sha256,args.artifact,args.points,args.points_sha256)
        if args.native:result=tool.native_receipt(args.native,args.shoes)
        else:
            points=tool.static_points();tool.verify_unchanged();result={'kind':'coastal-bounded-contact-source-check-v1','manifest':{'file':tool.manifest_path.relative_to(tool.repo).as_posix(),'sha256':digest(tool.manifest_path)},'artifact_digest':tool.manifest['artifact_digest'],'source_points_sha256':digest(args.points),'tool_sha256':digest(__file__),'bound_files':dict(sorted(tool.used.items())),'points':points,'fixed_point_roi_size_px':[41,41],'native_verified':False,'physical_contact_acceptance':False,'support_flight_slide_acceptance':False,'soil_or_target_acceptance':False,'art_acceptance':False,'user_approval':False,'release_eligible':False}
        with args.output.open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'output':str(args.output),'raster_matrix_complete':result.get('raster_matrix_complete',False),'physical_contact_acceptance':False}));return 0
    except (ValueError,OSError) as error:
        print(json.dumps({'passed':False,'error':str(error)}));return 2


if __name__=='__main__':raise SystemExit(main())
