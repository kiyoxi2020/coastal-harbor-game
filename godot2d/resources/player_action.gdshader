shader_type canvas_item;
render_mode unshaded;
uniform float bend = 0.0;
uniform float side = 1.0;
uniform float pinned_from = 0.62;
varying vec4 tint;
void vertex() { tint = COLOR; }
void fragment() {
	// Rig the upper body while the boots remain anchored in the bottom strip.
	vec2 uv = UV;
	float torso = clamp((pinned_from - uv.y) / max(pinned_from, 0.1), 0.0, 1.0);
	uv.x -= side * bend * torso * 0.045;
	uv.y -= abs(bend) * torso * 0.018;
	COLOR = tint * texture(TEXTURE, uv);
}
