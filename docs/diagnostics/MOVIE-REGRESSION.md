# Controlled intro-movie investigation

The B01 intro CTD remains unresolved. Boss-disabled installed executables and
all 512 previous recipes match the published Experience release. The native
Display build difference is an isolation lead, not a confirmed cause.

`tools/experience/prepare_movie_ab.py` assembles independent local JPRE or Retail
installations from verified pristine files and the B01 package. Supply the B01
GCC artifact and LLVM payload as native inputs. Output contains original game
assets: keep it local and never upload it to GitHub or release artifacts.

The two installations differ only in `ddraw.dll`, `vodisplay.dll`, and the
integrity/recovery metadata containing their hashes. The assembler rejects
other differences. No shared mutable directories, hardlinks or DLL swapping
are used. Launch one installation at a time.

## Development evidence

Diagnostics remain Off by default. F11 → Diagnostics → Development uses the
existing preference. Local UAT also provides explicit enable/disable commands
for setting that same preference before the first movie; restart after enabling.

The passive collector writes atomic, flushed checkpoints outside the game
process. Changes are persisted immediately after observation; unchanged state
is refreshed at most every five seconds. Windows sampling remains at 500 ms.
Four bounded files retain current, previous, last completed and last incomplete
sessions. Completion means the collector observed process exit, not successful
gameplay. A missing shutdown remains `INCOMPLETE_SESSION`, not proof of a crash.

| Evidence | Classification |
|---|---|
| Recognized movie window exists / visible | OBSERVED `MOVIE_WINDOW_CREATED` / `MOVIE_VISIBLE` |
| Movie window disappears | OBSERVED `WINDOW_CLOSED_UNKNOWN` |
| Any owned top-level window is visible | OBSERVED `PROCESS_WINDOW_VISIBLE`; not proof of a game frame |
| Process handle signals exit | OBSERVED `PROCESS_EXITED_UNKNOWN`, with exit code |
| Matching Windows Application Error event | CONFIRMED `SOFTWARE_EXCEPTION_CONFIRMED` |
| Natural completion, skip request, skip confirmation | UNKNOWN: no safe internal observation point added |
| Surface release/restoration, first game frame, attract state | UNKNOWN: window visibility cannot establish these operations |

Manual bypass is never inferred from duration or disappearance. Normal and
nonzero exits are not automatically classified as normal shutdown or exception.
No raw input, global hooks, renderer callbacks or game-code hooks are added.

Windows event collection reads at most 32 recent Application Error events after
exit with a five-second timeout. It accepts only `v_on.exe`, matching process ID
and session time. Export retains exception code, fault offset and a numeric
module category: 0 unknown, 1 game, 2 ddraw, 3 vodisplay, 4 avifil32, 5 ntdll.
An event published later may be missed; missing evidence remains UNKNOWN.
There is no stack or loaded-module inventory without a dump.

WER LocalDumps setup is not installed. Its usual machine-wide registry location
requires elevated access and the executable-name scope cannot distinguish the
two installations. Existing Windows crash policy is left untouched. No dump
collection, registry writes or replacement exception handlers are introduced.
Checkpoints are the mandatory fallback.

Manual export adds sanitized `runtime-state.json` to the existing archive.
It never includes dumps, game binaries/assets, raw input, arbitrary strings,
private paths or process memory. Off stops new collection and retains prior
records for manual export. Storage is four checkpoints of less than 8 KiB each;
the existing event-log retention policy remains unchanged.

## Windows acceptance

Use a Windows desktop already set to 2560×1440. The test does not change Windows
resolution. Initial settings: bosses Off, intro On, Single Display, 16:9. The
validated internal rendering profile remains independent of physical output.

1. Enable Development explicitly in each installation, then launch `v_on.exe`.
2. Allow natural intro completion and attract mode. Do not skip during the
   primary comparison. Run each installation at least three times.
3. Export diagnostics after each run, retaining the run's archive.
4. Repeat paired tests in Dual Mirror using the same monitor assignments.
5. Separately test manual bypass and record the intentional action yourself;
   the passive collector will correctly leave the skip classification UNKNOWN.
6. Repeat representative paired tests with bosses enabled through the patcher.
   Rebuild both installations with identical options; do not hand-edit EXEs.

Record build, mode, run number, duration, complete cycles, natural/skip intent,
CTD/continuation, diagnostic completion and exception metadata. Three successes
are useful evidence, not proof against intermittent failure. Synthetic tests do
not validate Windows video decoding or establish the cause of this CTD.
