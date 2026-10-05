# L4D2_Dxvk_32to64_Bridge-Nightlybuild

Private repository for experimental builds of the L4D2-patched NVIDIA RTX Remix Bridge.

## Setup

Create a private GitHub repository named `L4D2_Dxvk_32to64_Bridge-Nightlybuild` and push this directory to its default branch. Enable Actions and run **Build new upstream Bridge releases** once from the Actions tab. No personal access token or external scheduler is required by the workflow: it uses the repository's temporary `GITHUB_TOKEN`.

The workflow checks hourly at minute 23 UTC. GitHub may delay scheduled runs; schedules only run on the default branch. Private Windows runner usage counts against your account's Actions allowance. Public repositories may have schedules disabled after 60 days without activity.

## Behavior

First run builds the newest stable upstream release. It also tracks stable releases published on or after 2026-10-05, including releases missed between checks. Draft and upstream prerelease versions are excluded. At most eight missing releases are attempted per run. Completed local releases prevent duplicate builds. Failed builds are retried on subsequent checks.

Each build resolves the upstream tag to an exact commit, applies `patches/l4d2-bridge.patch`, and builds both the x86 client and x64 Host. Patch conflicts are fatal; the job never silently falls back to an unpatched upstream build. New upstream releases may require manual patch or toolchain updates. Automation cannot guarantee arbitrary future source compatibility.

The existing backend in `config/backend.json` is independently pinned. This automation upgrades Bridge, not DXVK. Successful builds run x86 diagnostics, validate PE architectures, and publish an experimental prerelease with a full installation ZIP, SHA-256 checksums, licenses, backend metadata and exact upstream/build-recipe commits. ZIP creation includes `.l4d2bridge`.

Release upload uses a draft until all assets are uploaded. Failed uploads can be retried. Publishing runs in a separate Linux job; compiling upstream source has no release-write permission. Use both client and matching Host when testing; compilation tests do not prove gameplay compatibility.

## Local build

Requires the Visual Studio/MSVC/SDK and Python tools described in README.md:

```powershell
./scripts/build_bridge.ps1 -UpstreamCommit <40-character-upstream-commit>
./scripts/test_diagnostics.ps1
```

Existing dependency checkouts are preserved and rejected if they do not match the requested commit. Build from a fresh checkout for each version.

## Upstream currently has no GitHub Releases

As verified on 2026-10-05, the dxvk-remix Releases API returns an empty list. A successful detection-only run therefore skips compilation. It does not follow every branch commit or automatically infer releases from a different repository.

To verify the complete build pipeline, run the workflow manually and fill `upstream_commit` with `9aa74f8dfad2188efbd0f717c64d9f8fa909787e` (the existing validated baseline). Another full upstream commit may be supplied, but the L4D2 patch must apply and compile. Manual builds are deduplicated by their full commit SHA. Leave the field empty for normal release detection.
