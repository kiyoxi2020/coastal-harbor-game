shader_type canvas_item;
render_mode unshaded;
// Sample the GPT tile's interior at shared borders. Exposed sides retain the
// generated ragged soil edge, so patches connect without doubling grassy rims.
uniform bool join_left = false;
uniform bool join_right = false;
uniform bool join_top = false;
uniform bool join_bottom = false;
varying vec4 tint;
void vertex() { tint = COLOR; }
void fragment() {
	vec2 pixel = UV * 16.0;
	if (join_left && pixel.x < 2.0) pixel.x += 4.0;
	if (join_right && pixel.x > 13.0) pixel.x -= 4.0;
	if (join_top && pixel.y < 2.0) pixel.y += 4.0;
	if (join_bottom && pixel.y > 13.0) pixel.y -= 4.0;
	COLOR = tint * texture(TEXTURE, pixel / 16.0);
}
