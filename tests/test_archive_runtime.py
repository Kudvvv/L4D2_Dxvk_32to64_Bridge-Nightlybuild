"""The full ZIP carries only the exact engine repair and selected runtime files."""
import hashlib
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
import l4n_payload as l4n


class Packaging(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.source.mkdir()
        for name in runtime.REQUIRED + runtime.NOTICE_INPUTS + ("UPSTREAM.json",):
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"fixture")
        self.engine_files = engine.source_engine_files()
        self.l4n_files = l4n.source_l4n_files()
        for relative, data in {**self.engine_files, **self.l4n_files}.items():
            destination = self.source / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        (self.source / "VERSION").write_bytes(b"1.1.4\n")
        manifest = {name: hashlib.sha256((self.source / name).read_bytes()).hexdigest()
                    for name in runtime.REQUIRED if name.endswith((".dll", ".exe"))}
        (self.source / "SHA256.json").write_text(json.dumps(manifest), encoding="utf-8")
        self.output = self.root / "full.zip"

    def test_full_package_contains_only_audited_runtime_and_two_text_documents(self):
        for name in ("bin/.l4d2bridge/ReShade.dll", "bin/.l4d2bridge/resource-retention.db",
                     "bin/other-engine.dll", "player.dmp", "private.log", "docs/guide.md",
                     "config/example.conf", "scripts/tool.py", "config.json", "licenses/private.txt"):
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"must not ship")
        runtime.runtime_archive(self.source, self.output)
        with zipfile.ZipFile(self.output) as archive:
            names = set(archive.namelist())
            l4n_runtime = runtime.select_l4n_runtime(self.l4n_files)
            expected = set(runtime.REQUIRED) | set(l4n_runtime) | {
                "bin/studiorender.dll", "README.txt", "THIRD-PARTY-NOTICES.txt"}
            expected.remove("optional/L4N/L4D2BridgePlugin.dll")
            expected.add("bin/neko/plugins/L4D2BridgePlugin.dll")
            self.assertEqual(names, expected)
            self.assertEqual(len(names), 68)
            for name in runtime.REQUIRED:
                destination = ("bin/neko/plugins/L4D2BridgePlugin.dll"
                               if name == "optional/L4N/L4D2BridgePlugin.dll" else name)
                self.assertEqual(archive.read(destination), (self.source / name).read_bytes())
            self.assertFalse(any(name.startswith("optional/") for name in names))
            self.assertEqual(archive.read("bin/studiorender.dll"), self.engine_files["bin/studiorender.dll"])
            for name, data in l4n_runtime.items():
                self.assertEqual(archive.read(name), data)
            self.assertIn("left4dead2/neko/server_name_filter_template.txt", names)
            self.assertIn("left4dead2/bin/game_shader_generic_neko", names)
            # These original L4N companion files were lost during ZIP slimming.
            # Check delivery independently of the packager's runtime selection.
            for basename in ("localize_overrides_template.vdf", "mdl_extension.qc",
                             "neko_proxy.vmt", "scheme_overrides_template.vdf",
                             "sequence_event_template.vdf"):
                name = "left4dead2/neko/" + basename
                self.assertIn(name, names)
                self.assertEqual(archive.read(name), self.l4n_files[name])
            self.assertNotIn("left4dead2/neko/config_template.vdf", names)
            self.assertFalse(any(name.endswith((".json", ".md", ".py", ".ps1", ".bat", ".7z")) for name in names))
            self.assertFalse(any(name.startswith(("scripts/", "docs/", "config/", "licenses/")) for name in names))
            self.assertEqual({name for name in names if name.startswith("bin/neko/")},
                             {"bin/neko/plugins/L4D2BridgePlugin.dll"})
            self.assertNotIn("readme_l4n.txt", names)
            notices = archive.read("THIRD-PARTY-NOTICES.txt")
            for name in runtime.NOTICE_INPUTS:
                self.assertIn((self.source / name).read_bytes(), notices)
            self.assertNotIn(b"must not ship", notices)
            guide = archive.read("README.txt").decode("utf-8")
            self.assertIn("v1.1.4", guide)
            self.assertIn("无需运行修复工具", guide)
            self.assertIn("原始备份", guide)
            self.assertIn("Starfelll", guide)
            self.assertIn("bin/neko/plugins/L4D2BridgePlugin.dll", guide)
            self.assertNotIn("optional/", guide)
            self.assertIn(engine.ORIGINAL_SHA256, guide)
            self.assertIn(engine.PATCHED_SHA256, guide)
            self.assertNotIn("ENGINE-PATCH.json", guide)
            self.assertNotIn("L4N-PAYLOAD.json", guide)
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

    def test_archive_uses_verified_l4n_snapshot_and_excludes_private_archives(self):
        original_read = runtime.staged_l4n_files
        expected = self.l4n_files["left4dead2.exe"]
        for name in ("logs.7z", "L4N_v2.51.0.7z", "crash_dumps/player.dmp"):
            (self.source / name).write_bytes(b"private or duplicate archive")

        def change_after_read(source):
            files = original_read(source)
            (source / "left4dead2.exe").write_bytes(b"unverified later contents")
            return files

        with patch.object(runtime, "staged_l4n_files", change_after_read):
            runtime.runtime_archive(self.source, self.output)
        with zipfile.ZipFile(self.output) as archive:
            self.assertEqual(archive.read("left4dead2.exe"), expected)
            for name in ("logs.7z", "L4N_v2.51.0.7z", "crash_dumps/player.dmp"):
                self.assertNotIn(name, archive.namelist())
            self.assertNotIn("bin/neko/other_tools.7z", archive.namelist())

    def test_excluded_source_developer_tools_still_require_valid_provenance(self):
        path = self.source / "bin/neko/other_tools.7z"
        path.write_bytes(b"unverified source archive")
        with self.assertRaisesRegex(ValueError, "differs"):
            runtime.runtime_archive(self.source, self.output)
        self.assertFalse(self.output.exists())

    def test_binary_receipt_or_required_license_failure_never_creates_output(self):
        binary = self.source / "bin/.l4d2bridge/L4D2Bridge64.exe"
        original = binary.read_bytes()
        binary.write_bytes(b"unverified replacement host")
        with self.assertRaisesRegex(ValueError, "source package receipt"):
            runtime.runtime_archive(self.source, self.output)
        self.assertFalse(self.output.exists())
        binary.write_bytes(original)
        (self.source / "licenses/DXVK-GPLALL-LICENSE.txt").unlink()
        with self.assertRaises(FileNotFoundError):
            runtime.runtime_archive(self.source, self.output)
        self.assertFalse(self.output.exists())

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
