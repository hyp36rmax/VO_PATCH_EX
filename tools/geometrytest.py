#!/usr/bin/env python3
"""Private geometry contracts and exact output regression; no Windows emulation.

Without arguments: pure geometry and generated-site checks.
With a pristine executable: compare complete patch output with D02-S01.
"""
from fractions import Fraction
import hashlib
from pathlib import Path
import subprocess
import sys
import types

import selftest

ROOT = Path(__file__).resolve().parents[1]
BASELINE = '04d32ebe6b62e2d7f4167ef0779b4c4c385eaaed'
MATRIX = [
    (640, 480, 20, 80, 256, 640, 640, 0, True),
    (1024, 768, 32, 128, 256, 640, 1024, 0, True),
    (1280, 720, 40, 160, 256, 854, 1280, 0, True),
    (1920, 1080, 60, 240, 256, 854, 1920, 0, True),
    (2560, 1080, 80, 320, 512, 1138, 1920, 320, True),
    (3440, 1440, 108, 432, 512, 1146, 2560, 440, False),
    (3840, 1080, 120, 480, 512, 1706, 1920, 960, False),
    (5120, 1440, 160, 640, 768, 1706, 2560, 1280, False),
]


def baseline():
    source = subprocess.check_output(['git', 'show', BASELINE + ':v-on-patcher.py'], cwd=ROOT)
    module = types.ModuleType('s01_reference')
    module.__file__ = str(ROOT / 'v-on-patcher.py')
    exec(compile(source, module.__file__, 'exec'), module.__dict__)
    return module


def rejects(fn, *args):
    try:
        fn(*args)
    except ValueError:
        return
    raise AssertionError(('accepted invalid input', fn.__name__, args))


def geometry(vp, old):
    for w, h, words, used, pitch, logical, hud, origin, supported in MATRIX:
        g = vp.resolution_geometry(w, h)
        assert (g['mask_used_words'], g['mask_used_bytes'], g['candidate_mask_row_pitch']) == (words, used, pitch)
        assert g['aspect_ratio'] == Fraction(w, h)
        assert g['vertical_projection_scale'] == Fraction(h, 480)
        assert g['horizontal_projection_extent'] == Fraction(3*w, 4*h)
        assert (g['viewport_x'], g['viewport_y'], g['viewport_width'], g['viewport_height']) == (0, 0, w, h)
        assert g['framebuffer_pitch'] is None and g['framebuffer_min_row_bytes'] == 2*w
        padded_fb = vp.resolution_geometry(w, h, 2*w+64)
        assert {k:v for k,v in padded_fb.items() if k != 'framebuffer_pitch'} == {k:v for k,v in g.items() if k != 'framebuffer_pitch'}
        assert g['canvas_logical_width'] == logical and g['canvas_fits']
        assert g['canvas_pitch'] == 4096 and g['canvas_rows'] == 480 and g['canvas_capacity'] == 2048
        assert (g['hud_composition_width'], g['hud_horizontal_origin']) == (hud, origin)
        assert g['hud_vertical_origin'] == 0 and g['hud_composition_height'] == h
        assert 2*origin + hud == w and 0 <= origin and hud <= w
        assert g['patch_size_admitted'] == supported
        assert g['physical_validation'] == 'UNKNOWN'
        assert g == vp.resolution_geometry(w, h)
        if supported:
            vp._hires_check_size(w, h)
            assert used <= g['mask_row_pitch'] == old.mask_pitch(w)
            assert vp._ui_words(w, h) == old._ui_words(w, h)
        else:
            assert g['mask_row_pitch'] is None
            rejects(vp._hires_check_size, w, h)
            rejects(vp.hires_install, bytearray(), w, h)
            rejects(vp.build_sites, w, h, 0, 0, 0, (0, 8000))
    # Word and padded-row boundaries: first/last bit belongs to exactly one word.
    for w in (1, 31, 32, 33, 63, 64, 65, 2015, 2016, 2017, 2040, 2047, 2048, 2049, 4095, 4096, 4097):
        words, used, pitch = vp._mask_geometry(w)
        assert (words-1)*32 < w <= words*32
        assert used == 4*words and used <= pitch < used+256 and pitch % 256 == 0
    assert [vp._mask_geometry(w)[2] for w in (2048, 2049, 4096, 4097)] == [256, 512, 512, 768]
    for w in (2046, 2047, 2048, 2049, 2050):
        g = vp.resolution_geometry(w, 480)
        assert g['canvas_logical_width'] == (w+1)&~1
        assert g['canvas_fits'] == (w <= 2048)
        assert g['visible_width'] == w  # research never rounds requested dimensions
        assert g['canvas_active_width'] == min(g['canvas_logical_width'], 2048)
    # Preserve the historical admission policy throughout its width boundary.
    for w in range(1984, 2081):
        g = vp.resolution_geometry(w, 480)
        assert g['patch_size_admitted'] == (w % 32 == 0 and w <= 2040)
    for w, h in ((2560, 720), (2560, 1088), (1920, 1079), (3440, 1440)):
        rejects(vp._hires_check_size, w, h)
    for bad in (0, -1, True, 1.5, '1920', None):
        rejects(vp.resolution_geometry, bad, 480)
        rejects(vp._hires_check_size, 640, bad)
    for bad in (0, -1280, 1279, True, 1280.0):
        rejects(vp.resolution_geometry, 640, 480, bad)
    assert vp.UI_OFF_SIZE == old.UI_OFF_SIZE
    assert [vp.UI_CANVAS_OFF, vp.UI_CANVAS_STAGE, vp.UI_CANVAS_COPY] == [vp.UI_OFF+n*4096*480 for n in (1,2,3)]
    assert vp.UI_CODE == old.UI_CODE and vp.UI_REFS == old.UI_REFS
    # Every supported research tuple plus legacy width limit: exact sites include
    # Renderer B horizontal origins, projection, HUD and DirectDraw dimensions.
    for w, h in [(r[0], r[1]) for r in MATRIX if r[-1]] + [(2016,480)]:
        args = (w, h, 0x4000000, 0x4100000, 0x4200000, (0x4300000, 8000))
        assert vp.build_sites(*args) == old.build_sites(*args), (w,h)
    print('PASS eight-mode geometry, mask/canvas boundaries, unsupported rejection, runtime-pitch independence, HUD/Y, regions and deterministic exact sites')


