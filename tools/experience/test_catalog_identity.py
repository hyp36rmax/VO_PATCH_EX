"""Reconstruct every shipped option recipe and test strict activated VS identity."""
import ast,hashlib,json,struct,sys
from contextlib import nullcontext
from compact_catalog import Catalog
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'dual_display'))
import startup_image as s
from functools import cache
s.mode_profiles.engineering3840.load_private=cache(s.mode_profiles.engineering3840.load_private)
catalog=Path(sys.argv[1]);v=s.mode_profiles.engineering3840.load_private()
v.by_key=cache(v.by_key)
index=json.loads((catalog/'catalog.json').read_text())
# Credits-disabled boss-free masks retain the I01 recipes exactly.
# test_title_catalog.py checks intentional title-only changes for every mask.
import lzma,subprocess
baseline=json.loads(lzma.decompress(subprocess.check_output(
 ['git','show','4a6ef2e3e3bc4354a4b75e00b86e677bf61fa83b:tools/experience/ci/catalog.json.xz'],
 cwd=Path(__file__).resolve().parents[2])))
for name,entry in baseline['index']['entries'].items():
 if not (int(Path(name).stem) & (1 << index['keys'].index('credits'))):
  assert index['entries'][name]==entry, ('credits-disabled recipe changed',name)
print('PASS 256 credits-disabled boss-free recipe identities preserved; title-enabled masks checked separately',flush=True)
rows=[ast.literal_eval(line.rstrip(',').replace('{','[').replace('}',']')) for line in (catalog/'game_profiles.h').read_text().splitlines() if line.startswith('{0x')]
assert len({tuple(row[:3]) for row in rows})==len(rows),'ambiguous first-match identity'
def accepted(image,base,stamp,size):
 for row in rows:
  if row[:3]==[base,stamp,size]:return image[row[3]-base:row[3]-base+32]==bytes(row[8])
 return False
count=0
with nullcontext(Catalog(catalog)) as archive:
 for folder in map(Path,sys.argv[2:]):
  raw=(folder/'v_on.exe').read_bytes();edition=v.BUILDS[hashlib.md5(raw).hexdigest()]
  for mask in range(1 << len(index['keys'])):
   wanted=dict.fromkeys(v.ESSENTIAL,True);wanted.update({key:bool(mask&(1<<i)) for i,key in enumerate(index['keys'])})
   wanted['bossunlock']=False
   original,_,skipped=v.apply_selected(bytearray(raw),wanted,edition);assert not skipped
   if wanted.get('credits'):v.stamp_version(original,edition)
   recipe=json.loads(archive.read(f'{edition.short}/{mask}.json'))
   assert hashlib.sha256(raw).hexdigest()==recipe['original']
   assert recipe['edition']==edition.short and recipe['mask']==mask
   assert hashlib.sha256(original).hexdigest()==recipe['base']
   final=original+bytes(max(0,recipe['size']-len(original)))
   for offset,hexdata in recipe['writes']:final[offset:offset+len(bytes.fromhex(hexdata))]=bytes.fromhex(hexdata)
   assert len(final)==recipe['size']
   assert hashlib.sha256(final).hexdigest()==recipe['final']
   pe=v._PE(final);image=s.mapped(final);boot=next(sec for sec in pe.sections if sec['name']==b'.voboot')
   table=boot['raddr']+512
   assert struct.unpack_from('<II',final,table)==(0x33504f56,2)
   assert struct.unpack_from('<I',final,table+16)[0]==int(wanted['hires'])
   pos=table+20
   for profile in range(5):
    n=struct.unpack_from('<I',final,pos)[0];pos+=4
    for _ in range(n):
     off,length=struct.unpack_from('<II',final,pos);pos+=8
     before=final[pos:pos+length];after=final[pos+length:pos+2*length];pos+=2*length
     if profile==4:
      assert image[off:off+length]==before
      image[off:off+length]=after
   stamp=v._pe_stamp(final);size=struct.unpack_from('<I',final,pe.opt+56)[0]
   assert accepted(image,pe.base,stamp,size),(edition.short,mask)
   assert not accepted(image,pe.base,stamp^1,size)
   assert not accepted(image,pe.base,stamp,size+4096*128)
   row=next(row for row in rows if row[:3]==[pe.base,stamp,size]);image[row[3]-pe.base]^=1
   assert not accepted(image,pe.base,stamp,size)
   count+=1
print('PASS',count,'reconstructed images, default aspect, activated VS signatures; unknown stamp/size and altered signatures rejected')
