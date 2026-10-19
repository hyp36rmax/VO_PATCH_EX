"""Find instruction-shape candidates for native boss adapters, without patching.

A match is not proof of player ownership or a safe hook continuation. In
particular, absolute relocations and branch destinations are masked; callers,
object lifetimes and side effects still require separate verification.
"""
import argparse
import bisect
import hashlib
import json
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import selftest
import vomap


def audit(path):
    v = selftest.load_patcher()
    digest = hashlib.md5(path.read_bytes()).hexdigest()
    if digest not in v.BUILDS:
        raise ValueError('Expected a recognized pristine executable')
    build = v.BUILDS[digest]
    exe = vomap.Exe(str(path))
    text = exe.d[exe.off(exe.text_lo):exe.off(exe.text_hi)]
    relocations = sorted(exe.relocs)
    symbols = {}
    for name, address in build.symbols.items():
        if not name.startswith('BS_') or not isinstance(address, int):
            continue
        if not exe.text_lo <= address < exe.text_hi:
            continue
        raw = exe.d[exe.off(address):exe.off(address) + 128]
        instructions = list(vomap.md.disasm(raw, address))[:16]
        if len(instructions) < 6:
            continue
        size = instructions[-1].address + instructions[-1].size - address
        mask = set()
        for insn in instructions:
            begin = bisect.bisect_left(relocations, insn.address)
            end = bisect.bisect_left(relocations, insn.address + insn.size)
            for relocation in relocations[begin:end]:
                mask.update(range(relocation-address, relocation-address+4))
            if insn.group(vomap.capstone.CS_GRP_JUMP) or insn.group(vomap.capstone.CS_GRP_CALL):
                if insn.imm_size:
                    offset = insn.address-address+insn.imm_offset
                    mask.update(range(offset, offset+insn.imm_size))
        pattern = b''.join(b'.' if i in mask else re.escape(bytes([raw[i]])) for i in range(size))
        matches = [exe.text_lo + match.start() for match in re.finditer(b'(?=('+pattern+b'))', text, re.S)]
        assert address in matches, (build.short, name)
        symbols[name] = {'source': hex(address), 'window_size': size,
                         'instruction_count': len(instructions),
                         'candidates': [hex(a) for a in matches if a != address]}
    assert hashlib.md5(path.read_bytes()).hexdigest() == digest
    return {'edition': build.short, 'original_md5': digest,
            'status': 'NEEDS VALIDATION: candidate addresses, not verified B adapters',
            'symbols': symbols}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = audit(args.original)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(result['edition'], len(result['symbols']), 'code windows; executable unchanged')


if __name__ == '__main__':
    main()
