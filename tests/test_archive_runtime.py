"""The full ZIP carries only the exact engine repair and selected runtime files."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import archive_runtime as runtime
import engine_payload as engine


class Packaging(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.source.mkdir()
        for name in runtime.REQUIRED + runtime.SUPPORT_FILES + ("UPSTREAM.json", "licenses/Bridge-MIT.txt"):
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"fixture")
        self.engine_files = engine.source_engine_files()
        for relative, data in self.engine_files.items():
            destination = self.source / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        self.output = self.root / "full.zip"

    def test_full_package_contains_paired_runtime_and_exact_engine(self):
        for name in ("bin/.l4d2bridge/ReShade.dll", "bin/.l4d2bridge/resource-retention.db",
                     "bin/other-engine.dll", "player.dmp", "private.log"):
            (self.source / name).write_bytes(b"must not ship")
        runtime.runtime_archive(self.source, self.output)
        with zipfile.ZipFile(self.output) as archive:
            names = set(archive.namelist())
            self.assertTrue(set(runtime.REQUIRED).issubset(names))
            self.assertIn("UPSTREAM.json", names)
            self.assertFalse(any(name.startswith("tools/") for name in names))
            for name, data in self.engine_files.items():
                self.assertEqual(archive.read(name), data)
            self.assertEqual({name for name in names if name.endswith(".dll")},
                             {"bin/d3d9.dll", "bin/.l4d2bridge/d3d9vk_x64.dll", "bin/.l4d2bridge/d3d9vk_x86.dll",
                              "optional/L4N/L4D2BridgePlugin.dll", "bin/studiorender.dll"})
            for name in ("bin/dxvk_d3d9.dll", "d3d9.dll", "bin/.l4d2bridge/ReShade.dll",
                         "bin/.l4d2bridge/resource-retention.db", "bin/other-engine.dll", "player.dmp", "private.log"):
                self.assertNotIn(name, names)
            guide = archive.read("README.txt").decode("utf-8")
            self.assertLess(guide.index("先从临时目录移除"), guide.index("然后将临时目录内容合并"))
            self.assertIn("无需运行修复工具", guide)
            self.assertIn("原始备份", guide)
            self.assertNotIn("update 包", guide)
        before = self.output.read_bytes()
        with self.assertRaises(FileExistsError):
            runtime.runtime_archive(self.source, self.output)
        self.assertEqual(self.output.read_bytes(), before)

    def test_missing_engine_is_rejected(self):
        (self.source / "bin/studiorender.dll").unlink()
        with self.assertRaises(FileNotFoundError):
            runtime.runtime_archive(self.source, self.output)
        self.assertFalse(self.output.exists())

    def test_legacy_tool_is_not_published(self):
        tool = self.source / "tools/thinflex/ThinFlexPatch.exe"
        tool.parent.mkdir(parents=True)
        tool.write_bytes(b"old bundled Python tool")
        runtime.runtime_archive(self.source, self.output)
        with zipfile.ZipFile(self.output) as archive:
            self.assertFalse(any(name.startswith("tools/") for name in archive.namelist()))

    def test_engine_and_record_tampering_are_rejected(self):
        for name in ("bin/studiorender.dll", "ENGINE-PATCH.json"):
            with self.subTest(name=name):
                path = self.source / name
                data = path.read_bytes()
                path.write_bytes(data + b"tampered")
                with self.assertRaisesRegex(ValueError, "differs"):
                    runtime.runtime_archive(self.source, self.output)
                self.assertFalse(self.output.exists())
                path.write_bytes(data)

    def test_archive_uses_verified_engine_snapshot(self):
        original_read = runtime.staged_engine_files
        original_bytes = self.engine_files["bin/studiorender.dll"]

        def change_after_read(source):
            files = original_read(source)
            (source / "bin/studiorender.dll").write_bytes(b"unverified later contents")
            return files

        with patch.object(runtime, "staged_engine_files", change_after_read):
            runtime.runtime_archive(self.source, self.output)
        with zipfile.ZipFile(self.output) as archive:
            self.assertEqual(archive.read("bin/studiorender.dll"), original_bytes)

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
