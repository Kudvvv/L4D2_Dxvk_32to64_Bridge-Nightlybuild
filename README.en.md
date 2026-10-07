# L4D2 Bridge Nightly

[简体中文](README.md) | **English**

Based on [NVIDIA dxvk-remix Bridge](https://github.com/NVIDIAGameWorks/dxvk-remix), this repository retains the patches from the [original L4D2 project](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge) and automatically builds an x86 client and an x64 Host for 32-bit Left 4 Dead 2.

## Differences from upstream

- Builds only Bridge; the RTX Remix renderer is neither built nor distributed.
- Applies L4D2 patches for Host and backend loading paths, surface and buffer shadow-memory management, diagnostic logging, and game-specific configuration. See [patches/l4d2-bridge.patch](patches/l4d2-bridge.patch).
- Uses **DXVK-GPLALL 2.6.8-2 x64** as the default backend. Its version and download checksum are pinned separately in [config/backend.json](config/backend.json); updating Bridge does not automatically update the backend.
- Adds upstream monitoring, automated builds and tests, Nightly releases, and minimal runtime packaging.
- Fixes volume-texture byte pitches and upload offsets to prevent corrupted color-correction lookup tables. See [fix provenance and validation](docs/VOLUME-TEXTURE-COLOR-FIX.md).

`dxvk_d3d9.dll` is the 32-bit Bridge client; `d3d9vk_x64.dll` is the 64-bit DXVK backend. They serve different purposes.

## Automatic and manual builds

The workflow checks the upstream default branch (currently `main`) every hour at minute 23. It builds unpublished commits and skips commits that already have a published release. GitHub scheduling may be delayed.

Under **Actions → Build latest upstream Bridge → Run workflow**:

- Leave `upstream_commit` empty to follow the latest source, or enter a full 40-character SHA to select a commit.
- Enable `force_rebuild` to recompile an already published commit and replace the assets for the same version. This option is disabled by default.

Versions use `nightly-YYYYMMDD-shortSHA`. The date is the upstream commit date (UTC), rather than the workflow execution date. Release notes link to the exact upstream commit and build configuration. Patch conflicts or compilation failures prevent publication.

## Download and installation

Download the ZIP from [Releases](https://github.com/YuuMJ/L4D2_Dxvk_32to64_Bridge-Nightlybuild/releases). It contains only runtime files, a short installation guide, and license notices. A separate `.sha256` checksum file is provided.

Exit the game and back up the original files. Merge the package's `bin` folder into the game's `bin` folder, preserving the `.l4d2bridge` directory structure. To uninstall, remove the files installed from this package and restore your backups.

Automated tests check compilation and diagnostic logic; they do not verify in-game compatibility.

## License

- Project-specific additions and modifications: **MIT**, see [LICENSE](LICENSE). The original copyright notice for `yeyunyyds` is retained.
- NVIDIA Bridge: **MIT**, see [licenses/Bridge-MIT.txt](licenses/Bridge-MIT.txt).
- DXVK / DXVK-GPLALL: distributed with the **zlib/libpng** license; see [licenses/DXVK-LICENSE.txt](licenses/DXVK-LICENSE.txt) and [licenses/DXVK-GPLALL-LICENSE.txt](licenses/DXVK-GPLALL-LICENSE.txt).
- Dependencies included in Bridge, such as Detours and Tracy, retain their respective licenses. See [licenses/Bridge-third-party.txt](licenses/Bridge-third-party.txt).

The root MIT license does not replace third-party licenses. Release packages retain copyright and license notices. See [THIRD_PARTY.md](THIRD_PARTY.md) for full attribution. The Left 4 Dead 2 game itself is outside the scope of this project's license.
