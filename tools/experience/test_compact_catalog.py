"""Compact storage preserves exact recipes and rejects malformed input."""
import json
import lzma
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path
from compact_catalog import Catalog, NAME, MAGIC, encoded, digest, pack

class CompactTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.recipe = dict(original='a'*64, base='b'*64, final='c'*64,
                           size=100, writes=[[2,'1234'],[10,'abcd']], edition='jpre', mask=0)
        self.raw = encoded(self.recipe)
        self.index = {'keys':['bosses'], 'entries':{'jpre/0.json':{'sha256':digest(self.raw),'final':'c'*64}}}
        (self.root/'catalog.json').write_bytes(encoded(self.index))
        with zipfile.ZipFile(self.root/'recipes.zip','w') as z:z.writestr('jpre/0.json',self.raw)
        pack(self.root, self.root/NAME)

    def mutate(self, change):
        data=lzma.decompress((self.root/NAME).read_bytes())
        length,=struct.unpack_from('<I',data,8)
        header=json.loads(data[12:12+length]);body=bytearray(data[12+length:])
        change(header,body)
        head=encoded(header)
        (self.root/NAME).write_bytes(lzma.compress(MAGIC+struct.pack('<I',len(head))+head+body))

    def test_exact_deterministic(self):
        first=(self.root/NAME).read_bytes();pack(self.root,self.root/NAME)
        self.assertEqual(first,(self.root/NAME).read_bytes())
        self.assertEqual(Catalog(self.root).read('jpre/0.json'),self.raw)

    def test_missing_option(self):
        with self.assertRaises(ValueError):Catalog(self.root).read('jpre/1.json')

    def test_corrupt_stream_no_legacy_fallback(self):
        (self.root/NAME).write_bytes(b'broken')
        with self.assertRaises((ValueError,lzma.LZMAError)):Catalog(self.root)

    def test_overlap(self):
        self.mutate(lambda h,b:struct.pack_into('<I',b,8,3))
        with self.assertRaises(ValueError):Catalog(self.root).read('jpre/0.json')

    def test_out_of_order(self):
        self.mutate(lambda h,b:struct.pack_into('<I',b,8,0))
        with self.assertRaises(ValueError):Catalog(self.root).read('jpre/0.json')

    def test_corrupt_shared_value(self):
        self.mutate(lambda h,b:h['pool'].__setitem__(0,'ffff'))
        with self.assertRaises(ValueError):Catalog(self.root).read('jpre/0.json')

    def test_missing_entry(self):
        self.mutate(lambda h,b:h['entries'].clear())
        with self.assertRaises(ValueError):Catalog(self.root)

    def test_wrong_index(self):
        self.index['keys']=['movie'];(self.root/'catalog.json').write_bytes(encoded(self.index))
        with self.assertRaises(ValueError):Catalog(self.root)

    def test_bad_pool_id(self):
        self.mutate(lambda h,b:struct.pack_into('<I',b,4,999))
        with self.assertRaises(ValueError):Catalog(self.root).read('jpre/0.json')

    def test_wrong_mask(self):
        self.mutate(lambda h,b:h['entries']['jpre/0.json'].__setitem__('mask',1))
        with self.assertRaises(ValueError):Catalog(self.root).read('jpre/0.json')

    def test_outside_body(self):
        self.mutate(lambda h,b:h['entries']['jpre/0.json'].__setitem__('writes',[0,999]))
        with self.assertRaises(ValueError):Catalog(self.root).read('jpre/0.json')

    def test_trailing_stream(self):
        with (self.root/NAME).open('ab') as f:f.write(b'extra')
        with self.assertRaises(ValueError):Catalog(self.root)

if __name__=='__main__':unittest.main()