def images(vp, old, path):
    from attribution_baseline import align
    align(old, vp)
    data, _ = selftest.pristine(path, vp)
    assert data is not None, 'pristine executable required'
    md5 = hashlib.md5(data).hexdigest()
    for size in ((640,480), (1024,768), (1280,720), (1920,1080), (2560,1080)):
        results = []
        for m in (old, vp):
            build = m.BUILDS[md5]
            wanted = dict.fromkeys(m.by_key(build), True)
            wanted.update(bosses=False, bossunlock=False)
            wanted['hires'] = size
            if size in ((640,480), (1024,768)):
                # Existing S01 cannot pair 4:3 with its default 16:9 alternate:
                # preserve the explicit failure rather than claim admission is
                # successful generation. Compare 4:3 using identical alternates.
                try:
                    m.apply_selected(bytearray(data), wanted, build)
                except m.PatchFailed as error:
                    assert isinstance(error.__cause__, AssertionError)
                    tb = error.__cause__.__traceback__
                    while tb.tb_next:
                        tb = tb.tb_next
                    assert tb.tb_frame.f_code.co_name == 'hires_install'
                    frame = tb.tb_frame.f_locals
                    assert (frame['off'] != frame['aoff'] or
                            frame['old_'] != frame['aold'] or
                            len(frame['new_']) != len(frame['anew']))
                else:
                    raise AssertionError('baseline F4 mismatch unexpectedly disappeared')
                wanted['hires'] = False
                result, _, skipped = m.apply_selected(bytearray(data), wanted, build)
                m.hires_install(result, *size, alt=size)
            else:
                result, _, skipped = m.apply_selected(bytearray(data), wanted, build)
            assert not skipped
            results.append(result)
        assert results[0] == results[1], size
        print('PASS', build.short, size,
              'same-size alternate' if size[0] in (640,1024) else 'default alternate',
              'full generated image identical', hashlib.sha256(results[1]).hexdigest())


if __name__ == '__main__':
    current, reference = selftest.load_patcher(), baseline()
    geometry(current, reference)
    for argument in sys.argv[1:]:
        images(current, reference, argument)
