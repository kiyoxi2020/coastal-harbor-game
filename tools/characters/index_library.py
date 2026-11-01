"""Build navigation and explicit capability rows from the actual current manifests."""
from pathlib import Path
from collections import defaultdict
import json,hashlib
ROOT=Path(__file__).resolve().parents[2]
LIB=ROOT/'art/characters'

def write(path,data):
    path=LIB/path;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def read(path):return json.loads((LIB/path).read_text())
def main():
    static=read('static-index.json');designs={x['design_id']:{'design_id':x['design_id'],'static_status':x['status'],'category':x['category'],'motion_adaptations':[]} for x in static['candidates'] if x['category']!='body'}
    views=defaultdict(list);rows=[]
    for group in ['wardrobe','headwear']:
        catalog=read('reviews/'+group+'/catalog.json')
        for entry in catalog['samples']:
            sample_path=entry['sample'].removeprefix('art/characters/');s=read(sample_path);recipe_id=group+'-'+entry['id'];slots=s.get('recipe',{}).get('slots',{})
            for frame in s['frames']+[s['idle']]:
                for layer in frame.get('layers',[]):
                    slot=layer.get('slot');design=layer.get('design_id',slots.get(slot))
                    if not design:continue
                    views[design].append({'recipe_id':recipe_id,'pose_id':frame['pose_id'],'part_id':layer['id'],'slot':slot or layer['id'],'view':layer})
                for part,view in frame.get('parts',{}).items():
                    design='hair-chestnut-short-v1' if part.startswith('hair') else 'hat-straw-navy-band-v1' if part=='hat' else slots.get(part)
                    if design:views[design].append({'recipe_id':recipe_id,'pose_id':frame['pose_id'],'part_id':part,'slot':part,'view':view})
            states=['bare','hair','hat','hair_hat'] if group=='headwear' else [None]
            for state in states:
                rows.append({'recipe_id':recipe_id,'head_state':state,'template_id':s['template_id'],'action_id':s['action_id'],'direction':s['direction'],'manifest':sample_path,'pose_count':len(s['frames']),'has_matching_idle':True,'source_available':True,'baked_available':True,'component_scope':'exact sampled pose/recipe only','migration_native':'pending','user_acceptance':group+'-'+entry['id'] if group=='wardrobe' or entry['id'] in ['run-east','hoe-west'] else 'not-recorded'})
    for design,entries in views.items():
        category = 'hair' if design.startswith('hair') else entries[0]['slot']
        path=f'parts/{category}/{design}/adult-standard-v1/review-motion-v1/r001/views.json'
        write(path,{'resource_root':'art/characters','design_id':design,'template_id':'adult-standard-v1','scope':'Only explicitly listed pose/recipe adaptations. No full wardrobe compatibility inferred.','views':entries})
        item=designs.setdefault(design,{'design_id':design,'category':entries[0]['slot'],'static_status':'not-listed','motion_adaptations':[]})
        item['motion_adaptations'].append(path)
    loc=read('builds/locomotion-r001/manifest.json')
    for garment in ['A','B']:
        for action,info in loc['actions'].items():
            for direction,poses in info['directions'].items():rows.append({'recipe_id':'base-'+garment,'template_id':'adult-standard-v1','action_id':action,'direction':direction,'manifest':'builds/locomotion-r001/manifest.json','pose_count':len(poses),'source_available':True,'baked_available':True,'component_scope':'existing imported interfaces only','migration_native':'pending','user_acceptance':'locomotion'})
    run=read('builds/run-r001/candidate.json')
    for garment in ['A','B']:
        for direction in run['directions']:rows.append({'recipe_id':'base-'+garment,'template_id':'adult-standard-v1','action_id':'run','direction':direction,'manifest':'builds/run-r001/candidate.json','garments':'builds/run-r001/run-garments.json','additional_accepted_views':'builds/run-r001/run-diagnostics.json' if garment=='B' and direction in ['north','south'] else None,'pose_count':4,'source_available':True,'baked_available':True,'component_scope':'complete-frame and existing layered interfaces; hidden body not inferred','migration_native':'pending','user_acceptance':'run'})
    for entry in read('reviews/farming/catalog.json')['clips']:
        path=entry['candidate'].removeprefix('art/characters/');s=read(path)
        rows.append({'recipe_id':'farming-'+entry['garment'],'template_id':'adult-standard-v1','action_id':entry['action_id'],'direction':entry['direction'],'manifest':path,'pose_count':len(s['frames']),'source_available':True,'baked_available':True,'component_scope':'complete clothed reference; not hidden-body or arbitrary garment adaptation','migration_native':'pending','user_acceptance':'farming'})
    static_catalog=read('reviews/static-candidates/catalog.json')
    static_by_id={c['id']:c for entries in static_catalog['categories'].values() for c in entries if c['category']!='body'}
    for item in designs.values():
        definition=f"parts/{item['category']}/{item['design_id']}/design.json"
        if not (LIB/definition).exists():
            candidate=static_by_id.get(item['design_id'],{})
            write(definition,{'design_id':item['design_id'],'label':candidate.get('label',item['design_id']),'category':item['category'],'source':candidate.get('source'),'static_scope':candidate.get('compatibility'),'static_status':item['static_status'],'motion_adaptations':item['motion_adaptations'],'identity_status':'legacy-scoped-baseline-label' if item['design_id'].startswith('original-') else 'declared-design-id','scope':'Only listed references and exact adaptations; no implied all-motion compatibility.'})
        for adaptation in item['motion_adaptations']:
            entries=read(adaptation)['views'];base=str(Path(adaptation).parent)
            write(base+'/pose-map.json',{'design_id':item['design_id'],'mapping':[{'recipe_id':v['recipe_id'],'pose_id':v['pose_id'],'part_id':v['part_id'],'view_index':i} for i,v in enumerate(entries)],'views':'views.json','multi_pose_view_reuse_allowed':True})
            write(base+'/adaptation.json',{'design_id':item['design_id'],'template_id':'adult-standard-v1','motion_set_id':'review-motion-v1','revision':'r001','pose_map':'pose-map.json','views':'views.json','coverage_and_occlusion':'Stored separately in each referenced view; do not infer from source ownership','scope':'Exact sampled recipes only'})
        p=f"parts/{item['category']}/{item['design_id']}/design.json"
        if (LIB/p).exists():item['definition']=p
    write('catalog.json',{'schema_version':1,'resource_root':'art/characters','character_model_id':'unified-composable-character-v1','status':'development-library-not-production-release','selected_template':'templates/adult-standard-v1/template.json','static_candidates':'static-index.json','parts':sorted(designs.values(),key=lambda x:x['design_id']),'reviews':{name:'reviews/'+name+'/review.json' for name in ['locomotion','farming','wardrobe','headwear','static-candidates']},'coverage':'coverage.json','source_index':[str(p.relative_to(LIB)) for p in sorted((LIB/'sources').glob('*/source.json'))],'production_release':None})
    write('templates/adult-standard-v1/template.json',{'template_id':'adult-standard-v1','active_revision':static['selected_template']['active_revision'],'static_selection':'templates/adult-standard-v1/selection.json','motion_set':'templates/adult-standard-v1/motions/review-motion-v1/motion-set.json','scope':'Selected appearance plus imported motion references/interfaces. Not a complete hidden-body or all-combination capability claim.'})
    action_index={}
    for action in ['idle','walk','run','hoe','water','harvest']:
        action_base=f'templates/adult-standard-v1/motions/review-motion-v1/actions/{action}/r001';directions={}
        for direction in ['south','west','east','north']:
            variants={}
            if action in ['idle','walk']:
                pose_ids=loc['actions'][action]['directions'][direction]
                for garment in ['A','B']:
                    variant_frames=[f for f in loc['recipes'][garment]['frames'] if f['pose_id'] in pose_ids]
                    variants[garment]={'canvas_px':loc['canvas_px'],'root_anchor_px':loc['root_anchor_px'],'display_scale':loc['display_scale'],'frames':variant_frames}
            elif action=='run':
                poses=[f for f in run['frames'] if f['direction']==direction]
                variants['A']={'canvas_px':run['canvas_px'],'root_anchor_px':run['root_anchor_px'],'display_scale':run['display_scale'],'frames':poses}
                variants['B']={'reference':'builds/run-r001/run-diagnostics.json' if direction in ['south','north'] else 'builds/run-r001/run-garments.json','direction':direction,'pose_ids':[f['pose_id'] for f in poses],'scope':'Existing accepted B views; resolve exact frame paths in referenced garment/diagnostic record.'}
            else:
                for e in read('reviews/farming/catalog.json')['clips']:
                    if e['action_id']==action and e['direction']==direction:
                        build=e['candidate'].removeprefix('art/characters/');data=read(build)
                        variants[e['garment']]={k:data[k] for k in ['canvas_px','root_anchor_px','display_scale','frames']};variants[e['garment']]['reference_manifest']=build
            path=action_base+'/'+direction+'/poses.json';write(path,{'template_id':'adult-standard-v1','action_id':action,'direction':direction,'variants':variants,'body_view_scope':'Imported same-pose complete-frame references and existing interfaces only; hidden anatomy not implied.'});directions[direction]=path
        path=action_base+'/action.json';write(path,{'action_id':action,'loop':action in ['idle','walk','run'],'directions':directions,'revision':'r001','events_scope':'Existing source events only; no new gameplay events introduced by storage migration.'});action_index[action]=path
    motion=read('templates/adult-standard-v1/motions/review-motion-v1/motion-set.json');motion['actions']=action_index;write('templates/adult-standard-v1/motions/review-motion-v1/motion-set.json',motion)
    write('coverage.json',{'schema_version':1,'resource_root':'art/characters','rows':rows,'missing_capabilities':['Complete same-recipe hair/hat views across all actions and directions','Strict foot/grip/target contact contracts','Required hidden-body and untested garment-shape interfaces','Additional body types dynamic adaptations','Complete production-role release and old model retirement'],'policy':'Rows describe only actual imported artifacts. Native migration and original acceptance are separate; no new art/compatibility inferred.'})
    suites={'locomotion':{'scene':'res://dev/characters/character_walk_trial.tscn','args':['--trial-review','--trial-run-root={library}/builds/run-r001','--trial-run-diagnostics']},'farming':{'scene':'res://dev/characters/character_walk_trial.tscn','args':['--trial-review','--trial-run-root={library}/builds/run-r001','--trial-run-diagnostics','--trial-farming-transitions','--trial-farming-catalog={library}/reviews/farming/catalog.json']},'wardrobe':{'scene':'res://dev/characters/character_wardrobe_trial.tscn','args':[]},'headwear':{'scene':'res://dev/characters/character_headwear_hoe_review.tscn','args':[]},'static-candidates':{'html':'reviews/static-candidates/gallery.html'}}
    for name,config in suites.items():
        config.update(suite_id=name,scope='Development review; no production-release switch',catalog='reviews/'+name+'/catalog.json' if name in ['farming','wardrobe','headwear','static-candidates'] else 'builds/locomotion-r001/manifest.json')
        write('reviews/'+name+'/review.json',config)
    print(json.dumps({'part_resource_ids':len(designs),'source_groups':len(list((LIB/'sources').glob('*/source.json'))),'capability_rows':len(rows)}))
if __name__=='__main__':main()
