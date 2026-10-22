"""Source-locked recipes with shared values and bounded binary write lists."""
import hashlib
import json
import lzma
import struct
import zipfile
from pathlib import Path

MAGIC = b'VOEXCAT1'
LIMIT = 128 * 1024 * 1024
HEADER_LIMIT = 4 * 1024 * 1024
NAME = 'recipes.bin.xz'


def encoded(value):
    return json.dumps(value, separators=(',', ':')).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pack(source, destination):
    """Build from verified legacy recipes; never generate new patch bytes."""
    source, destination = Path(source), Path(destination)
    index = json.loads((source / 'catalog.json').read_text())
    pool, ids, entries, lists = [], {}, {}, {}
    body = bytearray()
    with zipfile.ZipFile(source / 'recipes.zip') as archive:
        if set(archive.namelist()) != set(index['entries']):
            raise ValueError('Catalog membership mismatch')
        for name in sorted(index['entries']):
            raw = archive.read(name)
            if digest(raw) != index['entries'][name]['sha256']:
                raise ValueError('Recipe integrity failure')
            recipe = json.loads(raw)
            records = bytearray()
            for offset, value in recipe['writes']:
                if value not in ids:
                    ids[value] = len(pool)
                    pool.append(value)
                records.extend(struct.pack('<II', offset, ids[value]))
            key = bytes(records)
            if key not in lists:
                lists[key] = len(body)
                body.extend(records)
            recipe['writes'] = [lists[key], len(records) // 8]
            entries[name] = recipe
    header = encoded({'index': digest(encoded(index)), 'pool': pool, 'entries': entries})
    if len(header) > HEADER_LIMIT or 12 + len(header) + len(body) > LIMIT:
        raise ValueError('Catalog exceeds format limits')
    data = MAGIC + struct.pack('<I', len(header)) + header + body
    destination.write_bytes(lzma.compress(data, preset=9))


class Catalog:
    def __init__(self, folder, index=None):
        self.folder = Path(folder)
        self.index = index or json.loads((self.folder / 'catalog.json').read_text())
        self.data = None
        path = self.folder / NAME
        if path.exists():
            if path.stat().st_size > LIMIT:
                raise ValueError('Compressed catalog exceeds limit')
            decoder = lzma.LZMADecompressor(memlimit=256 * 1024 * 1024)
            data = decoder.decompress(path.read_bytes(), max_length=LIMIT + 1)
            if len(data) > LIMIT or not decoder.eof or decoder.unused_data:
                raise ValueError('Invalid catalog size or stream')
            if data[:8] != MAGIC or len(data) < 12:
                raise ValueError('Invalid catalog format')
            length, = struct.unpack_from('<I', data, 8)
            if length > HEADER_LIMIT or 12 + length > len(data):
                raise ValueError('Invalid catalog header')
            header = json.loads(data[12:12 + length])
            if header['index'] != digest(encoded(self.index)):
                raise ValueError('Catalog index mismatch')
            if set(header['entries']) != set(self.index['entries']):
                raise ValueError('Catalog membership mismatch')
            self.pool = header['pool']
            self.entries = header['entries']
            self.data = data
            self.start = 12 + length

    def read(self, name):
        if name not in self.index['entries']:
            raise ValueError('Unsupported recipe')
        if self.data is None:
            # Offline generation and existing regression fixtures retain legacy input.
            with zipfile.ZipFile(self.folder / 'recipes.zip') as archive:
                raw = archive.read(name)
        else:
            recipe = dict(self.entries[name])
            offset, count = recipe['writes']
            if type(offset) is not int or type(count) is not int or min(offset, count) < 0 or offset % 8:
                raise ValueError('Invalid write list')
            end = self.start + offset + count * 8
            if end > len(self.data):
                raise ValueError('Write list outside catalog')
            writes = []
            previous = 0
            for pos in range(self.start + offset, end, 8):
                target, value_id = struct.unpack_from('<II', self.data, pos)
                if value_id >= len(self.pool):
                    raise ValueError('Invalid shared value')
                value = self.pool[value_id]
                block = bytes.fromhex(value)
                if not block or target < previous or target + len(block) > recipe['size']:
                    raise ValueError('Overlapping or invalid recipe writes')
                previous = target + len(block)
                writes.append([target, value])
            recipe['writes'] = writes
            raw = encoded(recipe)
        entry = self.index['entries'][name]
        if digest(raw) != entry['sha256']:
            raise ValueError('Recipe integrity failure')
        recipe = json.loads(raw)
        if name != f"{recipe['edition']}/{recipe['mask']}.json" or recipe['final'] != entry['final']:
            raise ValueError('Recipe option identity mismatch')
        return raw
