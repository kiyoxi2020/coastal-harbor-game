extends SceneTree
const Construction=preload("res://dev/characters/character_construction_samples.gd")
const Support=preload("res://tests/life_test_support.gd")
var fixture_root="/private/tmp/coastal-foreground-consumer-fixture"
var inputs:Dictionary={}
func write_json(relative:String,data:Variant) -> Dictionary:
 var path=fixture_root.path_join(relative);DirAccess.make_dir_recursive_absolute(path.get_base_dir())
 var file=FileAccess.open(path,FileAccess.WRITE);file.store_string(JSON.stringify(data));file.close()
 inputs[relative]=FileAccess.get_sha256(path);return {"file":relative,"sha256":inputs[relative]}
func write_mask(relative:String,bytes:PackedByteArray) -> Dictionary:
 var path=fixture_root.path_join(relative);DirAccess.make_dir_recursive_absolute(path.get_base_dir())
 Image.create_from_data(2,2,false,Image.FORMAT_L8,bytes).save_png(path)
 inputs[relative]=FileAccess.get_sha256(path);return {"file":relative,"sha256":inputs[relative]}
func _initialize() -> void:
 var s=Support.new();var consumer=Construction.new()
 var frame={"pose_id":"hoe_south_key_1","operation":"supported-alpha-stack","layers":[{"id":"under_hat_hair"},{"id":"near_hat"}],"layer_order":["base","under_hat_hair","near_hat"],"compatibility":{"hat_source":{},"hat_ownership":{},"hat_identity_sha256":"a".repeat(64)}}
 s.check("foreground_shape_contract_exists",consumer.has_method("head_frame_shape_valid"))
 if not s.passed():quit(1);return
 s.check("existing_head_accepted",consumer.call("head_frame_shape_valid",frame,frame.pose_id))
 frame.base_foreground={};frame.layer_order.append("base_foreground")
 s.check("virtual_foreground_is_not_extra_texture",consumer.call("head_frame_shape_valid",frame,frame.pose_id))
 frame.layers.append({"id":"base_foreground"})
 s.check("supplied_body_layer_rejected",not consumer.call("head_frame_shape_valid",frame,frame.pose_id))
 frame.layers.pop_back();frame.layer_order=["base","base_foreground","under_hat_hair","near_hat"]
 s.check("wrong_depth_rejected",not consumer.call("head_frame_shape_valid",frame,frame.pose_id))
 frame.layer_order=["far_hat","base","under_hat_hair","near_hat","base_foreground"];frame.layers.push_front({"id":"far_hat"})
 s.check("far_hat_still_supported",consumer.call("head_frame_shape_valid",frame,frame.pose_id))
 frame.pose_id="wrong"
 s.check("wrong_pose_rejected",not consumer.call("head_frame_shape_valid",frame,"hoe_south_key_1"))
 var owner=write_mask("templates/owner.png",PackedByteArray([255,0,0,0]))
 var visible=write_mask("templates/head.png",PackedByteArray([0,255,255,0]))
 var poses=write_json("templates/poses.json",{})
 var clip=JSON.parse_string(JSON.stringify({"poses":poses,"variant":"B","canvas_px":[2,2],"root_anchor_px":[1,2],"display_scale":0.1}))
 var row=clip.duplicate(true);row.pose_id="hoe_south_key_1";row.record_id="foreground-test"
 row.surfaces={"head":{"layer_id":"base","mask":visible},"hands-tools-foreground":{"layer_id":"base","mask":owner}}
 var doc={"kind":"coastal-pose-annotations-v1","schema_version":1,"records":[row]}
 var ref=write_json("templates/annotation.json",doc)
 var binding={"mode":"canonical-rgba-ownership-split","surface_id":"hands-tools-foreground","target_pose":{"document":ref,"record":"foreground-test"},"ownership":{"role":"canonical-foreground-ownership","mask":owner}}
 var mapping={"mapping_id":"head-map","target_pose":binding.target_pose.duplicate(true)}
 var adaptations={"hair":write_json("parts/hair/views.json",{"mappings":[mapping]}),"hat":write_json("parts/hat/views.json",{"mappings":[mapping]})}
 var mapped_frame={"layers":[{"slot":"hair","view_binding":{"view_id":"hair","mapping_id":"head-map"}},{"slot":"hat","view_binding":{"view_id":"hat","mapping_id":"head-map"}}]}
 s.check("foreground_uses_actual_head_annotation",consumer.foreground_targets_valid(fixture_root,binding,mapped_frame,adaptations,inputs))
 mapping.target_pose.record="different-actual-head"
 adaptations.hair=write_json("parts/hair/views.json",{"mappings":[mapping]})
 s.check("separate_hair_head_authority_rejected",not consumer.foreground_targets_valid(fixture_root,binding,mapped_frame,adaptations,inputs))
 mapping.target_pose.record="foreground-test";adaptations.hair=write_json("parts/hair/views.json",{"mappings":[mapping]})
 adaptations.hat=write_json("parts/hat/views.json",{"mappings":[]})
 s.check("missing_near_hat_target_rejected",not consumer.foreground_targets_valid(fixture_root,binding,mapped_frame,adaptations,inputs))
 s.check("canonical_typed_binding_accepted",consumer.foreground_binding_valid(fixture_root,binding,clip,row.pose_id,inputs))
 s.check("other_pose_binding_rejected",not consumer.foreground_binding_valid(fixture_root,binding,clip,"hoe_south_key_2",inputs))
 binding.ownership.mask=visible
 s.check("substituted_mask_rejected",not consumer.foreground_binding_valid(fixture_root,binding,clip,row.pose_id,inputs))
 binding.ownership.mask=owner
 visible=write_mask("templates/head.png",PackedByteArray([255,255,0,0]));row.surfaces.head.mask=visible
 binding.target_pose.document=write_json("templates/annotation.json",doc)
 s.check("foreground_head_overlap_rejected",not consumer.foreground_binding_valid(fixture_root,binding,clip,row.pose_id,inputs))
 row.surfaces.head.mask=write_mask("templates/head.png",PackedByteArray([0,73,255,0]));binding.target_pose.document=write_json("templates/annotation.json",doc)
 s.check("nonbinary_head_surface_rejected",not consumer.foreground_binding_valid(fixture_root,binding,clip,row.pose_id,inputs))
 print("CONSTRUCTION_FOREGROUND checks=",s.checks.size()," passed=",s.passed());quit(0 if s.passed() else 1)
