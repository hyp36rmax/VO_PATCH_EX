"""Passive normal-game collector. Never launches or reconfigures the game."""
import argparse
import ctypes
import os
import time
from pathlib import Path
import diagnostics as d
import discovery
import movie_geometry
import runtime_checkpoint
import crash_evidence

RETURN='RETURN-THIS-VO-PATCH-EX-F01-P04-F02.zip'
STATE={'VO_EX_REQUESTED_MODE':'selected_mode','VO_EX_EFFECTIVE_MODE':'effective_mode',
       'VO_EX_PROFILE':'profile','VO_EX_PRIMARY':'primary','VO_EX_SECONDARY':'secondary',
       'VO_EX_FALLBACK':'fallback'}


def run(root, wait, ready, *, environ=None, snapshot=discovery.snapshot):
    root=Path(root);environ=os.environ if environ is None else environ
    started=time.monotonic()
    selected=d.level(root)
    if not selected:
        ready()
        return None
    marker=root/'diagnostics/session-active'
    if marker.exists():d.event(root,'previous_session_incomplete')
    level=d.LEVELS[selected]
    d.event(root,'startup',{'level':d.LEVELS.index(level)})
    marker.write_text('active\n')
    state={}
    for key,field in STATE.items():
        try:value=int(environ[key])
        except (KeyError,ValueError):continue
        if -1<=value<=65535:state[field]=value
    d.event(root,'selection',state)
    if selected>=3:d.event(root,'movie',movie_geometry.evidence(root,environ))
    if state.get('fallback'):d.event(root,'recovery',{'fallback':state['fallback']})
    for cfg in d.configurations(root,root).values():
        if 'scrsize' in cfg:
            d.event(root,'configuration',{'f4_state':cfg['scrsize']&1,'split_preference':cfg['scrsize']&2})
    try:
        info=snapshot() if selected>=2 else {'displays':[], 'controllers':[], 'available':False}
        d.event(root,'display_discovery',{'count':len(info['displays']),'ok':bool(info['available'])})
        d.event(root,'controller_discovery',{'count':len(info['controllers']),'ok':bool(info['available'])})
        for row in info['displays']:d.event(root,'display_discovery',row)
        for row in info['controllers']:d.event(root,'controller_discovery',row)
    except OSError:d.event(root,'error',{'module':5,'code':3})
    if selected>=3:d.event(root,'module_init',{'module':5,'elapsed_ms':min(60000,max(0,int((time.monotonic()-started)*1000)))})
    # Parent waits only before renderer entry; no I/O runs on game frame/input paths.
    ready()
    try:code=wait()
    except OSError:
        d.event(root,'error',{'module':5,'exit_known':False})
        raise
    d.event(root,'shutdown',{'exit_known':True,'exit_code':code})
    marker.unlink(missing_ok=True)
    return None  # exports are exclusively player initiated


def sample(root, prior=None, *, snapshot=discovery.snapshot):
    """Bounded numeric changes, only after the current consent check."""
    if d.level(root)<2:return prior
    current=(d.configurations(root,root),snapshot())
    if current!=prior:
        for cfg in current[0].values():
            for player in (1,2):
                key=f'{player}p device no.'
                if key in cfg:d.event(root,'configuration',{'player':player,'device':cfg[key]})
        hardware=current[1]
        d.event(root,'display_discovery',{'count':len(hardware['displays'])})
        d.event(root,'controller_discovery',{'count':len(hardware['controllers'])})
        for row in hardware['displays']:d.event(root,'display_discovery',row)
        for row in hardware['controllers']:d.event(root,'controller_discovery',row)
    return current


def movie_state(pid):
    """Read only class/visibility for this process; never window text or input."""
    from ctypes import wintypes as w
    user=ctypes.WinDLL('user32',use_last_error=True)
    callback=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
    user.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
    user.GetClassNameW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int]
    user.IsWindowVisible.argtypes=[w.HWND];user.IsWindowVisible.restype=w.BOOL
    user.EnumWindows.argtypes=[callback,w.LPARAM]
    user.EnumChildWindows.argtypes=[w.HWND,callback,w.LPARAM]
    user.GetWindowRect.argtypes=[w.HWND,ctypes.POINTER(w.RECT)];user.GetWindowRect.restype=w.BOOL
    found=set();visible=set();seen=set();bounds=[];process_window_visible=[False]
    def visit(hwnd,unused):
        if hwnd in seen:return True
        if len(seen)>=256:return False
        seen.add(hwnd)
        owner=w.DWORD();user.GetWindowThreadProcessId(hwnd,ctypes.byref(owner))
        if owner.value!=pid:return True
        name=ctypes.create_unicode_buffer(128)
        if user.GetClassNameW(hwnd,name,128) and name.value in ('AVIWnd32','MCIAVI','AVI Window','MCIWndClass','VideoRenderer'):
            found.add(hwnd)
            if user.IsWindowVisible(hwnd):
                visible.add(hwnd)
                rect=w.RECT()
                if user.GetWindowRect(hwnd,ctypes.byref(rect)) and len(bounds)<4:
                    bounds.append((rect.left,rect.top,rect.right-rect.left,rect.bottom-rect.top))
        return True
    child=callback(visit)
    def top(hwnd,unused):
        visit(hwnd,unused)
        owner=w.DWORD();user.GetWindowThreadProcessId(hwnd,ctypes.byref(owner))
        if owner.value==pid:
            if user.IsWindowVisible(hwnd):process_window_visible[0]=True
            user.EnumChildWindows(hwnd,child,0)
        return True
    if not user.EnumWindows(callback(top),0):raise ctypes.WinError(ctypes.get_last_error())
    return len(found),len(visible),tuple(sorted(bounds)),process_window_visible[0]


