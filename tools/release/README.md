# Experience prerelease publication

Experience releases promote an approved Windows ZIP without rebuilding it. The release tag points to the application commit; the publication workflow can be a later infrastructure-only commit.

## Current authorization

The authorized version is `v0.18.0`, defined by `tools/experience/release_version.py`. Its authorization record binds the application commit, successful CI run and attempt, artifact ID, package size and SHA-256, and release-note checksum. The previous `v0.18.0-experience.1` record remains historical evidence.

The accepted implementation baseline is `55bcb76425144d3e138b19e89e4f15887a218f68`, including merged PR #5. This release preserves that implementation. A separate Git ancestry and file-difference check rejects gameplay, controller, display, movie, recipe and networking changes. Only version presentation, release instructions and build validation/naming may differ.

Prior physical acceptance is retained as baseline evidence. The new artifact is **not** claimed physically tested. Exact-artifact Windows build and runtime checks are independently required. This distinction does not extend the documented hardware matrix.

## Promotion

Run **Publish approved Experience prerelease** manually from `Experience`. The workflow accepts no version, commit or artifact parameters. Both jobs validate current remote HEAD, trusted workflow identity, source ancestry, permitted infrastructure changes, exact CI provenance, successful required jobs and the artifact checksum.

The write-scoped job repeats validation, creates a new source tag and draft prerelease, uploads the unchanged ZIP, downloads it to verify SHA-256, rechecks the tag, then publishes with `prerelease=true` and `make_latest=false`. Existing tags and releases cannot be overwritten. A failed partial publication requires inspection; reruns do not silently replace it.

Only the publication job has `contents: write`. It uses the ephemeral Actions token and sends no credentials to redirected download hosts. Repository permissions and protections remain unchanged.

## Original tag workflow

The original tag build remains closed to Experience. Its signing path does not select integrated Experience packaging. Promotion uses the already validated branch artifact; the Actions-created tag does not trigger a second build. The unsigned branch launcher retains its independent upstream version. Python runtime signatures and required dependency notices remain included.

## Verification and recovery

Run `python3 tools/release/test_experience.py` before dispatch. Independently download the public package and compare its SHA-256 after publication. Preserve the old release notes, asset hashes, verified asset copies and tag target before superseding it. Do not delete historical tags or assets.
