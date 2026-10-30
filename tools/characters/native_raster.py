"""Measure protected source surfaces against actual native screenshots.

This measures an offset; it never moves pixels or changes registrations. Masks
must already have independently reviewed anatomical/material semantics. It does
not infer support/flight, certify legal targets, or grant visual approval.
"""
import math
from build_contract import require


def _float32_boundary_guard(coordinate):
    """Local four-binary32-ULP guard, expressed in source texel units.

    Binary32 spacing in binade[2**k,2**(k+1)) is2**(k-23). Four
    spacings conservatively bracket a small sequence of float32 vertex/UV
    rounding operations at that source magnitude. This excludes uncertain
    samples; it is not an extra pixel/error tolerance or a guarantee for
    arbitrary ill-conditioned transforms. Use the nearest integer magnitude
    too so both sides of a power-of-two boundary use the larger spacing.
    """
    nearest=round(coordinate)
    magnitude=max(1.0,abs(coordinate),abs(nearest))
    exponent=math.frexp(magnitude)[1]
    guard=4*math.ldexp(1.0,exponent-24)
    return abs(coordinate-nearest)<=guard


def measure(source, mask, actual, transform, sprite_offset, crop_origin, radius=3):
    require(source.size==mask.size,'Protected mask canvas differs')
    require(type(radius) is int and 0<=radius<=8,'Invalid measurement radius')
    require(len(transform)==6 and len(sprite_offset)==2 and len(crop_origin)==2
            and all(math.isfinite(float(x)) for x in [*transform,*sprite_offset,*crop_origin]),'Invalid screen transform')
    a,b,c,d,tx,ty=transform;det=a*d-b*c
    require(abs(det)>1e-12,'Singular screen transform')
    source=source.convert('RGBA');mask=mask.convert('L')
    require(not any(count for value,count in enumerate(mask.histogram()) if value not in [0,255]),'Protected mask must be binary')
    box=mask.getbbox();require(box is not None,'No opaque protected surface')
    def forward(x,y):
        x+=sprite_offset[0];y+=sprite_offset[1]
        return a*x+c*y+tx-crop_origin[0],b*x+d*y+ty-crop_origin[1]
    corners=[forward(x,y) for x in [box[0],box[2]] for y in [box[1],box[3]]]
    samples=[];alphas=[];skipped=0;pixels=source.load();owner=mask.load()
    for sy in range(math.floor(min(y for x,y in corners)),math.ceil(max(y for x,y in corners))):
        for sx in range(math.floor(min(x for x,y in corners)),math.ceil(max(x for x,y in corners))):
            dx=sx+crop_origin[0]+0.5-tx;dy=sy+crop_origin[1]+0.5-ty
            uf=(d*dx-c*dy)/det-sprite_offset[0]
            vf=(-b*dx+a*dy)/det-sprite_offset[1]
            u=math.floor(uf);v=math.floor(vf)
            if 0<=u<source.width and 0<=v<source.height and owner[u,v]==255 and pixels[u,v][3]>=250:
                if _float32_boundary_guard(uf) or _float32_boundary_guard(vf):
                    skipped+=1
                    continue
                samples.append((sx,sy,pixels[u,v][:3]))
                alphas.append(pixels[u,v][3])
    require(len(samples)>=4,'Insufficient opaque protected surface samples after float32 boundary exclusion')
    # Select all eligible source samples before reading any actual colour.
    actual=actual.convert('RGBA');screen=actual.load()
    results=[]
    for dy in range(-radius,radius+1):
        for dx in range(-radius,radius+1):
            if any(not(0<=x+dx<actual.width and 0<=y+dy<actual.height) for x,y,_ in samples):continue
            error=sum(sum(abs(rgb[i]-screen[x+dx,y+dy][i]) for i in range(3)) for x,y,rgb in samples)
            results.append((error,dx*dx+dy*dy,dx,dy))
    require(results,'Protected surface is outside screenshot')
    results.sort();error,_,dx,dy=results[0]
    equal=[[x,y] for value,_,x,y in results if value==error]
    mean=error/(len(samples)*3)
    blend_bound=256-min(alphas)
    return {'offset_px':[dx,dy],'error_px':math.hypot(dx,dy),'mean_rgb_error':mean,
            'sample_count':len(samples),'equally_good_offsets':equal,
            'float32_boundary_samples_skipped':skipped,
            'eligible_sample_count_before_precision_filter':len(samples)+skipped,
            'sampling_precision':{'float32_ulp_multiplier':4,
                'source_coordinate_magnitude_floor':1,
                'rule':'Skip a source-qualified screen sample if either inverse source coordinate is within4binary32ULP of its nearest integer. ULP uses max(1,abs(coordinate),abs(nearest_integer)). Select before reading actual colours; no neighbour colour search.'},
            'minimum_source_alpha':min(alphas),'mean_rgb_error_limit':blend_bound,
            'within_one_pixel':mean<=blend_bound and all(math.hypot(x,y)<=1 for x,y in equal),
            'scope':'near-opaque protected raster correspondence only; no support/flight/slide/target approval'}
