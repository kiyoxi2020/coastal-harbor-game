"""Independent raster correspondence catches wrong roots and wrong pose pixels."""
from pathlib import Path
import sys
import unittest
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from native_raster import measure

class NativeRasterTests(unittest.TestCase):
    def fixture(self):
        source=Image.new('RGBA',(8,8))
        mask=Image.new('L',(8,8))
        for x,y,color in [(1,5,(80,40,20,255)),(2,5,(30,20,10,255)),(2,6,(15,10,5,255)),
                          (5,4,(110,70,40,255)),(5,5,(50,25,15,255))]:
            source.putpixel((x,y),color);mask.putpixel((x,y),255)
        # Hand-author a 2x rendered crop, independently of the measurement code.
        actual=Image.new('RGBA',(24,24),(230,220,200,255))
        for y in range(8):
            for x in range(8):
                if source.getpixel((x,y))[3]:
                    for dy in range(2):
                        for dx in range(2):actual.putpixel((4+x*2+dx,2+y*2+dy),source.getpixel((x,y)))
        return source,mask,actual

    def test_actual_correspondence_and_source_preserving_transparent_boundary(self):
        source,mask,actual=self.fixture()
        result=measure(source,mask,actual,[2,0,0,2,4,2],[0,0],[0,0])
        self.assertEqual(result['offset_px'],[0,0]);self.assertEqual(result['mean_rgb_error'],0)
        self.assertTrue(result['within_one_pixel'])

    def test_wrong_root_is_measured_and_fails_one_pixel_target(self):
        source,mask,actual=self.fixture()
        result=measure(source,mask,actual,[2,0,0,2,6,2],[0,0],[0,0])
        self.assertEqual(result['offset_px'],[-2,0]);self.assertFalse(result['within_one_pixel'])

    def test_no_opaque_protected_surface_is_not_evidence(self):
        source,mask,actual=self.fixture()
        with self.assertRaisesRegex(ValueError,'opaque'):
            measure(source,Image.new('L',(8,8)),actual,[2,0,0,2,4,2],[0,0],[0,0])

    def test_near_opaque_source_records_bounded_background_blend(self):
        source,mask,actual=self.fixture()
        for y in range(8):
            for x in range(8):
                pixel=source.getpixel((x,y))
                if pixel[3]:
                    source.putpixel((x,y),(*pixel[:3],252))
                    for dy in range(2):
                        for dx in range(2):
                            actual.putpixel((4+x*2+dx,2+y*2+dy),tuple(round(pixel[i]*252/255+230*3/255) for i in range(3))+(255,))
        result=measure(source,mask,actual,[2,0,0,2,4,2],[0,0],[0,0])
        self.assertTrue(result['within_one_pixel']);self.assertEqual(result['minimum_source_alpha'],252)
        source.putalpha(128)
        with self.assertRaisesRegex(ValueError,'opaque'):measure(source,mask,actual,[2,0,0,2,4,2],[0,0],[0,0])

    def boundary_fixture(self,epsilon=1e-7):
        source=Image.new('RGBA',(8,8));mask=Image.new('L',(8,8),255)
        for y in range(8):
            for x in range(8):source.putpixel((x,y),((37*x+11*y)%251,(17*x+43*y)%251,(53*x+19*y)%251,255))
        # Independent GPU-style2x nearest output: one nominal source texel
        # boundary straddles a rounded vertex position. No actual-colour search.
        actual=Image.new('RGBA',(16,16))
        for y in range(16):
            for x in range(16):actual.putpixel((x,y),source.getpixel((x//2,y//2)))
        return source,mask,actual,[2,0,0,2,.5+epsilon*2,0]

    def test_float32_integer_boundary_samples_are_excluded_and_counted(self):
        for epsilon in [1e-7,-1e-7]:
            source,mask,actual,transform=self.boundary_fixture(epsilon)
            result=measure(source,mask,actual,transform,[0,0],[0,0])
            with self.subTest(epsilon=epsilon):
                self.assertIn('float32_boundary_samples_skipped',result)
                self.assertGreater(result['float32_boundary_samples_skipped'],0)
                self.assertEqual(result['eligible_sample_count_before_precision_filter'],result['sample_count']+result['float32_boundary_samples_skipped'])
                self.assertEqual(result['sampling_precision']['float32_ulp_multiplier'],4)
                self.assertEqual(result['mean_rgb_error'],0)
                self.assertTrue(result['within_one_pixel'])

    def test_distance_beyond_fixed_four_ulp_is_not_excluded(self):
        # At source coords<=8,4ULP<=3.82e-6; this is1.53e-5, clearly outside.
        source,mask,actual,transform=self.boundary_fixture(2**-16)
        result=measure(source,mask,actual,transform,[0,0],[0,0])
        self.assertIn('float32_boundary_samples_skipped',result)
        self.assertEqual(result['float32_boundary_samples_skipped'],0)
        self.assertEqual(result['eligible_sample_count_before_precision_filter'],result['sample_count'])

    def test_actual_colours_cannot_change_precision_sampling_set(self):
        source,mask,actual,transform=self.boundary_fixture()
        one=measure(source,mask,actual,transform,[0,0],[0,0]);two=measure(source,mask,Image.new('RGBA',actual.size,(250,1,130,255)),transform,[0,0],[0,0])
        for key in ['sample_count','float32_boundary_samples_skipped','eligible_sample_count_before_precision_filter','sampling_precision']:
            self.assertIn(key,one);self.assertEqual(one[key],two[key])

    def test_four_nominal_samples_with_two_uncertain_remain_insufficient(self):
        source,_,actual,transform=self.boundary_fixture();mask=Image.new('L',source.size);mask.putpixel((3,3),255)
        with self.assertRaisesRegex(ValueError,'Insufficient.*opaque'):
            measure(source,mask,actual,transform,[0,0],[0,0])

    def test_actual_is_not_read_before_source_sample_set_is_admissible(self):
        source,mask,actual,transform=self.boundary_fixture();source.putalpha(249);reads=[]
        class Actual:
            def convert(self,mode):reads.append(mode);return actual.convert(mode)
        with self.assertRaisesRegex(ValueError,'opaque'):measure(source,mask,Actual(),transform,[0,0],[0,0])
        self.assertEqual(reads,[])
