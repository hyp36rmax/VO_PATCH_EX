"""Check product and generated title versions while preserving upstream provenance."""
import ast
import json
import runpy
import subprocess
import sys
from pathlib import Path
import unittest
from release_version import VERSION, configure, validate_release_tag, build_identity


class ProductVersion(unittest.TestCase):
    def test_presentation_preserves_patch_version(self):
        scope = {'VERSION': 'dev', 'EX_VERSION': '0.1-dev',
                 'TITLE': 'V-On Patcher EX',
                 'EX_ATTRIBUTION': 'VO PATCH EX 0.1-dev — hyp36rmax\nOriginal attribution'}
        configure(scope)
        self.assertEqual(scope['VERSION'], 'dev')
        self.assertEqual(scope['EX_VERSION'], VERSION)
        self.assertEqual(scope['TITLE'], 'V-On Patcher EX ' + VERSION)
        self.assertEqual(scope['EX_ATTRIBUTION'], 'VO PATCH EX ' + VERSION + ' — hyp36rmax\nOriginal attribution')

    def test_release_tag_gate(self):
        validate_release_tag(VERSION)
        validate_release_tag('')
        with self.assertRaises(ValueError):
            validate_release_tag('v0.18.0-experience.2')

    def test_build_kinds(self):
        revision = '0123456789abcdef0123456789abcdef01234567'
        for kind, rc, label in [('release', None, ''), ('prerelease', None, 'Pre-Release'), ('rc', 2, 'RC2'), ('development', None, 'Dev')]:
            identity = build_identity(revision, kind, rc)
            self.assertEqual(identity['subtitle'], label + ' · 0123456' if label else '')
        for bad in ('', 'abcdef0', 'not-a-commit'):
            with self.assertRaises(ValueError): build_identity(bad)

    def test_documented_release(self):
        root = Path(__file__).resolve().parents[2]
        self.assertTrue((root/'docs/releases'/ (VERSION + '.md')).is_file())
        tree = ast.parse((root/'v-on-patcher.py').read_text())
        values = {n.targets[0].id: ast.literal_eval(n.value) for n in tree.body
                  if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
                  and n.targets[0].id in ('VERSION', 'EX_VERSION', 'TITLE_RELEASE')}
        self.assertEqual(values, {'VERSION': 'dev', 'EX_VERSION': '0.1-dev', 'TITLE_RELEASE': VERSION.removeprefix('v')})


if __name__ == '__main__':
    if len(sys.argv) == 2:
        package = Path(sys.argv.pop()).resolve()
        internal = package/'_internal'
        sys.path.insert(0, str(internal))
        scope = runpy.run_path(str(internal/'v-on-patcher.py'), run_name='version_check')
        assert scope['EX_VERSION'] == VERSION
        assert scope['TITLE'] == 'V-On Patcher EX ' + VERSION
        assert scope['VERSION'] == 'dev'
        assert scope['version_text']() == 'VO PATCH EX ' + VERSION.removeprefix('v')
        assert scope['EX_ATTRIBUTION'].startswith('VO PATCH EX ' + VERSION)
        assert VERSION in (package/'READ-ME.txt').read_text()
        metadata = json.loads((internal/'experience/payload-manifest.json').read_text())
        assert metadata['version']['release'] == VERSION
        identity = build_identity(metadata['version']['revision'],metadata['version']['kind'],metadata['version'].get('rc'))
        assert all(metadata['version'][k] == value for k, value in identity.items())
        scope['title_data'](identity['subtitle'])
        output = subprocess.check_output([sys.executable, str(internal/'v-on-patcher.py'), '--version'], text=True)
        assert output.strip() == VERSION, output
        print('PASS packaged window/About globals, CLI, readme and installed version metadata')
    unittest.main()
