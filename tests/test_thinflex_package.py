"""The tool archive must exclude private evidence and all game binaries."""
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import package_thinflex_test as pack


def tool_pe():
    """Small synthetic executable header; contains no third-party binary."""
    data = bytearray(512)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 0x80)
    data[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<HHIIIHH", data, 0x84, 0x8664, 1, 0, 0, 0, 240, 2)
    struct.pack_into("<H", data, 0x98, 0x20B)
    return bytes(data)


class ThinFlexPackage(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for _, relative in pack.SOURCE_FILES:
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(pack.ROOT / relative, destination)
        (self.root / "VERSION").write_text("1.0.6\n")
        self.exe = self.root / "ThinFlexPatch.exe"
        self.exe.write_bytes(tool_pe())
        self.python_license = self.root / "python-license.txt"
        self.python_license.write_text("Synthetic Python license fixture\n")
        self.pyinstaller_license = self.root / "pyinstaller-license.txt"
        self.pyinstaller_license.write_text("Synthetic PyInstaller license fixture\n")
        self.output = self.root / "l4d2-bridge-thinflex-test-test.1.zip"
        self.sidecar = self.output.with_name(self.output.name + ".sha256")
        self.kwargs = dict(version="1.0.6", recipe_commit="b" * 40, run_id="123456",
                           python_license=self.python_license, pyinstaller_license=self.pyinstaller_license,
                           root=self.root)

    def package(self, **kwargs):
        return pack.package(self.exe, self.output, **(self.kwargs | kwargs))

    def test_exact_allowlist_metadata_and_sha256(self):
        # These files are intentionally adjacent to inputs, to catch traversal.
        for relative in ("studiorender.dll", "bridge64.log", "left4dead2.dmp", "docs/private.log"):
            (self.root / relative).write_bytes(b"private material must never ship")
        metadata = self.package()
        with zipfile.ZipFile(self.output) as archive:
            self.assertEqual(set(archive.namelist()), {
                "ThinFlexPatch.exe", "patch_studiorender_flex.py", "docs/THINFLEX-CRASH-FIX.md",
                "README.txt", "LICENSE", "BUILD.json", "licenses/Python-LICENSE.txt",
                "licenses/PyInstaller-COPYING.txt", "licenses/EXE-NOTICES.txt",
            })
            self.assertEqual(json.loads(archive.read("BUILD.json")), metadata)
            self.assertEqual(metadata["version"], "1.0.6")
            self.assertEqual(metadata["recipe_commit"], "b" * 40)
            self.assertEqual(metadata["run_id"], "123456")
            self.assertEqual(metadata["input_dll_sha256"], "3f5f5b0f539e8ad22bcfc4381be41571257c0c29e8061057682f9b8525ca7b85")
            self.assertEqual(metadata["output_dll_sha256"], "03964dedcf8b7f4ebde24cd3d0738873d37c075a7a9b313dad001bb937f9d1b6")
            self.assertIs(metadata["signature_invalid"], True)
            self.assertIs(metadata["game_validated"], False)
            self.assertIs(metadata["game_dll_included"], False)
            self.assertIs(metadata["automatic_installation"], False)
            for name, digest in metadata["sha256"].items():
                self.assertEqual(digest, hashlib.sha256(archive.read(name)).hexdigest())
            self.assertEqual(archive.read("licenses/Python-LICENSE.txt"), self.python_license.read_bytes())
            self.assertEqual(archive.read("licenses/PyInstaller-COPYING.txt"), self.pyinstaller_license.read_bytes())
        digest = hashlib.sha256(self.output.read_bytes()).hexdigest()
        self.assertEqual(self.sidecar.read_text(), f"{digest}  {self.output.name}\n")

    def test_missing_tool_rejected_without_output(self):
        self.exe.unlink()
        with self.assertRaises(FileNotFoundError):
            self.package()
        self.assertFalse(self.output.exists())
        self.assertFalse(self.sidecar.exists())

    def test_invalid_pe_or_dll_rejected(self):
        dll = bytearray(tool_pe())
        struct.pack_into("<H", dll, 0x96, 0x2002)
        malformed_offset = bytearray(tool_pe())
        struct.pack_into("<I", malformed_offset, 0x3C, 0xFFFFFFFF)
        for data in (b"", b"not an executable", b"MZ" + bytes(100), tool_pe()[:100], dll, malformed_offset):
            with self.subTest(length=len(data)):
                self.exe.write_bytes(data)
                with self.assertRaises(ValueError):
                    self.package()
                self.assertFalse(self.output.exists())

    def test_existing_outputs_preserved(self):
        for existing in (self.output, self.sidecar):
            with self.subTest(name=existing.name):
                existing.write_bytes(b"keep previous build")
                with self.assertRaises(FileExistsError):
                    self.package()
                self.assertEqual(existing.read_bytes(), b"keep previous build")
                for target in (self.output, self.sidecar):
                    if target != existing:
                        self.assertFalse(target.exists())
                existing.unlink()

    def test_recipe_changes_require_digest_revalidation(self):
        recipe = self.root / "scripts/patch_studiorender_flex.py"
        recipe.write_bytes(recipe.read_bytes() + b"\n# unvalidated change\n")
        with self.assertRaisesRegex(ValueError, "revalidate"):
            self.package()
        self.assertFalse(self.output.exists())

    def test_metadata_rejected_before_output(self):
        for change in ({"version": "1.0.7"}, {"recipe_commit": "HEAD"}, {"run_id": "0"},
                       {"version": "a\nb"}, {"run_id": "local-test"}):
            with self.subTest(change=change):
                with self.assertRaises(ValueError):
                    self.package(**change)
                self.assertFalse(self.output.exists())

    def test_missing_license_rejected(self):
        self.pyinstaller_license.unlink()
        with self.assertRaises(FileNotFoundError):
            self.package()
        self.assertFalse(self.output.exists())

    def test_partial_archive_cleanup(self):
        with patch.object(zipfile.ZipFile, "writestr", side_effect=OSError("simulated disk full")):
            with self.assertRaises(OSError):
                self.package()
        self.assertFalse(self.output.exists())
        self.assertFalse(self.sidecar.exists())

    def test_sidecar_creation_race_preserves_other_file(self):
        original_open = Path.open

        def race(path, *args, **kwargs):
            if path == self.sidecar and args and args[0] == "x":
                with original_open(path, "wb") as handle:
                    handle.write(b"another build")
            return original_open(path, *args, **kwargs)

        with patch.object(Path, "open", race):
            with self.assertRaises(FileExistsError):
                self.package()
        self.assertFalse(self.output.exists())
        self.assertEqual(self.sidecar.read_bytes(), b"another build")


if __name__ == "__main__":
    unittest.main()
