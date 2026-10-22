# Windows distribution dependencies

The portable patcher and installed Experience have separate Python runtimes. Apply copies the installed runtime into the game directory; the game must remain independent when the patcher folder is moved or deleted. Sharing those files through paths back to the patcher would break this contract. Neither runtime requires a system Python installation.

`_internal/Lib/site-packages/certifi` supplies certificate validation for supported HTTPS downloads. `_internal/DLLs` supplies Python extensions and their native dependencies, while Tcl/Tk resources support the original patcher UI. The installed lifecycle and diagnostics modules are production components even though they are Python scripts. Native controller, Display and networking binaries and their license notices remain unchanged.

## Assembly exclusions

| File | Reason |
|---|---|
| `_internal/DLLs/_ctypes_test.pyd` | CPython test extension; not referenced by shipped application or standard-library modules |
| `_internal/experience/payload/experience-runtime/DLLs/_ctypes_test.pyd` | Same test extension in the installed-runtime copy |
| `_internal/experience/catalog/game_profiles.h` | Compile-time identity table already embedded in the Display wrapper; the installer reads only the catalog index and recipe ZIP |

Other extension modules remain until their dependencies are established. File extensions alone are not grounds for removal. Unknown dependencies must not be silently discarded.

## Recipe compression

The v0.18.1 catalog contains 2,048 distinct sparse recipe payloads across Retail/JPRE options. Its recipe ZIP accounts for 61,963,899 bytes of the 62,148,420-byte increase over v0.18.0. The two runtime copies did not cause that increase.

Assembly recompresses each recipe with Python's built-in ZIP-LZMA support. Before replacing the archive, it verifies exact membership and each recipe's existing SHA-256, then verifies every decompressed result again. The catalog index, recipe bytes, original-executable identities and resulting patched images do not change. The outer distribution remains an ordinary Deflate ZIP for Windows extraction; only the patcher's internal recipe archive uses LZMA. No new launcher, external utility or extraction framework is required.

The measured internal archive shrinks from 83,182,010 to 56,976,966 bytes. Repeated sequences remain within distinct option recipes to preserve the existing independent lookup and verification contract. There are no byte-identical recipe members to remove.

## Validation boundary

The distribution-size workflow rebuilds only package assembly from the checksum-locked v0.18.1 release. It verifies unchanged retained runtime bytes, all recipe checksums, bundled-Python decoding, launcher selfcheck and a copied installed runtime with the patcher directory unavailable. Retail/JPRE Apply/Restore and full recipe reconstruction run locally against authorized original files.

These checks do not establish physical Windows gameplay acceptance. The optimized candidate remains private test material until accepted; published release assets and application versions are unchanged.

## Compact Experience catalog

The compact distribution retains upstream Apply and applies the same verified
Experience delta afterward. `compact_catalog.py` stores shared hex values once
and deduplicates identical binary offset/value-ID lists, including pre-unlock
aliases. The unchanged catalog index retains every option mask and recipe hash.
Only the requested recipe is reconstructed and checked before installation.

`recipes.bin.xz` contains a versioned header and little-endian write records.
Decoding is bounded to 128 MiB, with a 4 MiB header and a 256 MiB LZMA memory
limit. Invalid streams, missing entries, overlapping ranges, invalid references,
wrong option identities and recipe hash mismatches fail closed. A corrupt compact
file never falls back to legacy data. Legacy ZIP input remains supported for
existing offline generation and regression fixtures.

Source, upstream-result and final-image hashes, installation ownership, rollback
and Restore remain authoritative. The installed runtime and native binaries are
unchanged. The compact catalog is an installation resource, not a game runtime
or a new patch engine. Windows acceptance is required before release.
