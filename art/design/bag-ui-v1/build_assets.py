from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent
OUT=ROOT.parents[2]/"godot2d/assets/ui/bag-v1"
OUT.mkdir(parents=True,exist_ok=True)
shutil.copy2(ROOT/"background-original.png",OUT/"background.png")
# Buttons/slots are reused unchanged from trade-v5; regenerate with its slice_assets.py.
