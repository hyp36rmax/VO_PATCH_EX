"""Offline option-complete patch data. No game binaries shipped, no player compiler."""
import argparse,hashlib,json,struct,sys,zipfile
from functools import cache
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'dual_display'))
import startup_image as si
import engineering_shared

def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('retail',type=Path);p.add_argument('jpre',type=Path);a=p.parse_args()
 # This offline process uses one private patcher instance; generators only
 # read its tables. Avoid recompiling the embedded blobs for every profile.
 si.mode_profiles.engineering3840.load_private=cache(si.mode_profiles.engineering3840.load_private)
 out=a.output;out.mkdir(exist_ok=True,parents=True);v=si.mode_profiles.engineering3840.load_private()
 keys=list(v.EXTRA[:7]+v.ABOUT)+['bosses','bossunlock'];index={'keys':keys,'entries':{}};rows=set();count=0
 with zipfile.ZipFile(out/'recipes.zip','w',zipfile.ZIP_DEFLATED) as z:
  for folder in [a.retail,a.jpre]:
   raw=(folder/'v_on.exe').read_bytes();edition=v.BUILDS[hashlib.md5(raw).hexdigest()]
   cached={}
   for mask in range(1<<len(keys)):
    # Pre-unlock is a file transaction only; reuse the verified executable
    # recipe while retaining the distinct requested mask in its metadata.
    if mask & (1 << keys.index('bossunlock')):
     recipe=dict(cached[mask & ~(1 << keys.index('bossunlock'))],mask=mask)
     name=f'{edition.short}/{mask}.json';payload=json.dumps(recipe,separators=(',',':')).encode();z.writestr(name,payload)
     index['entries'][name]={'sha256':sha(payload),'final':recipe['final']}
     count+=1
     continue
    wanted=dict.fromkeys(v.ESSENTIAL,True);wanted.update({key:bool(mask&(1<<i)) for i,key in enumerate(keys)})
    # Pre-unlock changes progression, not executable bytes. Normalize the
    # dependency for offline generation, retaining every stable option mask.
    wanted['bossunlock']=False
    final,meta=si.build(raw,wanted);pe=v._PE(final)
    original,_,skipped=v.apply_selected(bytearray(raw),wanted,edition);assert not skipped
    if wanted.get('credits'):v.stamp_version(original,edition)
    base=bytes(original)+bytes(max(0,len(final)-len(original)))
    writes=[[off,after.hex()] for off,before,after in si.spans(base,final)]
    rebuilt=bytearray(base[:len(final)])
    for off,hexdata in writes:rebuilt[off:off+len(bytes.fromhex(hexdata))]=bytes.fromhex(hexdata)
    assert rebuilt==final
    recipe={'original':sha(raw),'base':sha(original),'final':sha(final),'size':len(final),'writes':writes,'edition':edition.short,'mask':mask}
    cached[mask]=recipe
    name=f'{edition.short}/{mask}.json';payload=json.dumps(recipe,separators=(',',':')).encode();z.writestr(name,payload)
    index['entries'][name]={'sha256':sha(payload),'final':sha(final)}
    dual,dm=engineering_shared.build(raw,wanted);dp=v._PE(dual)
    port=None if edition.short=='retail' else v.PORT['%08x'%v._pe_stamp(raw)]
    loop=0x6bc94c if port is None else port['va'][0x6bc94c]
    sig=dm['shared']['signature'];off=dp.off(sig-dp.base)
    size=struct.unpack_from('<I',final,pe.opt+56)[0]
    row='{'+','.join(hex(x) for x in (pe.base,v._pe_stamp(raw),size,sig,loop,dm['state']['mode1'],dm['state']['split'],dm['ui']+0x1e88))+',{'+','.join(hex(b) for b in dual[off:off+32])+'}}'
    rows.add(row);count+=1
    if count%16==0:print('validated option images',count,flush=True)
 (out/'catalog.json').write_text(json.dumps(index,indent=2)+'\n')
 (out/'game_profiles.h').write_text('/* Exact F01-P04 generated image identities. */\n#include <stdint.h>\ntypedef struct {uintptr_t base;unsigned stamp,size;uintptr_t signature,loop,mode,split,show;unsigned char bytes[32];} VoGameProfile;\nstatic const VoGameProfile vo_profiles[]={\n'+',\n'.join(sorted(rows))+'\n};\n')
 print('PASS',count,'option images;',len(rows),'strict wrapper identities',flush=True)
if __name__=='__main__':main()
