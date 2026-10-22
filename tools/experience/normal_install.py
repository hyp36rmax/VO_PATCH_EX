"""Private distribution adapter around the unchanged upstream Apply/Restore UI.

Only the packaged copy binds this adapter. Offline recipes are verified against
both the pristine executable and the exact output of upstream Apply. No assembler
or developer runtime is used on the player's machine.
"""
import hashlib,json,os,tempfile
from pathlib import Path
from compact_catalog import Catalog
from release_version import build_identity

JOURNAL='.vo-ex-backup'
def sha(data):return hashlib.sha256(data).hexdigest()
def atomic(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.vo-ex-',suffix='.new',dir=path.parent)
    temp=Path(name)
    try:
        with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(temp,path)
    finally:
        if temp.exists():temp.unlink()

def safe(root,name):
    p=Path(name)
    if p.is_absolute() or '..' in p.parts or not p.parts:raise ValueError('Unsafe owned path')
    target=root/p
    if target.is_symlink() or any(x.is_symlink() for x in target.parents if x!=root.parent):raise ValueError('Symbolic link in installation path')
    return target

def bind(cls,scope,package):
    package=Path(package);original_apply=cls.apply;original_restore=cls.restore
    index=json.loads((package/'catalog/catalog.json').read_text())
    payload=json.loads((package/'payload-manifest.json').read_text())
    def recipe(edition,mask):
        name=f'{edition}/{mask}.json'
        data=Catalog(package/'catalog', index).read(name)
        if sha(data)!=index['entries'][name]['sha256']:raise ValueError('Patch data integrity failure')
        return json.loads(data)
    def mask_for(wanted):return sum(1<<i for i,k in enumerate(index['keys']) if wanted.get(k))
    def restore_extra(root):
        journal=root/JOURNAL
        if not journal.exists():return []
        manifest=json.loads((journal/'ownership.json').read_text());logs=[];remaining=[]
        for row in manifest['files']:
            name=row['name'];target=safe(root,name)
            if name not in payload['files'] and name not in ('experience-version.json','vontanita.dll'):
                raise ValueError('Unrecognized ownership record')
            if row['before'] is not None:
                backup=journal/row['backup']
                if backup.parent!=journal or sha(backup.read_bytes())!=row['before']:raise ValueError('Recovery backup integrity failure')
            if target.exists() and sha(target.read_bytes()) not in (row['installed'],row['before']):
                logs.append('restore: preserved modified '+name);remaining.append(row);continue
            if row['before'] is None:
                if target.exists():target.unlink()
            else:atomic(target,(journal/row['backup']).read_bytes())
            logs.append('restore: Experience '+name)
        if not remaining:
            # Delete only indexed backup files and our journal. Keep unknown files.
            for row in manifest['files']:
                if row['before'] is not None:(journal/row['backup']).unlink(missing_ok=True)
            (journal/'ownership.json').unlink()
            try:journal.rmdir()
            except OSError:logs.append('restore: retained unrelated files in '+JOURNAL)
        for name in sorted(payload['files'],reverse=True):
            p=safe(root,name).parent
            while p!=root:
                try:p.rmdir()
                except OSError:break
                p=p.parent
        return logs
    def apply(self,wanted):
        root=Path(self.exe_path).resolve().parent
        if (root/JOURNAL).exists():return False,['Experience: use Restore Original before applying again.']
        before={};journal=root/JOURNAL
        try:
            raw=Path(self.exe_path).read_bytes();mask=mask_for(wanted);r=recipe(self.build.short,mask)
            if sha(raw)!=r['original']:return False,['Experience: verified original game required. Use Restore Original first.']
            assets={}
            for name,digest in payload['files'].items():
                data=safe(package/'payload',name).read_bytes()
                if sha(data)!=digest:raise ValueError('Runtime integrity failure: '+name)
                assets[name]=data
            # Snapshot every file the original Apply can change, including backups.
            names={Path(self.exe_path).name,self.build.art[0],scope['SCRSTFCG'],scope['SCRSTFMP'],'v_on.ini','vontanita.dll',scope['BOSSES_FILE']}
            names|={n+s for n in tuple(names) for s in ('.bak','.new','.patched')}
            names|=set(assets)|{'experience-version.json'}
            for name in names:
                path=safe(root,name)
                if path.exists() and not path.is_file():raise ValueError('Installation path is not a file: '+name)
                before[name]=path.read_bytes() if path.exists() else None
            ok,logs=original_apply(self,wanted)
            if not ok:
                # Upstream can stage a helper before a later failure; restore the
                # exact pre-Apply state for this failed integrated transaction.
                raise RuntimeError('\n'.join(logs))
            patched=Path(self.exe_path).read_bytes()
            if sha(patched)!=r['base'] and wanted.get('credits'):
                # Preserve upstream's permitted missing-credit-assets skip.
                r=recipe(self.build.short,mask & ~(1<<index['keys'].index('credits')))
            if sha(patched)!=r['base']:raise ValueError('Upstream output does not match selected patch data')
            result=bytearray(patched[:r['size']]);result.extend(bytes(r['size']-len(result)))
            end=0
            for off,data in r['writes']:
                block=bytes.fromhex(data)
                if off<end or off+len(block)>len(result):raise ValueError('Invalid patch data range')
                result[off:off+len(block)]=block;end=off+len(block)
            if sha(result)!=r['final']:raise ValueError('Generated image integrity failure')
            identity=build_identity(payload['version']['revision'],payload['version']['kind'],payload['version'].get('rc'))
            if any(payload['version'].get(k)!=value for k,value in identity.items()):raise ValueError('Build identity mismatch')
            if r['mask'] & (1<<index['keys'].index('credits')):
                scope['stamp_build_identity'](result,identity['subtitle'],self.build)
            version=dict(payload['version'],game=self.build.short,image_sha256=sha(result),movie_framing=bool(wanted.get('movie')))
            assets['experience-version.json']=(json.dumps(version,indent=2)+'\n').encode()
            # Existing controller helper is owned too: restore/remove exactly what
            # upstream Apply installed, while keeping upstream's game .bak files.
            helper=root/'vontanita.dll'
            if helper.is_file():assets['vontanita.dll']=helper.read_bytes()
            journal.mkdir();owned=[]
            for i,(name,data) in enumerate(assets.items()):
                prior=before.get(name);backup=f'{i}.bin'
                if prior is not None:atomic(journal/backup,prior)
                owned.append({'name':name,'before':sha(prior) if prior is not None else None,'backup':backup,'installed':sha(data)})
            atomic(journal/'ownership.json',json.dumps({'files':owned},indent=2).encode())
            for name,data in assets.items():atomic(safe(root,name),data)
            atomic(Path(self.exe_path),result)
            return True,logs+['Experience: Display settings and diagnostics installed. Launch v_on.exe normally.']
        except Exception as exc:
            failures=[]
            for name,data in before.items():
                try:
                    path=safe(root,name)
                    if data is None:path.unlink(missing_ok=True)
                    elif not path.exists() or path.read_bytes()!=data:atomic(path,data)
                except OSError:failures.append(name)
            # Journal is ours from this call; never recurse over unknown content.
            if journal.is_dir() and before and not failures:
                for p in journal.iterdir():
                    if p.is_file() and (p.name=='ownership.json' or p.name[:-4].isdigit() and p.suffix=='.bin'):p.unlink()
                try:journal.rmdir()
                except OSError:pass
            return False,['Experience: '+str(exc)]+(['Recovery required for: '+', '.join(failures)] if failures else ['No integrated changes applied.'])
    def restore(self):
        root=Path(self.exe_path).resolve().parent
        journal=root/JOURNAL
        try:
            if journal.exists():
                manifest=json.loads((journal/'ownership.json').read_text())
                for row in manifest['files']:
                    safe(root,row['name'])
                    if row['name'] not in payload['files'] and row['name'] not in ('experience-version.json','vontanita.dll'):raise ValueError('Unrecognized ownership record')
                    if row['before'] is not None:
                        backup=journal/row['backup']
                        if backup.parent!=journal or sha(backup.read_bytes())!=row['before']:raise ValueError('Recovery backup integrity failure')
        except (OSError,ValueError,KeyError) as exc:return ['Experience restore: '+str(exc)]
        logs=original_restore(self)
        try:
            exe=Path(self.exe_path);backup=exe.with_name(exe.name+'.bak')
            if journal.exists() and (not backup.is_file() or exe.read_bytes()!=backup.read_bytes()):
                return logs+['Experience: runtime retained because the game executable was not restored.']
            return logs+restore_extra(root)
        except (OSError,ValueError,KeyError) as exc:return logs+['Experience restore: '+str(exc)]
    cls.apply=apply;cls.restore=restore
