"""Compare every image against S03; only the linked title blob may differ."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import types
from functools import cache
from compact_catalog import Catalog
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import selftest
ROOT=Path(__file__).resolve().parents[2]
old=types.ModuleType('title_reference');old.__file__=str(ROOT/'v-on-patcher.py')
exec(subprocess.check_output(['git','show','3de7647:v-on-patcher.py'],cwd=ROOT),old.__dict__)
new=selftest.load_patcher()
old.by_key=cache(old.by_key);new.by_key=cache(new.by_key)
a,b=Catalog(sys.argv[1]),Catalog(sys.argv[2])
assert a.index['keys']==b.index['keys'] and set(a.index['entries'])==set(b.index['entries'])
changed=unchanged=0
for folder in map(Path,sys.argv[3:]):
 raw=(folder/'v_on.exe').read_bytes();md5=hashlib.md5(raw).hexdigest();edition=new.BUILDS[md5]
 for mask in range(1<<len(b.index['keys'])):
  name=f'{edition.short}/{mask}.json';ra=json.loads(a.read(name));rb=json.loads(b.read(name))
  options=dict.fromkeys(new.ESSENTIAL,True);options.update({k:bool(mask&(1<<i)) for i,k in enumerate(b.index['keys'])});options['bossunlock']=False
  images=[]
  for module,r in ((old,ra),(new,rb)):
   assert r['original']==hashlib.sha256(raw).hexdigest()
   data,_,skipped=module.apply_selected(bytearray(raw),options,module.BUILDS[md5]);assert not skipped
   if options['credits']:module.stamp_version(data,module.BUILDS[md5])
   assert hashlib.sha256(data).hexdigest()==r['base']
   data.extend(bytes(r['size']-len(data)))
   for offset,value in r['writes']:data[offset:offset+len(value)//2]=bytes.fromhex(value)
   assert len(data)==r['size'] and hashlib.sha256(data).hexdigest()==r['final']
   images.append(data)
  assert ra['writes']==rb['writes'],'unexpected Display delta change'
  if options['credits']:
   start=int(new.site('TITLEVER').for_build(edition));end=start+len(new.TITLEVER_CODE)
   assert len(new.TITLEVER_CODE)==len(old.TITLEVER_CODE)==155
   assert images[0][:start]==images[1][:start] and images[0][end:]==images[1][end:],name
   assert images[0][start:end]!=images[1][start:end]
   assert b'VO PATCH EX 0.18.1\0' in images[1][start:end]
   assert b'V-On Patcher dev' not in images[1] and b'VO PATCH EX 0.1-dev' not in images[1]
   changed+=1
  else:
   assert images[0]==images[1] and ra==rb,name
   unchanged+=1
print('PASS',changed,'title-only image changes;',unchanged,'byte-identical images; all Display writes unchanged')
