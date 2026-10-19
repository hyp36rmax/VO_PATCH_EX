"""Local, bounded diagnostics API v1. No game hooks, raw input or uploads.

Future callers use event(root, name, numeric_fields) and export(root). Free-form
module text is never copied: adapters project only named numeric fields.
"""
import configparser
import datetime
import json
import os
from pathlib import Path
import re
import zipfile

LIMIT = 256 * 1024
ROTATIONS = 3
LEVELS = ('OFF', 'NORMAL', 'DETAILED', 'DEVELOPMENT')
EVENTS = {'startup', 'shutdown', 'module_init', 'controller_discovery',
          'display_discovery', 'configuration', 'selection', 'presentation',
          'movie', 'warning', 'error', 'recovery', 'previous_session_incomplete'}
FIELDS = set('code count mode profile fallback player device type vid pid width height '
             'primary uploads draw_frames presented_pairs complete_mirror mirror_p1 '
             'strict_test_stopped classified transitions recorded capture elapsed_ms '
             'exit_known exit_code samples truncated io_error ok targets visible '
             'movie_p1_present_suppressed primary_only local_vs_shared local_vs_gameplay '
             'unknown connected xinput_slot stage level module hr movie_events event reason result tick restore_pending previous_p1_visible selected_mode effective_mode secondary f4_state split_preference restart_required save_stage winerror source_width source_height picture_verified picture_x picture_y picture_width picture_height geometry_fallback framing_enabled display_x display_y display_width display_height expected_x expected_y expected_width expected_height window_index window_x window_y window_width window_height geometry_match'.split())
CONFIG_KEYS = {'mode', 'gameaspect', 'mirrorplayer1', '1p device no.', '2p device no.',
               '1p deadzone', '2p deadzone', '1p padtype', '2p padtype', 'scrsize', 'sshoriz'}
LOGS = {'selection': 'selection.txt', 'presentation': 'game/D04-P02B-presentation.log',
        'movie': 'movie-windows.log'}


