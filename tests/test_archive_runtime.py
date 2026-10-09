"""The single full runtime ZIP carries the validated tool, never game DLLs."""
import json
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import archive_runtime as runtime
import package_thinflex_test as tool


class Packaging(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.source.mkdir()
        for name in runtime.REQUIRED + ("UPSTREAM.json", "licenses/Bridge-MIT.txt"):
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"fixture")
        recipe = self.root / "recipe"
        for _, relative in tool.SOURCE_FILES:
            destination = recipe / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(tool.ROOT / relative, destination)
        (recipe / "VERSION").write_text("1.0.6\n")
        exe = recipe / "ThinFlexPatch.exe"
        data = bytearray(512)
        data[:2] = b"MZ"
        struct.pack_into("<I", data, 0x3C, 0x80)
        data[0x80:0x84] = b"PE\0\0"
        struct.pack_into("<HHIIIHH", data, 0x84, 0x8664, 1, 0, 0, 0, 240, 2)
        struct.pack_into("<H", data, 0x98, 0x20B)
        exe.write_bytes(data)
        license_path = recipe / "license-fixture.txt"
        license_path.write_bytes(b"synthetic license fixture")
        self.tool_directory = self.source / "tools/thinflex"
        self.metadata = tool.package(exe, self.tool_directory, version="1.0.6", recipe_commit="b" * 40,
                                     run_id="123456", python_license=license_path,
                                     pyinstaller_license=license_path, root=recipe)
        self.output = self.root / "full.zip"

    def test_full_package_contains_paired_runtime_and_exact_tools(self):
        for name in ("bin/.l4d2bridge/ReShade.dll", "bin/.l4d2bridge/resource-retention.db",
                     "bin/studiorender.dll", "player.dmp", "private.log"):
            (self.source / name).write_bytes(b"must not ship")
        runtime.runtime_archive(self.source, self.output)
        with zipfile.ZipFile(self.output) as archive:
            names = set(archive.namelist())
            self.assertTrue(set(runtime.REQUIRED).issubset(names))
            self.assertIn("UPSTREAM.json", names)
            expected_tools = {"tools/thinflex/" + name for name in tool.TOOL_FILES}
            self.assertEqual({name for name in names if name.startswith("tools/")}, expected_tools)
            self.assertEqual(json.loads(archive.read("tools/thinflex/BUILD.json")), self.metadata)
            self.assertEqual({name for name in names if name.endswith(".dll")},
                             {"bin/d3d9.dll", "bin/.l4d2bridge/d3d9vk_x64.dll"})
            for name in ("bin/dxvk_d3d9.dll", "d3d9.dll", "bin/.l4d2bridge/ReShade.dll",
                         "bin/.l4d2bridge/resource-retention.db", "bin/studiorender.dll", "player.dmp", "private.log"):
                self.assertNotIn(name, names)
            guide = archive.read("README.txt").decode("utf-8")
            self.assertLess(guide.index("先从临时目录移除"), guide.index("然后将临时目录内容合并"))
            self.assertIn("tools/thinflex", guide)
            self.assertNotIn("update 包", guide)
        before = self.output.read_bytes()
        with self.assertRaises(FileExistsError):
            runtime.runtime_archive(self.source, self.output)
        self.assertEqual(self.output.read_bytes(), before)

    def test_missing_tool_directory_is_rejected(self):
        self.tool_directory.rename(self.tool_directory.with_name("elsewhere"))
        with self.assertRaisesRegex(ValueError, "ThinFlex tool directory"):
            runtime.runtime_archive(self.source, self.output)
        self.assertFalse(self.output.exists())

    def test_unexpected_tool_file_is_rejected_without_archive(self):
        for name in ("studiorender.dll", "private.log", "player.dmp"):
            with self.subTest(name=name):
                path = self.tool_directory / name
                path.write_bytes(b"must not ship")
                with self.assertRaisesRegex(ValueError, "Unexpected ThinFlex tool entry"):
                    runtime.runtime_archive(self.source, self.output)
                self.assertFalse(self.output.exists())
                path.unlink()

    def test_tool_payload_tampering_is_rejected(self):
        (self.tool_directory / "README.txt").write_bytes(b"changed after packaging")
        with self.assertRaisesRegex(ValueError, "hashes"):
            runtime.runtime_archive(self.source, self.output)
        self.assertFalse(self.output.exists())

    def test_archive_uses_verified_tool_snapshot(self):
        original_read = runtime.read_tool_directory
        original_bytes = (self.tool_directory / "README.txt").read_bytes()

        def change_after_read(source):
            files = original_read(source)
            (source / "README.txt").write_bytes(b"unverified later contents")
            return files

        with patch.object(runtime, "read_tool_directory", change_after_read):
            runtime.runtime_archive(self.source, self.output)
        with zipfile.ZipFile(self.output) as archive:
            self.assertEqual(archive.read("tools/thinflex/README.txt"), original_bytes)

    def test_competing_output_is_preserved(self):
        original_archive = runtime.archive

        def race(source, output):
            original_archive(source, output)
            self.output.write_bytes(b"another build")

        with patch.object(runtime, "archive", race):
            with self.assertRaises(FileExistsError):
                runtime.runtime_archive(self.source, self.output)
        self.assertEqual(self.output.read_bytes(), b"another build")

    def test_partial_final_archive_is_removed(self):
        original_copy = shutil.copyfileobj

        def fail(source, target, *args, **kwargs):
            if getattr(target, "name", None) == str(self.output):
                target.write(b"partial archive")
                raise OSError("simulated disk full")
            return original_copy(source, target, *args, **kwargs)

        with patch.object(shutil, "copyfileobj", fail):
            with self.assertRaisesRegex(OSError, "disk full"):
                runtime.runtime_archive(self.source, self.output)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
