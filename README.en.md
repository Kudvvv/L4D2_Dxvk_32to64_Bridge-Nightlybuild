# L4D2 Bridge Nightly

[简体中文](README.md) | **English**

## Download and installation — start here

**[Download the full package from Releases](https://github.com/NPCodex/L4D2_Dxvk_32to64_Bridge-Nightlybuild/releases)**. Each release has one `l4d2-bridge-*.zip` and its `.sha256` checksum. It includes the repaired `bin/studiorender.dll`; no patch tool or Python installation is needed.

1. **Exit the game and Bridge Host, then back up existing files.** Save the original client, Host, configuration and `bin/studiorender.dll`. Extract the ZIP into a temporary directory. If ThinFlex is already installed, keep the initial original-DLL backup; do not replace it with the repaired file.
2. **Preserve configuration before upgrading:** remove the packaged `bin/.l4d2bridge/bridge.conf` from the temporary extraction directory, keeping your installed configuration. If you customized your backend, also remove `bin/.l4d2bridge/d3d9vk_x64.dll` from that temporary directory. Skip this step on first installation. Existing `dxvk.conf`, ReShade and the DB are not included and will not be overwritten.
3. **Check the installed engine DLL:** run `Get-FileHash 'your-game-directory\bin\studiorender.dll' -Algorithm SHA256` in PowerShell and compare with the table below. The supported original can be replaced. If the repair is already installed, retain it and the original backup. **For any other hash, remove `bin/studiorender.dll` from the temporary extraction directory and update Bridge only.**
4. **Copy the prepared files:** merge them into the game root beside `left4dead2.exe`, updating the client and Host together. Replacing the matching `studiorender.dll` applies the ThinFlex repair directly. The client goes in `bin/d3d9.dll`; the matching x64 Host, backend and configuration stay in `bin/.l4d2bridge`. Remove `-vulkan` for the default loading path.

| Installed `bin/studiorender.dll` | SHA-256 |
|---|---|
| Supported original | `3f5f5b0f539e8ad22bcfc4381be41571257c0c29e8061057682f9b8525ca7b85` |
| Packaged repair | `03964dedcf8b7f4ebde24cd3d0738873d37c075a7a9b313dad001bb937f9d1b6` |

The user has reported a successful ThinFlex retest, limited to this exact version. Recheck after game updates: copying files does not automatically check the installed version. `ENGINE-PATCH.json` records the changes, and `licenses/Valve-engine-NOTICE.txt` preserves attribution. The modified DLL's original digital signature is invalid. See the [installation and restoration guide](docs/THINFLEX-TEST-README.txt).

To use `-vulkan`, rename the client to `dxvk_d3d9.dll` within the game `bin`. When switching to the default loading path, back up the old `bin/dxvk_d3d9.dll` and remove `-vulkan`. Both paths share `bin/.l4d2bridge`.

Roll back the Bridge client and Host together. Restore your original `studiorender.dll` backup to undo ThinFlex. To uninstall, remove the installed files and restore your backups.

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
- Enable `thinflex_test` to label a performance + ThinFlex test release (Pre-release, not Latest). Every build includes the fixed ThinFlex engine DLL in one full package; check the installed game version before copying it.

Deduplication checks both upstream SHA and a fingerprint of build/package/test inputs. Versions use `nightly-YYYYMMDD-upstreamSHA-rRecipeDigest-bRunID.Attempt`. Dates use upstream commit UTC time. Rebuilds and reruns have separate versions, preserving old assets. Release notes and packaged `UPSTREAM.json` record full identities. Patch, compile or test failures prevent publication.

When reusing a local source checkout, the build script verifies the complete patch and index, rejecting additional source changes while preserving the checkout. Rerunning a failed publish job searches paginated release listings for the unpublished draft, verifies existing assets and uploads only missing files. Conflicting assets stop publication; existing files are never overwritten.

## License

- Project-specific additions and modifications: **MIT**, see [LICENSE](LICENSE). The original copyright notice for `yeyunyyds` is retained.
- NVIDIA Bridge: **MIT**, see [licenses/Bridge-MIT.txt](licenses/Bridge-MIT.txt).
- DXVK / DXVK-GPLALL: distributed with the **zlib/libpng** license; see [licenses/DXVK-LICENSE.txt](licenses/DXVK-LICENSE.txt) and [licenses/DXVK-GPLALL-LICENSE.txt](licenses/DXVK-GPLALL-LICENSE.txt).
- Dependencies included in Bridge, such as Detours and Tracy, retain their respective licenses. See [licenses/Bridge-third-party.txt](licenses/Bridge-third-party.txt).
- The modified `studiorender.dll` comes from the maintainer's matching local game file, with the limited ThinFlex repair applied at the user's request. The original engine belongs to Valve and is outside the root MIT license; see [engine attribution](licenses/Valve-engine-NOTICE.txt).

The root MIT license does not replace third-party licenses. Release packages retain copyright and license notices. See [THIRD_PARTY.md](THIRD_PARTY.md) for full attribution. The Left 4 Dead 2 game itself is outside the scope of this project's license.
