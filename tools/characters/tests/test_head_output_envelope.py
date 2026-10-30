"""Whole-frame padding retains canonical pixels and legal overscan head art."""
import copy
from pathlib import Path
import sys
import unittest
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import build
import review
import test_registered_headwear as head_fixture

class HeadOutputEnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.parent=head_fixture.RegisteredHeadwearTests();self.parent.setUp();self.addCleanup(self.parent.tearDown)
        self.repo=self.parent.repo;self.lib=self.parent.lib

    def padded(self,pad):
        head=self.parent
        original={name:image.copy() for name,image in build.render(head.check())}
        for clip,base in zip(head.recipe['clips'],head.fixture.recipe['clips']):
            clip['output_padding_px']=pad
            for frame in clip['frames']:
                for layer in frame['layers']:
                    old=Image.open(self.lib/layer['texture']['file']).convert('RGBA')
                    image=Image.new('RGBA',(old.width+pad[0]+pad[2],old.height+pad[1]+pad[3]))
                    image.paste(old,(pad[0],pad[1]))
                    ref=head.write(layer['texture']['file'].replace('.png','-padded.png'),image)
                    mapping=next(m for m in head.adaptations[layer['slot']]['mappings'] if m['mapping_id']==layer['view_binding']['mapping_id'])
                    mapping['texture']=ref;layer['texture']=ref
        for slot,data in head.adaptations.items():
            head.recipe['adaptations'][slot]=head.write(head.recipe['adaptations'][slot]['file'],data)
        head.save();return original

    def test_pad_all_layers_and_root_without_modifying_canonical_body(self):
        original=self.padded([2,1,1,0]);head=self.parent
        output=self.lib/'builds/padded-r001';manifest=build.construct(self.repo,head.path,output);build.verify(self.repo,output)
        for item in manifest['outputs']:
            before=original[item['file']];after=Image.open(output/item['file']).convert('RGBA')
            self.assertEqual(after.size,(before.width+3,before.height+1))
            self.assertEqual(after.crop((2,1,2+before.width,1+before.height)).tobytes(),before.tobytes())
        expected={(c['action_id'],c['direction']) for c in head.fixture.recipe['clips']}
        clips=review._scoped_action_clips(head.fixture.recipe,head.recipe,expected)
        for key,clip in clips.items():
            old=next(c for c in head.fixture.recipe['clips'] if (c['action_id'],c['direction'])==key)
            self.assertEqual(clip['root_anchor_px'],[old['root_anchor_px'][0]+2,old['root_anchor_px'][1]+1])
            self.assertEqual(clip['canvas_px'],[old['canvas_px'][0]+3,old['canvas_px'][1]+1])

    def test_negative_fractional_bool_or_excessive_padding_rejected(self):
        original=copy.deepcopy(self.parent.recipe)
        for pad in [None,[-1,0,0,0],[0.5,0,0,0],[True,0,0,0],[513,0,0,0],[0,0,0]]:
            with self.subTest(pad=pad):
                self.parent.recipe=copy.deepcopy(original);self.parent.recipe['clips'][0]['output_padding_px']=pad;self.parent.save()
                with self.assertRaises(ValueError):self.parent.check()

    def test_real_support_outside_canonical_canvas_is_preserved_only_with_envelope(self):
        head=self.parent
        annotation=copy.deepcopy(head.fixture.annotations)
        # Use the existing head annotation (its surface is base/head).
        import json
        annotation=json.loads((self.lib/head.annotation['file']).read_text())
        walk_pose=head.recipe['clips'][1]['frames'][0]['pose_id']
        next(r for r in annotation['records'] if r['pose_id']==walk_pose)['landmarks_px']['cloth']=[0,1]
        head.annotation=head.write(head.annotation['file'],annotation)
        for data in head.adaptations.values():
            for view in data['views']:view['source_pose']['document']=head.annotation
            for mapping in data['mappings']:
                mapping['target_pose']['document']=head.annotation
                if mapping['target_pose']['record']==walk_pose:mapping['anchors']['target_px']=[0,1]
        head.rebind_hat_compatibility();head.refresh()
        with self.assertRaisesRegex(ValueError,'crop owned'):head.check()
        clip=head.recipe['clips'][1];body=head.fixture.recipe['clips'][1];clip['output_padding_px']=[1,0,0,0]
        for frame in clip['frames']:
            for layer in frame['layers']:
                data=head.adaptations[layer['slot']]
                view=next(v for v in data['views'] if v['view_id']==layer['view_binding']['view_id'])
                mapping=next(m for m in data['mappings'] if m['mapping_id']==layer['view_binding']['mapping_id'])
                with Image.open(self.lib/view['source']['file']) as src,Image.open(self.lib/view['source_ownership']['mask']['file']) as owner:
                    extracted=Image.composite(src.convert('RGBA'),Image.new('RGBA',src.size),owner)
                image=Image.new('RGBA',(body['canvas_px'][0]+1,body['canvas_px'][1]))
                a=mapping['anchors'];image.paste(extracted,(a['target_px'][0]-a['source_px'][0]+1,a['target_px'][1]-a['source_px'][1]))
                mapping['texture']=head.write(layer['texture']['file'].replace('.png','-overscan.png'),image);layer['texture']=mapping['texture']
        for slot,data in head.adaptations.items():head.recipe['adaptations'][slot]=head.write(head.recipe['adaptations'][slot]['file'],data)
        head.save();output=self.lib/'builds/overscan-r001';manifest=build.construct(self.repo,head.path,output);build.verify(self.repo,output)
        item=next(x for x in manifest['outputs'] if x['file'].endswith('/'+walk_pose+'.png'))
        result=Image.open(output/item['file']).convert('RGBA')
        self.assertEqual(result.getpixel((0,0)),(240,20,30,128))

    def test_base_clips_cannot_request_head_output_envelope(self):
        self.parent.fixture.recipe['clips'][0]['output_padding_px']=[1,0,0,0]
        self.parent.fixture.save()
        with self.assertRaises(ValueError):self.parent.fixture.check()

    def test_non_object_head_clip_fails_as_contract_error(self):
        original=copy.deepcopy(self.parent.recipe)
        for bad in [None,'invalid',3,[],False]:
            with self.subTest(bad=bad):
                self.parent.recipe=copy.deepcopy(original);self.parent.recipe['clips'][0]=bad
                with self.assertRaises(ValueError):self.parent.check()
