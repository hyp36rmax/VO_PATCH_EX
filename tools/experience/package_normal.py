"""Assemble the installable distribution using upstream's Windows launcher."""
import argparse,hashlib,json,os,shutil,subprocess
from release_version import VERSION as RELEASE_VERSION, validate_release_tag, build_identity
from pathlib import Path
from compact_catalog import pack, NAME
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('baseline',type=Path);p.add_argument('catalog',type=Path);p.add_argument('wrapper',type=Path);p.add_argument('helper',type=Path);p.add_argument('--build-kind',choices=('release','prerelease','rc','development'),default='prerelease');p.add_argument('--rc',type=int);a=p.parse_args()
 validate_release_tag(os.environ.get('GITHUB_REF_NAME', '') if os.environ.get('GITHUB_REF_TYPE') == 'tag' else '')
 if subprocess.run(['git','diff','--quiet','HEAD','--'],cwd=ROOT).returncode:
  raise ValueError('Commit tracked source changes before building an identified package')
 out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 shutil.copy2(a.baseline/'v-on-patcher.exe',out/'v-on-patcher.exe')
 shutil.copytree(a.baseline/'_internal',out/'_internal',ignore=shutil.ignore_patterns('__pycache__','*.pyc','_ctypes_test.pyd'))
 internal=out/'_internal'
 # Tcl's nmake directory is build tooling, not the shipped Tk runtime.
 shutil.rmtree(internal/'tcl/nmake',ignore_errors=True)
 experience=internal/'experience';experience.mkdir()
 # The profile header is compiled into the wrapper, never read at runtime.
 (experience/'catalog').mkdir()
 shutil.copy2(a.catalog/'catalog.json',experience/'catalog/catalog.json')
 pack(a.catalog, experience/'catalog'/NAME)
 # The original UI/source is used verbatim except for binding Apply/Restore's
 # private distribution adapter before main. No second installer or game launcher.
 source=(ROOT/'v-on-patcher.py').read_text();needle="if __name__ == '__main__':"
 assert source.count(needle)==1
 adapter="from release_version import VERSION as _release_version, configure as _configure_version\n_configure_version(globals())\nif __name__ == '__main__' and '--version' in __import__('sys').argv[1:]:\n    print(_release_version)\n    raise SystemExit(0)\nfrom normal_install import bind as _experience_bind\n_experience_bind(Patcher, globals(), os.path.join(os.path.dirname(__file__), 'experience'))\n\n"
 (internal/'v-on-patcher.py').write_text(source.replace(needle,adapter+needle))
 shutil.copy2(HERE/'normal_install.py',internal/'normal_install.py')
 shutil.copy2(HERE/'compact_catalog.py',internal/'compact_catalog.py')
 shutil.copy2(HERE/'release_version.py',internal/'release_version.py')
 payload=experience/'payload';payload.mkdir()
 shutil.copy2(a.helper,payload/'vodisplay.dll');shutil.copy2(a.wrapper/'ddraw.dll',payload/'ddraw.dll')
 shutil.copy2(ROOT/'input/vontanita.dll',internal/'input/vontanita.dll')
 ini=HERE/'ci/ddraw.ini'
 shutil.copy2(ini,payload/'ddraw.ini')
 runtime=payload/'experience-runtime';runtime.mkdir()
 for name in ('pythonw.exe','python312.dll','python3.dll','python312.zip','vcruntime140.dll','vcruntime140_1.dll','LICENSE.txt'):
  shutil.copy2(internal/name,runtime/name)
 shutil.copytree(internal/'DLLs',runtime/'DLLs')
 (runtime/'python312._pth').write_text('python312.zip\n.\nDLLs\n')
 for name in ('normal_lifecycle.py','diagnostics.py','discovery.py','movie_geometry.py'):shutil.copy2(HERE/name,runtime/name)
 shutil.copy2(HERE/'EXPORT-DIAGNOSTICS.cmd',payload/'EXPORT-DIAGNOSTICS.cmd')
 # Package the notices for the exact dependencies selected by the build.
 assert '__version__ = "2026.07.22"' in (internal/'Lib/site-packages/certifi/__init__.py').read_text()
 identity=build_identity(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),a.build_kind,a.rc)
 version=dict(identity, **{'wrapper_sha256':sha(payload/'ddraw.dll'),'helper_sha256':sha(payload/'vodisplay.dll'),'experience':'Experience'})
 manifest={'version':version,'files':{f.relative_to(payload).as_posix().replace('\\','/'):sha(f) for f in sorted(payload.rglob('*')) if f.is_file()}}
 (experience/'payload-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 notices=out/'Licenses';notices.mkdir();shutil.copy2(ROOT/'LICENSE',notices/'Pairomaniac-MIT.txt');shutil.copy2(a.wrapper/'LICENSE',notices/'cnc-ddraw-MIT.txt');shutil.copy2(internal/'LICENSE.txt',notices/'Python.txt')
 shutil.copy2(HERE/'ci/licenses/certifi-LICENSE.txt',notices/'certifi-LICENSE.txt')
 shutil.copy2(a.wrapper/'MinGW-runtime.txt',notices/'MinGW-runtime.txt')
 (notices/'Playable-Bosses.txt').write_text('Playable Bosses by Vortyne, from Pairomaniac\'s V-On Patcher.\nVO PATCH EX integration and expansions by hyp36rmax.\nUpstream source: https://github.com/pairomaniac/v-on-patcher\nPinned commit: 2c36b5ebe2bc879bc9c87baaaabf7aed4adfa4a0\nBoss portraits are pixel art after SEGA renders of SEGA characters.\nThe MIT license covers patcher code, not SEGA characters, game assets or trademarks.\n')
 (out/'READ-ME.txt').write_text((ROOT/'docs/releases'/(RELEASE_VERSION + '.md')).read_text())

 files={f.relative_to(out).as_posix():sha(f) for f in sorted(out.rglob('*')) if f.is_file()}
 (out/'PACKAGE-SHA256.json').write_text(json.dumps(files,indent=2)+'\n')
 print(out)
if __name__=='__main__':main()
