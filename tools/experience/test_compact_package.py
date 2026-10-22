"""Compare compact distribution against the immutable public release inputs."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile
from compact_catalog import Catalog, NAME

original, candidate = map(Path, sys.argv[1:])
def inventory(root):
    return {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file()}
a, b = inventory(original), inventory(candidate)
removed = {'_internal/DLLs/_ctypes_test.pyd',
           '_internal/experience/payload/experience-runtime/DLLs/_ctypes_test.pyd',
           '_internal/experience/catalog/game_profiles.h',
           '_internal/experience/catalog/recipes.zip'}
added = {'_internal/compact_catalog.py', '_internal/experience/catalog/'+NAME}
assert set(a)-set(b)==removed
assert set(b)-set(a)==added
allowed={'PACKAGE-SHA256.json','_internal/experience/payload-manifest.json','_internal/normal_install.py'}
changed={n for n in set(a)&set(b) if a[n].read_bytes()!=b[n].read_bytes()}
assert changed<=allowed, changed-allowed
old=json.loads(a['_internal/experience/payload-manifest.json'].read_text())
new=json.loads(b['_internal/experience/payload-manifest.json'].read_text())
old['files'].pop('experience-runtime/DLLs/_ctypes_test.pyd')
old['version']['revision']=new['version']['revision']
assert old==new
catalog=Catalog(candidate/'_internal/experience/catalog')
with zipfile.ZipFile(original/'_internal/experience/catalog/recipes.zip') as source:
    assert set(source.namelist())==set(catalog.index['entries'])
    for name in source.namelist():
        raw=catalog.read(name)
        assert raw==source.read(name),name
        assert hashlib.sha256(raw).hexdigest()==catalog.index['entries'][name]['sha256']
print('PASS 2048 exact recipes; only compact loader/storage and S01 exclusions differ; native/runtime bytes unchanged')
