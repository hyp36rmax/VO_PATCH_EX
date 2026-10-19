"""Bounded passive Development checkpoints; no render callbacks or input hooks."""
import datetime
import json
import os
import time
import uuid
from pathlib import Path
import diagnostics

FILES = ('current.json', 'previous.json', 'last-completed.json', 'last-incomplete.json')
STATES = {'UNKNOWN', 'PROCESS_RUNNING', 'MOVIE_WINDOW_CREATED', 'MOVIE_VISIBLE',
          'WINDOW_CLOSED_UNKNOWN', 'PROCESS_TERMINATED', 'PROCESS_WINDOW_VISIBLE'}
RESULTS = {'UNKNOWN', 'NATURAL_COMPLETION', 'MANUAL_SKIP_REQUESTED',
           'MANUAL_SKIP_CONFIRMED', 'WINDOW_CLOSED_UNKNOWN', 'PROCESS_TERMINATED',
           'SOFTWARE_EXCEPTION_CONFIRMED', 'NORMAL_EXIT', 'INCOMPLETE_SESSION',
           'PROCESS_EXITED_UNKNOWN', 'EXTERNAL_TERMINATION_CONFIRMED'}
NUMBERS = {'elapsed_ms', 'timestamp_ms', 'process_id', 'display_mode', 'movie_visible',
           'exception_code', 'fault_offset', 'fault_module', 'process_window_visible', 'exit_code', 'error_code', 'process_running', 'complete'}


def sanitize(row):
    """Project edited checkpoints too; never export arbitrary strings or paths."""
    out = {k: v for k, v in row.items() if k in NUMBERS and type(v) in (int, bool)
           and -2**63 <= v < 2**64}
    for k in ('state', 'previous_state', 'presentation'):
        if row.get(k) in STATES: out[k] = row[k]
    for k in ('movie_result', 'termination'):
        if row.get(k) in RESULTS: out[k] = row[k]
    token = row.get('session', '')
    if isinstance(token, str) and len(token) == 32 and all(c in '0123456789abcdef' for c in token):
        out['session'] = token
    out['evidence'] = 'CONFIRMED' if row.get('termination') == 'SOFTWARE_EXCEPTION_CONFIRMED' else 'OBSERVED'
    return out


def read(path):
    try:
        with Path(path).open('rb') as stream: data = stream.read(8193)
        if len(data) > 8192: return {}
        row = json.loads(data)
        return sanitize(row) if isinstance(row, dict) else {}
    except (OSError, ValueError): return {}


def write(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.new')
    with temp.open('w', encoding='utf-8') as stream:
        json.dump(sanitize(row), stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def exported(root):
    folder = Path(root)/'diagnostics/runtime-state'
    return {name: read(folder/name) for name in FILES if (folder/name).is_file()}


class Checkpoints:
    def __init__(self, root, pid, mode=-1, clock=time.monotonic):
        self.root = Path(root)
        self.folder = self.root/'diagnostics/runtime-state'
        self.clock = clock
        self.started = clock()
        self.last = -10.0
        self.row = dict(session=uuid.uuid4().hex, process_id=pid, display_mode=mode,
                        state='UNKNOWN', previous_state='UNKNOWN', presentation='UNKNOWN',
                        movie_result='UNKNOWN', termination='UNKNOWN', movie_visible=False,
                        process_running=True, complete=False)
        if diagnostics.level(root) == 3:
            prior = read(self.folder/'current.json')
            if prior and not prior.get('complete'):
                prior['termination'] = 'INCOMPLETE_SESSION'
                write(self.folder/'last-incomplete.json', prior)
            self.update('PROCESS_RUNNING')

    def update(self, state, **fields):
        if diagnostics.level(self.root) != 3: return
        now = self.clock()
        candidate = dict(self.row, **fields, state=state)
        if candidate == self.row and now-self.last < 5: return
        candidate['previous_state'] = self.row['state']
        candidate['elapsed_ms'] = max(0, int((now-self.started)*1000))
        candidate['timestamp_ms'] = int(datetime.datetime.now(datetime.timezone.utc).timestamp()*1000)
        old = read(self.folder/'current.json')
        if old: write(self.folder/'previous.json', old)
        write(self.folder/'current.json', candidate)
        self.row = sanitize(candidate)
        self.last = now

    def windows(self, count, visible, process_window_visible=False):
        state = ('MOVIE_VISIBLE' if visible else 'MOVIE_WINDOW_CREATED' if count else
                 'WINDOW_CLOSED_UNKNOWN' if self.row['state'] in ('MOVIE_VISIBLE', 'MOVIE_WINDOW_CREATED')
                 else 'PROCESS_WINDOW_VISIBLE' if process_window_visible else self.row['state'])
        result = 'WINDOW_CLOSED_UNKNOWN' if state == 'WINDOW_CLOSED_UNKNOWN' else self.row['movie_result']
        self.update(state, movie_visible=bool(visible), process_window_visible=bool(process_window_visible),
                    presentation='UNKNOWN', movie_result=result)

    def exited(self, code, exception=None):
        # Even zero does not establish the game's normal shutdown path.
        self.update('PROCESS_TERMINATED', exit_code=code, process_running=False,
                    complete=True, termination='SOFTWARE_EXCEPTION_CONFIRMED' if exception else 'PROCESS_EXITED_UNKNOWN',
                    **(exception or {}))
        if diagnostics.level(self.root) == 3:
            write(self.folder/'last-completed.json', self.row)
