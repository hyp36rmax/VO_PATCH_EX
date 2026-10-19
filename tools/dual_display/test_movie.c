/* Production integration under API doubles; no decoded video claims. */
#define VO_DUAL_TEST
#include "presentation_test_api.h"
#include "presentation.h"
#include <assert.h>
static void setup(void){
 memset(&vo_dual,0,sizeof vo_dual);memset(&fake,0,sizeof fake);fake.foreground=1;fake.enabled=1;
 g_ddraw.width=3840;g_ddraw.height=1080;g_ddraw.bpp=16;g_ddraw.hwnd=(HWND)1;
 g_d3d9.params.Windowed=1;g_d3d9.tex_width=4096;g_d3d9.tex_height=2048;g_d3d9.surface_tex[0]=(void*)10;
 count=2;monitors[0]=(VoMonitor){"a",{0,0,2560,1440},1,1};monitors[1]=(VoMonitor){"b",{2560,0,1920,1080},0,1};
 test_policy=VO_PRIMARY_ONLY;vo_dual_uploaded(0);vo_dual_present(0);
 assert(fake.window_visible[0]&&fake.window_visible[1]);
}
static void movie(void){fake.movie_present=1;fake.movie_visible=1;vo_dual_pump();assert(vo_dual.movie.active==(HWND)1000&&!fake.window_visible[0]&&fake.window_visible[1]);}
int main(void){
 setup();movie();int calls=fake.position_calls[0];vo_dual_visibility(TRUE);assert(fake.position_calls[0]==calls&&!fake.window_visible[0]);
 int draws=fake.draws,presents=fake.presents;vo_dual_present(0);assert(fake.draws==draws&&fake.presents==presents+1&&vo_dual.movie_frames==1);assert(fake.foreground==1&&!fake.original_moves);
 /* A visible AVI keeps P2 black without repeated graphics work. */
 int gpu_calls=fake.calls; presents=fake.presents;
 for(int frame=0;frame<20;frame++){vo_dual_uploaded(0);vo_dual_present(0);}
 assert(fake.calls==gpu_calls&&fake.presents==presents&&!fake.original_moves);
 /* Skip, natural completion and unexpected destruction share the observed end. */
 fake.movie_present=0;vo_dual_pump();assert(!vo_dual.movie.active&&fake.window_visible[0]&&fake.p1_above);vo_dual_end();assert(!fake.live&&fake.destroyed==2);
 setup();movie();fake.movie_visible=0;vo_dual_pump();assert(fake.window_visible[0]&&!vo_dual.movie.active);vo_dual_end();
 for(int kind=0;kind<8;kind++){
  setup();fake.movie_present=fake.movie_visible=1;
  if(kind==0)fake.movie_wrong_pid=1;if(kind==1)fake.movie_wrong_parent=1;if(kind==2)fake.movie_wrong_owner=1;if(kind==3)fake.movie_wrong_class=1;
  if(kind==4)fake.movie_bad_bounds=1;if(kind==5)fake.movie_nochild=1;if(kind==6)fake.movie_duplicate=1;if(kind==7)fake.movie_capped=1;
  vo_dual_pump();assert(!vo_dual.movie.active&&fake.window_visible[0]&&!vo_dual.disabled);vo_dual_end();
 }
 setup();vo_dual_pump();assert(!vo_dual.movie.active&&fake.window_visible[0]);vo_dual_end();
 setup();movie();fake.foreground=0;vo_dual_pump();assert(!vo_dual.visible);fake.movie_present=0;vo_dual_pump();assert(vo_dual.movie.restore_pending&&!fake.window_visible[0]);fake.foreground=1;vo_dual_present(0);assert(!vo_dual.movie.restore_pending&&fake.window_visible[0]);vo_dual_end();
 setup();movie();fake.movie_present=0;fake.movie_restore_fail=1;vo_dual_pump();assert(vo_dual.disabled&&!vo_dual.visible&&!fake.window_visible[0]);vo_dual_end();assert(!fake.live);
 setup();fake.movie_present=fake.movie_visible=fake.movie_hide_fail=1;vo_dual_pump();assert(vo_dual.disabled);fake.movie_hide_fail=0;vo_dual_end();
 setup();movie();test_policy=VO_LOCAL_VS_GAMEPLAY;vo_dual_uploaded(0);vo_dual_present(0);assert(!vo_dual.movie.active&&fake.window_visible[0]&&vo_dual.output[1].source.x==1920);vo_dual_end();
 const int sizes[][2]={{1920,1080},{2560,1440},{1600,1200},{3440,1440},{5120,1440},{1080,1920}};
 for(unsigned i=0;i<6;i++){setup();monitors[0].desktop=(VoRect){-sizes[i][0],-sizes[i][1],sizes[i][0],sizes[i][1]};movie();fake.movie_present=0;vo_dual_pump();assert(fake.window_visible[0]&&!fake.original_moves&&fake.foreground==1);vo_dual_end();}
 setup();for(unsigned i=0;i<100;i++){movie();fake.movie_present=0;vo_dual_pump();}assert(vo_dual.movie.used==64&&vo_dual.movie.total>64);vo_dual_end();
 /* With the dual environment disabled, no output or movie action occurs. */
 setup();vo_dual_end();memset(&vo_dual,0,sizeof vo_dual);fake.enabled=0;fake.movie_present=fake.movie_visible=1;calls=fake.position_calls[0];vo_dual_uploaded(0);vo_dual_present(0);vo_dual_pump();assert(!vo_dual.attempted&&!vo_dual.movie.active&&fake.position_calls[0]==calls);
 assert(!vo_dual.uploads&&!vo_dual.texture_valid[0]);
 /* Readiness failure must stop before any render-target operation. */
 fake.enabled=1;
 setup();void *device=g_d3d9.device;g_d3d9.device=NULL;calls=fake.calls;
 vo_dual_present(0);assert(vo_dual.disabled&&fake.calls==calls&&!fake.live);
 g_d3d9.device=device;vo_dual_end();
 setup();void *texture=g_d3d9.surface_tex[0];g_d3d9.surface_tex[0]=NULL;calls=fake.calls;
 vo_dual_present(0);assert(vo_dual.disabled&&fake.calls==calls&&!fake.live);
 g_d3d9.surface_tex[0]=texture;vo_dual_end();
 puts("PASS movie identity, bounds, ambiguity/limit rejection, hide/restore, lifecycle end, absent/destruction, focus-deferred restoration, visibility failures, single-mode gate, P2 black and gameplay resumption; host API doubles only");
}