def attach(root,pid,event_name):
    from ctypes import wintypes as w
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
    k.OpenEventW.argtypes=[w.DWORD,w.BOOL,w.LPCWSTR];k.OpenEventW.restype=w.HANDLE
    k.SetEvent.argtypes=[w.HANDLE];k.SetEvent.restype=w.BOOL
    k.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD];k.WaitForSingleObject.restype=w.DWORD
    k.GetExitCodeProcess.argtypes=[w.HANDLE,ctypes.POINTER(w.DWORD)];k.GetExitCodeProcess.restype=w.BOOL
    k.CloseHandle.argtypes=[w.HANDLE]
    if pid<=0 or not event_name.startswith('Local\\VOEX-'):raise ValueError('invalid lifecycle attachment')
    process=k.OpenProcess(0x100000|0x1000,False,pid)
    if not process:raise ctypes.WinError(ctypes.get_last_error())
    event=None
    try:
        event=k.OpenEventW(2,False,event_name)
        if not event:raise ctypes.WinError(ctypes.get_last_error())
        def ready():
            if not k.SetEvent(event):raise ctypes.WinError(ctypes.get_last_error())
        def wait():
            previous=None;probe_failed=False;prior=None;ticks=0
            geometry=None
            checkpoints=None
            session_ms=int(time.time()*1000)
            if d.level(root)==3:
                try:mode=int(os.environ.get("VO_EX_EFFECTIVE_MODE", "-1"))
                except ValueError:mode=-1
                checkpoints=runtime_checkpoint.Checkpoints(root,pid,mode)
            while True:
                result=k.WaitForSingleObject(process,500)
                if result==0:break
                if result!=258:raise ctypes.WinError(ctypes.get_last_error())
                selected=d.level(root)
                if not selected:return 0
                ticks+=1
                if selected>=2 and ticks%4==0:
                    try:prior=sample(root,prior)
                    except OSError:d.event(root,'error',{'module':5,'code':3})
                if selected<3:continue
                if checkpoints is None:
                    try:mode=int(os.environ.get("VO_EX_EFFECTIVE_MODE", "-1"))
                    except ValueError:mode=-1
                    checkpoints=runtime_checkpoint.Checkpoints(root,pid,mode)
                if geometry is None:geometry=movie_geometry.evidence(root,os.environ)
                try:
                    current=movie_state(pid)
                    checkpoints.windows(current[0],current[1],current[3])
                    if current!=previous:
                        d.event(root,'movie',{'count':current[0],'visible':current[1],
                                             'event':1 if current[1] and (not previous or not previous[1]) else 3 if previous and previous[1] and not current[1] else 2})
                        for i,(x,y,width,height) in enumerate(current[2]):
                            d.event(root,'movie',{'window_index':i,'window_x':x,'window_y':y,'window_width':width,'window_height':height,
                                                 'geometry_match':not geometry['geometry_fallback'] and (x,y,width,height)==tuple(geometry[k] for k in ('expected_x','expected_y','expected_width','expected_height'))})
                        previous=current
                except OSError as error:
                    try:checkpoints.update(checkpoints.row['state'],error_code=getattr(error,'winerror',0) or 0)
                    except OSError:pass  # a failed checkpoint must not affect the game
                    if not probe_failed:d.event(root,'error',{'module':4,'code':1})
                    probe_failed=True
            if previous and previous[0]:d.event(root,'movie',{'count':0,'visible':0,'event':3})
            code=w.DWORD()
            if not k.GetExitCodeProcess(process,ctypes.byref(code)):raise ctypes.WinError(ctypes.get_last_error())
            if checkpoints and d.level(root)==3:
                checkpoints.exited(code.value)
                evidence=crash_evidence.collect(pid,session_ms)
                if evidence:checkpoints.exited(code.value,evidence)
            return code.value
        return run(root,wait,ready)
    finally:
        if event:k.CloseHandle(event)
        k.CloseHandle(process)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('game',type=Path)
    p.add_argument('--pid',type=int);p.add_argument('--ready');p.add_argument('--export',action='store_true')
    a=p.parse_args()
    if a.export:
        try:
            result=d.export(a.game,game_directory=a.game,return_name=RETURN)
            if os.name=='nt':
                import subprocess
                subprocess.Popen(['explorer.exe','/select,',str(result.resolve())])
        except Exception as error:
            if os.name=='nt':
                ctypes.windll.user32.MessageBoxW(None,
                    'No diagnostic records are available.' if isinstance(error,ValueError)
                    else 'Export failed. Existing diagnostic records have been preserved.',
                    'VO PATCH EX Diagnostics',0x40)
            else:raise
    elif a.pid and a.ready:attach(a.game,a.pid,a.ready)
    else:p.error('normal lifecycle attachment or export required')
