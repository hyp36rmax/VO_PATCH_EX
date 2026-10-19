"""Assemble local-only controlled movie installations from verified player files.

Never upload the output: it contains original game assets. Both builds use the
same B01 patcher and recipes. Native provenance and recovery hashes follow the
selected DLLs; all other installed runtime bytes must match.
"""
import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('package','game','gcc','llvm','output'): p.add_argument(name,type=Path)
    p.add_argument('--bosses',action='store_true',help='Enable bosses identically in both installations')
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    package=a.package.resolve();here=Path(__file__).resolve().parent
    sys.dont_write_bytecode=True
    sys.path.insert(0,str(package/'_internal'))
    spec=importlib.util.spec_from_file_location('movie_ab_patcher',package/'_internal/v-on-patcher.py')
    v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    raw=(a.game/'v_on.exe').read_bytes()
    assert hashlib.md5(raw).hexdigest() in v.BUILDS,'Verified pristine game required'
    assert (a.game/'von.avi').is_file(),'Original intro movie required'
    # Apply once, then copy a complete independent installation, never hardlinks.
    first=a.output/'A-GCC-MSVCRT';shutil.copytree(a.game,first)
    patcher=v.Patcher();assert patcher.load(str(first/'v_on.exe'))[1]
    wanted=v.default_state();wanted.update(bosses=a.bosses,bossunlock=False,movie=True)
    ok,logs=patcher.apply(wanted);assert ok,logs
    for name in ('normal_lifecycle.py','diagnostics.py','runtime_checkpoint.py','crash_evidence.py'):
        shutil.copy2(here/name,first/'experience-runtime'/name)
    (first/'player-displays.ini').write_text('[Presentation]\nMode=0\nGameAspect=1\n[Diagnostics]\nLevel=OFF\n')
    # Explicit UAT opt-in; default installation stays Off.
    (first/'ENABLE-DEVELOPMENT.cmd').write_text('@echo off\r\ncd /d "%~dp0"\r\n"experience-runtime\\python.exe" "experience-runtime\\movie_uat.py" enable\r\npause\r\n')
    (first/'DISABLE-DEVELOPMENT.cmd').write_text('@echo off\r\ncd /d "%~dp0"\r\n"experience-runtime\\python.exe" "experience-runtime\\movie_uat.py" disable\r\npause\r\n')
    shutil.copy2(here/'movie_uat.py',first/'experience-runtime/movie_uat.py')
    second=a.output/'B-LLVM-UCRT';shutil.copytree(first,second)
    inventories={}
    for root,native in ((first,a.gcc),(second,a.llvm)):
        for name in ('ddraw.dll','vodisplay.dll'):shutil.copy2(native/name,root/name)
        meta=json.loads((root/'experience-version.json').read_text())
        meta.update(wrapper_sha256=sha(root/'ddraw.dll'),helper_sha256=sha(root/'vodisplay.dll'))
        (root/'experience-version.json').write_text(json.dumps(meta,indent=2)+'\n')
        # Keep Restore correct after diagnostic additions and native selection.
        journal=root/'.vo-ex-backup/ownership.json';ownership=json.loads(journal.read_text())
        for row in ownership['files']:
            file=root/row['name']
            if file.is_file():row['installed']=sha(file)
        journal.write_text(json.dumps(ownership,indent=2)+'\n')
        inventories[root.name]={f.relative_to(root).as_posix():sha(f) for f in root.rglob('*') if f.is_file()}
        (a.output/(root.name+'-SHA256.json')).write_text(json.dumps(inventories[root.name],indent=2)+'\n')
    left,right=inventories.values();assert left.keys()==right.keys()
    changed={n:{'A':left[n],'B':right[n]} for n in left if left[n]!=right[n]}
    assert set(changed)=={'ddraw.dll','vodisplay.dll','experience-version.json','.vo-ex-backup/ownership.json'},changed
    (a.output/'comparison.json').write_text(json.dumps({'expected_native':['ddraw.dll','vodisplay.dll'],
        'derived_native_hash_metadata':['experience-version.json','.vo-ex-backup/ownership.json'],
        'unexpected':[], 'files':changed,'options':wanted},indent=2)+'\n')
    print('PASS two complete independent installations; only native DLLs and their required integrity/recovery hash metadata differ')

if __name__=='__main__':main()
