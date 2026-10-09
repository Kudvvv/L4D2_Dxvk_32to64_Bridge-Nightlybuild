# L4D2 Bridge Nightly

[简体中文](README.md) | **English**

## Download and installation — start here

**[Download the full package from Releases](https://github.com/NPCodex/L4D2_Dxvk_32to64_Bridge-Nightlybuild/releases)**. Each release has one `l4d2-bridge-*.zip` and its `.sha256` checksum. There is no separate update ZIP or ThinFlex download.

1. **Exit the game and Bridge Host, then back up existing files.** Extract the ZIP into a temporary directory.
2. **Preserve configuration before upgrading:** remove the packaged `bin/.l4d2bridge/bridge.conf` from the temporary extraction directory, keeping your installed configuration. If you customized your backend, also remove `bin/.l4d2bridge/d3d9vk_x64.dll` from that temporary directory. Skip this step on first installation. Existing `dxvk.conf`, ReShade and the DB are not included and will not be overwritten.
3. **Install Bridge:** merge the prepared contents into the game root beside `left4dead2.exe`, updating the client and Host together. The client goes in `bin/d3d9.dll`; the matching x64 Host, backend and configuration stay in `bin/.l4d2bridge`. Remove `-vulkan` for the default loading path.
4. **Applying the ThinFlex crash repair:** use the included `tools/thinflex/ThinFlexPatch.exe`; Python is not required. Follow the [tool guide](docs/THINFLEX-TEST-README.txt) or packaged `tools/thinflex/README.txt` to create, verify, back up and install the repaired copy. **Extracting the ZIP does not automatically patch `studiorender.dll`.** An already installed, working ThinFlex repair can be retained.

The user has reported a successful ThinFlex retest. The repair remains restricted to the exact original DLL documented in the guide; other versions are rejected. Recheck compatibility after game updates.

To use `-vulkan`, rename the client to `dxvk_d3d9.dll` within the game `bin`. When switching to the default loading path, back up the old `bin/dxvk_d3d9.dll` and remove `-vulkan`. Both paths share `bin/.l4d2bridge`.

Roll back the Bridge client and Host together. The tool guide covers restoring ThinFlex. To uninstall, remove the installed files and restore your backups.

See the [three paired performance runs and limitations](docs/PERFORMANCE-2026-10-10.md) and [game validation guide](docs/GAME-VALIDATION.md).

Based on [NVIDIA dxvk-remix Bridge](https://github.com/NVIDIAGameWorks/dxvk-remix), this repository retains the patches from the [original L4D2 project](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge) and automatically builds an x86 client and an x64 Host for 32-bit Left 4 Dead 2.

## Differences from upstream

- Builds only Bridge; the RTX Remix renderer is neither built nor distributed.
- Applies L4D2 patches for Host and backend loading paths, surface and buffer shadow-memory management, diagnostic logging, and game-specific configuration. See [patches/l4d2-bridge.patch](patches/l4d2-bridge.patch).
- Uses **DXVK-GPLALL 2.6.8-2 x64** as the default backend. Its version and download checksum are pinned separately in [config/backend.json](config/backend.json); updating Bridge does not automatically update the backend.
- Adds upstream monitoring, automated builds and tests, Nightly releases, and minimal runtime packaging.
- Fixes volume-texture byte pitches and upload offsets to prevent corrupted color-correction lookup tables. See [fix provenance and validation](docs/VOLUME-TEXTURE-COLOR-FIX.md).
- Ports texture-creation failure cleanup, ATI1/ATI2 compressed-transfer bounds fixes, and event-based command-queue wakeups from the original project, with native tests. See [update tracking](docs/ORIGINAL-PROJECT-UPDATES.md).
- Extends creation-failure cleanup to volume/cube textures, vertex/index buffers and standalone surfaces, releasing client wrappers and clearing outputs. Response timeouts retain ordered server cleanup.
- Hardens buffer-lock bounds and volume temporary ownership, and optimizes contiguous uploads and queue reads. See [validation methodology](docs/RUNTIME-RELIABILITY.md).

`d3d9.dll` is the 32-bit Bridge client; `d3d9vk_x64.dll` is the 64-bit DXVK backend. They serve different purposes.

## Automatic and manual builds

The workflow checks the upstream default branch (currently `main`) every hour at minute 23. It builds unpublished commits and skips commits that already have a published release. GitHub scheduling may be delayed.

Under **Actions → Build latest upstream Bridge → Run workflow**:

- Leave `upstream_commit` empty to follow the latest source, or enter a full 40-character SHA to select a commit.
- Enable `force_rebuild` to create a new independent build without replacing existing assets. This option is disabled by default.
- Enable `validation_only` to build, test and run A/B benchmarks, saving artifacts and skipping publication.
- Enable `thinflex_test` to label a performance + ThinFlex test release (Pre-release, not Latest). Every build includes `tools/thinflex` in one full package; applying the engine repair remains a separate step.

Deduplication checks both upstream SHA and a fingerprint of build/package/test inputs. Versions use `nightly-YYYYMMDD-upstreamSHA-rRecipeDigest-bRunID.Attempt`. Dates use upstream commit UTC time. Rebuilds and reruns have separate versions, preserving old assets. Release notes and packaged `UPSTREAM.json` record full identities. Patch, compile or test failures prevent publication.

When reusing a local source checkout, the build script verifies the complete patch and index, rejecting additional source changes while preserving the checkout. Rerunning a failed publish job searches paginated release listings for the unpublished draft, verifies existing assets and uploads only missing files. Conflicting assets stop publication; existing files are never overwritten.

## License

- Project-specific additions and modifications: **MIT**, see [LICENSE](LICENSE). The original copyright notice for `yeyunyyds` is retained.
- NVIDIA Bridge: **MIT**, see [licenses/Bridge-MIT.txt](licenses/Bridge-MIT.txt).
- DXVK / DXVK-GPLALL: distributed with the **zlib/libpng** license; see [licenses/DXVK-LICENSE.txt](licenses/DXVK-LICENSE.txt) and [licenses/DXVK-GPLALL-LICENSE.txt](licenses/DXVK-GPLALL-LICENSE.txt).
- Dependencies included in Bridge, such as Detours and Tracy, retain their respective licenses. See [licenses/Bridge-third-party.txt](licenses/Bridge-third-party.txt).

The root MIT license does not replace third-party licenses. Release packages retain copyright and license notices. See [THIRD_PARTY.md](THIRD_PARTY.md) for full attribution. The Left 4 Dead 2 game itself is outside the scope of this project's license.
