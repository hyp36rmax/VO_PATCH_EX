"""G02 attribution preservation and title-hook execution; no Windows claim."""
import pathlib, subprocess, sys, types, struct
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EAX
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import selftest
v=selftest.load_patcher()
baseline=subprocess.check_output(['git','show','3de764720c89da3e355ea05013c1f6f57fcc8d40:v-on-patcher.py'],cwd=ROOT,text=True)
old=types.ModuleType('attribution_baseline');old.__file__=str(ROOT/'v-on-patcher.py');sys.modules[old.__name__]=old
exec(compile(baseline,old.__file__,'exec'),old.__dict__)
assert v.CREDITS==old.CREDITS and v.CREDIT_NEW_TILES==old.CREDIT_NEW_TILES and v.CREDIT_CELLS==old.CREDIT_CELLS
assert v.LABEL==old.LABEL and v.REPO_URL==old.REPO_URL and v.LOGO_CREDIT==old.LOGO_CREDIT
assert {k for k in v.BLOBS if v.BLOBS[k]!=old.BLOBS[k]}=={'TITLEVER'}
assert 'Unified Overlay Menu Expansion: not included.' in v.EX_ATTRIBUTION
for edition in (v.RETAIL,v.JPRE):
 for mode,state,visible in ((1,6,True),(1,0x17,True),(1,0x11,True),(1,7,False),(4,6,False)):
  mu=Uc(UC_ARCH_X86,UC_MODE_32);mu.mem_map(0x400000,0x4000000);mu.mem_map(0x7000000,0x10000)
  origin=v.cave_va('TITLEVER',edition);code=v.link('TITLEVER',edition)
  mu.mem_write(origin,code);mu.mem_write(origin+len(code)-v.TITLEVER_LEN,v.version_text().encode()+b'\0')
  for sym,val in (('MODE',mode),('SUBMODE',state),('PRIMARY',0x12345678)):
   mu.mem_write(v.symbol_va(sym,edition),struct.pack('<I',val))
  cursor=v.symbol_va('CURSOR',edition);printer=v.symbol_va('PRINT',edition)
  for addr in (cursor,printer):mu.mem_write(addr,b'\xc3')
  stop=0x7001000;sp=0x700f000;mu.mem_write(sp,struct.pack('<I',stop));mu.reg_write(UC_X86_REG_ESP,sp)
  calls=[]
  def hook(machine,addr,size,user):
   stack=machine.reg_read(UC_X86_REG_ESP)
   if addr==cursor:calls.append(('cursor',struct.unpack('<II',machine.mem_read(stack+4,8))))
   if addr==printer:
    ptr=struct.unpack('<I',machine.mem_read(stack+4,4))[0]
    text=bytes(machine.mem_read(ptr,64)).split(b'\0')[0].decode();calls.append(('text',text))
  mu.hook_add(UC_HOOK_CODE,hook);mu.emu_start(origin,stop,count=1000)
  assert mu.reg_read(UC_X86_REG_EAX)==0x12345678 and mu.reg_read(UC_X86_REG_ESP)==sp+4
  expected=[('cursor',(79-2*len(v.version_text()),48)),('text','VO PATCH EX 0.18.1')]
  assert calls==(expected if visible else []),(edition.short,calls)
 print('PASS',edition.short,'title states, single release line, no development draw, displaced load and stack')
print('PASS exact upstream credits/resources/constants and all non-title blobs preserved')
# Resource failure behavior and Restore Original, exercised only on copies.
import tempfile
for folder in map(pathlib.Path, sys.argv[1:]):
 raw=(folder/'v_on.exe').read_bytes()
 for missing in (v.SCRSTFCG,v.SCRSTFMP):
  with tempfile.TemporaryDirectory() as td:
   t=pathlib.Path(td);(t/'v_on.exe').write_bytes(raw)
   other=v.SCRSTFMP if missing==v.SCRSTFCG else v.SCRSTFCG
   original=(folder/other).read_bytes();(t/other).write_bytes(original)
   patch=v.Patcher();assert patch.load(str(t/'v_on.exe'))[1]
   ok,log=patch.apply({'credits':True});assert not ok,log
   assert any('skipped' in line for line in log)
   assert b'VO PATCH EX 0.18.1' not in (t/'v_on.exe').read_bytes()
   assert (t/other).read_bytes()==original and not (t/(other+'.bak')).exists()
   patch.restore();assert (t/'v_on.exe').read_bytes()==raw
 print('PASS',folder.name,'each missing credit resource skips attribution; exact executable restore')
