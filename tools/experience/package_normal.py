"""Assemble the installable private distribution using upstream's Windows launcher."""
import argparse,hashlib,json,os,shutil,subprocess
from release_version import VERSION as RELEASE_VERSION, validate_release_tag
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('baseline',type=Path);p.add_argument('catalog',type=Path);p.add_argument('wrapper',type=Path);p.add_argument('helper',type=Path);a=p.parse_args()
 validate_release_tag(os.environ.get('GITHUB_REF_NAME', '') if os.environ.get('GITHUB_REF_TYPE') == 'tag' else '')
 out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 shutil.copy2(a.baseline/'v-on-patcher.exe',out/'v-on-patcher.exe')
 shutil.copytree(a.baseline/'_internal',out/'_internal',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 internal=out/'_internal'
 # Tcl's nmake directory is build tooling, not the shipped Tk runtime.
 shutil.rmtree(internal/'tcl/nmake',ignore_errors=True)
 experience=internal/'experience';experience.mkdir()
 shutil.copytree(a.catalog,experience/'catalog',ignore=shutil.ignore_patterns('*.log'))
 # The original UI/source is used verbatim except for binding Apply/Restore's
 # private distribution adapter before main. No second installer or game launcher.
 source=(ROOT/'v-on-patcher.py').read_text();needle="if __name__ == '__main__':"
 assert source.count(needle)==1
 adapter="from release_version import VERSION as _release_version, configure as _configure_version\n_configure_version(globals())\nif __name__ == '__main__' and '--version' in __import__('sys').argv[1:]:\n    print(_release_version)\n    raise SystemExit(0)\nfrom normal_install import bind as _experience_bind\n_experience_bind(Patcher, globals(), os.path.join(os.path.dirname(__file__), 'experience'))\n\n"
 (internal/'v-on-patcher.py').write_text(source.replace(needle,adapter+needle))
 shutil.copy2(HERE/'normal_install.py',internal/'normal_install.py')
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
 for name in ('normal_lifecycle.py','diagnostics.py','discovery.py','movie_geometry.py','runtime_checkpoint.py','crash_evidence.py'):shutil.copy2(HERE/name,runtime/name)
 shutil.copy2(HERE/'EXPORT-DIAGNOSTICS.cmd',payload/'EXPORT-DIAGNOSTICS.cmd')
 # Package the notices for the exact dependencies selected by the build.
 assert '__version__ = "2026.07.22"' in (internal/'Lib/site-packages/certifi/__init__.py').read_text()
 version={'release':RELEASE_VERSION,'revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'wrapper_sha256':sha(payload/'ddraw.dll'),'helper_sha256':sha(payload/'vodisplay.dll'),'experience':'Experience-private','display':'F01-P04'}
 manifest={'version':version,'files':{f.relative_to(payload).as_posix().replace('\\','/'):sha(f) for f in sorted(payload.rglob('*')) if f.is_file()}}
 (experience/'payload-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 notices=out/'Licenses';notices.mkdir();shutil.copy2(ROOT/'LICENSE',notices/'Pairomaniac-MIT.txt');shutil.copy2(a.wrapper/'LICENSE',notices/'cnc-ddraw-MIT.txt');shutil.copy2(internal/'LICENSE.txt',notices/'Python.txt')
 shutil.copy2(HERE/'ci/licenses/certifi-LICENSE.txt',notices/'certifi-LICENSE.txt')
 shutil.copy2(a.wrapper/'MinGW-runtime.txt',notices/'MinGW-runtime.txt')
 (notices/'Playable-Bosses.txt').write_text('Playable Bosses by Vortyne, from Pairomaniac\'s V-On Patcher.\nVO PATCH EX integration and expansions by hyp36rmax.\nUpstream source: https://github.com/pairomaniac/v-on-patcher\nPinned commit: 4ecae6237e1fc432c0be2f2b0aeab5303120e444\nBoss portraits are pixel art after SEGA renders of SEGA characters.\nThe MIT license covers patcher code, not SEGA characters, game assets or trademarks.\n')
 (out/'READ-ME.txt').write_text('VO PATCH EX ' + RELEASE_VERSION + ''' — PRIVATE WINDOWS UAT

Use your original Virtual-On disc image/files with the supplied v-on-patcher.exe.
If the game is already patched, use Restore Original before Apply.
Use the existing ISO/file selection and patch options; click Apply as usual.
B01 adds optional Playable bosses (off by default) and Pre-unlock the bosses.
Pre-unlock requires Playable bosses. Jaguarandi and Z-Gradt are single-player
only. Z-Gradt's laser uses Dash/turbo. Unlocks in bosses.bin survive Restore.
This private candidate requires Windows gameplay acceptance; it is not a release.
Launch the installed v_on.exe normally. No special game launcher is required.

F5 Graphic Settings -> Display... selects Single, Dual Versus or Dual Mirror,
monitors and aspect ratio. OK saves for next launch; Cancel discards changes.
A fresh default installation uses 16:9 Single Display. Explicitly unchecking
high resolution starts from Original 4:3 until a saved Display choice overrides it.
Dual mode retains high resolution when F4 requests an unsupported transition.
Mirror includes both Local VS views; Versus separates the player views.

Diagnostics are Off by default. F11 Extras selects Off/Normal/Detailed/Development.
Restart after enabling. Off stops new collection; existing logs are retained.
F11 Export Diagnostics... or EXPORT-DIAGNOSTICS.cmd exports only on request.
The local return ZIP is RETURN-THIS-VO-PATCH-EX-F01-P04-F02.zip. No uploads occur.
If no logs exist, enable a level, restart and reproduce before exporting.
Restore Original restores upstream files and owned runtime files. Display choices,
diagnostic logs and unrelated files are retained. Modified runtime files are
preserved and reported instead of deleted.

Boss acceptance: verify both optional boxes and their dependency. Test the
original eight machines with bosses disabled, then Jaguarandi and Z-Gradt with
bosses enabled. Test earned unlocks separately from pre-unlock; restart and
Restore/reapply must retain progression. Check each lever's Dash/turbo edge for
Z-Gradt's laser, movement, weapons, replay, victory/defeat and ending. Repeat
camera and portrait checks at each supported aspect ratio and in both dual
presentation modes, including mixed monitor sizes. Local VS/online retain eight
machines; this candidate does not add Local VS bosses.

Movie check: use the default enabled movie patch. In Single, confirm a centered
16:9 visible picture without distortion. In Dual Versus and Dual Mirror, confirm
Display 1 shows the movie and Display 2 stays black. Let it finish once and skip
it once; confirm normal presentation returns. Include different monitor sizes.

Physical UAT is pending. Check normal launch, F5 OK/Cancel, restart activation,
missing-monitor fallback, F4, F7/controllers, saved split, all three display modes,
mixed monitor sizes, movies, exit/cleanup, export, and Restore Original.
This package contains patch data and redistributables, not game executables/assets.
No administrator privileges, manual INI edits or compilation are required.
''')
 files={f.relative_to(out).as_posix():sha(f) for f in sorted(out.rglob('*')) if f.is_file()}
 (out/'PACKAGE-SHA256.json').write_text(json.dumps(files,indent=2)+'\n')
 print(out)
if __name__=='__main__':main()
