"""Import overrides must not evade runtime pixel integrity verification."""
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import godot_integration as integration


class ImportSectionTests(unittest.TestCase):
    def test_duplicate_or_unknown_sections_are_rejected(self):
        texture = 'res://assets/characters/integrations/fixture/frames/idle/north/p.png'
        original = integration.import_config(texture)
        cases = ['\n[params]\nprocess/premult_alpha=true\n',
                 '\n[remap]\npath="res://wrong.ctex"\n',
                 '\n[deps]\nsource_file="res://wrong.png"\n',
                 '\n  [params] ; overridden\nprocess/fix_alpha_border=true\n',
                 '\n[unregistered]\nvalue=true\n']
        with tempfile.TemporaryDirectory(prefix='coastal-import-sections-', dir='/private/tmp') as temp:
            path = Path(temp)/'fixture.png.import'
            path.write_text(original)
            integration.verify_import(path, texture)
            for extra in cases:
                with self.subTest(section=extra):
                    path.write_text(original + extra)
                    with self.assertRaises(ValueError):
                        integration.verify_import(path, texture)

    def test_spaced_or_quoted_override_keys_are_rejected(self):
        texture = 'res://assets/characters/integrations/fixture/frames/idle/north/p.png'
        original = integration.import_config(texture)
        with tempfile.TemporaryDirectory(prefix='coastal-import-keys-', dir='/private/tmp') as temp:
            path = Path(temp)/'fixture.png.import'
            for section, key, value in [('remap', 'path ', '"res://wrong.ctex"'),
                                        ('remap', '"path"', '"res://wrong.ctex"'),
                                        ('deps', 'source_file ', '"res://wrong.png"'),
                                        ('deps', '"source_file"', '"res://wrong.png"')]:
                with self.subTest(section=section, key=key):
                    following = 'deps' if section == 'remap' else 'params'
                    text = original.replace('\n\n['+following+']', '\n'+key+'='+value+'\n\n['+following+']')
                    path.write_text(text)
                    with self.assertRaises(ValueError):
                        integration.verify_import(path, texture)
