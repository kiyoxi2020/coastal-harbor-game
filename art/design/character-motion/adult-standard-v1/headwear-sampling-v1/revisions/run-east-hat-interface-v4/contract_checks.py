"""Assess frozen target masks and actual source provenance, not RGB skin guesses."""
from PIL import Image
CAP_OWNERS={3,4}
def assess(contract,images):
 size=images['base'].size
 keys=['old_hat','hat','final','owners','required_cover','required_contact','frozen_hat','allowed_edit']
 if any(images[key].size!=size for key in keys):raise ValueError('Every target mask must use original full-frame coordinates.')
 base=list(images['base'].convert('RGBA').get_flattened_data());old=list(images['old_hat'].convert('RGBA').get_flattened_data());hat=list(images['hat'].convert('RGBA').get_flattened_data());final=list(images['final'].convert('RGBA').get_flattened_data());owners=list(images['owners'].get_flattened_data())
 cover=list(images['required_cover'].get_flattened_data());contact=list(images['required_contact'].get_flattened_data());frozen=list(images['frozen_hat'].get_flattened_data());edit=list(images['allowed_edit'].get_flattened_data());alpha=contract.get('minimum_solid_alpha',200)
 opening=list(images.get('required_opening',Image.new('L',size)).get_flattened_data())
 visible_head=images.get('visible_head_in_edit_band',Image.new('L',size))
 if visible_head.size!=size:raise ValueError('Visible head mask must use original full-frame coordinates.')
 visible_head=list(visible_head.get_flattened_data())
 result={'hat_inside_required_opening':0,'hat_inside_visible_head':0,'uncovered_scalp':0,'uncovered_contact':0,'contact_alpha_gaps':0,'non_hat_source_pixels':0,'changed_frozen_hat_pixels':0,'outside_authorized_rgba_differences':0,'unapproved_placement':int(contract.get('placement_px')!=[0,0])}
 for i in range(len(base)):
  result['hat_inside_required_opening']+=bool(opening[i] and owners[i] in CAP_OWNERS)
  result['hat_inside_visible_head']+=bool(visible_head[i] and owners[i] in CAP_OWNERS)
  result['uncovered_scalp']+=bool(cover[i] and (owners[i] not in CAP_OWNERS or hat[i][3]<alpha or final[i][3]<alpha))
  result['uncovered_contact']+=bool(contact[i] and owners[i] not in CAP_OWNERS)
  result['contact_alpha_gaps']+=bool(contact[i] and (hat[i][3]<alpha or final[i][3]<alpha))
  result['changed_frozen_hat_pixels']+=bool(frozen[i] and old[i]!=hat[i])
  result['outside_authorized_rgba_differences']+=bool(not edit[i] and base[i]!=final[i])
 for source in images['source_checks']:
  if source['ownership'].size!=source['forbidden'].size:raise ValueError('Source masks use different coordinate systems.')
  for own,forbidden in zip(source['ownership'].get_flattened_data(),source['forbidden'].get_flattened_data()):result['non_hat_source_pixels']+=bool(own and forbidden)
 result['passed']=not any(result.values())
 return result
