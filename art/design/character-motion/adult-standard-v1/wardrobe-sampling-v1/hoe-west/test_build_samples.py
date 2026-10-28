import unittest
from PIL import ImageChops, ImageOps
from PIL import Image
from build_samples import compose_visible, register, check_exact, validate_structure, interface_ownership, supplement_surface


class SlotChecks(unittest.TestCase):
    def fixture(self):
        old=Image.new('RGBA',(8,8));old.paste((40,70,100,255),(1,1,7,7))
        raw=old.copy();raw.paste((160,100,70,255),(2,2,6,6))
        mask=Image.new('L',(8,8));mask.paste(255,(2,2,6,6))
        return old,raw,mask

    def test_only_authorized_rgb_and_original_alpha(self):
        old,raw,m=self.fixture();out=compose_visible(old,{'top':raw},{'top':m})
        check_exact(old,out,m);self.assertEqual(out.getchannel('A').tobytes(),old.getchannel('A').tobytes())
        self.assertEqual(out.getpixel((3,3)),raw.getpixel((3,3)))

    def test_overlapping_slot_ownership_rejected(self):
        old,raw,m=self.fixture()
        with self.assertRaisesRegex(ValueError,'overlap'):compose_visible(old,{'top':raw,'pants':raw},{'top':m,'pants':m})

    def test_missing_source_under_visible_cloth_rejected(self):
        old,raw,m=self.fixture();raw.putpixel((3,3),(160,100,70,0))
        with self.assertRaisesRegex(ValueError,'missing'):compose_visible(old,{'top':raw},{'top':m})

    def test_noncloth_or_alpha_damage_rejected(self):
        old,raw,m=self.fixture();out=compose_visible(old,{'top':raw},{'top':m});out.putpixel((1,1),(41,70,100,255))
        with self.assertRaisesRegex(ValueError,'non-clothing'):check_exact(old,out,m)
        out=compose_visible(old,{'top':raw},{'top':m});out.putpixel((3,3),(160,100,70,254))
        with self.assertRaisesRegex(ValueError,'alpha'):check_exact(old,out,m)

    def test_whole_frame_registration_only(self):
        old,_,_=self.fixture();out=register(old,[16,16],[3,4])
        self.assertEqual(out.crop((3,4,11,12)).tobytes(),old.tobytes())
        with self.assertRaisesRegex(ValueError,'bounds'):register(old,[8,8],[3,4])

    def test_interface_skin_stays_original_only_in_declared_boundary(self):
        old,raw,m=self.fixture();raw.putpixel((2,3),(250,180,120,255))
        with self.assertRaisesRegex(ValueError,'skin'):interface_ownership(m,raw,[])
        owned,retained=interface_ownership(m,raw,[[[2,2],[2,4],[3,4],[3,2]]])
        self.assertEqual(owned.getpixel((2,3)),0);self.assertEqual(retained.getpixel((2,3)),255)

    def test_same_pose_supplement_only_missing_pixels_in_manual_panel(self):
        old,raw,m=self.fixture();primary=raw.copy();primary.putpixel((3,3),(0,0,0,0))
        panel=Image.new('L',(8,8));panel.putpixel((3,3),255)
        selected,used=supplement_surface(primary,raw,m,panel)
        self.assertEqual(selected.tobytes(),raw.tobytes());self.assertEqual(used.histogram()[255],1)
        outside=Image.new('L',(8,8));selected,used=supplement_surface(primary,raw,m,outside)
        self.assertEqual(selected.tobytes(),primary.tobytes());self.assertEqual(used.histogram()[255],0)
        raw.putpixel((3,3),(1,1,1,0))
        with self.assertRaisesRegex(ValueError,'missing'):supplement_surface(primary,raw,m,panel)

    def test_structure_missing_slot_phase_hash_or_idle_rejected(self):
        s={'schema_version':1,'status':'sampled-not-exhaustive','recipe':{'slots':{'top':'top03','pants':'original-pants','shoes':'original-shoes'}},'frames':[{'pose_id':str(i),'phase':str(i),'duration_ms':100,'sha256':'a'*64,'file':str(i)} for i in range(4)],'idle':{'file':'idle.png','sha256':'b'*64}}
        validate_structure(s)
        for change in ['slot','phase','hash','idle']:
            import copy
            q=copy.deepcopy(s)
            if change=='slot':del q['recipe']['slots']['pants']
            if change=='phase':q['frames'].pop()
            if change=='hash':q['frames'][0]['sha256']=''
            if change=='idle':del q['idle']
            with self.assertRaises(ValueError):validate_structure(q)

if __name__=='__main__':unittest.main()
