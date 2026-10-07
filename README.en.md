# L4D2 Bridge Nightly

[简体中文](README.md) | **English**

Based on [NVIDIA dxvk-remix Bridge](https://github.com/NVIDIAGameWorks/dxvk-remix), this repository retains the patches from the [original L4D2 project](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge) and automatically builds an x86 client and an x64 Host for 32-bit Left 4 Dead 2.

## Differences from upstream

- Builds only Bridge; the RTX Remix renderer is neither built nor distributed.
- Applies L4D2 patches for Host and backend loading paths, surface and buffer shadow-memory management, diagnostic logging, and game-specific configuration. See [patches/l4d2-bridge.patch](patches/l4d2-bridge.patch).
- Uses **DXVK-GPLALL 2.6.8-2 x64** as the default backend. Its version and download checksum are pinned separately in [config/backend.json](config/backend.json); updating Bridge does not automatically update the backend.
- Adds upstream monitoring, automated builds and tests, Nightly releases, and minimal runtime packaging.
- Fixes volume-texture byte pitches and upload offsets to prevent corrupted color-correction lookup tables. See [fix provenance and validation](docs/VOLUME-TEXTURE-COLOR-FIX.md).
- Ports texture-creation failure cleanup, ATI1/ATI2 compressed-transfer bounds fixes, and event-based command-queue wakeups from the original project, with native tests. See [update tracking](docs/ORIGINAL-PROJECT-UPDATES.md).

`dxvk_d3d9.dll` is the 32-bit Bridge client; `d3d9vk_x64.dll` is the 64-bit DXVK backend. They serve different purposes.

## Automatic and manual builds

The workflow checks the upstream default branch (currently `main`) every hour at minute 23. It builds unpublished commits and skips commits that already have a published release. GitHub scheduling may be delayed.

Under **Actions → Build latest upstream Bridge → Run workflow**:

- Leave `upstream_commit` empty to follow the latest source, or enter a full 40-character SHA to select a commit.
- Enable `force_rebuild` to create a new independent build without replacing existing assets. This option is disabled by default.

Deduplication checks both upstream SHA and a fingerprint of build/package/test inputs. Versions use `nightly-YYYYMMDD-upstreamSHA-rRecipeDigest-bRunID.Attempt`. Dates use upstream commit UTC time. Rebuilds and reruns have separate versions, preserving old assets. Release notes and packaged `UPSTREAM.json` record full identities. Patch, compile or test failures prevent publication.

## Download and installation

Download the ZIP from [Releases](https://github.com/Kudvvv/L4D2_Dxvk_32to64_Bridge-Nightlybuild/releases). It contains only runtime files, a short installation guide, and license notices. A separate `.sha256` checksum file is provided.

For first installation, exit the game, back up files and merge the full package's `bin` folder into the game's `bin`, preserving `.l4d2bridge`. The full package contains configuration and backend files and replaces them when overwritten.

For an existing installation, prefer the `l4d2-bridge-update-*` ZIP. It updates the client and Host together, preserving configuration, DXVK, ReShade and the retention DB. Roll back the client and Host together. See [game validation and performance baselines](docs/GAME-VALIDATION.md); measured game results are still pending.

Automated tests check compilation and diagnostic logic; they do not verify in-game compatibility.

## License

- Project-specific additions and modifications: **MIT**, see [LICENSE](LICENSE). The original copyright notice for `yeyunyyds` is retained.
- NVIDIA Bridge: **MIT**, see [licenses/Bridge-MIT.txt](licenses/Bridge-MIT.txt).
- DXVK / DXVK-GPLALL: distributed with the **zlib/libpng** license; see [licenses/DXVK-LICENSE.txt](licenses/DXVK-LICENSE.txt) and [licenses/DXVK-GPLALL-LICENSE.txt](licenses/DXVK-GPLALL-LICENSE.txt).
- Dependencies included in Bridge, such as Detours and Tracy, retain their respective licenses. See [licenses/Bridge-third-party.txt](licenses/Bridge-third-party.txt).

The root MIT license does not replace third-party licenses. Release packages retain copyright and license notices. See [THIRD_PARTY.md](THIRD_PARTY.md) for full attribution. The Left 4 Dead 2 game itself is outside the scope of this project's license.
