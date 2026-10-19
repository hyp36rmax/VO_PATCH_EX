# Local VS boss execution boundaries

**Implementation status: incomplete.** Local VS bosses are not enabled, and no
playable B03 candidate is available. This record and its tools establish native
boundaries that must be resolved before exposing the optional feature.

Frozen B02: `b6518d3f3c0777335fbb2100c1b99e8304797d2b`.
Development branch: `feature/playable-bosses-local-vs`, directly from B02.
Upstream single-player implementation remains Pairomaniac and Vortyne's work;
hyp36rmax maintains the VO PATCH EX integration and expansions.

## Native evidence

`tools/bosses/test_local_vs_boundary.py` executes the actual linked B02 routines
in Unicorn, preserving register and stack checks. These are tests of the existing
boundary, not evidence that a Local VS extension works.

| Boundary | Result |
|---|---|
| `selmax_a` | VERIFIED: both cursor indices allow boss positions only in mode 0. Local mode 1 and network mode 2 retain the bound of seven. |
| `zfire_a` | VERIFIED: the A player object uses either decoded turbo edge (`0xff`); a held value does not retrigger. |
| B object input through `zfire_a` | VERIFIED: turbo edges on the known B object candidates do not take the A player special-attack path. This fixture does not establish which candidate owns P2 in every runtime state. |
| Four editions | VERIFIED: linked-code fixtures run for Retail, JPRE, OEM and JP. The B object candidate checks use Retail/JPRE addresses only. No pristine OEM/JP execution or physical gameplay is claimed. |

The game has two engine copies, each with a subject/opponent pair. An engine
copy is not a permanent human-player identity. The A opponent object is not the
B controlled object. Player role and camera state can select different members
of each pair. A safe extension must identify both engine and object ownership.

## Candidate mapping

`tools/bosses/local_vs_audit.py` scans recognized pristine executables without
writing them. It compares 16-instruction windows, masking relocations and branch
destinations. Every source window must match its original location. A candidate
is **NEEDS VALIDATION**, even if unique: caller reachability, operand ownership,
stack continuation and resource lifetime are not proved by opcode similarity.

Retail and JPRE each expose 93 inspected code windows; 54 have one alternate
match. Selected findings:

| Native boundary | Retail candidates | JPRE candidates | Status |
|---|---|---|---|
| AI tick continuation | `4c736f`, `4c7435`, `5b8c0b` | `4c4f0f`, `4c4fd5`, `5b35e3` | UNKNOWN owner; three matches each |
| Model-clone continuation | `468e79`, `4eb949`, `5773b3` | `467ebd`, `4e89cd`, `57269f` | UNKNOWN owner; three matches each |
| Z-Gradt draw entry | None in this comparison | None in this comparison | UNKNOWN; absence of a pattern match does not mean the game lacks the routine |
| Clip bank 0 continuation | `4c5798` | `4c33c0` | NEEDS VALIDATION |
| Clip bank 3 continuation | `4c57b2` | `4c33da` | NEEDS VALIDATION |

Addresses are native virtual addresses, not file offsets. There is no assumed
constant A-to-B or cross-edition delta.

## Resource contracts still requiring implementation

The existing boss flag, palette owner, model clone, AI bank, temporary state,
laser lock-on, gauge state and replay sidecar are single-player state. Z-Gradt's
banking/model-copy paths are guarded by the final-stage/player conditions; they
are not a demonstrated arbitrary-arena, two-human implementation.

The following contracts remain UNKNOWN or NEEDS VALIDATION:

1. B initialization, draw, weapon/update and cleanup entry/exit contracts.
2. Which engine/object pair owns each human input in selection, fight and replay.
3. Per-object AI/model/palette/event storage and the lifetime of shared assets.
4. Simultaneous laser state and complete replay save/restore boundaries.
5. P2 boss camera/HUD/animation and round-result paths.

Selection-only unlocking is UNSUITABLE: it bypasses the existing guard without
repairing these dependencies. No guessed hook, second copy of the complete boss
implementation, placeholder option or unverified generated recipe was added.

## Remaining B03 scope

After those adapters are verified, add one independently optional local-mode
extension requiring Playable Bosses. Mode 0 must retain B02 unlocks and behavior;
mode 2 must retain the original online behavior. Mode 1 must allow the original
eight, Jaguarandi and Z-Gradt for either player without unlock requirements.

All eight required orientations remain NEEDS VALIDATION: Jaguarandi/standard,
standard/Jaguarandi, Z-Gradt/standard, standard/Z-Gradt, Jaguarandi/Jaguarandi,
Jaguarandi/Z-Gradt, Z-Gradt/Jaguarandi and Z-Gradt/Z-Gradt. No balancing, damage
scaling or artificial weapon restrictions are permitted.

The existing 512 boss-free and 2,048 B02 catalog entries remain untouched.
Controller assignments, F7, movie ownership, display modes, networking,
Apply/Restore and saved progression remain unchanged. A B03 UAT ZIP must only
be assembled once the native extension and its tests exist; renaming B02 would
not provide a Local VS test candidate.
