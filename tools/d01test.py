#!/usr/bin/env python3
"""Private D01 gates: pristine sites, real x86 execution and CE.2 isolation.

Requires capstone, Unicorn, nasm and a pristine retail/JPRE executable.
No Windows driver, display or physical gameplay is emulated here.
"""
import hashlib
from pathlib import Path
import struct
import subprocess
import sys
import types

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import vonpatcher_hires as vp
import selftest
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX,
                              UC_X86_REG_ESP, UC_X86_REG_EFLAGS)

BASELINE = 'a60f5f7ff628d2c7853cfefa2eaf5bfb8cd9ee5a'
STACK, RET = 0x20000000, 0x30000000
HORIZONTAL = [0x1c7907, 0x1c7961, 0x1c7a2c, 0x1c7a8e, 0x1c7b89, 0x1c7c0e]


def baseline_module():
    source = subprocess.check_output(['git', 'show', BASELINE + ':v-on-patcher.py'],
                                     cwd=ROOT)
    module = types.ModuleType('ce2_reference')
    module.__file__ = str(ROOT / 'v-on-patcher.py')
    exec(compile(source, module.__file__, 'exec'), module.__dict__)
    from attribution_baseline import align
    align(module, vp)
    return module


def image(data):
    pe = vp._PE(data)
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    end = max(s['vaddr'] + max(s['vsize'], s['rsize']) for s in pe.sections)
    mu.mem_map(pe.base, (end + 4095) & ~4095)
    for s in pe.sections:
        mu.mem_write(pe.base + s['vaddr'], bytes(data[s['raddr']:s['raddr'] + s['rsize']]))
    mu.mem_map(STACK, 0x10000)
    mu.mem_map(RET, 0x1000)
    return mu, pe


def run(mu, start, stop=RET, count=1000000):
    mu.reg_write(UC_X86_REG_ESP, STACK + 0x8000 - 4)
    mu.mem_write(STACK + 0x8000 - 4, struct.pack('<I', RET))
    mu.ctl_remove_cache(RET, RET + 0x1000)  # private probe code is rewritten
    mu.emu_start(start, stop, count=count)
    from unicorn.x86_const import UC_X86_REG_EIP
    assert mu.reg_read(UC_X86_REG_EIP) == stop, 'instruction limit / unexpected exit'


