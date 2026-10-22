"""Execute frozen boss entry points; distinguish SP guarantees from VS support.

These are evidence fixtures for B03, not tests of an implemented VS extension.
They deliberately preserve B02's existing behavior until verified replacements
are available. No game files are patched or copied.
"""
from pathlib import Path
import struct
import sys
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EBP, UC_X86_REG_ESP, UC_X86_REG_EFLAGS
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import selftest

v = selftest.load_patcher()
STACK = 0x10000000
STOP = 0x11000000
B_OBJECTS = {'retail': (0x01ef8ab0, 0x01ef9f60),
             'jpre': (0x01ef5450, 0x01ef5ad0)}

class Fixture:
    def __init__(self, build):
        self.build = build
        self.uc = Uc(UC_ARCH_X86, UC_MODE_32)
        self.pages = set()
        self.base = v.cave_va('BOSSES', build)
        self.labels = v.BLOBS['BOSSES'][2]
        blob = v.link('BOSSES', build)
        self.write(self.base, blob)
        self.write(STACK, bytes(4096))
        self.write(STOP, b'\x90')

    def write(self, address, data):
        for page in range(address & ~4095, (address + len(data) + 4095) & ~4095, 4096):
            if page not in self.pages:
                self.uc.mem_map(page, 4096)
                self.pages.add(page)
        self.uc.mem_write(address, data)

    def word(self, address, value):
        self.write(address, struct.pack('<I', value))

    def run(self, name, eax=0, obj=0):
        self.word(STACK + 2048, STOP)
        self.word(STACK + 1032, obj)
        self.uc.reg_write(UC_X86_REG_ESP, STACK + 2048)
        self.uc.reg_write(UC_X86_REG_EBP, STACK + 1024)
        self.uc.reg_write(UC_X86_REG_EAX, eax)
        self.uc.reg_write(UC_X86_REG_ECX, 0x55667788)
        self.uc.emu_start(self.base + self.labels[name], STOP, count=1000)
        assert self.uc.reg_read(UC_X86_REG_ESP) == STACK + 2052
        return self.uc.reg_read(UC_X86_REG_ECX), self.uc.reg_read(UC_X86_REG_EFLAGS)

for build in v.BUILDS.values():
    f = Fixture(build)
    f.word(f.base + f.labels['boss'], 9)
    a = build.symbols['BS_OBJA']
    f.write(a, bytes(0x200))
    f.write(a + 0x142, b'\xff\x00')
    assert f.run('zfire_a', obj=a)[0] == 255
    f.write(a + 0x142, b'\x00\xff')
    assert f.run('zfire_a', obj=a)[0] == 255
    f.write(a + 0x142, b'\xfe\x00')
    assert f.run('zfire_a', obj=a)[0] != 255
    # The SP hook accepts only the A object, not the other native engine.
    for b in B_OBJECTS.get(build.short, ()):
        f.write(b, bytes(0x200))
        f.write(b + 0x142, b'\xff\xff')
        assert f.run('zfire_a', obj=b)[0] == 0
        assert bytes(f.uc.mem_read(a + 0x142, 2)) == b'\xfe\x00'
    for mode in (0, 1, 2):
        f.word(build.symbols['GAMEMODE'], mode)
        f.word(f.base + f.labels['unl_level'], 2)
        for player_index in (0, 21):
            f.word(build.symbols['BS_SELCUR'] + player_index * 4, 8)
            ecx, flags = f.run('selmax_a', eax=player_index)
            assert ecx == 0x55667788
            # cmp cursor, bound: 8 < 9 only for single-player mode.
            assert bool(flags & 1) == (mode == 0)
    print('PASS frozen selection/laser native boundaries:', build.short)
print('VERIFIED: B02 SP laser and selection contracts. Local VS is NOT implemented by these fixtures.')
