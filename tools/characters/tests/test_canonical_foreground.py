"""Same-base foreground is a disjoint RGBA partition, not an erase mask."""
import copy
import json
from pathlib import Path
import sys
import unittest
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import build
from composition_contract import compose
import test_registered_headwear as fixtures
import test_head_output_envelope as envelopes

class CanonicalForegroundTests(unittest.TestCase):
    def setUp(self):
        self.head=fixtures.RegisteredHeadwearTests();self.head.setUp();self.addCleanup(self.head.tearDown)

    def foreground(self,point=(1,0)):
        h=self.head;doc=json.loads((h.lib/h.annotation['file']).read_text());row=doc['records'][0]
        mask=Image.new('L',(2,2));mask.putpixel(point,255)
        owner=h.write('templates/test/motions/motion/annotations/head-r001/hands-tools.png',mask)
        visible=Image.new('L',(2,2),255);visible.putpixel(point,0)
        row['surfaces']['head']['mask']=h.write('templates/test/motions/motion/annotations/head-r001/visible-head.png',visible)
        row['surfaces']['hands-tools-foreground']={'layer_id':'base','mask':owner}
        h.annotation=h.write(h.annotation['file'],doc)
        for data in h.adaptations.values():
            for view in data['views']:view['source_pose']['document']=h.annotation
            for mapping in data['mappings']:mapping['target_pose']['document']=h.annotation
        h.rebind_hat_compatibility();h.refresh()
        frame=h.recipe['clips'][0]['frames'][0]
        frame['base_foreground']={'mode':'canonical-rgba-ownership-split',
            'target_pose':{'document':h.annotation,'record':row['record_id']},
            'surface_id':'hands-tools-foreground',
            'ownership':{'role':'canonical-foreground-ownership','mask':owner}}
        frame['layer_order'].append('base_foreground');h.save()
        return frame

    def test_shared_builder_preserves_actual_foreground_and_whole_frame_padding(self):
        self.foreground();h=self.head
        helper=envelopes.HeadOutputEnvelopeTests();helper.parent=h;helper.repo=h.repo;helper.lib=h.lib
        original=helper.padded([1,2,0,0]);output=h.lib/'builds/foreground-r001'
        manifest=build.construct(h.repo,h.path,output);build.verify(h.repo,output)
        first=Image.open(output/manifest['outputs'][0]['file']).convert('RGBA')
        self.assertEqual(first.getpixel((2,2)),(10,20,30,255))
        self.assertEqual(first.crop((1,2,3,4)).tobytes(),original[manifest['outputs'][0]['file']].tobytes())

    def test_clothing_cannot_be_reclassified_as_hand_tool_foreground(self):
        self.foreground((0,0))
        with self.assertRaisesRegex(ValueError,'clothing'):self.head.check()

    def test_wrong_pose_or_mask_binding_is_rejected(self):
        frame=self.foreground();original=copy.deepcopy(frame['base_foreground'])
        frame['base_foreground']['target_pose']['record']='wave_west_0'
        with self.assertRaises(ValueError):self.head.check()
        frame['base_foreground']=copy.deepcopy(original)
        frame['base_foreground']['ownership']['mask']=self.head.masks['near_hat']
        with self.assertRaises(ValueError):self.head.check()

    def test_source_rgba_is_split_once_before_alpha_composition(self):
        base=Image.new('RGBA',(2,1));base.putpixel((0,0),(220,120,80,73));base.putpixel((1,0),(90,50,20,253))
        hat=Image.new('RGBA',(2,1));hat.putpixel((0,0),(20,40,220,200))
        owner=Image.new('L',(2,1),255)
        assets={'hat':hat,'mask':owner}
        frame={'operation':'supported-alpha-stack','layers':[{'id':'near_hat','texture':'hat'}],
               'layer_order':['base','near_hat','base_foreground'],
               'base_foreground':{'mode':'canonical-rgba-ownership-split','ownership':{'mask':'mask'}}}
        result=compose(base,frame,lambda ref:assets[ref])
        expected=Image.alpha_composite(hat,base)
        self.assertEqual(result.getpixel((0,0)),expected.getpixel((0,0)))
        self.assertEqual(result.getpixel((1,0)),base.getpixel((1,0)))

    def test_foreground_cannot_include_visible_face(self):
        frame=self.foreground();h=self.head
        doc=json.loads((h.lib/h.annotation['file']).read_text())
        doc['records'][0]['surfaces']['head']['mask']=frame['base_foreground']['ownership']['mask']
        ref=h.write(h.annotation['file'],doc)
        frame['base_foreground']['target_pose']['document']=ref
        # Rebind the actual mapper to the same changed annotation as well.
        for data in h.adaptations.values():
            for view in data['views']:view['source_pose']['document']=ref
            for mapping in data['mappings']:mapping['target_pose']['document']=ref
        h.rebind_hat_compatibility();h.refresh();h.save()
        with self.assertRaisesRegex(ValueError,'visible head'):h.check()

    def test_foreground_order_cannot_be_an_extra_painted_body_texture(self):
        frame=self.foreground();frame['layers'].append(copy.deepcopy(frame['layers'][0]))
        frame['layers'][-1]['id']='base_foreground'
        with self.assertRaises(ValueError):self.head.check()

    def test_foreground_sidecar_cannot_relabel_the_actual_selected_head_surface(self):
        frame=self.foreground();h=self.head
        doc=json.loads((h.lib/h.annotation['file']).read_text());doc['revision']='alternate-foreground'
        row=doc['records'][0];owner=Image.new('L',(2,2));owner.putpixel((1,0),255);owner.putpixel((0,1),255)
        owner_ref=h.write('templates/test/motions/motion/annotations/alternate-foreground/claimed-hand.png',owner)
        head=Image.open(h.lib/row['surfaces']['head']['mask']['file']).convert('L');self.assertEqual(head.getpixel((0,1)),255);head.putpixel((0,1),0)
        row['surfaces']['head']['mask']=h.write('templates/test/motions/motion/annotations/alternate-foreground/relabelled-head.png',head)
        row['surfaces']['hands-tools-foreground']['mask']=owner_ref
        alternate=h.write('templates/test/motions/motion/annotations/alternate-foreground/poses.json',doc)
        frame['base_foreground']['target_pose']['document']=alternate;frame['base_foreground']['ownership']['mask']=owner_ref
        h.save()
        with self.assertRaisesRegex(ValueError,'actual head mapping'):h.check()
