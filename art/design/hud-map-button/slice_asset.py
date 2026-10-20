"""Trim generated icon's faint outside shadow; preserve opaque art RGB, no resampling."""
from pathlib import Path
from PIL import Image
import json
root = Path(__file__).resolve().parent
image = Image.open(root / 'original.png').convert('RGBA')
alpha = image.getchannel('A').point(lambda value: value if value >= 128 else 0)
image.putalpha(alpha)
rect = alpha.getbbox()
output = root.parents[2] / 'godot2d/assets/ui/hud-map/map.png'
image.crop(rect).save(output)
(root / 'slice.json').write_text(json.dumps({'source': 'original.png', 'rect': rect, 'alpha_min': 128, 'resampled': False, 'filter': 'nearest'}, indent=2))
