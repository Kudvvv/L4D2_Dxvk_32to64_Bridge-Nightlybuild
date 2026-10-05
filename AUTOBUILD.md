# L4D2 Bridge Nightlybuild

This private repository follows the latest source code on NVIDIA dxvk-remix's default branch (currently main), independently of GitHub Releases.

## Automatic updates

The GitHub Actions workflow **Build latest upstream Bridge** checks hourly at minute 23 UTC (also minute 23 in Beijing). Scheduling may be delayed by GitHub. The workflow must be on the default branch and enabled in Actions.

Each check resolves upstream's current default branch to an exact commit SHA. If a completed local release already exists for that SHA, compilation is skipped. Otherwise the workflow fetches that exact commit, applies the L4D2 patch, builds the x86 client and matching x64 Host, runs diagnostics, validates architectures, and publishes an experimental prerelease. Changes arriving between checks are coalesced into the newest HEAD: it does not build every intermediate commit. Changes anywhere in the upstream repository can trigger a build, including changes outside Bridge.

Failed builds and incomplete draft uploads are retried. A patch conflict or compilation failure stops publishing; a green detection-only run is not proof of a new binary build. Future incompatible source or toolchain changes may require adapting the patch. GitHub Actions allowance applies to private Windows runners.

## Manual runs

Open Actions -> Build latest upstream Bridge -> Run workflow. Leave upstream_commit empty to check and build the latest default-branch HEAD. Supply a full 40-character upstream SHA only to build a specific revision. Already published revisions are skipped in either mode.

## Package provenance

UPSTREAM.json records the exact upstream commit, source branch, and build-recipe commit. BACKEND.json records the separately pinned DXVK-GPLALL backend. SHA256.json covers the three executable files, and the release includes an archive checksum. ZIP names use forward-slash relative paths with no ./ prefix and preserve bin/.l4d2bridge.

Both client and matching Host are included. Automatic compilation tests do not verify L4D2 gameplay. Back up an existing installation before testing.

## Baseline as of 2026-10-05

The upstream main HEAD is 9aa74f8dfad2188efbd0f717c64d9f8fa909787e, identical to the original project's pinned baseline. Therefore the existing baseline package already uses current upstream source; automatic monitoring now follows subsequent commits instead of waiting for nonexistent Releases. The independent backend remains DXVK-GPLALL 2.6.8-2.
