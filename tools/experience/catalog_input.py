"""Compact, hash-locked offline recipes; never embeds a complete game image."""
import argparse
import lzma
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]

def digest(data):
    return hashlib.sha256(data).hexdigest()

def sources():
    paths = [ROOT / 'v-on-patcher.py', ROOT / 'tools/experience/build_catalog.py',
             ROOT / 'tools/experience/catalog_input.py', * (ROOT / 'asm').glob('*.asm'),
             * (ROOT / 'tools/dual_display').glob('*.py'),
             * (ROOT / 'tools/dual_display').glob('*.h'),
             * (ROOT / 'tools').glob('engineering*.py')]
    return {p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in sorted(paths)}

def pack(catalog, destination):
    index = json.loads((catalog / 'catalog.json').read_text())
    pool, ids, entries = [], {}, {}
    with zipfile.ZipFile(catalog / 'recipes.zip') as archive:
        for name in sorted(index['entries']):
            raw = archive.read(name)
            assert digest(raw) == index['entries'][name]['sha256']
            recipe = json.loads(raw)
            writes = []
            for offset, value in recipe['writes']:
                if value not in ids:
                    ids[value] = len(pool)
                    pool.append(value)
                writes.append([offset, ids[value]])
            recipe['writes'] = writes
            entries[name] = recipe
    data = {'sources': sources(), 'index': index, 'pool': pool, 'recipes': entries,
            'profiles': (catalog / 'game_profiles.h').read_text()}
    destination.write_bytes(lzma.compress(json.dumps(data, separators=(',', ':')).encode(), preset=9))

def unpack(source, destination):
    data = json.loads(lzma.decompress(source.read_bytes()))
    assert data['sources'] == sources(), 'Catalog source drift: regenerate and validate offline'
    assert data['index']['keys'] == ['hires', 'padxinput', 'nodisc', 'debugbox', 'defaults', 'sound', 'movie', 'credits', 'bosses', 'bossunlock']
    expected = {f'{edition}/{mask}.json' for edition in ('retail', 'jpre') for mask in range(1 << len(data['index']['keys']))}
    assert set(data['recipes']) == set(data['index']['entries']) == expected
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(destination / 'recipes.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, recipe in data['recipes'].items():
            recipe['writes'] = [[offset, data['pool'][i]] for offset, i in recipe['writes']]
            assert sum(len(bytes.fromhex(value)) for _, value in recipe['writes']) < recipe['size']
            raw = json.dumps(recipe, separators=(',', ':')).encode()
            assert digest(raw) == data['index']['entries'][name]['sha256'], name
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, raw)
    (destination / 'catalog.json').write_text(json.dumps(data['index'], indent=2) + '\n')
    (destination / 'game_profiles.h').write_text(data['profiles'])
    print('PASS source-locked catalog:', len(expected), 'sparse recipes')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('pack', 'unpack'))
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    (pack if args.mode == 'pack' else unpack)(args.source, args.destination)
