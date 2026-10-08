import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import prepare_bridge


class Preparation(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "Bridge Test")
        self.git("config", "user.email", "bridge-test@example.invalid")
        self.git("config", "core.autocrlf", "false")
        (self.source / ".gitignore").write_text("build/\n", encoding="utf-8", newline="\n")
        self.original = "".join(f"original line {line}\n" for line in range(40))
        self.patched = self.original.replace("original line 2\n", "patched line 2\n")
        (self.source / "patched.cpp").write_text(self.original, encoding="utf-8", newline="\n")
        (self.source / "unrelated.cpp").write_text("unchanged\n", encoding="utf-8", newline="\n")
        (self.source / "removed.cpp").write_text("obsolete\n", encoding="utf-8", newline="\n")
        self.git("add", ".")
        self.git("commit", "-qm", "upstream")
        self.commit = self.git("rev-parse", "HEAD").decode().strip()
        (self.source / "patched.cpp").write_text(self.patched, encoding="utf-8", newline="\n")
        (self.source / "new.h").write_text("expected new header\n", encoding="utf-8", newline="\n")
        (self.source / "removed.cpp").unlink()
        self.git("add", ".")
        (self.root / "patches").mkdir()
        self.patch_file = self.root / "patches" / "l4d2-bridge.patch"
        self.patch_file.write_bytes(self.git("diff", "--cached", "--binary", "HEAD"))
        self.git("reset", "--hard", "HEAD")
        self.real_run = prepare_bridge.run
        self.submodule_updates = 0
        self.addCleanup(patch.stopall)
        patch.object(prepare_bridge, "ROOT", self.root).start()
        patch.object(prepare_bridge, "run", side_effect=self.run_without_fetch).start()

    def git(self, *args, cwd=None):
        return subprocess.check_output(
            ["git", *args], cwd=cwd or self.source, stderr=subprocess.PIPE)

    def run_without_fetch(self, *args, **kwargs):
        if args[:3] == ("git", "submodule", "update"):
            self.submodule_updates += 1
            return
        return self.real_run(*args, **kwargs)

    def prepare(self):
        prepare_bridge.prepare(self.source, self.commit)

    def snapshot(self):
        files = {
            str(path.relative_to(self.source)): path.read_bytes()
            for path in self.source.rglob("*")
            if ".git" not in path.relative_to(self.source).parts and path.is_file()
        }
        return files, (self.source / ".git" / "index").read_bytes()

    def assert_preserved_rejection(self):
        before = self.snapshot()
        updates = self.submodule_updates
        with self.assertRaisesRegex(RuntimeError, "checkout preserved"):
            self.prepare()
        self.assertEqual(before, self.snapshot())
        self.assertEqual(updates, self.submodule_updates)

    def add_submodule(self):
        origin = self.root / "module-origin"
        origin.mkdir()
        self.git("init", "-q", cwd=origin)
        self.git("config", "user.name", "Bridge Test", cwd=origin)
        self.git("config", "user.email", "bridge-test@example.invalid", cwd=origin)
        (origin / "detours.cpp").write_text("original detours\n", encoding="utf-8", newline="\n")
        (origin / ".gitignore").write_text("build/\n", encoding="utf-8", newline="\n")
        self.git("add", ".", cwd=origin)
        self.git("commit", "-qm", "module upstream", cwd=origin)
        self.git("-c", "protocol.file.allow=always", "submodule", "add",
                 str(origin), "submodules/Detours")
        self.git("commit", "-qm", "add module")
        self.commit = self.git("rev-parse", "HEAD").decode().strip()
        return self.source / "submodules" / "Detours"

    def test_first_and_repeated_apply_preserve_index_and_ignored_output(self):
        index = (self.source / ".git" / "index").read_bytes()
        build = self.source / "build"
        build.mkdir()
        (build / "client.dll").write_bytes(b"build output")
        self.prepare()
        self.assertEqual(self.patched, (self.source / "patched.cpp").read_text())
        self.assertEqual("expected new header\n", (self.source / "new.h").read_text())
        self.assertFalse((self.source / "removed.cpp").exists())
        applied = self.snapshot()
        self.prepare()
        self.assertEqual(applied, self.snapshot())
        self.assertEqual(index, (self.source / ".git" / "index").read_bytes())
        self.assertEqual(2, self.submodule_updates)

    def test_rejects_extra_tracked_change_after_patch(self):
        self.prepare()
        (self.source / "unrelated.cpp").write_text("unexpected\n", encoding="utf-8", newline="\n")
        self.git("apply", "--reverse", "--check", str(self.patch_file))
        self.assert_preserved_rejection()

    def test_rejects_extra_change_outside_patch_hunk(self):
        self.prepare()
        (self.source / "patched.cpp").write_text(self.patched + "extra line\n", encoding="utf-8", newline="\n")
        self.git("apply", "--reverse", "--check", str(self.patch_file))
        self.assert_preserved_rejection()

    def test_rejects_untracked_source_before_or_after_patch(self):
        for applied in (False, True):
            with self.subTest(applied=applied):
                if applied:
                    self.prepare()
                extra = self.source / "extra.cpp"
                extra.write_text("unexpected\n", encoding="utf-8", newline="\n")
                self.assert_preserved_rejection()
                extra.unlink()

    def test_rejects_staged_change_even_when_worktree_is_expected(self):
        self.prepare()
        unrelated = self.source / "unrelated.cpp"
        unrelated.write_text("unexpected staged content\n", encoding="utf-8", newline="\n")
        self.git("add", "unrelated.cpp")
        unrelated.write_text("unchanged\n", encoding="utf-8", newline="\n")
        self.assert_preserved_rejection()

    def test_rejects_staged_new_file_even_when_removed_from_worktree(self):
        self.prepare()
        extra = self.source / "extra.cpp"
        extra.write_text("unexpected staged file\n", encoding="utf-8", newline="\n")
        self.git("add", "extra.cpp")
        extra.unlink()
        self.assert_preserved_rejection()

    def test_accepts_staging_expected_patch_files(self):
        self.prepare()
        self.git("add", "new.h", "patched.cpp")
        before = self.snapshot()
        self.prepare()
        self.assertEqual(before, self.snapshot())

    def test_accepts_intent_to_add_expected_patch_file(self):
        self.prepare()
        self.git("add", "-N", "new.h")
        before = self.snapshot()
        self.prepare()
        self.assertEqual(before, self.snapshot())

    def test_rejects_intent_to_add_extra_worktree_file(self):
        self.prepare()
        extra = self.source / "extra.cpp"
        extra.write_bytes(b"unexpected source\n")
        self.git("add", "-N", "extra.cpp")
        self.assert_preserved_rejection()

    def test_rejects_staged_empty_patch_file_with_expected_worktree(self):
        self.prepare()
        added = self.source / "new.h"
        expected = added.read_bytes()
        added.write_bytes(b"")
        self.git("add", "new.h")
        added.write_bytes(expected)
        self.assert_preserved_rejection()

    def test_rejects_staged_empty_extra_file_removed_from_worktree(self):
        self.prepare()
        extra = self.source / "extra.cpp"
        extra.write_bytes(b"")
        self.git("add", "extra.cpp")
        extra.unlink()
        self.assert_preserved_rejection()

    def test_rejects_incomplete_patch(self):
        self.prepare()
        (self.source / "new.h").unlink()
        self.assert_preserved_rejection()

    def test_rejects_change_to_patch_added_file(self):
        self.prepare()
        (self.source / "new.h").write_text("modified header\n", encoding="utf-8", newline="\n")
        self.assert_preserved_rejection()

    def test_rejects_assume_unchanged_worktree_modification(self):
        self.prepare()
        self.git("update-index", "--assume-unchanged", "unrelated.cpp")
        (self.source / "unrelated.cpp").write_text("unexpected hidden change\n", encoding="utf-8", newline="\n")
        self.assert_preserved_rejection()

    def test_accepts_clean_initialized_and_uninitialized_submodules(self):
        module = self.add_submodule()
        (module / "build").mkdir()
        (module / "build" / "detours.lib").write_bytes(b"ignored module output")
        self.prepare()
        self.prepare()
        self.git("submodule", "deinit", "-f", "submodules/Detours")
        self.prepare()
        self.assertEqual(3, self.submodule_updates)

    def test_rejects_submodule_tracked_and_untracked_changes(self):
        module = self.add_submodule()
        self.prepare()
        source = module / "detours.cpp"
        source.write_text("unexpected module change\n", encoding="utf-8", newline="\n")
        self.assert_preserved_rejection()
        source.write_text("original detours\n", encoding="utf-8", newline="\n")
        (module / "extra.cpp").write_text("unexpected module file\n", encoding="utf-8", newline="\n")
        self.assert_preserved_rejection()


if __name__ == "__main__":
    unittest.main()
