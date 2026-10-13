shader_type canvas_item;
uniform float hidden_fraction : hint_range(0.0, 1.0) = 0.0;
uniform float frame_height = 48.0;
varying float frame_y;
void vertex() {
	// AtlasTexture UVs cover the source atlas, so normalize local frame vertices.
	frame_y = VERTEX.y / frame_height + 0.5;
}
void fragment() {
	if (frame_y < hidden_fraction || hidden_fraction >= 1.0) { discard; }
}
