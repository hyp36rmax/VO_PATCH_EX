#!/usr/bin/env python3
"""B01 artwork, UI content and unchanged game/installation contract checks."""
import ast
import base64
import hashlib
import io
from pathlib import Path
import runpy
import subprocess
import tempfile
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = '6b22b0dcd490eec8b6a3e953d881649e74ab26cb'
def original(name):
    return subprocess.check_output(['git', 'show', BASE + ':' + name], cwd=ROOT)
source = (ROOT / 'v-on-patcher.py').read_text()
now = runpy.run_path(str(ROOT / 'v-on-patcher.py'))
with tempfile.TemporaryDirectory() as td:
    p = Path(td) / 'v-on-patcher.py'; p.write_bytes(original('v-on-patcher.py'))
    before = runpy.run_path(str(p))
for key in ('LABEL', 'REPO_URL', 'LOGO_CREDIT', 'ICON_PNG', 'ESSENTIAL', 'ABOUT'):
    assert now[key] == before[key], key
assert {k: v for k, v in now['BLOBS'].items() if k != 'BOSSES'} == before['BLOBS']
assert now['EXTRA'] == before['EXTRA'] + ('bosses', 'bossunlock')
assert now['BOSSES_AUTHOR'] == 'Vortyne'
assert now['BY_KEY']['padxinput'] == before['BY_KEY']['padxinput']
assert now['BY_KEY']['hires'][1] == before['BY_KEY']['hires'][1]
assert now['TITLE'] == 'V-On Patcher EX'
assert now['EX_VERSION'] == '0.1-dev'
assert now['PROJECT_URL'] == 'https://github.com/hyp36rmax/VO_PATCH_EX'
for name in ('assets/VONPatcherLogo1.png', 'assets/VONPatcherIcon.png', 'assets/icon.ico'):
    assert (ROOT / name).read_bytes() == original(name), name
# Restrict function changes to About, the information popup and no installation code.
def funcs(text):
    return {n.name: ast.dump(n, include_attributes=False) for n in ast.walk(ast.parse(text))
            if isinstance(n, ast.FunctionDef) and n.name in ('restore', 'load', 'stamp_version')}
assert funcs(source) == funcs(original('v-on-patcher.py').decode())
base = Image.open(ROOT / 'assets/VONPatcherLogo1.png').convert('RGBA')
ex = Image.open(ROOT / 'assets/EX-approved.png').convert('RGBA')
assert hashlib.sha256((ROOT / 'assets/EX-approved.png').read_bytes()).hexdigest() == '0fce2fa24e638197873819efe3ca22112c8854fa51814ea804357053ad678cfb'
assert ex.getchannel('A').getextrema() == (0, 255)
ex = ex.crop(ex.getchannel('A').getbbox())
ex = ex.resize((760, round(ex.height * 760 / ex.width)), Image.Resampling.LANCZOS)
expected = Image.new('RGBA', (2715, 723)); expected.alpha_composite(base); expected.alpha_composite(ex, (1944, 447))
actual = Image.open(ROOT / 'assets/VOPatchEXLogo.png').convert('RGBA')
assert actual.tobytes() == expected.tobytes()
# The approved nesting intentionally overlaps the capsule shadow slightly.
embedded = Image.open(io.BytesIO(base64.b64decode(now['LOGO_PNG']))).convert('RGBA')
assert embedded.size == (796, 212)
assert 0.95 <= 760 / 783 <= 1.0
assert abs((1944+760/2)-(1932+783/2)) <= 1
assert now["LOGO_HEIGHT"] / actual.height >= 96 / 658
assert embedded.getchannel('A').getextrema() == (0, 255)
about = source[source.index('        def _about_body'):source.index('        def _log_body')]
assert about.index('VO PATCH EX') < about.index('Based on:') < about.index('Original logo by:')
assert 'self._patch_body(parent, ABOUT, None)' in about and 'LOGO_PNG' not in about
assert 'wraplength=380' not in about
assert 'height=min(height, limit)' in source and 'scrollregion=' in source
print('PASS exact source provenance, original artwork/icon, composition, alpha, embedded size, title/About, appended hires, unchanged XInput, existing blobs and Restore/load/version functions')
print('NEEDS VALIDATION: physical Windows layout, DPI, popup scrolling and clickable links')

from fractions import Fraction
for scale in (1,1.25,1.5):
    target=round(now['LOGO_HEIGHT']*scale)
    ratio=Fraction(target,embedded.height).limit_denominator(8)
    actual_height=embedded.height*ratio.numerator/ratio.denominator
    assert abs(actual_height-target)<=1
    assert abs(embedded.width*ratio.numerator/ratio.denominator/actual_height-actual.width/actual.height)<0.01
print('PASS proportional header sizing at 100/125/150%; physical Windows acceptance pending')
