#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <wchar.h>
#include "layout.h"
typedef int BOOL;typedef int32_t HRESULT;typedef unsigned UINT;typedef uint32_t DWORD;
typedef wchar_t WCHAR;typedef void *HWND;typedef void *HANDLE;typedef uintptr_t WPARAM;typedef intptr_t LPARAM;typedef intptr_t LRESULT;
typedef void IDirect3DSwapChain9;typedef void IDirect3DSurface9;typedef void IDirect3DStateBlock9;typedef void IDirect3DBaseTexture9;
typedef struct {float x,y,z,rhw,u,v;} CUSTOMVERTEX;
typedef struct {int Windowed,SwapEffect,BackBufferCount,BackBufferWidth,BackBufferHeight,BackBufferFormat,PresentationInterval;HWND hDeviceWindow;} D3DPRESENT_PARAMETERS;
typedef struct {DWORD x,y,w,h;float minz,maxz;} D3DVIEWPORT9;
typedef struct {LRESULT (*lpfnWndProc)(HWND,UINT,WPARAM,LPARAM);void *hInstance;const char *lpszClassName;} WNDCLASSA;
typedef struct {int unused;} MSG;
typedef struct {long left,top,right,bottom;} RECT;
#define GW_OWNER 4
#define GA_ROOT 2
#define GWL_STYLE -16
#define WS_CHILD 0x40000000
#define CALLBACK
#define TRUE 1
#define FALSE 0
#define FAILED(x) ((x)<0)
#define SUCCEEDED(x) ((x)>=0)
#define E_FAIL ((HRESULT)-1)
#define MAX_PATH 260
#define INFINITE UINT32_MAX
#define WAIT_TIMEOUT 258
#define WM_CLOSE 16
#define WM_DISPLAYCHANGE 126
#define WM_MOUSEACTIVATE 33
#define MA_NOACTIVATEANDEAT 4
#define HWND_TOP ((HWND)0)
#define HWND_TOPMOST ((HWND)(intptr_t)-1)
#define SWP_NOMOVE 1
#define SWP_NOSIZE 2
#define SWP_NOACTIVATE 4
#define SWP_SHOWWINDOW 8
#define SW_HIDE 0
#define PM_REMOVE 1
#define WS_EX_NOACTIVATE 1
#define WS_EX_TOOLWINDOW 2
#define WS_POPUP 1
#define ERROR_CLASS_ALREADY_EXISTS 1410
#define D3DSWAPEFFECT_DISCARD 1
#define D3DFMT_UNKNOWN 0
#define D3DPRESENT_INTERVAL_IMMEDIATE 0
#define D3DBACKBUFFER_TYPE_MONO 0
#define D3DSBT_ALL 0
#define D3DSAMP_MINFILTER 0
#define D3DSAMP_MAGFILTER 1
#define D3DTEXF_POINT 1
#define D3DCLEAR_TARGET 1
#define D3DPT_TRIANGLESTRIP 1
#define min(a,b) ((a)<(b)?(a):(b))
static struct {int cs,width,height,bpp;HWND hwnd;struct {int run;}render;} g_ddraw;
static struct {D3DPRESENT_PARAMETERS params;int tex_width,tex_height;void *device,*surface_tex[2],*vertex_buf;} g_d3d9 = {.device=(void*)1};
static VoMonitor monitors[VO_MAX_MONITORS];static WCHAR config[MAX_PATH];static unsigned count;
static struct {int movie_present,movie_visible,movie_wrong_pid,movie_wrong_parent,movie_wrong_owner,movie_wrong_class,movie_bad_bounds,movie_nochild,movie_duplicate,movie_hide_fail,movie_restore_fail,movie_capped;int window_visible[2];int clears;unsigned clear_color;int calls,fail_at,live,draws,presents,restores,streams,destroyed,foreground,enabled,closed;int minimized,p1_topmost,p1_above,position_calls[2],original_moves;HWND windows[2];void *bound,*texture[16];CUSTOMVERTEX vertices[16][4];} fake;
static HRESULT api(void){return ++fake.calls==fake.fail_at?E_FAIL:0;}
static HRESULT acquire(void **out){HRESULT h=api();if(SUCCEEDED(h)){*out=(void*)(uintptr_t)(100+ ++fake.live);}return h;}
static int release(void *p){(void)p;--fake.live;return 0;}
static int discover(void){return 1;}
static void load_id(const WCHAR *key,char *id){(void)key;id[0]=0;}
#define DefWindowProcA(...) 0
#define EnterCriticalSection(...) ((void)0)
#define LeaveCriticalSection(...) ((void)0)
#define IDirect3DStateBlock9_Release(p) release(p)
#define IDirect3DSurface9_Release(p) release(p)
#define IDirect3DSwapChain9_Release(p) release(p)
static BOOL real_SetWindowPos(HWND h,HWND after,int x,int y,int w,int height,int flags){
    (void)x;(void)y;(void)w;(void)height;
    if(h==g_ddraw.hwnd){++fake.original_moves;return FALSE;}
    int i=h==fake.windows[0]?0:1;
    ++fake.position_calls[i];
    if(i==0 && fake.movie_restore_fail)return FALSE;
    if(flags&SWP_SHOWWINDOW)fake.window_visible[i]=1;
    if(!(flags&SWP_NOACTIVATE))fake.foreground=(int)(uintptr_t)h;
    if(i==0 && after==HWND_TOPMOST){fake.p1_topmost=1;fake.p1_above=1;}
    return TRUE;
}
static BOOL EnumWindows(BOOL (*callback)(HWND,LPARAM),LPARAM value){
    HWND first=fake.p1_above?fake.windows[0]:g_ddraw.hwnd;
    HWND second=fake.p1_above?g_ddraw.hwnd:fake.windows[0];
    if(callback(first,value))callback(second,value);
    return TRUE;
}
static BOOL IsWindow(HWND h){return h==(HWND)1000||h==(HWND)1001?fake.movie_present:h!=NULL;}
static BOOL IsWindowVisible(HWND h){if(h==fake.windows[0])return fake.window_visible[0];if(h==fake.windows[1])return fake.window_visible[1];if(h==(HWND)1000||h==(HWND)1001)return fake.movie_present&&fake.movie_visible;return h==g_ddraw.hwnd;}
static void ShowWindow(HWND h,int state){(void)state;if(h==fake.windows[0]){if(!fake.movie_hide_fail)fake.window_visible[0]=0;}else if(h==fake.windows[1])fake.window_visible[1]=0;}
static DWORD GetCurrentProcessId(void){return 123;}
static DWORD GetWindowThreadProcessId(HWND h,DWORD *pid){*pid=((h==(HWND)1000||h==(HWND)1001)&&fake.movie_wrong_pid)?456:123;return 1;}
static int GetClassNameA(HWND h,char *name,int size){(void)h;(void)size;strcpy(name,fake.movie_wrong_class?"Other":"AVIWnd32");return (int)strlen(name);}
static HWND GetParent(HWND h){(void)h;return fake.movie_wrong_parent?(HWND)99:g_ddraw.hwnd;}
static HWND GetAncestor(HWND h,int flag){(void)h;(void)flag;return g_ddraw.hwnd;}
static HWND GetWindow(HWND h,int flag){(void)h;(void)flag;return fake.movie_wrong_owner?(HWND)99:NULL;}
static long real_GetWindowLongA(HWND h,int flag){(void)h;(void)flag;return fake.movie_nochild?0:WS_CHILD;}
static BOOL GetWindowRect(HWND h,RECT *r){(void)h;VoRect m=monitors[0].desktop;*r=(RECT){m.x,m.y,m.x+m.w,m.y+m.h};if(fake.movie_bad_bounds)r->right+=100;return TRUE;}
static BOOL EnumChildWindows(HWND h,BOOL (*cb)(HWND,LPARAM),LPARAM value){(void)h;if(fake.movie_present){if(!cb((HWND)1000,value))return FALSE;if(fake.movie_duplicate)cb((HWND)1001,value);if(fake.movie_capped)for(int i=0;i<70;i++)if(!cb((HWND)1000,value))break;}return TRUE;}
#define PeekMessageA(...) 0
#define DispatchMessageA(...) ((void)0)
#define GetForegroundWindow() ((HWND)(uintptr_t)fake.foreground)
#define IsIconic(...) fake.minimized
static DWORD GetTickCount(void){static DWORD t;return ++t;}
static DWORD WaitForSingleObject(HANDLE h,DWORD timeout){(void)h;(void)timeout;return 0;}
static DWORD GetEnvironmentVariableA(const char *key,char *out,DWORD size){(void)key;(void)size;out[0]=fake.enabled?'1':'0';return 1;}
static DWORD GetModuleFileNameW(void *module,WCHAR *out,DWORD size){(void)module;(void)size;wcscpy(out,L"C:\\game.exe");return 11;}
#define GetModuleHandleA(...) NULL
#define RegisterClassA(...) 1
#define UnregisterClassA(...) ((void)0)
#define GetLastError() 0
static HWND real_CreateWindowExA(int a,const char*b,const char*c,int d,int x,int y,int w,int h,void *i,void*j,void*k,void*l){(void)a;(void)b;(void)c;(void)d;(void)x;(void)y;(void)w;(void)h;(void)i;(void)j;(void)k;(void)l;static uintptr_t id=5;HWND window=(HWND)++id;if(!fake.windows[0])fake.windows[0]=window;else fake.windows[1]=window;return window;}
#define IDirect3DDevice9_CreateAdditionalSwapChain(d,p,out) acquire((void**)out)
#define IDirect3DSwapChain9_GetBackBuffer(d,i,t,out) acquire((void**)out)
#define IDirect3DDevice9_CreateStateBlock(d,t,out) acquire((void**)out)
#define IDirect3DDevice9_GetRenderTarget(d,i,out) acquire((void**)out)
#define IDirect3DStateBlock9_Capture(...) api()
#define IDirect3DDevice9_SetPixelShader(...) api()
static HRESULT set_texture(void *tex){fake.bound=tex;return api();}
#define IDirect3DDevice9_SetTexture(d,i,t) set_texture(t)
#define IDirect3DDevice9_SetSamplerState(...) api()
#define IDirect3DDevice9_SetRenderTarget(...) api()
#define IDirect3DDevice9_SetViewport(...) api()
static HRESULT clear_output(unsigned color){++fake.clears;fake.clear_color=color;return api();}
#define IDirect3DDevice9_Clear(d,n,r,f,color,z,s) clear_output(color)
#define IDirect3DDevice9_BeginScene(...) api()
static HRESULT draw(const CUSTOMVERTEX *v){HRESULT h=api();if(SUCCEEDED(h)){memcpy(fake.vertices[fake.draws],v,4*sizeof *v);fake.texture[fake.draws++]=fake.bound;}return h;}
#define IDirect3DDevice9_DrawPrimitiveUP(d,t,n,v,s) draw(v)
#define IDirect3DDevice9_EndScene(...) api()
static HRESULT restore(void){++fake.restores;return api();}
#define IDirect3DStateBlock9_Apply(...) restore()
static HRESULT fake_stream(void){++fake.streams;return api();}
#define IDirect3DDevice9_SetStreamSource(...) fake_stream()
static HRESULT present(void){HRESULT h=api();if(SUCCEEDED(h))++fake.presents;return h;}
#define IDirect3DSwapChain9_Present(...) present()
#define PostMessageA(...) (++fake.closed)
#define DestroyWindow(...) (++fake.destroyed)
static FILE *_wfopen(const WCHAR *path,const WCHAR *mode){(void)path;(void)mode;return NULL;}

static unsigned test_policy=2;
static unsigned vo_completed_policy(void){return test_policy;}
#define GetPrivateProfileIntW(...) 0

static unsigned vo_unknown_policy_count(void){return 0;}

static unsigned vo_unknown_policy_value(unsigned i){(void)i;return 0;}

static void vo_policy_log(FILE *log){(void)log;}
