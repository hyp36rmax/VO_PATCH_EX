"""Explicit local UAT consent using the existing Diagnostics preference."""
import configparser
import sys
from pathlib import Path


def main():
    action=sys.argv[1] if len(sys.argv)>1 else ''
    if action not in ('enable','disable'):raise SystemExit('Use enable or disable')
    path=Path(__file__).resolve().parent.parent/'player-displays.ini'
    cfg=configparser.ConfigParser(interpolation=None)
    data=path.read_bytes() if path.exists() else b''
    cfg.read_string(data.decode('utf-16' if data.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig'))
    section=next((s for s in cfg.sections() if s.lower()=='diagnostics'),'Diagnostics')
    if not cfg.has_section(section):cfg.add_section(section)
    cfg.set(section,'Level','DEVELOPMENT' if action=='enable' else 'OFF')
    temp=path.with_suffix('.new')
    with temp.open('w',encoding='utf-16') as stream:cfg.write(stream)
    temp.replace(path)
    print('Development diagnostics enabled for next launch.' if action=='enable' else 'Diagnostics Off. Existing local evidence retained.')

if __name__=='__main__':main()
