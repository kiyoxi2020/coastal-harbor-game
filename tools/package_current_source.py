"""Package only Git-tracked current 2D sources. Run from any directory."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import subprocess,hashlib,json,re
root=Path(__file__).resolve().parents[1]
delivery=root/"交付与预览/2D"
names=subprocess.check_output(["git","ls-files","-z"],cwd=root).decode().split("\0")[:-1]
selected=[n for n in names if n.startswith(("godot2d/","art/godot2d/","docs/")) or n=="沿海小镇复兴-游戏设计简稿.md"]
assert "godot2d/scripts/harbor.gd" in selected
assert not any("tree-study-v3" in n or "test_tree_study" in n for n in selected)
version=re.search(r'application/short_version="([0-9.]+)"',(root/"godot2d/export_presets.cfg").read_text()).group(1)
path=delivery/f"CoastalHarbor2D-v{version}-source.zip"
with ZipFile(path,"w",ZIP_DEFLATED) as z:
    for name in selected:
        z.write(root/name,name)
    z.write(root/"godot2d/README.md","README.md")
with ZipFile(path) as z:
    assert z.testzip() is None
    assert all(z.read(n)==(root/n).read_bytes() for n in selected)
    assert all(i.flag_bits&0x800 for i in z.infolist() if not i.filename.isascii())
    count=len(z.namelist())
report_path=delivery/"package-verification.json"
report=json.loads(report_path.read_text())
report["source_files_matched"]=count
report["source_scope"]="current Git-tracked 2D sources only; retired tree studies removed"
report[path.name]={"bytes":path.stat().st_size,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print("Verified current source ZIP:",count,"files,",path.stat().st_size,"bytes")
