"""Verify pristine B-engine initialization and logical input routing slices.

Usage: python tools/bosses/test_player_b_native.py ORIGINAL.exe

These tests execute existing game instructions, not an implemented Local VS
extension. Initialization stops before terrain, palette and weapon setup;
Z-Gradt stops at entry to its setup routine. No callee is replaced with a stub.
"""
import hashlib
from pathlib import Path
import struct
import sys

from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EIP

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vomap import Exe

# Addresses checked against each pristine executable, not a constant delta.
EDITION = {
    'a464b0ff32d5bab499f265e45658504e': dict(
        name='Retail', init=0x4c74e6, initialized=0x4c7695,
        standard=0x4c722e, cpu=0x4c7366, alternate=0x4c7308,
        replay=0x4c7337, ztick=0x4c742c, zsetup=0x5771d1,
        cpu_setup=0x5adc1f, models=0x6070a0,
        objects=(0x1ef8ab0, 0x1ef9f60), a_object=0x1ae0c40,
        input=0x4c5772, input_end=0x4c591d,
        banks=(0x365198c, 0x3651994, 0x3651a0c, 0x3651a14)),
    'd19320bdc3381a48228990907910a391': dict(
        name='JPRE', init=0x4c5086, initialized=0x4c5235,
        standard=0x4c4dce, cpu=0x4c4f06, alternate=0x4c4ea8,
        replay=0x4c4ed7, ztick=0x4c4fcc, zsetup=0x5724bd,
        cpu_setup=0x5a8995, models=0x601e30,
        objects=(0x1ef5450, 0x1ef5ad0), a_object=0x1adb930,
        input=0x4c339a, input_end=0x4c3545,
        banks=(0x364c66c, 0x364c674, 0x364c5ec, 0x364c5f4)),
}
STACK = 0x10000000


class Native:
    def __init__(self, exe):
        self.uc = Uc(UC_ARCH_X86, UC_MODE_32)
        for _, va, virtual, offset, raw in exe.secs:
            address = 0x400000 + va
            self.uc.mem_map(address, (max(virtual, raw) + 4095) & ~4095)
            if raw:
                self.uc.mem_write(address, exe.d[offset:offset + raw])
        self.uc.mem_map(STACK, 4096)

    def word(self, address, value):
        self.uc.mem_write(address, struct.pack('<I', value))

    def read_word(self, address):
        return struct.unpack('<I', self.uc.mem_read(address, 4))[0]

    def run(self, entry, arguments, stops):
        sp = STACK + 2048
        self.word(sp, 0xdeadbeef)
        for i, value in enumerate(arguments):
            self.word(sp + 4 + i * 4, value)
        self.uc.reg_write(UC_X86_REG_ESP, sp)
        reached = []

        def stop(uc, address, size, data):
            if address in stops:
                reached.append(address)
                uc.emu_stop()

        hook = self.uc.hook_add(UC_HOOK_CODE, stop)
        try:
            self.uc.emu_start(entry, 0, count=10000)
        finally:
            self.uc.hook_del(hook)
        assert len(reached) == 1, hex(self.uc.reg_read(UC_X86_REG_EIP))
        return reached[0]


def test(path):
    digest = hashlib.md5(path.read_bytes()).hexdigest()
    spec = EDITION[digest]  # Refuse patched or unknown images.
    exe = Exe(str(path))
    native = Native(exe)
    uc = native.uc
    sentinel = b'\xa5' * 0x600
    uc.mem_write(spec['a_object'], sentinel)
    count = 0
    for obj in spec['objects']:
        other = spec['objects'][1] if obj == spec['objects'][0] else spec['objects'][0]
        for machine in range(10):
            model = exe.u32(spec['models'] + machine * 4)
            assert exe.off(model) is not None
            for mode in (0, 1, 3, 4):
                uc.mem_write(obj, bytes(0x600))
                uc.mem_write(other, sentinel)
                # object, opponent, mode, identity, opponent identity, side,
                # model, x, z, angle: the original ten-argument call layout.
                end = native.run(spec['init'],
                                 [obj, other, mode, machine, 0, 1, model, 0, 0, 0],
                                 {spec['initialized'], spec['zsetup'], spec['cpu_setup']})
                callback = {0: 'standard', 1: 'cpu', 3: 'alternate', 4: 'replay'}[mode]
                expected_end = spec['cpu_setup'] if mode == 1 else spec['initialized']
                if machine == 9 and mode in (0, 1):
                    callback, expected_end = 'ztick', spec['zsetup']
                assert end == expected_end, (machine, mode, hex(end))
                assert native.read_word(obj + 4) == spec[callback]
                assert native.read_word(obj + 0x64) == machine
                assert native.read_word(obj + 0x6c) == model
                assert native.read_word(obj + 0x74) == other
                assert bytes(uc.mem_read(other, 0x600)) == sentinel
                assert bytes(uc.mem_read(spec['a_object'], 0x600)) == sentinel
                count += 1
    print(f"PASS {spec['name']}: {count} native initialization dispatch cases")

    # Mode 0 takes bank zero; mode 3 takes the alternate bank. Distinct
    # sentinels ensure routing is not accidentally attributed to machine ID.
    values = (0x12345678, 0x55aa55aa, 0x87654321, 0xaa55aa55)
    for address, value in zip(spec['banks'], values):
        native.word(address, value)
    count = 0
    for obj in spec['objects']:
        other = spec['objects'][1] if obj == spec['objects'][0] else spec['objects'][0]
        for machine in range(10):
            for mode in (0, 3):
                uc.mem_write(obj, bytes(0x600))
                uc.mem_write(other, sentinel)
                native.word(obj + 0x30, mode)
                native.word(obj + 0x64, machine)
                native.run(spec['input'], [obj], {spec['input_end']})
                bank = 0 if mode == 0 else 2
                assert native.read_word(obj + 0xec) == values[bank]
                assert native.read_word(obj + 0xf0) == values[bank + 1]
                assert bytes(uc.mem_read(other, 0x600)) == sentinel
                assert bytes(uc.mem_read(spec['a_object'], 0x600)) == sentinel
                count += 1
    print(f"PASS {spec['name']}: {count} native logical input-bank cases")
    assert hashlib.md5(path.read_bytes()).hexdigest() == digest
    print('Bounded native contracts only; no movement, weapon or full-match validation claimed.')


if __name__ == '__main__':
    test(Path(sys.argv[1]))
