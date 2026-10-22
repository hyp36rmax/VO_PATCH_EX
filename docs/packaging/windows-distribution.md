# Windows distribution dependencies

The portable patcher and installed Experience have separate Python runtimes. Apply copies the installed runtime into the game directory; the game must remain independent when the patcher folder is moved or deleted. Sharing those files through paths back to the patcher would break this contract. Neither runtime requires a system Python installation.

`_internal/Lib/site-packages/certifi` supplies certificate validation for supported HTTPS downloads. `_internal/DLLs` supplies Python extensions and their native dependencies, while Tcl/Tk resources support the original patcher UI. The installed lifecycle and diagnostics modules are production components even though they are Python scripts. Controller, Display and networking implementations and required license notices are preserved.

## Assembly exclusions

| File | Reason |
|---|---|
| `_internal/DLLs/_ctypes_test.pyd` | CPython test extension; not referenced by shipped application or standard-library modules |
| `_internal/experience/payload/experience-runtime/DLLs/_ctypes_test.pyd` | Same test extension in the installed-runtime copy |
| `_internal/experience/catalog/game_profiles.h` | Compile-time identity table already embedded in the Display wrapper; the installer reads the catalog index and compact recipe data |

Other extension modules remain until their dependencies are established. File extensions alone are not grounds for removal. Unknown dependencies must not be silently discarded.

## Initial ZIP compression measurements

The v0.18.1 catalog contains 2,048 distinct sparse recipe payloads across Retail/JPRE options. Its recipe ZIP accounts for 61,963,899 bytes of the 62,148,420-byte increase over v0.18.0. The two runtime copies did not cause that increase.

The initial size experiment recompressed each recipe with Python's built-in ZIP-LZMA support. Before replacing the archive, it verifies exact membership and each recipe's existing SHA-256, then verifies every decompressed result again. The catalog index, recipe bytes, original-executable identities and resulting patched images do not change. The outer distribution remains an ordinary Deflate ZIP for Windows extraction; only the patcher's internal recipe archive uses LZMA. No new launcher, external utility or extraction framework is required.

The measured internal archive shrinks from 83,182,010 to 56,976,966 bytes. Repeated sequences remain within distinct option recipes to preserve the existing independent lookup and verification contract. There are no byte-identical recipe members to remove.

## Validation boundary

The production workflow builds the native dependencies and Windows launcher, assembles the compact package, and checks recipe hashes, bundled-Python decoding, launcher selfcheck and an installed runtime with the patcher directory unavailable. Retail/JPRE Apply/Restore and exhaustive executable comparison run locally against authorized original files. The earlier release-download-based experiment is superseded; production packaging does not depend on the asset being replaced.

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
and Restore remain authoritative. The installed runtime contract and native implementations are
unchanged. The compact catalog is an installation resource, not a game runtime
or a new patch engine. Windows acceptance is required before release.

## In-game release title

`asm/build.py` copies `release_version.VERSION` without its leading `v` into
`TITLE_RELEASE` in the generated patcher data. The title hook draws the product
line through the original green tile font at row 48, with an optional build
subtitle on row 50. Its 155-byte footprint remains fixed; reserved data now
contains cursor positions and text runs. No SEGA artwork or adjacent native blob
moves. The obsolete `V-On Patcher dev` label is removed.

The existing credits/title option and missing-credit-resource behavior remain
unchanged. Title-enabled recipes intentionally receive new base/final hashes;
`test_title_catalog.py` requires every other executable byte and every Display
delta write to match S03. Credits-disabled outputs remain byte-identical.

## Release-source identity

The central release authority supplies the product version and build kind. The
normal packager records the full source commit and constructs the title subtitle:
`Pre-Release · <seven-character commit>`, `RC<n> · <commit>`, or `Dev · <commit>`.
Official releases omit the subtitle. The source catalog retains canonical,
commit-independent title data, avoiding a generated-file/commit hash cycle.

Apply verifies the pristine source, upstream output and complete reconstructed
image before stamping only the reserved 59-byte title-data region. The package
manifest supplies the build identity; installation metadata records the actual
stamped executable hash. All other output bytes remain covered by the canonical
recipe hash. The native hook remains 155 bytes and uses the original tile printer.
Its middle-dot separator is the existing period moved one tile row upward, since
the printer accepts seven-bit glyph indices rather than Unicode. Visual placement
requires Windows acceptance.

Build the final candidate from the exact commit intended for the release tag.
A later source commit requires rebuilding and revalidating the candidate. Promote
that commit to Experience by fast-forward after acceptance to retain its identity.
The normal Windows workflow packages the compact catalog; integrity validation
rejects a redundant legacy recipe ZIP. No game assets are included.
