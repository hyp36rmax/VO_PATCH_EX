"""Preserve every pre-boss recipe identity and verify pre-unlock byte aliases."""
import json
import lzma
from pathlib import Path
import subprocess
ROOT = Path(__file__).resolve().parents[2]
BASE = '6b22b0dcd490eec8b6a3e953d881649e74ab26cb'
PATH = 'tools/experience/ci/catalog.json.xz'
old = json.loads(lzma.decompress(subprocess.check_output(['git','show',BASE+':'+PATH],cwd=ROOT)))
new = json.loads(lzma.decompress((ROOT/PATH).read_bytes()))
assert new['index']['keys'] == old['index']['keys'] + ['bosses','bossunlock']
def expanded(data, name):
    row = dict(data['recipes'][name])
    row['writes'] = [[offset, data['pool'][i]] for offset,i in row['writes']]
    return row
for name in old['recipes']:
    assert expanded(old,name) == expanded(new,name), name
    assert old['index']['entries'][name] == new['index']['entries'][name], name
old_rows = {line.rstrip(',') for line in old['profiles'].splitlines() if line.startswith('{0x')}
new_rows = {line.rstrip(',') for line in new['profiles'].splitlines() if line.startswith('{0x')}
assert old_rows <= new_rows
for edition in ('retail','jpre'):
    for mask in range(512):
        original = expanded(new,f'{edition}/{mask}.json')
        alias = expanded(new,f'{edition}/{mask+512}.json')
        assert dict(original,mask=mask+512) == alias, (edition,mask)
print('PASS all 512 existing recipes and wrapper identities preserved; 1024 pre-unlock aliases verified')
