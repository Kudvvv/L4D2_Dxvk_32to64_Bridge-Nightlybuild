"""Validate PE architectures before assembling a non-deploying test package."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct

ROOT = Path(__file__).resolve().parents[1]


def machine(path):
    data = path.read_bytes()
    if len(data) < 64 or data[:2] != b"MZ":
        raise ValueError(f"Not a PE file: {path}")
    offset = struct.unpack_from("<I", data, 60)[0]
    if data[offset:offset + 4] != b"PE\0\0":
        raise ValueError(f"Invalid PE signature: {path}")
    return struct.unpack_from("<H", data, offset + 4)[0]


def package(source, dxvk, output):
    inputs = {
        "bin/dxvk_d3d9.dll": (source / "bridge/_compDebugOptimized_x86/src/client/d3d9.dll", 0x14c),
        "bin/.l4d2bridge/L4D2Bridge64.exe": (source / "bridge/_compDebugOptimized_x64/src/server/L4D2Bridge64.exe", 0x8664),
        "bin/.l4d2bridge/d3d9vk_x64.dll": (dxvk, 0x8664),
    }
    # Validate all inputs before creating output. Never deploy into a game directory.
    for path, expected in inputs.values():
        if machine(path) != expected:
            raise ValueError(f"Wrong architecture: {path}")
    output.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for relative, (path, _) in inputs.items():
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        hashes[relative] = hashlib.sha256(destination.read_bytes()).hexdigest()
    shutil.copy2(ROOT / "config/bridge.conf", output / "bin/.l4d2bridge/bridge.conf")
    shutil.copy2(ROOT / "docs/TESTING.md", output / "TESTING.md")
    shutil.copy2(ROOT / "docs/MEMORY-DIAGNOSTICS.md", output / "MEMORY-DIAGNOSTICS.md")
    licenses = output / "licenses"
    licenses.mkdir()
    shutil.copy2(source / "bridge/LICENSE-MIT", licenses / "Bridge-MIT.txt")
    shutil.copy2(source / "bridge/ThirdPartyLicenses.txt", licenses / "Bridge-third-party.txt")
    shutil.copy2(ROOT / "licenses/DXVK-LICENSE.txt", licenses / "DXVK-LICENSE.txt")
    (output / "SHA256.json").write_text(json.dumps(hashes, indent=2) + "\n")
    print(f"Experimental package: {output}; game runtime is not validated")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--dxvk", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/l4d2-experiment")
    args = parser.parse_args()
    package(args.source.resolve(), args.dxvk.resolve(), args.output.resolve())
