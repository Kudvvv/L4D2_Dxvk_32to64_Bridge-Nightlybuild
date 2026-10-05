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

## Release names and tag categories

Releases are grouped by the newest semantic version tag (remix-X.Y.Z) that is an ancestor of the selected source commit. Exact tag revisions are labeled Tag 构建; commits after the tag are labeled Nightly. A branch with no reachable version tag is classified as untagged. The classification never substitutes the old tag's source for the selected latest commit.

Titles use `[remix-X.Y.Z] Nightly · YYYY-MM-DD · shortSHA`. Git tags use `bridge-remix-X.Y.Z-nightly-YYYYMMDD-shortSHA`; packages use `l4d2-bridge-remix-X.Y.Z-nightly-YYYYMMDD-shortSHA.zip`. Dates refer to the upstream commit date (UTC), giving retries the same identity. Full SHA, exact source branch, category, and distance from the version tag are preserved in provenance and release notes. Tagged builds remain experimental because gameplay is not automatically tested.