def main(path, width=2560, vp=vp):
    original, _ = selftest.pristine(path, vp)
    assert original is not None, 'pristine executable required'
    build = vp.BUILDS[hashlib.md5(original).hexdigest()]
    assert build.short in ('retail', 'jpre')
    port = None if build.short == 'retail' else vp.PORT['%08x' % vp._pe_stamp(original)]
    translate = lambda o: o if port is None else port['off'][o][0]
    addr = lambda a: a if port is None else port['va'][a]
    old = baseline_module()
    # Identical synthetic addresses isolate generated values from allocation relocation.
    args = (1920, 1080, 0x4000000, 0x4100000, 0x4200000, (0x4300000, 8000))
    moved_hooks = 0
    for a, b in zip(old.build_sites(*args), vp.build_sites(*args), strict=True):
        if a == b:
            continue
        assert a[:2] == b[:2] and len(a[2]) == len(b[2])
        assert a[2][0] in (0xe8, 0xe9) and a[2][:1] == b[2][:1]
        assert a[2][5:] == b[2][5:]
        assert struct.unpack_from('<i', b[2], 1)[0] - struct.unpack_from('<i', a[2], 1)[0] == 8
        moved_hooks += 1
    assert moved_hooks == 26, 'unexpected 1920 hook movement'
    for offset, value in old._ui_words(1920, 1080).items():
        assert vp._ui_words(1920, 1080)[offset] == value
    assert old.BLOBS == {k:v for k,v in vp.BLOBS.items() if k != 'BOSSES'}, 'controller/shared annex blobs changed'
    assert old.TANITA_DLL_SHA == vp.TANITA_DLL_SHA
    assert old.TANITA_SRC_SHA == vp.TANITA_SRC_SHA
    keys = set(vp.by_key(build)) - {'hires', 'bosses', 'bossunlock'}
    assert selftest.apply(old, original, keys, old.BUILDS[build.md5]) == selftest.apply(vp, original, keys, build), 'non-display generated image changed'
    print(build.short, 'CE.2: 1920 values (26 UI hooks move +8), words, blobs, helper pins and non-display image identical')

    for w, h in [(3440, 1440), (3840, 1080), (5120, 1440), (2560, 720), (2559, 1080)]:
        if width == 3840 and (w,h) == (3840,1080):
            continue  # Explicit private proof only; default gate still rejects.
        try:
            vp._hires_check_size(w, h)
        except ValueError:
            pass
        else:
            raise AssertionError('unsupported mode accepted')
    assert vp.mask_pitch(1920) == 240 and vp.mask_pitch(2560) == 512
    assert (2560 // 32, 2560 // 8) == (80, 320)
    assert vp.UI_CANVAS_PITCH == 4096 and vp.UI_CANVAS_ROWS == 480
    assert vp.UI_CANVAS_REGION == 4096 * 480
    assert [vp.UI_CANVAS_OFF, vp.UI_CANVAS_STAGE, vp.UI_CANVAS_COPY] == [vp.UI_OFF + n * vp.UI_CANVAS_REGION for n in (1, 2, 3)]
    assert len(vp.UI_CODE) == 6764 and vp.UI_PASS_STUBS - len(vp.UI_CODE) == 4
    wanted = dict.fromkeys(vp.by_key(build), True)
    wanted['hires'] = (width, 1080)
    patched, _, skipped = vp.apply_selected(bytearray(original), wanted, build)
    assert not skipped, skipped
    mu, pe = image(patched)
    sec = next(s for s in pe.sections if s['name'] == b'.vohr')
    base, raw = pe.base + sec['vaddr'], sec['raddr']
    u32 = lambda off: struct.unpack_from('<I', patched, off)[0]
    mask = base + vp.UI_OFF + vp.UI_OFF_SIZE
    rowtable = mask + 1080 * 512
    assert u32(translate(0x1cd5d4)) == rowtable
    assert u32(translate(0x1cd60c)) == 1080 * 512 // 4
    assert u32(raw + vp.UI_ROWTAB) == rowtable + 1080 * 4
    assert sec['vsize'] == 0x8f83b0
    assert u32(raw + vp.UI_SPREADMAX) == 240
    for off, sign in ((0x205d38,-1),(0x205d3c,1),(0x1fb4a0,-1),(0x1fb4a4,1)):
        assert bytes(patched[translate(off):translate(off)+4]) == struct.pack('<f',sign*(256.0*width/(1080/480)/640))
    for off in (0x147b60,0x147cc8,0x074ed0,0x075038):
        assert u32(translate(off)) == (0x1f22 if width == 2560 else 0x2753)
    for off in HORIZONTAL:
        assert u32(translate(off)) == width//16, 'horizontal origin must use visible width'
    for off in (0x1c79bd, 0x1c7bd0):
        assert u32(translate(off)) == 540 * 512
    for off in (0x1c7af4, 0x1c7c55):
        assert u32(translate(off)) == 270 * 512
    for off in vp.MASK_EDX:
        assert u32(translate(off + 1)) == 512

    assert vp.MASK_PACK == [0x1cd8b8, 0x1cd9ee, 0x1ce11b, 0x1d162c,
                            0x1d1a3d, 0x1d877e, 0x1d88ba, 0x1d8ff1,
                            0x1dc502, 0x1dc923], 'incomplete packed-site inventory'
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    for off in vp.MASK_PACK:
        actual = translate(off)
        assert original[actual:actual+3] == b'\x83\xc8\x50'
        assert patched[actual:actual+3] == b'\xb4\x02\x90'
        site = vp._va_at(pe, actual)
        pitch = addr(0x6bf5ac) + (8 if off >= 0x1d8000 else 0)
        entry = patched.rfind(b'\xa1' + struct.pack('<I', pitch), actual-180, actual)
        assert entry >= 0
        before = list(md.disasm(bytes(patched[entry:actual]), vp._va_at(pe, entry)))
        assert before[-1].address + before[-1].size == site
        shifts = [i for i, ins in enumerate(before) if ins.mnemonic == 'shl' and ins.op_str == 'eax, 0x10']
        assert len(shifts) == 1
        for ins in before[shifts[0]+1:]:
            from capstone.x86 import X86_REG_EAX, X86_REG_AX, X86_REG_AH, X86_REG_AL
            assert not set(ins.regs_access()[1]) & {X86_REG_EAX, X86_REG_AX, X86_REG_AH, X86_REG_AL}
        # Execute the actual entry through the insertion, with padded as well
        # as tightly packed frame pitches; inspect EAX and untouched flags.
        for fb_pitch in (width*2, width*2+64, 8192):
            mu.mem_write(pitch, struct.pack('<I', fb_pitch))
            run(mu, vp._va_at(pe, entry), site)
            assert mu.reg_read(UC_X86_REG_EAX) == fb_pitch << 16
            flags = mu.reg_read(UC_X86_REG_EFLAGS)
            run(mu, site, site + 3)
            assert mu.reg_read(UC_X86_REG_EAX) == (fb_pitch << 16) | 512
            assert mu.reg_read(UC_X86_REG_EFLAGS) == flags
        # Follow the real local path (including unconditional joins). No
        # conditional branch may read flags before the first SUB overwrites.
        pc = site + 3
        for _ in range(80):
            f = pe.off(pc - pe.base)
            ins = next(md.disasm(bytes(patched[f:f+16]), pc))
            if ins.mnemonic == 'jmp':
                pc = ins.operands[0].imm
                continue
            assert not ins.mnemonic.startswith(('j', 'cmov', 'set')), ins
            if ins.eflags:
                assert ins.mnemonic == 'sub', (hex(pc), ins.mnemonic)
                break
            pc += ins.size
        else:
            raise AssertionError('no flags overwrite')
        # Execute through the original MMX word expansion, stopping just
        # after PSRLD MM0,16. Store MM0 through a private probe instruction.
        seq = list(md.disasm(bytes(patched[actual:actual+150]), site))
        final = next(i for i in seq if i.mnemonic == 'psrld' and i.op_str == 'mm0, 0x10')
        mu.reg_write(UC_X86_REG_EAX, (width*2 << 16) | 512)
        run(mu, site + 3, final.address + final.size)
        probe = b'\x0f\x7f\x05' + struct.pack('<I', RET + 0x800)  # movq [scratch],mm0
        mu.mem_write(RET, probe)
        run(mu, RET, RET + len(probe))
        assert bytes(mu.mem_read(RET + 0x800, 8)) == struct.pack('<4H', 512, 0, width*2, 0)
        consumer = next(i for i in seq if i.address > final.address and
                        i.mnemonic == 'pmaddwd' and i.op_str == 'mm2, mm0')
        for row in (1, 1079):
            mu.mem_write(RET + 0x810, struct.pack('<4H', row, 0, row, 0))
            probe = (b'\x0f\x6f\x15' + struct.pack('<I', RET + 0x810)
                     + bytes(consumer.bytes) + b'\x0f\x7f\x15'
                     + struct.pack('<I', RET + 0x820))
            mu.mem_write(RET, probe)
            run(mu, RET, RET + len(probe))
            assert bytes(mu.mem_read(RET + 0x820, 8)) == struct.pack('<II', row*512, row*width*2)
        print(' packed', hex(off), '->', hex(actual), 'b40290; EAX/flags/MMX PASS')

    # Run real row initialization/clear with sentinels, including padding.
    mu.mem_write(mask, b'\xa5' * (1080 * 512 + 1080 * 4))
    mu.mem_write(mask-4, b'LEFT')
    mu.mem_write(rowtable+1080*4, b'RGHT')
    run(mu, addr(0x5ce180))
    table = struct.unpack('<1080I', mu.mem_read(rowtable, 4320))
    assert table == tuple(mask + y * 512 for y in range(1080))
    clear = vp._va_at(pe, translate(0x1cd60c)) - 12
    run(mu, clear)
    assert bytes(mu.mem_read(mask, 552960)) == bytes(552960)
    assert bytes(mu.mem_read(mask-4, 4)) == b'LEFT'
    assert bytes(mu.mem_read(rowtable+4320, 4)) == b'RGHT'
    assert struct.unpack('<1080I', mu.mem_read(rowtable, 4320)) == table
    # All ordinary rewritten row-advance instructions execute independently
    # of the unrelated retained instructions around them.
    for off, size, _ in vp.MASK_ADVANCE:
        at = translate(off)
        instrs = list(md.disasm(bytes(patched[at:at+size]), vp._va_at(pe, at)))
        advance = [i for i in instrs if i.mnemonic == 'add' and '0x200' in i.op_str]
        assert len(advance) == 1
        ptr = addr(vp.ADDR['MASKPTR'])
        mu.mem_write(ptr, struct.pack('<I', mask + 1078*512))
        i = advance[0]
        run(mu, i.address, i.address+i.size)
        assert struct.unpack('<I', mu.mem_read(ptr,4))[0] == mask + 1079*512
    print(' mask rows/clear/padding/canaries: PASS; 24 advances / 4 EDX / B origins: PASS')

    # Every relocated operand must match its source and the edition map.
    assert len(vp.UI_REFS) == len(old.UI_REFS)
    assert [v for _, v in vp.UI_REFS] == [v for _, v in old.UI_REFS]
    for off, value in vp.UI_REFS:
        assert struct.unpack_from('<I', vp.UI_CODE, off)[0] == value
        assert u32(raw + off) == addr(value)
    assert not any(v in (vp.UI_CANVAS_OFF, vp.UI_CANVAS_STAGE, vp.UI_CANVAS_COPY) for _, v in vp.UI_REFS)

    # Execute F4 apply (not a Windows surface recreate): stub font rebuilding,
    # keep real mask initialization. Verify each record both ways.
    import uibuild
    _, labels = uibuild.assemble((ROOT/'asm/ui.asm').read_text())
    # f4_apply follows the five-byte call in f4_switch; recover its call target.
    instrs = list(md.disasm(vp.UI_CODE[labels['f4_toggle']:labels['dlg_init']], base+labels['f4_toggle']))
    init_call = next(i for i in instrs if i.mnemonic == 'call' and i.operands[0].imm > i.address + 5)
    switch = init_call.operands[0].imm
    f = pe.off(switch - pe.base)
    call = next(md.disasm(bytes(patched[f:f+5]), switch))
    assert call.mnemonic == 'call'
    apply_va = call.operands[0].imm
    mu.mem_write(addr(0x5c8ca0), b'\xc3')
    tab = u32(raw + vp.UI_F4TAB)
    records = []
    p = pe.off(tab - pe.base)
    while u32(p):
        va, n = struct.unpack_from('<II', patched, p)
        a, b = bytes(patched[p+8:p+8+n]), bytes(patched[p+8+n:p+8+2*n])
        assert bytes(mu.mem_read(va, n)) == a
        records.append((va, a, b)); p += 8+2*n
    for which in (2, 1):
        mu.reg_write(UC_X86_REG_EBX, base)
        run(mu, apply_va)
        for record in records:
            assert bytes(mu.mem_read(record[0],len(record[1]))) == record[which]
        active_w = 1280 if which == 2 else width
        active_h = 720 if which == 2 else 1080
        pitch = vp.mask_pitch(active_w)
        rt = mask + active_h*pitch
        assert struct.unpack('<I',mu.mem_read(rt+(active_h-1)*4,4))[0] == mask+(active_h-1)*pitch
    print(' generated relocations and F4 actual apply/row-table round trip: PASS')
    # Both real world projection entry points retain height-based scale.
    mu.mem_write(RET, b'\x0f\x77\xdb\xe3')  # emms; fninit
    run(mu, RET, RET + 4)
    for scale, aspect in ((0x6bc1e4, 0x6bc1e8), (0x6c8b24, 0x6c8b28)):
        mu.mem_write(addr(scale), struct.pack('<f', 2.25))
        mu.mem_write(addr(aspect), struct.pack('<f', 1.21875))
    for routine, projection, offsets in (('world_a',0x6db4c8,(0,8,12)),
                                         ('world_b',0x708818,(0,4,8))):
        mu.mem_write(STACK + 0x8000, struct.pack('<f',600))
        run(mu, base + labels[routine])
        values = tuple(struct.unpack('<f',mu.mem_read(addr(projection)+o,4))[0] for o in offsets)
        assert values == (1645.3125,2.7421875,1350), values
    print(' Renderer A/B world projection: unchanged vertical scale PASS')

    if build.short == 'retail':
        import uiemu
        uiemu.W = width
        e = uiemu.Emu(original, module=vp)
        # All four regions keep row-tail canaries outside active columns.
        tails = [e.blob + vp.UI_OFF + region*vp.UI_CANVAS_REGION +
                 row*vp.UI_CANVAS_PITCH + vp.UI_CANVAS_PITCH - 64
                 for region in range(4) for row in range(480)]
        for at in tails:
            e.mu.mem_write(at, b'\xa5'*64)
        assert uiemu.check_spread(e)
        for stub, ring, split, show in [('stub1','RING1',0,0), ('stub3','RING2',1,2)]:
            assert uiemu.check_photo(e, 'D01 '+stub, width, split, show, stub, ring, 0, 2.25, 0, inset=1 if width==3840 else 0)
            assert e.r32(uiemu.D['LW']) == vp.resolution_geometry(width,1080)['canvas_active_width']
        for at in tails:
            assert bytes(e.mu.mem_read(at,64)) == b'\xa5'*64, hex(at)
        # Padded framebuffer pitch: pre/post must leave untouched rows and
        # per-row padding intact when no UI pixels change.
        e.viewport(width,1080)
        e.d('BASEPTR',uiemu.G['FB_PTR']); e.d('PHASE',0); e.d('SHOW',0)
        e.w32(uiemu.G['FB_PITCH'], width*2+64)
        data = b'\x17\x29' * ((width*2+64)*1080//2)
        e.mu.mem_write(uiemu.SURF, data)
        e.routine('pre'); e.routine('post')
        assert bytes(e.mu.mem_read(uiemu.SURF,len(data))) == data
        print(' canvas four-region row-tail canaries / padded framebuffer no-op: PASS')
        print(' D01 retail A/B photo walkers + HUD/reticle/no-op compositor: PASS')
    print('D01 PASS', build.short)


if __name__ == '__main__':
    main(sys.argv[1])
