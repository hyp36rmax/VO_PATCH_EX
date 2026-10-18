"""Upstream fidelity and optional-feature boundaries; no gameplay acceptance claim."""
from pathlib import Path
import subprocess
import sys
import types
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import selftest
ROOT = Path(__file__).resolve().parents[2]
PIN = '4ecae6237e1fc432c0be2f2b0aeab5303120e444'
BASE = '6b22b0dcd490eec8b6a3e953d881649e74ab26cb'
def load(ref):
    source = subprocess.check_output(['git', 'show', ref + ':v-on-patcher.py'], cwd=ROOT)
    m = types.ModuleType('reference'); m.__file__ = str(ROOT/'v-on-patcher.py')
    exec(compile(source, m.__file__, 'exec'), m.__dict__)
    return m
v = selftest.load_patcher(); upstream = load(PIN); baseline = load(BASE)
assert v.BLOBS['BOSSES'] == upstream.BLOBS['BOSSES']
for path in ('asm/bosses.asm', 'assets/portrait_jaguarandi.png', 'assets/portrait_z-gradt.png'):
    assert (ROOT/path).read_bytes() == subprocess.check_output(['git','show',PIN+':'+path],cwd=ROOT)
assert v.NEEDS == {'bossunlock':'bosses'}
assert not v.default_state()['bosses'] and not v.default_state()['bossunlock']
assert set(v.BUILDS) == set(upstream.BUILDS) == set(baseline.BUILDS)
for md5, build in v.BUILDS.items():
    ref = upstream.BUILDS[md5]
    expected = upstream.by_key(ref)['bosses'][2]
    # CE annex size relocates the entire boss section. The only changed
    # game symbol is the verified Experience hangar entry displacement.
    for key, value in ref.symbols.items():
        if key != 'BS_HDOFF':assert build.symbols[key] == value, (build.short,key)
    assert build.symbols['BS_HDOFF'] == v.UI_HANGAR_DRAW
    ref.symbols['BS_HDOFF'] = v.UI_HANGAR_DRAW
    ref.annex = build.annex
    assert v.link('BOSSES', build) == upstream.link('BOSSES', ref, blobs=v.BLOBS, base=v.cave_va('BOSSES',build)), build.short
    actual = v.by_key(build)['bosses'][2]
    assert [(int(o),str(b)) for o,b,_ in actual if len(b)<1000] == [(int(o),str(b)) for o,b,_ in expected if len(b)<1000]
    print('PASS upstream boss mapping/blob:',build.short,md5)
for folder in sys.argv[1:]:
    raw, _ = selftest.pristine(str(Path(folder)/'v_on.exe'), v)
    import hashlib
    md5 = hashlib.md5(raw).hexdigest()
    for wanted in (baseline.default_state(), dict.fromkeys(baseline.BY_KEY, True)):
        old, _, skip = baseline.apply_selected(bytearray(raw), wanted, baseline.BUILDS[md5]); assert not skip
        new, _, skip = v.apply_selected(bytearray(raw), wanted, v.BUILDS[md5]); assert not skip
        assert new == old, 'boss-disabled Experience bytes changed'
    print('PASS boss-disabled byte-identical Experience:',folder)
print('PASS upstream assembly, portraits, all four relocated boss blobs/sites, optional defaults and dependency')