def level(root):
    """One existing authority; malformed/missing preferences fail closed."""
    ini = configparser.ConfigParser(interpolation=None)
    try:
        data=(Path(root) / 'player-displays.ini').read_bytes()
        if len(data)>LIMIT:return 0
        ini.read_string(data.decode('utf-16' if data.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig'))
        section=next((s for s in ini.sections() if s.lower()=='diagnostics'), 'Diagnostics')
        value = ini.get(section, 'Level', fallback='OFF').strip()
        return LEVELS.index(value) if value in LEVELS else 0
    except (OSError, UnicodeError, configparser.Error):
        return 0


def permitted(root, name):
    required = (1 if name in {'startup', 'shutdown', 'warning', 'error', 'recovery',
                             'previous_session_incomplete'} else
                3 if name == 'movie' else 2)
    return level(root) >= required


def numbers(fields):
    # Reject strings entirely, including numeric-looking identifiers/serials.
    return {k: v for k, v in fields.items() if k in FIELDS and type(v) in (int, bool)
            and -2**63 <= v < 2**64}


def rotate(path):
    path = Path(path)
    if not path.exists():
        return
    for i in range(ROTATIONS, 0, -1):
        source = path if i == 1 else Path(str(path) + f'.{i-1}')
        target = Path(str(path) + f'.{i}')
        if source.exists():
            os.replace(source, target)


def event(root, name, fields=None):
    if name not in EVENTS:
        raise ValueError('Unknown event')
    if not permitted(root, name):
        return
    record = {'event': name, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'fields': numbers(fields or {})}
    data = (json.dumps(record, sort_keys=True) + '\n').encode()
    path = Path(root) / 'diagnostics/events.jsonl'
    path.parent.mkdir(exist_ok=True)
    if path.exists() and path.stat().st_size + len(data) > LIMIT:
        return  # bounded collection; retain existing player logs
    with path.open('ab') as stream:
        stream.write(data)
        stream.flush()  # each event survives an unclean process exit


def read_bounded(path):
    with Path(path).open('rb') as stream:
        data = stream.read(LIMIT)
        if stream.read(1):
            stream.seek(-LIMIT//2, 2)
            data = data[:LIMIT//2] + b'\n' + stream.read(LIMIT//2)
        return data.decode('utf-8', errors='replace')


def project(text, limit=256):
    result = []
    for line in text.splitlines():
        line = re.sub(r'"[^"]*"', '', line)
        fields = {}
        for key, value in re.findall(r'\b([a-z_]+)=(-?(?:0x[0-9a-fA-F]+|[0-9]+))(?=\s|$)', line):
            if key in FIELDS:
                try:
                    fields[key] = int(value, 16 if '0x' in value else 10)
                except ValueError:
                    pass
        if fields:
            result.append(numbers(fields))
            if len(result) >= limit:
                break
    return result


def configurations(root, game_directory=None):
    result = {}
    for name in ('v_on.ini', 'player-displays.ini', 'session-display.ini'):
        path = (Path(game_directory) if game_directory is not None else Path(root) / 'game') / name
        if not path.is_file():
            continue
        # Original game INI may have no sections. Never export arbitrary strings.
        values = {}
        for line in read_bounded(path).splitlines():
            key, sep, value = line.partition('=')
            if sep and key.strip().lower() in CONFIG_KEYS and re.fullmatch(r'-?\d{1,6}', value.strip()):
                values[key.strip().lower()] = int(value)
        result[name] = values
    return result


def safe_events(path):
    result = []
    for line in read_bounded(path).splitlines():
        try:
            row = json.loads(line)
            if row.get('event') in EVENTS:
                # Do not trust an edited local log's free-form timestamp/fields.
                result.append({'event': row['event'], 'fields': numbers(row.get('fields', {}))})
        except (ValueError, TypeError, AttributeError):
            continue
    return result


def export(root, *, game_directory=None, return_name="RETURN-THIS-VO-PATCH-EX-G03.zip"):
    """Return verified archive path; failure never removes raw logs or old ZIP."""
    root = Path(root)
    if return_name not in ('RETURN-THIS-VO-PATCH-EX-G03.zip', 'RETURN-THIS-VO-PATCH-EX-F01-P02.zip', 'RETURN-THIS-VO-PATCH-EX-F01-P03.zip', 'RETURN-THIS-VO-PATCH-EX-F01-P04.zip', 'RETURN-THIS-VO-PATCH-EX-F01-P04-F02.zip'):
        raise ValueError('Unsupported diagnostic return name')
    if not any((root / ('diagnostics/events.jsonl' + suffix)).is_file()
               for suffix in ('', '.1', '.2', '.3')) and not any(
                   (root / name).is_file() for name in LOGS.values()):
        raise ValueError('No diagnostic records are available. Logging remains disabled unless you enable it in F11.')
    now = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    destination = root / f'VO-PATCH-EX-Diagnostics-{now}.zip'
    temp = root / 'diagnostics-export.new'
    reports = {}
    for kind, name in LOGS.items():
        path = (Path(game_directory) / name.removeprefix('game/')) if game_directory is not None and name.startswith('game/') else root / name
        reports[kind] = project(read_bounded(path)) if path.is_file() else []
    events = []
    for suffix in ('.3', '.2', '.1', ''):
        path = root / ('diagnostics/events.jsonl' + suffix)
        if path.is_file():
            events.extend(safe_events(path))
    meta_path = root / 'experience-version.json'
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    # Strict metadata allowlist and formats; no arbitrary user-edited data.
    versions = {k: v for k, v in meta.items() if k in ('revision', 'wrapper_sha256', 'helper_sha256')
                and isinstance(v, str) and re.fullmatch('[0-9a-f]{40}|[0-9a-f]{64}', v)}
    versions['experience'] = meta.get('experience') if meta.get('experience') in ('F01-P04-private', 'F01-P04-F01-private', 'F01-P04-F02-private', 'B01-F02-private') else '0.1-dev'; versions['diagnostics_schema'] = 1
    versions['controller'] = 'Controller-Expansion'; versions['display'] = 'F01-P04' if meta.get('display')=='F01-P04' else 'F04B'
    if meta.get('game') in ('retail','jpre'):versions['game']=meta['game']
    prepared = root / 'prepared.json'
    if prepared.is_file():
        edition = json.loads(prepared.read_text()).get('edition')
        if edition in ('retail', 'jpre'):
            versions['game'] = edition
    import runtime_checkpoint
    payload = {'runtime-state.json': runtime_checkpoint.exported(root), 'summary.json': {'versions': versions, 'physical_acceptance': 'PENDING',
                               'missing_module_logs': [k for k, v in reports.items() if not v],
                               'warnings': [e for e in events if e['event'] in ('warning', 'error', 'recovery', 'previous_session_incomplete')],
                               'assignment_evidence': 'saved configuration only; runtime ownership not inferred'},
               'events.json': events, 'module-logs.json': reports,
               'configuration.json': configurations(root, game_directory)}
    try:
        with zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name, data in payload.items():
                archive.writestr(name, json.dumps(data, indent=2))
        with zipfile.ZipFile(temp) as archive:
            if archive.testzip() or set(archive.namelist()) != set(payload):
                raise ValueError('Export verification failed')
        os.replace(temp, destination)
        # Keep a bounded history plus an obvious stable return filename.
        import shutil
        stable = root / return_name
        shutil.copyfile(destination, root / 'return.new')
        os.replace(root / 'return.new', stable)
        # Player-owned evidence is retained until explicitly deleted.
        return stable
    finally:
        if temp.exists():
            temp.unlink()
