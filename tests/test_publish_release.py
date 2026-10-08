import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import publish_release


class Publishing(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.addCleanup(os.chdir, Path.cwd())
        os.chdir(directory.name)
        Path("assets").mkdir()
        for name in ("full.zip", "update.zip"):
            path = Path("assets") / name
            path.write_bytes(b"archive " + name.encode("ascii"))
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            Path(str(path) + ".sha256").write_text(f"{digest}  {name}\n", encoding="ascii")
        self.enterContext(patch.dict(os.environ, {
            "RELEASE_TAG": "tag", "GITHUB_REPOSITORY": "owner/repo",
            "UPSTREAM_COMMIT": "a" * 40, "RECIPE_COMMIT": "b" * 40,
            "RECIPE_DIGEST": "c" * 64, "GITHUB_RUN_ID": "123",
        }))
        self.existing = None
        self.assets = []
        self.contents = {}
        self.api = self.enterContext(patch.object(publish_release, "api", side_effect=self.read_api))
        self.run = self.enterContext(patch.object(publish_release.subprocess, "run", side_effect=self.run_command))

    def read_api(self, path):
        if path == "repos/owner/repo/releases/tags/tag":
            if self.existing is None:
                raise HTTPError(path, 404, "missing", {}, None)
            return self.existing
        if path.startswith("repos/owner/repo/releases/42/assets?per_page=100&page="):
            page = int(path.rsplit("=", 1)[1])
            return self.assets[(page - 1) * 100:page * 100]
        raise AssertionError(f"Unexpected API call: {path}")

    def add_asset(self, name, digest=True, content=None):
        data = (Path("assets") / name).read_bytes() if content is None else content
        asset_id = len(self.assets) + 1
        asset = {"id": asset_id, "name": name, "state": "uploaded", "size": len(data),
                 "digest": "sha256:" + hashlib.sha256(data).hexdigest() if digest else None}
        self.assets.append(asset)
        self.contents[asset_id] = data
        return asset

    def run_command(self, command, check, stdout=None):
        self.assertTrue(check)
        if command[:2] == ["gh", "api"]:
            self.assertEqual(command[3:], ["-H", "Accept: application/octet-stream"])
            stdout.write(self.contents[int(command[2].rsplit("/", 1)[1])])
        elif command[:3] == ["gh", "release", "create"]:
            self.assertIsNone(self.existing)
            self.existing = {"id": 42, "draft": True}
        elif command[:3] == ["gh", "release", "upload"]:
            for filename in command[4:]:
                name = Path(filename).name
                if any(asset["name"] == name for asset in self.assets):
                    raise subprocess.CalledProcessError(1, command, stderr="asset already exists")
                self.add_asset(name)
        elif command[:3] == ["gh", "release", "edit"]:
            self.existing["draft"] = False
        else:
            raise AssertionError(f"Unexpected command: {command}")

    def release_commands(self):
        return [call.args[0] for call in self.run.call_args_list if call.args[0][1] == "release"]

    def test_new_release_uploads_without_replacement(self):
        publish_release.publish()
        commands = self.release_commands()
        self.assertEqual([command[2] for command in commands], ["create", "upload", "edit"])
        self.assertFalse(any("--clobber" in command for command in commands))
        notes = Path("notes.md").read_text(encoding="utf-8")
        self.assertIn("Recipe digest: " + "c" * 64, notes)
        self.assertIn("keyou91", notes)

    def test_published_collision_refused(self):
        self.existing = {"id": 42, "draft": False}
        with self.assertRaises(RuntimeError):
            publish_release.publish()
        self.run.assert_not_called()

    def test_bad_checksum_refused(self):
        Path("assets/full.zip.sha256").write_text("0" * 64 + "  full.zip\n", encoding="ascii")
        with self.assertRaises(ValueError):
            publish_release.publish()
        self.api.assert_not_called()
        self.run.assert_not_called()

    def test_partial_upload_failure_resumes_only_missing_assets(self):
        def fail_upload(command, **kwargs):
            if command[:3] == ["gh", "release", "upload"]:
                for filename in command[4:6]:
                    self.add_asset(Path(filename).name)
                raise subprocess.CalledProcessError(1, command)
            return self.run_command(command, **kwargs)

        self.run.side_effect = fail_upload
        with self.assertRaises(subprocess.CalledProcessError):
            publish_release.publish()
        self.assertTrue(self.existing["draft"])
        self.assertEqual(len(self.assets), 2)
        self.run.reset_mock()
        self.run.side_effect = self.run_command
        publish_release.publish()
        commands = self.release_commands()
        self.assertEqual([command[2] for command in commands], ["upload", "edit"])
        self.assertEqual([Path(name).name for name in commands[0][4:]],
                         ["update.zip", "update.zip.sha256"])
        self.assertEqual(len(self.assets), 4)
        self.assertFalse(self.existing["draft"])

    def test_edit_failure_resumes_without_uploading_again(self):
        def fail_edit(command, **kwargs):
            if command[:3] == ["gh", "release", "edit"]:
                raise subprocess.CalledProcessError(1, command)
            return self.run_command(command, **kwargs)

        self.run.side_effect = fail_edit
        with self.assertRaises(subprocess.CalledProcessError):
            publish_release.publish()
        self.assertEqual(len(self.assets), 4)
        self.assertTrue(self.existing["draft"])
        self.run.reset_mock()
        self.run.side_effect = self.run_command
        publish_release.publish()
        self.assertEqual([command[2] for command in self.release_commands()], ["edit"])
        self.assertEqual(len(self.assets), 4)
        self.assertFalse(self.existing["draft"])

    def test_missing_digest_downloads_and_verifies_actual_content(self):
        self.existing = {"id": 42, "draft": True}
        self.add_asset("full.zip", digest=False)
        self.add_asset("full.zip.sha256", digest=False)
        publish_release.publish()
        downloads = [call.args[0] for call in self.run.call_args_list if call.args[0][1] == "api"]
        self.assertEqual(len(downloads), 2)
        upload = self.release_commands()[0]
        self.assertEqual([Path(name).name for name in upload[4:]], ["update.zip", "update.zip.sha256"])

    def test_same_size_different_content_is_refused_with_or_without_digest(self):
        self.existing = {"id": 42, "draft": True}
        for digest in (True, False):
            with self.subTest(digest=digest):
                self.assets.clear()
                self.run.reset_mock()
                original = Path("assets/update.zip.sha256").read_bytes()
                self.add_asset("update.zip.sha256", digest=digest, content=b"x" * len(original))
                with self.assertRaisesRegex(RuntimeError, "content differs"):
                    publish_release.publish()
                self.assertEqual(self.release_commands(), [])
                self.assertTrue(self.existing["draft"])

    def test_incomplete_or_wrong_size_asset_is_refused(self):
        self.existing = {"id": 42, "draft": True}
        for change in ({"state": "starter"}, {"size": 0}):
            with self.subTest(change=change):
                self.assets.clear()
                self.add_asset("full.zip").update(change)
                with self.assertRaisesRegex(RuntimeError, "incomplete or differs"):
                    publish_release.publish()
                self.run.assert_not_called()

    def test_asset_download_failure_keeps_draft_untouched(self):
        self.existing = {"id": 42, "draft": True}
        self.add_asset("full.zip", digest=False)
        self.run.side_effect = subprocess.CalledProcessError(1, "gh api")
        with self.assertRaises(subprocess.CalledProcessError):
            publish_release.publish()
        self.assertEqual(self.release_commands(), [])
        self.assertTrue(self.existing["draft"])

    def test_asset_listing_failure_keeps_draft_untouched(self):
        self.existing = {"id": 42, "draft": True}

        def fail_listing(path):
            if "/assets?" in path:
                raise HTTPError(path, 503, "unavailable", {}, None)
            return self.read_api(path)

        self.api.side_effect = fail_listing
        with self.assertRaises(HTTPError):
            publish_release.publish()
        self.run.assert_not_called()
        self.assertTrue(self.existing["draft"])

    def test_asset_list_pagination_finds_existing_attachment(self):
        self.existing = {"id": 42, "draft": True}
        for index in range(100):
            self.add_asset(f"unrelated-{index}.txt", content=b"unrelated")
        self.add_asset("full.zip")
        publish_release.publish()
        uploaded = [Path(name).name for name in self.release_commands()[0][4:]]
        self.assertNotIn("full.zip", uploaded)
        self.assertEqual(len(uploaded), 3)
        self.api.assert_any_call("repos/owner/repo/releases/42/assets?per_page=100&page=2")


if __name__ == "__main__":
    unittest.main()
