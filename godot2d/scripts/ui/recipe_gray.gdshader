shader_type canvas_item;
uniform bool gray = false;
void fragment() {
 vec4 color = texture(TEXTURE, UV);
 if (gray) {
  float luminance = dot(color.rgb, vec3(0.299, 0.587, 0.114));
  color.rgb = vec3(luminance);
 }
 COLOR = color;
}
