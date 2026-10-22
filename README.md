# VO PATCH EX

VO PATCH EX is an expanded version of [Pairomaniac's V-On Patcher](https://github.com/pairomaniac/v-on-patcher)
for the original 1997 Windows release of *Cyber Troopers Virtual-On*. Maintained
by [hyp36rmax](https://github.com/hyp36rmax/VO_PATCH_EX), it adds dedicated Twin-Stick
support and configurable single- and dual-monitor presentation so original arcade
controllers and modern displays can be used with the existing game.

Controllers Expansion adds hardware profiles, explicit P1/P2 assignment and
Custom remapping. Display Expansion adds 4:3, 16:9, 21:9 and 32:9 presentation,
independent Local VS displays and complete mirroring. Install through the supplied
**V-On Patcher EX** using your original game files or disc image, then configure
controllers in F7 and displays in F5. The original patch options and Restore
original workflow remain available.

For the current integrated prerelease, see [GitHub Releases](https://github.com/hyp36rmax/VO_PATCH_EX/releases).
The [v0.18.1 release notes](docs/releases/v0.18.1.md) describe installation and compatibility.

VO PATCH EX is an independent community project, not affiliated with or endorsed
by SEGA. Original patcher logo and icon: **SirRockEmSockEm**. The header combines
the unchanged upstream artwork with the approved red EX lettering.

See [installation](docs/project/INSTALLATION-WORKFLOW.md),
[attribution and lineage](docs/project/ATTRIBUTION-AND-LINEAGE.md), and
[branding assets](assets/BRANDING.md).

## Overview

Controller Expansion adds native USB HID Twin-Stick profiles, independent P1/P2
controller selection and optional Custom XInput remapping. Original and modern
controllers feed the game's existing digital controls; known hardware has predefined
mappings, and Custom starts with working Xbox/Brook-style defaults.

The project preserves upstream mappings and gameplay, including Back/camera zoom,
and assigns physical controllers explicitly on supported builds instead of using
Windows connection order. New executable patches are limited to verified sites.

The upstream patcher remains the foundation. Its [game fixes](docs/PATCHER.md#what-the-patches-do),
[native widescreen](docs/PATCHER.md#native-widescreen),
[internet play](docs/PATCHER.md#internet-play),
[music from files](docs/PATCHER.md#music) and
[windowing/scaling add-on](docs/PATCHER.md#windowing-and-scaling-cnc-ddraw)
remain available alongside the original controller profiles.


## Playable Bosses

Optional single-player Jaguarandi and Z-Gradt support comes from **Vortyne's**
implementation in **Pairomaniac's V-On Patcher**. **Playable bosses** is off by
default; **Pre-unlock the bosses** requires it. Earned unlocks are stored in
`bosses.bin` and survive Restore Original. Z-Gradt's special laser uses the
existing Dash/turbo input. Local VS and online selection retain the original
eight machines.

Playable Bosses are supported in Single Player only. See the
[upstream boss reference](docs/BOSSES.md) and
[Experience integration and validation](docs/project/PLAYABLE-BOSSES.md).

## Display Expansion

Configure **F5 → Graphic Settings → Display...** after installing with the original
patcher. Fresh installations default to 16:9 Single Display; saved display changes
apply on next launch.

| Setting | Behavior |
|---|---|
| Single Display | One selected display; 4:3, 16:9, 21:9 or 32:9 game aspect ratio |
| Dual Display Versus | Independent P1/P2 gameplay views on separate displays |
| Dual Display Mirror | Complete primary presentation duplicated, including both Local VS views |

Choose Primary Display and, in dual modes, Secondary Display in F5. Outputs can
use different desktop resolutions and aspect ratios; each view fits its assigned
display independently. Hardware specifications do not imply that every combination
has been physically tested, and universal monitor compatibility is not claimed.
Local VS selection is shared; Versus separates gameplay views and Mirror duplicates
the complete primary presentation. Movies retain upstream framing compatibility;
dual-mode movie playback remains on the primary display with the secondary black.

Monitor assignments and saved preferences are retained during temporary hardware
fallback. Existing F4, F5 graphics controls, movies and Local VS settings remain
available. Dual-mode F4 transitions retain the current supported presentation.
Game aspect ratio controls the rendered view; physical monitor resolution controls
the output surface. Selecting 32:9 does not simply stretch a 16:9 image. A selected
aspect is fitted to each output, so unused space may remain on a differently shaped
monitor. Dual Versus uses its dedicated two-player profile.

See [current display implementation](docs/display/IMPLEMENTATION.md),
[display requirements](docs/display/DUX-V1.0.md) and
[installation](docs/project/INSTALLATION-WORKFLOW.md). Windows acceptance for the
current integrated package remains pending.

### Validated hardware

The maintainer reports these eight display configurations as validated. This is
not an exclusive compatibility list or evidence that every gameplay mode, monitor
pairing or refresh-rate combination was tested. Acceptance of the current
integrated Windows package remains pending.

| Display | Resolution | Refresh Rate |
|---|---|---|
| Acer Nitro 34" | 3440×1440 | 200 Hz |
| Samsung Odyssey G9 32" | 2560×1440 | 240 Hz |
| Samsung Odyssey G9 49" | 5120×1440 | 240 Hz |
| Samsung Odyssey CRG9 49" | 5120×1440 | 120 Hz |
| HyperX Armada 27 | 2560×1440 | 165 Hz |
| HyperX Armada 24 | 1920×1080 | 240 Hz |
| ASUS ROG Strix XG17 17.3" | 1920×1080 | 240 Hz |
| LG UltraGear 32" | 2560×1440 | 165 Hz |

## Diagnostics and Privacy

**Diagnostics are disabled by default.** In **F11 Extras**, select Off, Normal,
Detailed or Development. Enabling a session requires restarting the game; selecting
Off stops new collection and retains existing logs. The preference persists without
repatching. Keep the existing F11 Extras patch option enabled to access its controls.

Normal records startup/shutdown and errors/recovery; Detailed adds hardware,
assignment and display information; Development adds bounded technical observations.
Logs stay in the game folder. **Export Diagnostics...** creates a sanitized local
ZIP only when requested. There are no automatic uploads, screenshots, audio or raw
controller input recording. No export occurs automatically when the game closes.

See [Diagnostics and privacy](docs/project/EXPERIENCE-DIAGNOSTICS.md) for exact
locations, retention limits, disabling collection, export and deleting old logs.

## Getting Started

1. Download the complete Windows ZIP from the [published prerelease](https://github.com/hyp36rmax/VO_PATCH_EX/releases).
   Use release assets rather than development build artifacts.
2. Extract the complete package and keep its directory structure, including
   `_internal`, beside `v-on-patcher.exe`. The current Windows bundle includes
   its Python runtime; no separate Python installation is needed.
3. Run **v-on-patcher.exe**. In **GAME FILE**, select your unmodified `v_on.exe`.
   For a new installation, use **INSTALL** with your disc's `.cue` file first;
   the [patcher guide](docs/PATCHER.md#installing-from-a-disc-image) covers game
   installation and soundtrack extraction.
4. Leave **XInput gamepad support** enabled under **EXTRA PATCHES**, choose any
   other patches you want, then select **Apply patches**. This option also
   installs the native HID profiles on [compatible executables](#compatibility).
5. Open **ADD-ONS** for optional upstream components; read the information for each
   before installing. Launch Virtual-On normally. Use **F7** to select each player's profile, then follow
   the controller-selection prompt. Fixed profiles need no button setup;
   Custom remapping is optional. Use **F5 → Graphic Settings → Display...** for
   display mode, monitor assignments and aspect ratio; choose **OK**, then restart.

The patcher installs its supplied 32-bit `vontanita.dll` beside the game.
Keep the packaged helper: it requires the Windows Universal C Runtime and its
integrity is checked before installation. Python packages must retain `input/`
and `net/` beside the script and require a local Python/Tk installation.

Back up `v_on.ini` before restoring or repatching. **Restore original** restores
backed-up game files and retains patched settings as `v_on.ini.patched`; use it
instead of manually replacing only the executable, because the title artwork
must match. See [what gets written](docs/PATCHER.md#what-gets-written) and the
[full patcher guide](docs/PATCHER.md) for restoration, add-ons and Python usage.

## Installation and Display Questions

The [controller questions](#common-questions) and [controller troubleshooting](#troubleshooting)
remain below the profile reference.

**Which Virtual-On version do I need?**

Use original 1997 Windows game files. The integrated Controllers + Display recipe
set is verified for English retail/US–Global and the Japanese rerelease. The
upstream patcher recognizes additional editions; that does not establish the same
integrated expansion support. See [build identification](docs/PATCHER.md#builds).

**Does this replace Pairomaniac's work?**

It extends that implementation. Modern Windows fixes, installation, native
widescreen, XInput, F-key settings, music improvements and other upstream features
remain the foundation. Use the complete supplied patcher rather than layering
individual executables over an existing patched installation.

**Does it support ultrawide, and does 32:9 stretch the game?**

Single Display and Dual Mirror offer the selected 21:9 and 32:9 rendering profiles.
They change rendering dimensions rather than stretching a 16:9 picture. Output
fitting preserves aspect; a differently shaped monitor can have unused borders.

**Can each player use a separate monitor?**

Select **Dual Display — Versus**, assign distinct active displays, choose **OK**
and restart. Local VS gameplay routes P1 and P2 independently. **Dual Display —
Mirror** instead duplicates the complete presentation, including both split-screen
views; it is not a second independent camera.

**Do both monitors need the same resolution or aspect ratio?**

No. Each output fits its assigned desktop independently. The validated hardware
inventory is not a guarantee for every pairing or refresh-rate combination.

**What happens if a monitor disconnects?**

At the next launch, unavailable dual output can fall back to Single Display while
retaining saved preferences. Reconnect and restart to resolve the saved layout.
Do not assume a running dual renderer can switch modes seamlessly after display loss.

**How do I upgrade or restore the original game?**

Close the game, back up settings and use **Restore original** before **Apply
patches** with the new complete package. Do not replace individual patched game
files manually. See [installation and recovery](docs/project/INSTALLATION-WORKFLOW.md).

**Are diagnostics enabled automatically?**

No. F11 provides **Diagnostics (saved immediately)** and **Export Diagnostics...**.
Choose a level and restart to begin collection. Off stops new collection and keeps
existing logs. Export is local and player initiated; nothing uploads automatically.

### Display troubleshooting

First confirm Windows detects the intended active displays, check the selected
mode and assignments in F5, choose OK and restart. Keep the complete patcher/runtime
files together. Do not change drivers or administrator settings as a default remedy.

| Symptom | Check / action |
|---|---|
| Missing monitor | Check that Windows has an active desktop on it; reconnect and restart before reopening F5. |
| Wrong output | Re-select Primary Display and Secondary Display, save and restart. |
| Unexpected aspect or borders | Check Game Aspect Ratio separately from desktop resolution. Fitting preserves aspect; borders can be expected. |
| Both players appear together | Single retains the original split-screen; Mirror duplicates it. Use Dual Versus for independent gameplay outputs. |
| Mirror seems different during a movie | Original movie playback stays on the primary display with the secondary black. |
| Dual mode falls back | Use distinct active outputs; cloned outputs at the same desktop origin are not independent. Saved preferences remain available for the next launch. |
| Display settings cannot save | Record the dialog's step and Windows error. Check that the game folder and existing settings are writable; use F11 diagnostics for details. Do not delete saved preferences or run as administrator as a workaround. |
| Saved change is not visible | Restart the game. OK saves next-launch choices; Cancel discards pending edits. |

## Controller Profiles

The F7 labels below identify the profiles. Twin-Stick profiles translate twelve
lever, trigger and dash inputs into digital arcade controls. Lever combinations
retain movement, turning, jump and guard; both triggers fire the centre weapon.
Fixed Twin-Stick profiles have no gameplay rebinding editor; Custom, Gamepad and
the keyboard profiles offer their respective bind pages.

For HID tables, **B0 is zero-based button 0**, conventionally shown as **Button 1**
in Windows; add one when comparing those numbering schemes. Axis percentages
are the hardware test utility's measurements, not raw XInput values.

### Gamepad (XInput)

The original configurable gamepad profile maps named actions rather than two
arcade levers. Defaults are the same for both players:

| Game input | Default XInput control |
| --- | --- |
| Move forward / backward / left / right | Left thumbstick up / down / left / right |
| Turn left / right | Right thumbstick left / right |
| Left weapon / right weapon | LT / RB |
| Centre weapon | RT |
| Dash | LB |
| Jump | A |
| Guard | X |
| Menu navigation / accept | D-pad / A |
| Pause / camera | Start / Back |

Use F7 to rebind gameplay actions; **Default** restores them. The upstream
[gamepad guide](docs/PATCHER.md#gamepad) also covers the per-player XInput
stick deadzone (40% by default, adjustable in F11 Extras with **Disable menu bar**
enabled) and soft reset: **LB + RB + LT + RT + Start**, unavailable during an
internet match.

### Twin-stick (XInput)

The original arcade layout maps each thumbstick to one lever.

| Game input | XInput control |
| --- | --- |
| Left lever | Left thumbstick |
| Right lever | Right thumbstick |
| Left / right trigger | LT / RT |
| Left / right dash | LB / RB |
| Menu navigation / accept | D-pad / A |
| Pause / camera | Start / Back |

See [controller internals](docs/CONTROLLERS.md) for the shared lever engine.

### Twin-Stick (Custom)

A configurable profile for XInput Twin-Stick builds and adapters, developed with
a Brook reference setup. Its VID/PID depends on the PCB or adapter; this mapping
is a useful default, not a universal Twin-Stick standard.

| Game input | Default XInput control |
| --- | --- |
| Left lever up / down / left / right | D-pad up / down / left / right |
| Right lever up / down / left / right | Y / A / X / B |
| Left / right trigger | LT / RT |
| Left / right dash | LB / RB |
| Pause / camera | Start / Back — outside gameplay remapping |

All twelve gameplay actions can be remapped independently for each player.
See [Player Assignment & Remapping](#player-assignment--remapping) and the
[Custom hardware and implementation record](docs/controllers/custom-twinstick.md).

### Twin-Stick (Tanita)

Native HID profile for VID `1F4F`, PID `9001`, revision `0200`, Generic Desktop /
Game Pad. Axes become digital lever directions; they do not add analog movement.

| Game input | HID control |
| --- | --- |
| Left lever | X / Y axes |
| Right lever | Z / Rz axes |
| Left / right trigger | B4 / B5 |
| Left / right dash | B6 / B7; B10 / B11 accepted as top-control aliases |
| Menu navigation | POV hat |
| Accept / pause / camera | Cross / Options / Share |

The [Tanita hardware record](docs/controllers/tanita-twinstick.md) preserves the
axis measurements and button-report attribution, including two physical left
auxiliary/top controls reporting B10 and two right controls reporting B11.

### Twin-Stick (HORI EX)

Xbox 360 HORI Twin Stick EX, VID `1BAD` / PID `FF00`, selected manually through
XInput. These findings do not establish PlayStation-model compatibility.

| Game input | XInput control |
| --- | --- |
| Left lever | D-pad |
| Right lever | Right thumbstick |
| Left / right trigger | LT / RT |
| Left / right dash | LB / RB |
| Menu navigation / accept | D-pad / A |
| Pause / camera | Start / Back |

XInput provides independent triggers and direct lever/shoulder inputs. The
[HORI hardware record](docs/controllers/hori-twinstick-ex-x360.md) also preserves
its legacy Windows representation, including the shared trigger axis.

### Twin-Stick (Raphnet DC)

Sega Dreamcast **HKT-7500** through Raphnet Dreamcast-to-USB **v1**, VID `289B` /
PID `0008`. Both levers report buttons.

| Game input | HID control |
| --- | --- |
| Left lever up | B4 |
| Left lever down | B5 |
| Left lever left | B6 |
| Left lever right | B7 |
| Left trigger | B10 |
| Left dash / top | B9 |
| Right lever up | B12 |
| Right lever down | B13 |
| Right lever left | B14 |
| Right lever right | B15 |
| Right trigger | B2 |
| Right dash / top | B1 |
| Start — controller selection, then accept / intro skip | B3 |
| Pause / resume — separate physical control | B11 |

See the [DC hardware record](docs/controllers/raphnet-dreamcast-twinstick.md) for
measurements and the distinction between tested v1 hardware and
manufacturer-documented v2 support.

### Twin-Stick (Raphnet Saturn)

Sega Saturn **HSS-0151** through Raphnet Saturn-to-USB **v2**, VID `289B` /
PID `0043`. The left lever reports axes; the right reports buttons.

| Game input | HID control |
| --- | --- |
| Left lever neutral | X 50%, Y 50% |
| Left lever up | Y 0% |
| Left lever down | Y 100% |
| Left lever left | X 0% |
| Left lever right | X 100% |
| Left trigger | B6 |
| Left dash / top | B7 |
| Right lever up | B3 |
| Right lever down | B2 |
| Right lever left | B0 |
| Right lever right | B4 |
| Right trigger | B1 |
| Right dash / top | B5 |
| Start — controller selection, then accept / intro skip | B8 |
| Dedicated Pause | N/A — no physical control or generated Pause mapping |

See the [Saturn hardware record](docs/controllers/raphnet-saturn-twinstick.md)
and [shared Raphnet implementation](docs/controllers/raphnet-twinsticks.md) for
axis thresholds, ownership, Start/Pause handling and validation boundaries.

### Keyboard (Simple)

The original named-action keyboard profile shares the Gamepad bind page but
shows keyboard inputs and keeps its own saved bindings. These are the shipped
US-layout key positions; saved F7 assignments take precedence. **Num** means the
numeric keypad, distinct from the navigation cluster.

| Game input | P1 default | P2 default |
| --- | --- | --- |
| Move forward / backward | W / S | Home / End |
| Move left / right | A / D | Delete / Page Down |
| Turn left / right | Q / E | Insert / Page Up |
| Left weapon / right weapon | C / G | Num 0 / Num 3 |
| Dash | X | Num 1 |
| Jump | R | Num 5 |
| Guard | V | Num . |
| Centre weapon | F | Num 2 |

See the [keyboard guide](docs/PATCHER.md#keyboard-simple) and
[controller internals](docs/CONTROLLERS.md).

### Keyboard (Real)

The original two-lever keyboard scheme has its own F7 bind page and saved
layout. Defaults below use the same key-position convention as Simple.

| Game input | P1 default | P2 default |
| --- | --- | --- |
| Left lever up / down | 2 / W | Up arrow / Down arrow |
| Left lever left / right | Q / E | Left arrow / Right arrow |
| Left trigger | Z | Num 0 |
| Left dash | X | Num 2 |
| Right lever up / down | R / F | Num 8 / Num 5 |
| Right lever left / right | D / G | Num 4 / Num 6 |
| Right trigger | C | Num 1 |
| Right dash | X | Num 2 |

Both dash inputs share a key by default. **Default** resets the player being
edited. When both players use keyboards, keep their keys distinct. See the
[keyboard guide](docs/PATCHER.md#keyboard-real) for configuration and
[controller internals](docs/CONTROLLERS.md) for profile storage.

## Player Assignment & Remapping

Select P1 and P2 profiles independently in **F7**; XInput, native Tanita,
Raphnet DC, Raphnet Saturn and keyboard profiles can be mixed. When prompted,
release **Start / Options**, then press it on the controller intended for the
displayed player. Selection considers all four XInput slots or up to two native
units of the selected hardware family, so controllers can remain connected in any initial slot order.

| Assignment event | Behavior |
| --- | --- |
| First use in a game session | Prompt when an eligible, unowned controller is available |
| F7 confirmation / Custom's **Choose controller** | Explicit selection or reassignment |
| Choose the other player's controller | Swap assignments within the same input family; otherwise clear the other claim |
| Detected disconnect | Clear input and invalidate that claim; reselect through F7 after reconnecting |
| Restart | Keep profiles and saved bindings; establish controller ownership again |

Ownership is deterministic **within the session**, not a persistent hardware-ID
mapping across launches. XInput slot numbers are not saved as physical identities.
Native HID paths remain reserved for the process; changing USB ports after
both reservations are occupied requires a restart.

For Custom, choose **Next** in F7, focus an action with the mouse or Tab, release
all controls, then press one button or move one lever direction. Capture reads
only that player's selected XInput controller.

| Editor operation | Result |
| --- | --- |
| Capture or dropdown selection | Assign one of 20 inputs: face buttons, shoulders, triggers, thumbstick directions or D-pad directions |
| **None** | Unbind the action |
| Escape, 30-second timeout or disconnect during capture | Retain the current binding; Escape also leaves manual dropdown selection available |
| Held input on entry, chord or diagonal | Require release and a single-input retry |
| **OK** / **Cancel** | Save / discard pending binding edits |
| **Default**, then **OK** | Restore the Custom defaults for that player |

Custom layouts persist separately as `1P Custom Assign` and `2P Custom Assign`
in `v_on.ini`. D-pad gameplay directions can be reassigned while menu navigation
remains available; Start/pause and Back/camera are fixed controls outside the editor.

## Hardware Validation

Compatibility evidence combines device diagnostics, in-game control checks and
software regression tests. Hardware checks cover neutral state, each lever
direction, triggers, dash, simultaneous inputs and menu controls; two-player
checks cover player assignment and simultaneous input. Reconnect permutations
are recorded separately in the hardware records. This records how
original hardware behaves without treating API emulation as a substitute for a
working controller.

The matrix records maintainer-confirmed hardware results separately from
automated checks and manufacturer claims. Identical multi-unit configurations
remain separate from mixed-controller validation.

| Area | Status |
| --- | --- |
| Original Gamepad, Twin-stick and keyboard profiles | 1P Validated; 2P Validated; mixed VS Functionally Tested |
| Tanita movement, triggers and top controls | 1P Validated; 2P Validated; mixed VS Functionally Tested |
| Xbox 360 HORI EX controls | 1P Validated; 2P Validated; mixed VS Functionally Tested |
| Custom remapping/capture and controller reassignment | 1P Validated; 2P Validated; mixed VS Functionally Tested |
| Dual Tanita local versus | Functionally Tested; P1 and P2 validated |
| Dual HORI | Pending |
| Raphnet DC v1 / Saturn v2 | 1P Validated; 2P Validated; mixed VS Functionally Tested |
| Mixed Raphnet DC/Saturn local VS | Functionally Tested |
| Dual identical Raphnet DC / dual identical Saturn | Not Tested |
| Raphnet Dreamcast adapter v2 | Manufacturer-documented HKT-7500 support; local physical validation Pending |
| Retail / Japanese rerelease patching | Software checked: 812 patch combinations |

The [controller documentation index](docs/controllers/README.md) separates observed
measurements, implementation decisions and hardware results. See
[controller internals](docs/CONTROLLERS.md) for dispatch evidence and automated checks.

Use the [testing methodology](docs/controllers/profile-testing-methodology.md)
for community records: identify the exact model, platform, VID/PID/revision and
input mode, retain neutral and per-control diagnostics, then test the mapping
in-game for both players. Redact device-instance paths before posting logs.
Measured results do not establish support for another revision or platform.

## Compatibility

All four recognized game builds remain patchable, but expanded controller
profiles and explicit physical ownership are limited to the verified builds:

| Executable | Controller support |
| --- | --- |
| English retail / US–Global | Expanded profiles, per-player selection and Custom remapping |
| Japanese rerelease | Expanded profiles, per-player selection and Custom remapping |
| USA OEM / Japanese original | Upstream profiles and connected-slot assignment only |

USA, USA Alt and European discs share the English retail executable.
See [recognized builds and hashes](docs/PATCHER.md#builds) to identify your copy.
The tested hardware list records evidence; it is not an exclusive list of usable
XInput devices. Native HID profiles do require the implemented device identity
and report layout.

## Common Questions

**Can I use original Sega Twin-Sticks?**

Yes: Dreamcast HKT-7500 with the tested Raphnet DC v1 adapter, and Saturn
HSS-0151 with the tested Saturn v2 adapter. Other revisions need separate evidence.

**Do I need to configure every button?**

No. Select the matching fixed profile, or start with Custom's defaults.

**Can I use different controllers for local VS?**

Yes. P1/P2 profiles and physical controllers are selected independently;
mixed-controller local VS is Functionally Tested.

**Can I connect two identical Twin-Sticks?**

Dual Tanita is tested. Dual HORI is Pending, and identical Raphnet DC or Saturn
pairs are Not Tested; mixed DC/Saturn success does not validate those pairs.

**Why does the game ask me to press Start?**

It identifies which physical controller belongs to the displayed player. Release
Start/Options first, then press it; the claim press is suppressed until release.

**Do I need to unplug my other controllers?**

No. On expanded builds, selection checks all four XInput slots or up to two
native units per family. See the reconnect limits below if a USB path changes.

**Can I customize Twin-Stick controls?**

Choose **Twin-Stick (Custom)** for an XInput device and edit its twelve gameplay
actions through F7. Hardware-specific native HID profiles use fixed mappings.

**Does Controller Expansion change gameplay?**

It maps controllers to the existing digital commands; movement, weapons and
Twin-Stick gestures retain their game semantics. Other patch options are
explained in the upstream patcher guide.

**Are controller settings saved?**

Profiles and per-player bindings are saved in `v_on.ini`. Physical controller
ownership is established again each session.

**What happens when a controller disconnects?**

Its input and claim are cleared. Reconnect, then reselect it through F7.

**Does Controller Expansion replace the original patcher?**

It extends Pairomaniac's patcher and retains its game fixes and add-ons.

**How can I contribute hardware testing results?**

Follow the [testing methodology](docs/controllers/profile-testing-methodology.md)
and submit the exact hardware/configuration and results, separating observations
from assumptions and unperformed tests.

## Troubleshooting

First check the executable's [compatibility](#compatibility), that **XInput
gamepad support** was applied, and that the intended player's F7 profile matches
the connected controller. Then use the symptom below.

| Symptom | Check / action |
| --- | --- |
| Controller does not respond | Confirm Windows sees the device. Select the intended player in F7, release Start/Options, then press it on that controller alone. HORI EX and Custom require XInput presentation. |
| Wrong controller controls a player | Reassign through F7; Custom also provides **Choose controller**. Do not rely on Windows connection order. |
| Custom mapping is incorrect | Open **Next** in F7; select the action, release all controls, capture one input and choose **OK**. **Default**, then **OK**, restores that player's mapping. |
| Native HID controller is not detected | Compare VID/PID, revision where required, and report layout with the [hardware records](docs/controllers/README.md). Confirm the supplied `vontanita.dll` is beside the game and its Universal C Runtime dependency is available. |
| Controller stopped after disconnecting | Reconnect and reselect through F7. If new USB paths have exhausted a native family's two reserved paths, restart the game. |
| Patcher refuses the game or cannot apply a patch | Use an unmodified recognized executable or **Restore original** before repatching. Keep the complete package and supplied helper; do not bypass identity/integrity checks. See [build identification](docs/PATCHER.md#builds) and the [patcher guide](docs/PATCHER.md). |

## Known Limitations

- Controller ownership lasts for the game session; saved profiles and bindings
  do not save a persistent physical-device identity.
- Native HID families reserve two device paths per process. Reconnection requires
  F7 selection; moving to additional paths after both are reserved requires restart.
- Custom remaps XInput gameplay controls, not arbitrary HID reports or fixed
  pause/camera controls. Native profiles require their characterized report layouts.
- Dual-identical hardware and adapter revisions marked **Not Tested** or **Pending**
  in the validation matrix have no corresponding local validation; that is not a
  claim that they cannot work. Reconnect/persistence subtests not recorded in the
  hardware pages remain unconfirmed.
- USA OEM and Japanese original do not expose the expanded profiles or explicit
  physical-controller selection.

## Technical Documentation

| Reference | Contents |
| --- | --- |
| [Patcher guide](docs/PATCHER.md) | Installation, restoration, patches, widescreen, netplay, music and Python usage |
| [Controller hardware index](docs/controllers/README.md) | Observed hardware, implemented mappings and physical validation records |
| [Controller internals](docs/CONTROLLERS.md) | Dispatch, ownership, remapping, persistence and regression coverage |
| [Testing methodology](docs/controllers/profile-testing-methodology.md) | Repeatable characterization and community evidence |
| [Developer documentation](docs/README.md) | Build workflow, assembly, patch sites, executable maps and technical references |

## Project Status

The latest published CE pre-release is
[v0.17.0-controller-expansion.2](https://github.com/hyp36rmax/VO_PATCH_CONTROLLER_EXPANSION/releases/tag/v0.17.0-controller-expansion.2).
**Experience** is the default and integrated product branch. **Controller-Expansion**
preserves the controller release line; **Display-Expansion** remains independent
display development and **main** preserves the upstream foundation.
Unified Overlay development remains separate from this prerelease.

The integrated v0.18.0 release retains Controllers + Display Expansion and approved
upstream movie ownership. Its [release notes](docs/releases/v0.18.0.md) distinguish
supported configurations and installation requirements. Playable Bosses and
Unified Overlay are not included.
[Build artifacts](https://github.com/hyp36rmax/VO_PATCH_EX/actions/workflows/build.yml)
are development packages, not releases. CE releases remain explicitly approved
pre-releases. Preserve the existing
[release history](https://github.com/hyp36rmax/VO_PATCH_CONTROLLER_EXPANSION/releases) and
[CE.2 release notes](docs/releases/v0.17.0-controller-expansion.2.md).

## Credits & Project Lineage

[Pairomaniac](https://github.com/pairomaniac/v-on-patcher) created V-On Patcher and
its patching, XInput and Twin-Stick foundation.
[hyp36rmax](https://github.com/hyp36rmax/VO_PATCH_EX) maintains Controllers Expansion and Display Expansion
and supplies physical hardware characterization and testing.

The upstream [credits](docs/PATCHER.md#credits-and-licence) retain attribution to
UE2A-GEL's original VO_Patch work and SirRockEmSockEm's logo, icon and screenshots.
The [MIT license](LICENSE) covers the patcher, tools and documentation; rights to
the game remain with SEGA.
