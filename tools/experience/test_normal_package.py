"""Distribution integrity and game-asset exclusion, no Windows execution claim."""
from pathlib import Path
import hashlib,json,sys,zipfile
root=Path(sys.argv[1]).resolve();internal=root/'_internal';ex=internal/'experience'
manifest=json.loads((root/'PACKAGE-SHA256.json').read_text())
assert {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()} == set(manifest) | {'PACKAGE-SHA256.json'}, 'Unmanifested package files'
for name in manifest:
 assert not Path(name).is_absolute() and '..' not in Path(name).parts, name
for name,digest in manifest.items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
allowed={'v-on-patcher.exe','python.exe','pythonw.exe'}
for path in root.rglob('*'):
 if not path.is_file():continue
 assert path.name.lower() not in ('v_on.exe','von.bin','von.cue'),path
 assert path.suffix.lower() not in ('.iso','.avi','.wav','.img','.cue','.log','.dmp','.key','.pfx','.p12'),path
 if path.suffix.lower()=='.pem':
  assert path.relative_to(root).as_posix() == '_internal/Lib/site-packages/certifi/cacert.pem', path
  assert b'PRIVATE KEY' not in path.read_bytes() and b'BEGIN CERTIFICATE' in path.read_bytes()
 if path.suffix.lower()=='.exe':assert path.name in allowed,path
assert (root/'v-on-patcher.exe').read_bytes()[:2]==b'MZ'
assert (ex/'payload/vodisplay.dll').read_bytes()[:2]==b'MZ'
index=json.loads((ex/'catalog/catalog.json').read_text())
assert len(index['entries'])==2 * (1 << len(index['keys']))
with zipfile.ZipFile(ex/'catalog/recipes.zip') as z:
 assert z.testzip() is None and set(z.namelist())==set(index['entries'])
 for name,entry in index['entries'].items():
  data=z.read(name);assert hashlib.sha256(data).hexdigest()==entry['sha256']
  recipe=json.loads(data);assert recipe['final']==entry['final']
  # Recipes are sparse changes requiring a verified original, never full files.
  assert sum(len(bytes.fromhex(x[1])) for x in recipe['writes'])<recipe['size']
for name in ['normal_lifecycle.py','diagnostics.py','discovery.py','movie_geometry.py','runtime_checkpoint.py','crash_evidence.py','pythonw.exe','python312.dll','python312.zip']:
 assert (ex/'payload/experience-runtime'/name).is_file()
print('PASS manifest hashes, complete sparse option recipes, upstream Windows launcher, runtime completeness, game-asset exclusion')

for name in ['Playable-Bosses.txt','Pairomaniac-MIT.txt','cnc-ddraw-MIT.txt','Python.txt','certifi-LICENSE.txt','MinGW-runtime.txt']:
 assert (root/'Licenses'/name).is_file(), name
assert (internal/'input/vontanita.dll').is_file()
assert '_experience_bind(Patcher' in (internal/'v-on-patcher.py').read_text()
assert (ex/'payload/experience-runtime/diagnostics.py').read_bytes() == (Path(__file__).parent/'diagnostics.py').read_bytes()

for path in root.rglob('*.zip'):
 with zipfile.ZipFile(path) as archive:
  assert archive.testzip() is None, path
  for name in archive.namelist():
   entry=Path(name)
   assert not entry.is_absolute() and '..' not in entry.parts, (path,name)
   assert entry.name.lower() not in ('v_on.exe','von.bin','von.cue'), (path,name)
   assert entry.suffix.lower() not in ('.iso','.img','.avi','.wav','.dmp','.pfx','.p12'), (path,name)
print('PASS exact manifest coverage, nested archive exclusions, controller/runtime and license notices')
