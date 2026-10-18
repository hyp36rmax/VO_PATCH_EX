"""Prove module reuse leaves generated profile images unchanged."""
from functools import cache
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'dual_display'))
import startup_image as si
fresh = si.mode_profiles.engineering3840.load_private
for folder in map(Path, sys.argv[1:]):
    raw = (folder/'v_on.exe').read_bytes()
    v = fresh()
    wanted = dict(v.default_state(), bosses=True)
    si.mode_profiles.engineering3840.load_private = fresh
    uncached, _ = si.build(raw, wanted)
    si.mode_profiles.engineering3840.load_private = cache(fresh)
    shared, _ = si.build(raw, wanted)
    again, _ = si.build(raw, wanted)
    assert uncached == shared == again, folder
    print('PASS fresh/shared/repeated private generator identity:',folder,flush=True)
si.mode_profiles.engineering3840.load_private = fresh
