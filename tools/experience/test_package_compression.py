"""Check lossless recipe compression and refusal of corrupt package inputs."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from optimize_package import compress_recipes


class RecipeCompression(unittest.TestCase):
    def test_lossless_and_reproducible(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            values = {'retail/0.json': b'{"writes":[]}', 'jpre/0.json': b'{"writes":[[1,"ff"]]}'}
            index = {name: {'sha256': hashlib.sha256(data).hexdigest()} for name, data in values.items()}
            (root/'catalog.json').write_text(json.dumps({'entries': index}))
            with zipfile.ZipFile(root/'recipes.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
                for name, data in values.items():
                    archive.writestr(name, data)
            compress_recipes(root)
            first = (root/'recipes.zip').read_bytes()
            with zipfile.ZipFile(root/'recipes.zip') as archive:
                self.assertEqual({name: archive.read(name) for name in archive.namelist()}, values)
                self.assertTrue(all(i.compress_type == zipfile.ZIP_LZMA for i in archive.infolist()))
            compress_recipes(root)
            self.assertEqual(first, (root/'recipes.zip').read_bytes())
            index['retail/0.json']['sha256'] = 'invalid'
            (root/'catalog.json').write_text(json.dumps({'entries': index}))
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                compress_recipes(root)
            self.assertEqual(first, (root/'recipes.zip').read_bytes())
            index.pop('retail/0.json')
            (root/'catalog.json').write_text(json.dumps({'entries': index}))
            with self.assertRaisesRegex(ValueError, 'membership'):
                compress_recipes(root)
            self.assertEqual(first, (root/'recipes.zip').read_bytes())


if __name__ == '__main__':
    unittest.main()
