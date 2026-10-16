shader_type canvas_item;
uniform bool clip_enabled = false;
uniform float boundary_y = 0.0;
uniform float visible_side = 1.0;
varying float world_y;
void vertex() {
	world_y = (MODEL_MATRIX * vec4(VERTEX, 0.0, 1.0)).y;
}
void fragment() {
	if (clip_enabled && (world_y - boundary_y) * visible_side < 0.0) { discard; }
}
