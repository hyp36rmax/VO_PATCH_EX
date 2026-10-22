"""Verify packaging exclusions, exact recipe bytes and unchanged runtime files."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

original, candidate = map(Path, sys.argv[1:])
def inventory(root):
    return {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file()}
a, b = inventory(original), inventory(candidate)
removed = {
    '_internal/DLLs/_ctypes_test.pyd',
    '_internal/experience/payload/experience-runtime/DLLs/_ctypes_test.pyd',
    '_internal/experience/catalog/game_profiles.h',
}
assert set(a) - set(b) == removed
assert not set(b) - set(a), sorted(set(b) - set(a))
allowed = {'PACKAGE-SHA256.json', '_internal/experience/payload-manifest.json',
           '_internal/experience/catalog/recipes.zip'}
changed = {n for n in b if a[n].read_bytes() != b[n].read_bytes()}
assert changed <= allowed, changed - allowed
old = json.loads(a['_internal/experience/payload-manifest.json'].read_text())
new = json.loads(b['_internal/experience/payload-manifest.json'].read_text())
old['files'].pop('experience-runtime/DLLs/_ctypes_test.pyd')
old['version']['revision'] = new['version']['revision']
assert old == new
catalog = '_internal/experience/catalog/'
index = json.loads(b[catalog+'catalog.json'].read_text())['entries']
with zipfile.ZipFile(a[catalog+'recipes.zip']) as source, zipfile.ZipFile(b[catalog+'recipes.zip']) as target:
    assert set(source.namelist()) == set(target.namelist()) == set(index)
    for name, entry in index.items():
        data = target.read(name)
        assert data == source.read(name)
        assert hashlib.sha256(data).hexdigest() == entry['sha256']
        assert target.getinfo(name).compress_type == zipfile.ZIP_LZMA
print('PASS exact three development-file exclusions; all retained runtime bytes and 2048 recipe bytes unchanged')
