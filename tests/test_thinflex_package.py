"""The staged tool directory must exclude private evidence and game binaries."""
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

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
        self.output = self.root / "tools/thinflex"
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
        files = pack.read_tool_directory(self.output)
        self.assertEqual(set(files), {
            "ThinFlexPatch.exe", "patch_studiorender_flex.py", "docs/THINFLEX-CRASH-FIX.md",
            "README.txt", "LICENSE", "BUILD.json", "licenses/Python-LICENSE.txt",
            "licenses/PyInstaller-COPYING.txt", "licenses/EXE-NOTICES.txt",
        })
        self.assertEqual(json.loads(files["BUILD.json"]), metadata)
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
            self.assertEqual(digest, hashlib.sha256(files[name]).hexdigest())
        self.assertEqual(files["licenses/Python-LICENSE.txt"], self.python_license.read_bytes())
        self.assertEqual(files["licenses/PyInstaller-COPYING.txt"], self.pyinstaller_license.read_bytes())
        self.assertFalse(list(self.root.rglob("*.zip")))
        self.assertFalse(list(self.root.rglob("*.sha256")))

    def test_missing_tool_rejected_without_output(self):
        self.exe.unlink()
        with self.assertRaises(FileNotFoundError):
            self.package()
        self.assertFalse(self.output.exists())

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
        self.output.parent.mkdir(parents=True)
        for directory in (False, True):
            with self.subTest(directory=directory):
                if directory:
                    self.output.mkdir()
                    existing = self.output / "keep.txt"
                else:
                    existing = self.output
                existing.write_bytes(b"keep previous build")
                with self.assertRaises(FileExistsError):
                    self.package()
                self.assertEqual(existing.read_bytes(), b"keep previous build")
                existing.unlink()
                if directory:
                    self.output.rmdir()

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

    def test_partial_directory_cleanup(self):
        original_open = Path.open

        def fail(path, *args, **kwargs):
            if path == self.output / "patch_studiorender_flex.py" and args and args[0] == "xb":
                raise OSError("simulated disk full")
            return original_open(path, *args, **kwargs)

        with patch.object(Path, "open", fail):
            with self.assertRaises(OSError):
                self.package()
        self.assertFalse(self.output.exists())

    def test_directory_creation_race_preserves_other_output(self):
        original_mkdir = Path.mkdir

        def race(path, *args, **kwargs):
            if path == self.output:
                original_mkdir(path)
                (path / "another-build.txt").write_bytes(b"another build")
            return original_mkdir(path, *args, **kwargs)

        with patch.object(Path, "mkdir", race):
            with self.assertRaises(FileExistsError):
                self.package()
        self.assertEqual((self.output / "another-build.txt").read_bytes(), b"another build")
        self.assertEqual(list(self.output.iterdir()), [self.output / "another-build.txt"])

    def test_inventory_rejects_game_dll_private_files_and_missing_tools(self):
        self.package()
        for relative in ("studiorender.dll", "logs/private.log", "docs/player.dmp"):
            with self.subTest(relative=relative):
                path = self.output / relative
                path.parent.mkdir(exist_ok=True)
                path.write_bytes(b"must not ship")
                with self.assertRaisesRegex(ValueError, "Unexpected"):
                    pack.read_tool_directory(self.output)
                path.unlink()
                if path.parent not in (self.output, self.output / "docs"):
                    path.parent.rmdir()
        (self.output / "ThinFlexPatch.exe").unlink()
        with self.assertRaisesRegex(ValueError, "Missing ThinFlex tool files"):
            pack.read_tool_directory(self.output)

    def test_inventory_rejects_changed_payload_and_manifest(self):
        self.package()
        readme = self.output / "README.txt"
        original = readme.read_bytes()
        readme.write_bytes(original + b"\nchanged after staging\n")
        with self.assertRaisesRegex(ValueError, "hashes"):
            pack.read_tool_directory(self.output)
        readme.write_bytes(original)
        manifest = self.output / "BUILD.json"
        metadata = json.loads(manifest.read_bytes())
        metadata["sha256"]["studiorender.dll"] = "0" * 64
        manifest.write_text(json.dumps(metadata))
        with self.assertRaisesRegex(ValueError, "hashes"):
            pack.read_tool_directory(self.output)

    def test_inventory_rejects_linked_file(self):
        self.package()
        destination = self.output / "README.txt"
        target = self.root / "external.txt"
        target.write_bytes(destination.read_bytes())
        destination.unlink()
        try:
            destination.symlink_to(target)
        except OSError as error:
            self.skipTest(f"Symlinks unavailable: {error}")
        with self.assertRaisesRegex(ValueError, "Linked"):
            pack.read_tool_directory(self.output)


if __name__ == "__main__":
    unittest.main()
