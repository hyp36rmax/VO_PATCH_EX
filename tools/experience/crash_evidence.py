"""Read bounded Windows Application Error metadata; never enable dumps or upload."""
import datetime
import subprocess
import xml.etree.ElementTree as ET


def parse(text, pid, started_ms):
    try: root = ET.fromstring('<Events>'+text+'</Events>')
    except ET.ParseError: return None
    for event in root:
        def elements(name): return [e for e in event.iter() if e.tag.split('}')[-1] == name]
        data = {e.attrib.get('Name'): e.text or '' for e in elements('Data')}
        try:
            provider = elements('Provider')[0].attrib.get('Name')
            stamp = elements('TimeCreated')[0].attrib['SystemTime']
            when = datetime.datetime.fromisoformat(stamp.replace('Z', '+00:00')).timestamp()*1000
            process = int(data.get('ProcessId', ''), 0)
            code = int(data.get('ExceptionCode', ''), 16)
            offset = int(data.get('FaultingOffset', ''), 16)
        except (ValueError, KeyError, IndexError): continue
        if provider != 'Application Error' or process != pid or when < started_ms: continue
        if data.get('AppName', '').lower() != 'v_on.exe': continue
        module = {'v_on.exe': 1, 'ddraw.dll': 2, 'vodisplay.dll': 3,
                  'avifil32.dll': 4, 'ntdll.dll': 5}.get(data.get('ModuleName', '').lower(), 0)
        return {'exception_code': code, 'fault_offset': offset, 'fault_module': module}
    return None


def collect(pid, started_ms):
    try:
        result = subprocess.run(['wevtutil.exe', 'qe', 'Application',
            '/q:*[System[(EventID=1000)]]', '/c:32', '/rd:true', '/f:xml'],
            capture_output=True, timeout=5, creationflags=0x08000000, check=False)
        if result.returncode or len(result.stdout)>262144: return None
        return parse(result.stdout.decode('utf-8-sig', errors='replace'), pid, started_ms)
    except (OSError, subprocess.TimeoutExpired): return None
