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
