/* Included only in the pinned render_d3d9.c, after g_d3d9.
 * Read-only producer policy accompanies the renderer's uploaded texture. */
#ifndef VO_DUAL_TEST
#include "inventory.h"
#endif
#include "policy.h"
#ifndef VO_DUAL_TEST
#include "state_bridge.h"
#endif
#include "movie_window.h"
static struct {
    HWND window[2];
    IDirect3DSwapChain9 *chain[2];
    IDirect3DSurface9 *target[2];
    IDirect3DStateBlock9 *state;
    VoOutput output[2];
    BOOL attempted, disabled, visible, registered;
    HRESULT failure;
    unsigned long frames, pairs, uploads;
    unsigned long generation[2], presented_generation[2];
    BOOL texture_valid[2];
    VoPolicy policy[2];
    int mirror;
    VoPolicy last_phase;
    VoMovie movie;
    unsigned long movie_frames;
    BOOL movie_quiet;
    unsigned long phase_pairs[4];
} vo_dual;

/* Launch projection is authoritative; Single owns no extra output resources. */
static BOOL vo_dual_enabled(void)
{
    char enabled[2] = {0};
    return GetEnvironmentVariableA("VO_DUAL_DISPLAY", enabled, sizeof enabled) == 1 && enabled[0] == '1';
}

static LRESULT CALLBACK vo_output_proc(HWND window, UINT msg, WPARAM w, LPARAM l)
{
    if (msg == WM_MOUSEACTIVATE) return MA_NOACTIVATEANDEAT;
    if (msg == WM_DISPLAYCHANGE || msg == WM_CLOSE) {
        EnterCriticalSection(&g_ddraw.cs);
        vo_dual.disabled = TRUE;
        LeaveCriticalSection(&g_ddraw.cs);
        return 0;
    }
    return DefWindowProcA(window, msg, w, l);
}

/* Caller holds g_ddraw.cs. Release every default-pool reference before Reset.
 * Window destruction remains on the render thread that created the windows. */
static void vo_dual_release_gpu(void)
{
    if (vo_dual.state) IDirect3DStateBlock9_Release(vo_dual.state);
    vo_dual.state = NULL;
    for (int i = 0; i < 2; ++i) {
        if (vo_dual.target[i]) IDirect3DSurface9_Release(vo_dual.target[i]);
        if (vo_dual.chain[i]) IDirect3DSwapChain9_Release(vo_dual.chain[i]);
        vo_dual.target[i] = NULL;
        vo_dual.chain[i] = NULL;
    }
}
static void vo_dual_before_reset(void)
{
    if (!vo_dual.attempted) return;
    EnterCriticalSection(&g_ddraw.cs);
    vo_dual.movie_quiet = FALSE;
    if (vo_dual.attempted) vo_dual.disabled = TRUE;
    vo_dual_release_gpu();
    memset(vo_dual.texture_valid, 0, sizeof vo_dual.texture_valid);
    LeaveCriticalSection(&g_ddraw.cs);
}
/* EnumWindows stops at the first of our P1 window and the input window.
 * The original wrapper can raise its topmost combined window again on focus /
 * renderer transitions. Repair only an actual P1 stacking inversion. */
