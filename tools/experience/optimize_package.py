"""Losslessly compress patch recipes; preserve every runtime file and recipe byte."""
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile


def compress_recipes(catalog):
    catalog = Path(catalog)
    index = json.loads((catalog / 'catalog.json').read_text())['entries']
    source = catalog / 'recipes.zip'
    with tempfile.TemporaryDirectory(dir=catalog) as temp:
        target = Path(temp) / 'recipes.zip'
        with zipfile.ZipFile(source) as old, zipfile.ZipFile(target, 'w') as new:
            if len(old.namelist()) != len(index) or set(old.namelist()) != set(index):
                raise ValueError('Recipe archive membership differs from catalog')
            for name in sorted(index):
                data = old.read(name)
                if hashlib.sha256(data).hexdigest() != index[name]['sha256']:
                    raise ValueError('Recipe checksum mismatch: ' + name)
                info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_LZMA
                new.writestr(info, data)
        with zipfile.ZipFile(target) as new:
            for name in index:
                if hashlib.sha256(new.read(name)).hexdigest() != index[name]['sha256']:
                    raise ValueError('Recompressed recipe mismatch: ' + name)
        target.replace(source)

