"""A full merge must ship a matched trio and optional plugin without extra packages."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import package_release as package


class FullPackage(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "source"
        self.output = self.root / "dist/full"
        for name in ("README.md", "VERSION", "LICENSE", "THIRD_PARTY.md", "config/bridge.conf",
                     "docs/TESTING.md", "docs/MEMORY-DIAGNOSTICS.md", "docs/FIRST-GAME-VALIDATION.md",
                     "patches/l4d2-bridge.patch", "source/bridge/LICENSE-MIT", "source/bridge/ThirdPartyLicenses.txt",
                     "licenses/DXVK-LICENSE.txt", "licenses/DXVK-GPLALL-LICENSE.txt",
                     "scripts/analyze_api_wait.py", "scripts/analyze_color_diagnostics.py",
                     "scripts/analyze_data_diagnostics.py", "scripts/install_color_diagnostics.ps1"):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture", encoding="utf-8")
        (self.root / "VERSION").write_text("1.1\n", encoding="utf-8")
        self.identity = "l4d2-1.1+" + hashlib.sha256(b"fixture").hexdigest()[:16]
        self.client = self.binary("source/bridge/_compDebugOptimized_x86/src/client/d3d9.dll", 0x14c)
        self.host64 = self.binary("source/bridge/_compDebugOptimized_x64/src/server/L4D2Bridge64.exe", 0x8664)
        self.host32 = self.binary("source/bridge/_compDebugOptimized_x86_server/src/server/L4D2Bridge32.exe", 0x14c)
        self.backend64 = self.binary("backend64.dll", 0x8664)
        self.backend32 = self.binary("backend32.dll", 0x14c)
        self.plugin = self.binary("plugin.dll", 0x14c)
        archive = self.root / ".deps/gplall/backend.zip"
        archive.parent.mkdir(parents=True)
        archive.write_bytes(b"verified backend archive fixture")
        self.metadata = {"name": "DXVK-GPLALL", "version": "2.6.8-2", "release": "fixture-release",
                         "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                         "files": {"x64/d3d9.dll": hashlib.sha256(self.backend64.read_bytes()).hexdigest(),
                                   "x32/d3d9.dll": hashlib.sha256(self.backend32.read_bytes()).hexdigest()}}
        (self.root / "config/backend.json").write_text(json.dumps(self.metadata), encoding="utf-8")
        for target, value in (("ROOT", self.root), ("source_engine_files", lambda: {"bin/studiorender.dll": b"verified fixture"}),
                              ("source_l4n_files", lambda: {"left4dead2.exe": b"verified L4N fixture", "readme_l4n.txt": b"Starfell original"})):
            patcher = mock.patch.object(package, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch.object(package.subprocess, "check_output", return_value="a" * 40)
        patcher.start()
        self.addCleanup(patcher.stop)

    def binary(self, name, architecture):
        data = bytearray(128)
        data[:2] = b"MZ"
        struct.pack_into("<I", data, 60, 64)
        data[64:68] = b"PE\0\0"
        struct.pack_into("<H", data, 68, architecture)
        struct.pack_into("<H", data, 86, 0x20)
        data.extend(self.identity.encode())
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def run_package(self):
        package.package(self.source, self.backend64, self.output, self.backend32, self.plugin)

    def test_full_package_contains_all_features_with_exact_backend_receipt(self):
        self.run_package()
        self.assertEqual([path.name for path in self.output.parent.iterdir()], ["full"])
        receipt = json.loads((self.output / "BUILD-INFO.json").read_text())
        self.assertEqual(receipt["build_id"], self.identity)
        self.assertEqual(receipt["l4n_author"], "Starfell")
        self.assertEqual(receipt["l4n_version"], "2.51.0")
        self.assertEqual((self.output / "left4dead2.exe").read_bytes(), b"verified L4N fixture")
        self.assertEqual((self.output / "readme_l4n.txt").read_bytes(), b"Starfell original")
        manifest = json.loads((self.output / "SHA256.json").read_text())
        for relative, digest in manifest.items():
            self.assertEqual(hashlib.sha256((self.output / relative).read_bytes()).hexdigest(), digest)
        self.assertEqual((self.output / "optional/L4N/L4D2BridgePlugin.dll").read_bytes(), self.plugin.read_bytes())
        self.assertFalse((self.output / "bin/neko").exists())
        backend = json.loads((self.output / "BACKEND.json").read_text())
        self.assertEqual(backend["source"], "fixture-release")
        self.assertEqual(backend["files"]["x86"], self.metadata["files"]["x32/d3d9.dll"])
        self.assertEqual(backend["default_architecture"], "x86_64")

    def test_bad_identity_architecture_and_laa_fail_before_any_output(self):
        for target, offset, replacement, error in (
            (self.host32, 128, b"incorrect", "identity"),
            (self.backend32, 68, struct.pack("<H", 0x8664), "architecture"),
            (self.host32, 86, b"\0\0", "LARGEADDRESSAWARE"),
            (self.plugin, 60, struct.pack("<I", 0xfffffff0), "PE signature"),
        ):
            with self.subTest(error=error):
                original = target.read_bytes()
                data = bytearray(original)
                data[offset:offset + len(replacement)] = replacement
                target.write_bytes(data)
                with self.assertRaisesRegex(ValueError, error):
                    self.run_package()
                self.assertFalse(self.output.exists())
                target.write_bytes(original)

    def test_existing_output_is_preserved(self):
        self.output.mkdir(parents=True)
        (self.output / "private.txt").write_bytes(b"existing")
        with self.assertRaises(FileExistsError):
            self.run_package()
        self.assertEqual((self.output / "private.txt").read_bytes(), b"existing")


if __name__ == "__main__":
    unittest.main()