static BOOL CALLBACK vo_p1_order(HWND window, LPARAM value)
{
    if (window == vo_dual.window[0]) { *(BOOL*)value = TRUE; return FALSE; }
    return window != g_ddraw.hwnd;
}
static void vo_dual_visibility(BOOL show)
{
    if (!show) vo_dual.movie_quiet = FALSE;
    if (show && !vo_dual.movie.active && !vo_movie_restore(&vo_dual.movie, vo_dual.window[0])) {
        vo_dual.failure=E_FAIL;vo_dual.disabled=TRUE;show=FALSE;
    }
    if (show == vo_dual.visible) {
        if (show && !vo_dual.movie.active && vo_dual.window[0] && GetForegroundWindow() == g_ddraw.hwnd) {
            BOOL above = FALSE;
            EnumWindows(vo_p1_order, (LPARAM)&above);
            if (!above) real_SetWindowPos(vo_dual.window[0], HWND_TOPMOST, 0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
        }
        return;
    }
    for (int i = 0; i < 2; ++i) if (vo_dual.window[i]) {
        if (show && i==0 && vo_dual.movie.active) continue;
        if (show) real_SetWindowPos(vo_dual.window[i], i == 0 ? HWND_TOPMOST : HWND_TOP, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW);
        else ShowWindow(vo_dual.window[i], SW_HIDE);
    }
    vo_dual.visible = show;
}
static void vo_dual_pump(void)
{
    if (!vo_dual.attempted) return;
    MSG msg;
    /* Do not remove messages for the game's window or other libraries. */
    for (int i = 0; i < 2; ++i) if (vo_dual.window[i])
        while (PeekMessageA(&msg, vo_dual.window[i], 0, 0, PM_REMOVE))
            DispatchMessageA(&msg);
    EnterCriticalSection(&g_ddraw.cs);
    if (vo_dual.attempted && !vo_dual.disabled && vo_dual.window[0] && vo_dual.pairs) {
        BOOL eligible=vo_dual.last_phase==VO_PRIMARY_ONLY && vo_completed_policy()==VO_PRIMARY_ONLY;
        HWND previous_movie = vo_dual.movie.active;
        BOOL may_show=vo_dual.visible && GetForegroundWindow()==g_ddraw.hwnd && !IsIconic(g_ddraw.hwnd);
        if(!vo_movie_update(&vo_dual.movie,g_ddraw.hwnd,vo_dual.window[0],monitors[vo_dual.output[0].monitor].desktop,eligible,may_show)) {
            vo_dual.failure=E_FAIL;vo_dual.disabled=TRUE;
        }
        if (previous_movie != vo_dual.movie.active) vo_dual.movie_quiet = FALSE;
    }
    if (!vo_dual.movie.active) vo_dual.movie_quiet = FALSE;
    if (vo_dual.disabled || GetForegroundWindow() != g_ddraw.hwnd || IsIconic(g_ddraw.hwnd))
        vo_dual_visibility(FALSE);
    LeaveCriticalSection(&g_ddraw.cs);
}
static DWORD vo_dual_wait(HANDLE semaphore, DWORD timeout)
{
    if (!vo_dual.window[0] && !vo_dual.window[1]) return WaitForSingleObject(semaphore, timeout);
    DWORD start = GetTickCount();
    for (;;) {
        vo_dual_pump();
        DWORD elapsed = GetTickCount() - start;
        DWORD slice = timeout == INFINITE ? 50 : (elapsed >= timeout ? 0 : min(50, timeout - elapsed));
        DWORD result = WaitForSingleObject(semaphore, slice);
        if (result != WAIT_TIMEOUT || (timeout != INFINITE && GetTickCount() - start >= timeout)) return result;
        if (!g_ddraw.render.run) return WAIT_TIMEOUT;
    }
}
static BOOL vo_dual_init(void)
{
    char enabled[2];
    if (GetEnvironmentVariableA("VO_DUAL_DISPLAY", enabled, sizeof enabled) != 1 || enabled[0] != '1') return FALSE;
    vo_dual.attempted = TRUE;
    vo_dual.failure = E_FAIL;
    if (!g_d3d9.params.Windowed || g_ddraw.width != 3840 || g_ddraw.height != 1080 || g_ddraw.bpp != 16) goto fail;
    DWORD n = GetModuleFileNameW(NULL, config, MAX_PATH);
    if (!n || n >= MAX_PATH) goto fail;
    WCHAR *slash = wcsrchr(config, L'\\');
    if (!slash || slash-config+22 >= MAX_PATH) goto fail;
    wcscpy(slash+1, L"player-displays.ini");
    if (!discover()) goto fail;
    vo_dual.mirror = GetPrivateProfileIntW(L"Presentation", L"MirrorPlayer1", 0, config) == 1;
    char a[VO_ID_CHARS], b[VO_ID_CHARS];
    load_id(L"Player1", a); load_id(L"Player2", b);
    if (vo_plan(monitors, count, a, b, vo_dual.output) != VO_DUAL_READY) goto fail;
    WNDCLASSA wc = {0};
    wc.lpfnWndProc = vo_output_proc; wc.hInstance = GetModuleHandleA(NULL);
    wc.lpszClassName = "VoPrivatePlayerOutput";
    if (!RegisterClassA(&wc)) goto fail;
    vo_dual.registered = TRUE;
    for (int i = 0; i < 2; ++i) {
        VoRect r = monitors[vo_dual.output[i].monitor].desktop;
        vo_dual.window[i] = real_CreateWindowExA(WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW,
            wc.lpszClassName, i ? "Virtual-On Player 2" : "Virtual-On Player 1",
            WS_POPUP, r.x, r.y, r.w, r.h, NULL, NULL, wc.hInstance, NULL);
        if (!vo_dual.window[i]) goto fail;
        D3DPRESENT_PARAMETERS params = {0};
        params.Windowed = TRUE; params.SwapEffect = D3DSWAPEFFECT_DISCARD;
        params.hDeviceWindow = vo_dual.window[i]; params.BackBufferCount = 1;
        params.BackBufferWidth = r.w; params.BackBufferHeight = r.h;
        params.BackBufferFormat = D3DFMT_UNKNOWN;
        params.PresentationInterval = D3DPRESENT_INTERVAL_IMMEDIATE;
        vo_dual.failure = IDirect3DDevice9_CreateAdditionalSwapChain(g_d3d9.device, &params, &vo_dual.chain[i]);
        if (FAILED(vo_dual.failure)) goto fail;
        vo_dual.failure = IDirect3DSwapChain9_GetBackBuffer(vo_dual.chain[i], 0, D3DBACKBUFFER_TYPE_MONO, &vo_dual.target[i]);
        if (FAILED(vo_dual.failure)) goto fail;
    }
    vo_dual.failure = IDirect3DDevice9_CreateStateBlock(g_d3d9.device, D3DSBT_ALL, &vo_dual.state);
    if (FAILED(vo_dual.failure)) goto fail;
    return TRUE;
fail:
    vo_dual.disabled = TRUE;
    vo_dual_release_gpu();
    return FALSE;
}

/* Same render thread and same texture for both draws; no independent upload,
 * queue, CPU readback, or simulation. Sequential presents are not scanout sync. */
static void vo_dual_present(int texture_index)
{
    if (!vo_dual.attempted && !vo_dual_enabled()) return;
    vo_dual_pump();
    EnterCriticalSection(&g_ddraw.cs);
    if (vo_dual.disabled || !vo_dual.texture_valid[texture_index]) goto done;
    if (!vo_dual.attempted && (g_ddraw.width != 3840 || g_ddraw.height != 1080 || g_ddraw.bpp != 16)) goto done;
    if (!vo_dual.attempted && !vo_dual_init()) goto done;
    if (GetForegroundWindow() != g_ddraw.hwnd || IsIconic(g_ddraw.hwnd)) goto done;
    if (g_ddraw.width != 3840 || g_ddraw.height != 1080 || g_ddraw.bpp != 16) {
        vo_dual.disabled = TRUE; goto done;
    }
    /* Never resume extra presentation with an incomplete resource set. Reset
     * invalidates these references; ordinary initialization owns recreation. */
    if (!g_d3d9.device || !g_d3d9.surface_tex[texture_index] || !vo_dual.state ||
        !vo_dual.chain[0] || !vo_dual.chain[1] || !vo_dual.target[0] || !vo_dual.target[1]) {
        vo_dual.failure = E_FAIL; vo_dual.disabled = TRUE; goto done;
    }
    /* Once P2 is black, the visible native AVI needs no secondary GPU work.
     * Visibility observation changes only our outputs, never MCI or the AVI. */
    if (vo_dual.movie.active && vo_dual.movie_quiet) goto done;
    IDirect3DSurface9 *original = NULL;
    HRESULT hr = IDirect3DDevice9_GetRenderTarget(g_d3d9.device, 0, &original);
    if (FAILED(hr)) { vo_dual.failure = hr; vo_dual.disabled = TRUE; goto done; }
    hr = IDirect3DStateBlock9_Capture(vo_dual.state);
    if (FAILED(hr)) { IDirect3DSurface9_Release(original); vo_dual.failure = hr; vo_dual.disabled = TRUE; goto done; }
    ++vo_dual.frames;
#define VO_TRY(call) do { hr = (call); if (FAILED(hr)) goto restore; } while (0)
    VO_TRY(IDirect3DDevice9_SetPixelShader(g_d3d9.device, NULL));
    VO_TRY(IDirect3DDevice9_SetTexture(g_d3d9.device, 0, (IDirect3DBaseTexture9*)g_d3d9.surface_tex[texture_index]));
    /* Point sampling cannot blend the other player's edge texel. */
    VO_TRY(IDirect3DDevice9_SetSamplerState(g_d3d9.device, 0, D3DSAMP_MINFILTER, D3DTEXF_POINT));
    VO_TRY(IDirect3DDevice9_SetSamplerState(g_d3d9.device, 0, D3DSAMP_MAGFILTER, D3DTEXF_POINT));
    for (int i = 0; i < 2; ++i) {
        VoOutput o = vo_dual.output[i]; VoRect monitor = monitors[o.monitor].desktop;
        int black=0;
        if(!vo_route(vo_dual.policy[texture_index],vo_dual.mirror,i,monitor,&o,&black)){hr=E_FAIL;goto restore;}
        if(vo_dual.movie.active)black=1;
        vo_dual.output[i]=o;
        float x = (float)(o.destination.x-monitor.x)-0.5f;
        float y = (float)(o.destination.y-monitor.y)-0.5f;
        float right = x+o.destination.w, bottom = y+o.destination.h;
        float u0 = (float)o.source.x/g_d3d9.tex_width;
        float u1 = (float)(o.source.x+o.source.w)/g_d3d9.tex_width;
        float v1 = (float)o.source.h/g_d3d9.tex_height;
        CUSTOMVERTEX vertices[4] = {{x,bottom,0,1,u0,v1},{x,y,0,1,u0,0},{right,bottom,0,1,u1,v1},{right,y,0,1,u1,0}};
        D3DVIEWPORT9 viewport = {0,0,monitor.w,monitor.h,0,1};
        VO_TRY(IDirect3DDevice9_SetRenderTarget(g_d3d9.device, 0, vo_dual.target[i]));
        VO_TRY(IDirect3DDevice9_SetViewport(g_d3d9.device, &viewport));
        VO_TRY(IDirect3DDevice9_Clear(g_d3d9.device, 0, NULL, D3DCLEAR_TARGET, 0, 1, 0));
        if(black) continue;
        VO_TRY(IDirect3DDevice9_BeginScene(g_d3d9.device));
        hr = IDirect3DDevice9_DrawPrimitiveUP(g_d3d9.device, D3DPT_TRIANGLESTRIP, 2, vertices, sizeof vertices[0]);
        HRESULT end = IDirect3DDevice9_EndScene(g_d3d9.device);
        if (FAILED(hr) || FAILED(end)) { if (SUCCEEDED(hr)) hr = end; goto restore; }
    }
restore:;
    HRESULT rt = IDirect3DDevice9_SetRenderTarget(g_d3d9.device, 0, original);
    HRESULT state = IDirect3DStateBlock9_Apply(vo_dual.state);
    /* DrawPrimitiveUP clears stream 0; restore explicitly, including PUREDEVICE. */
    HRESULT stream = IDirect3DDevice9_SetStreamSource(g_d3d9.device, 0, g_d3d9.vertex_buf, 0, sizeof(CUSTOMVERTEX));
    IDirect3DSurface9_Release(original);
    if (SUCCEEDED(hr) && FAILED(rt)) hr=rt;
    if (SUCCEEDED(hr) && FAILED(state)) hr=state;
    if (SUCCEEDED(hr) && FAILED(stream)) hr=stream;
    if (FAILED(rt) || FAILED(state) || FAILED(stream)) {
        /* A failed restoration cannot safely resume the original renderer. */
        PostMessageA(g_ddraw.hwnd, WM_CLOSE, 0, 0);
    }
    if (SUCCEEDED(hr)) {
        for (int i=0;i<2;++i) {
            if(i==0 && vo_dual.movie.active)continue;
            hr = IDirect3DSwapChain9_Present(vo_dual.chain[i],NULL,NULL,NULL,NULL,0);
            if (FAILED(hr)) break;
            vo_dual.presented_generation[i] = vo_dual.generation[texture_index];
        }
    }
    if (FAILED(hr)) { vo_dual.failure=hr; vo_dual.disabled=TRUE; }
    else { vo_dual.movie_quiet = vo_dual.movie.active != NULL; vo_dual.last_phase=vo_dual.policy[texture_index]; if(vo_dual.movie.active)++vo_dual.movie_frames;else ++vo_dual.pairs; ++vo_dual.phase_pairs[vo_dual.policy[texture_index]]; vo_dual_visibility(TRUE); }
#undef VO_TRY
done:
    if (vo_dual.disabled) { vo_dual_visibility(FALSE); vo_dual_release_gpu(); }
    LeaveCriticalSection(&g_ddraw.cs);
}
static void vo_dual_uploaded(int index)
{
    if (!vo_dual.attempted && !vo_dual_enabled()) return;
    vo_dual.policy[index] = (VoPolicy)vo_completed_policy();
    vo_dual.texture_valid[index] = TRUE;
    vo_dual.generation[index] = ++vo_dual.uploads;
}
static void vo_dual_end(void)
{
    EnterCriticalSection(&g_ddraw.cs);
    unsigned output_mask = (vo_dual.window[0]?1u:0u)|(vo_dual.window[1]?2u:0u);
    BOOL was_visible = vo_dual.visible;
    if(vo_dual.movie.active)vo_movie_event(&vo_dual.movie,MOVIE_SHUTDOWN,MOVIE_OK,vo_dual.movie.active,IsWindowVisible(vo_dual.window[0]),1);
    vo_dual_visibility(FALSE); vo_dual_release_gpu();
    for(int i=0;i<2;++i) if(vo_dual.window[i]) DestroyWindow(vo_dual.window[i]);
    if(vo_dual.registered) UnregisterClassA("VoPrivatePlayerOutput", GetModuleHandleA(NULL));
    if(vo_dual.attempted) {
        WCHAR path[MAX_PATH]; DWORD n=GetModuleFileNameW(NULL,path,MAX_PATH);
        WCHAR *slash = n && n<MAX_PATH ? wcsrchr(path,L'\\') : NULL;
        if(slash && slash-path+27<MAX_PATH) {
            wcscpy(slash+1,L"D04-P02B-presentation.log");
            FILE *log=_wfopen(path,L"a");
            if(log) { fprintf(log,"uploads=%lu draw_frames=%lu presented_pairs=%lu fallback=%d hr=0x%08lx\n",vo_dual.uploads,vo_dual.frames,vo_dual.pairs,vo_dual.disabled,(unsigned long)vo_dual.failure);
                for (int i=0;i<2;++i) { VoOutput o=vo_dual.output[i]; fprintf(log,"player=%d id=%s source=%d,%d,%d,%d destination=%d,%d,%d,%d\n",i+1,monitors[o.monitor].id,o.source.x,o.source.y,o.source.w,o.source.h,o.destination.x,o.destination.y,o.destination.w,o.destination.h); }
                fprintf(log,"p1_generation=%lu p2_generation=%lu\n",vo_dual.presented_generation[0],vo_dual.presented_generation[1]);
                fprintf(log,"primary_only=%lu local_vs_shared=%lu local_vs_gameplay=%lu unknown=%lu mirror_p1=%d\n",vo_dual.phase_pairs[0],vo_dual.phase_pairs[1],vo_dual.phase_pairs[2],vo_dual.phase_pairs[3],vo_dual.mirror);
                fprintf(log,"unrecognized_state_samples=%u\n",vo_unknown_policy_count());
                fprintf(log,"last_unknown_loop=%u mode=%u split=%u show=%u\n",vo_unknown_policy_value(0),vo_unknown_policy_value(1),vo_unknown_policy_value(2),vo_unknown_policy_value(3));
                fprintf(log,"output_window_mask=0x%x visible_before_teardown=%d shutdown=render_thread_teardown phase_codes=0:PRIMARY_ONLY,1:LOCAL_VS_SHARED,2:LOCAL_VS_GAMEPLAY,3:UNKNOWN\n",output_mask,was_visible);
                vo_policy_log(log);
                fprintf(log,"movie_p1_present_suppressed=%lu\n",vo_dual.movie_frames);
                vo_movie_log(log,&vo_dual.movie);
                fclose(log); }
        }
    }
    memset(&vo_dual,0,sizeof vo_dual);
    LeaveCriticalSection(&g_ddraw.cs);
}
