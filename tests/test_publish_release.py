import hashlib
import json
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
import detect_release

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class Publishing(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.addCleanup(os.chdir, Path.cwd())
        os.chdir(directory.name)
        Path("assets").mkdir()
        self.write_package("full.zip")
        self.enterContext(patch.dict(os.environ, {
            "RELEASE_TAG": "tag", "GITHUB_REPOSITORY": "owner/repo",
            "UPSTREAM_COMMIT": "a" * 40, "RECIPE_COMMIT": "b" * 40,
            "RECIPE_DIGEST": "c" * 64, "GITHUB_RUN_ID": "123",
            "THINFLEX_TEST": "false", "RELEASE_TITLE": "v1.0.6", "ARCHIVE_NAME": "full.zip",
        }))
        self.enterContext(patch.object(publish_release, "ROOT", Path.cwd()))
        Path("VERSION").write_text("1.2.1\n", encoding="utf-8")
        Path("docs").mkdir()
        self.changes = "本次修复 IPC 数据覆盖与回绕；本候选尚未完成游戏复测，不宣称提帧。"
        Path("docs/RELEASE-NOTES.md").write_text("# v1.2.1\n\n" + self.changes + "\n", encoding="utf-8")
        Path("config").mkdir()
        Path("config/original-project.json").write_text(json.dumps({
            "repository": "upstream/project", "version": "1.2.2", "commit": "d" * 40,
        }), encoding="utf-8")
        self.existing = None
        self.other_releases = []
        self.assets = []
        self.contents = {}
        self.api = self.enterContext(patch.object(publish_release, "api", side_effect=self.read_api))
        self.run = self.enterContext(patch.object(publish_release.subprocess, "run", side_effect=self.run_command))

    def read_api(self, path):
        if path == "repos/owner/repo/releases/tags/" + os.environ["RELEASE_TAG"]:
            # GitHub's tag endpoint does not expose an unpublished draft tag.
            if self.existing is None or self.existing["draft"]:
                raise HTTPError(path, 404, "missing", {}, None)
            return self.existing
        if path.startswith("repos/owner/repo/releases?per_page=100&page="):
            page = int(path.rsplit("=", 1)[1])
            releases = self.other_releases + (
                [] if self.existing is None else [dict(self.existing, tag_name=os.environ["RELEASE_TAG"])])
            return releases[(page - 1) * 100:page * 100]
        if path.startswith("repos/owner/repo/releases/42/assets?per_page=100&page="):
            page = int(path.rsplit("=", 1)[1])
            return self.assets[(page - 1) * 100:page * 100]
        raise AssertionError(f"Unexpected API call: {path}")

    def write_package(self, name):
        path = Path("assets") / name
        path.write_bytes(b"archive " + name.encode("ascii"))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        Path(str(path) + ".sha256").write_text(f"{digest}  {name}\n", encoding="ascii")

    def enable_thinflex(self):
        os.environ.update({
            "THINFLEX_TEST": "true", "RELEASE_TAG": "v1.0.6-thinflex-test-build123",
            "RELEASE_TITLE": "v1.0.6 ThinFlex 测试版",
            "ARCHIVE_NAME": "full.zip",
        })

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
        for command in (commands[0], commands[2]):
            self.assertIn("--prerelease", command)
            self.assertIn("--latest=false", command)
        notes = Path("notes.md").read_text(encoding="utf-8")
        self.assertIn("Recipe digest: " + "c" * 64, notes)
        self.assertIn("Release channel: nightly", notes)
        self.assertNotIn("Experimental recipe digest:", notes)
        self.assertIn(self.changes, notes)
        self.assertIn("Upstream commit: " + "a" * 40, notes.splitlines())
        self.assertIn("Build recipe: " + "b" * 40, notes.splitlines())
        self.assertIn("/README.md)", notes)
        self.assertIn("<summary>构建指纹</summary>", notes)
        for old_content in ("ThinFlex 缓存", "L4N 2.51.0", "FLASHLIGHT-PERFORMANCE", "v1.0.10"):
            self.assertNotIn(old_content, notes)
        self.assertNotIn("tools/thinflex/ThinFlexPatch.exe", notes)
        self.assertEqual({asset["name"] for asset in self.assets}, {"full.zip", "full.zip.sha256"})

    def test_thinflex_publishes_one_full_package_with_current_notes(self):
        self.enable_thinflex()
        publish_release.publish()
        commands = self.release_commands()
        self.assertEqual([command[2] for command in commands], ["create", "upload", "edit"])
        self.assertEqual({asset["name"] for asset in self.assets}, {"full.zip", "full.zip.sha256"})
        for command in (commands[0], commands[2]):
            self.assertIn("--prerelease", command)
            self.assertIn("--latest=false", command)
            self.assertEqual(command[command.index("--title") + 1], "v1.0.6 ThinFlex 测试版")
        notes = Path("notes.md").read_text(encoding="utf-8")
        self.assertIn("Release channel: thinflex-test", notes.splitlines())
        self.assertIn("Experimental recipe digest: " + "c" * 64, notes.splitlines())
        self.assertNotIn("Recipe digest: " + "c" * 64, notes.splitlines())
        self.assertIn(self.changes, notes)
        self.assertNotIn("ThinFlex 缓存", notes)
        self.assertNotIn("runtime/engine/studiorender.manifest.json", notes)
        self.assertIn("/README.md)", notes)

    def test_stale_or_empty_current_notes_fail_before_network_calls(self):
        for content in ("# v1.2\n旧更新", "# v1.2.1\n\n", "旧更新", "# v1.2.10\n未来更新"):
            with self.subTest(content=content):
                Path("docs/RELEASE-NOTES.md").write_text(content, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "must match VERSION"):
                    publish_release.publish()
        self.api.assert_not_called()
        self.run.assert_not_called()

    def test_future_release_uses_its_own_notes(self):
        Path("VERSION").write_text("2.0\n", encoding="utf-8")
        Path("docs/RELEASE-NOTES.md").write_text("# v2.0\n\n本次修复其他问题。\n", encoding="utf-8")
        publish_release.publish()
        notes = Path("notes.md").read_text(encoding="utf-8")
        self.assertIn("本次修复其他问题。", notes)
        self.assertNotIn(self.changes, notes)
        self.assertNotIn("IPC 数据覆盖", notes)

    def test_repository_current_notes_match_the_release_version(self):
        notes = publish_release.current_release_notes(REPOSITORY_ROOT)
        self.assertTrue(notes.strip())

    def test_current_notes_metadata_remains_usable_for_channel_deduplication(self):
        for thinflex in (False, True):
            with self.subTest(thinflex=thinflex):
                self.existing = None
                self.assets.clear()
                if thinflex:
                    self.enable_thinflex()
                publish_release.publish()
                notes = Path("notes.md").read_text(encoding="utf-8")
                def detected_api(path):
                    if path == detect_release.UPSTREAM:
                        return {"default_branch": "main"}
                    if "/commits/" in path:
                        return {"sha": "a" * 40, "commit": {"committer": {"date": "2026-10-11T00:00:00Z"}}}
                    if "/releases?" in path:
                        return [{"draft": False, "tag_name": "previous", "body": notes}]
                    raise AssertionError(path)
                with patch.dict(os.environ, {"UPSTREAM_COMMIT": "", "FORCE_REBUILD": "false"}), \
                        patch.object(detect_release, "api", side_effect=detected_api), \
                        patch.object(detect_release, "recipe_digest", return_value="c" * 64):
                    self.assertEqual(detect_release.pending(), [])

    def test_thinflex_rejects_missing_unexpected_or_misnamed_package(self):
        self.enable_thinflex()
        Path("assets/full.zip").unlink()
        with self.assertRaisesRegex(ValueError, "exactly the named"):
            publish_release.publish()
        self.write_package("other.zip")
        with self.assertRaisesRegex(ValueError, "exactly the named"):
            publish_release.publish()
        self.write_package("full.zip")
        with self.assertRaisesRegex(ValueError, "exactly the named"):
            publish_release.publish()
        self.api.assert_not_called()
        self.run.assert_not_called()

    def test_thinflex_rejects_invalid_identity_before_network_calls(self):
        self.enable_thinflex()
        for key, value in (("RELEASE_TAG", "v1.0.6-nightly-build123"),
                           ("RELEASE_TITLE", "v1.0.6 ThinFlex"),
                           ("RELEASE_TITLE", "v1.0.6 测试版"),
                           ("ARCHIVE_NAME", "../full.zip"),
                           ("ARCHIVE_NAME", "..\\full.zip"),
                           ("ARCHIVE_NAME", "wrong.zip"),
                           ("ARCHIVE_NAME", "")):
            with self.subTest(key=key, value=value), patch.dict(os.environ, {key: value}):
                with self.assertRaises(ValueError):
                    publish_release.publish()
        self.api.assert_not_called()
        self.run.assert_not_called()

    def test_nightly_rejects_thinflex_tag_or_extra_package(self):
        os.environ["RELEASE_TAG"] = "v1.0.6-thinflex-test-build123"
        with self.assertRaisesRegex(ValueError, "experimental release channel"):
            publish_release.publish()
        os.environ["RELEASE_TAG"] = "tag"
        self.write_package("thinflex-tool.zip")
        with self.assertRaisesRegex(ValueError, "exactly the named"):
            publish_release.publish()
        self.api.assert_not_called()
        self.run.assert_not_called()

    def test_thinflex_rejects_bad_full_checksum_before_network_calls(self):
        self.enable_thinflex()
        Path("assets/full.zip.sha256").write_text("0" * 64 + "  full.zip\n", encoding="ascii")
        with self.assertRaisesRegex(ValueError, "Invalid archive checksum"):
            publish_release.publish()
        self.api.assert_not_called()
        self.run.assert_not_called()

    def test_thinflex_draft_resume_verifies_and_reuses_existing_full_package(self):
        self.enable_thinflex()
        self.existing = {"id": 42, "draft": True}
        self.add_asset("full.zip")
        publish_release.publish()
        commands = self.release_commands()
        self.assertEqual([command[2] for command in commands], ["upload", "edit"])
        self.assertEqual([Path(name).name for name in commands[0][4:]],
                         ["full.zip.sha256"])
        self.assertEqual(len(self.assets), 2)
        self.assertFalse(self.existing["draft"])

    def test_thinflex_draft_with_unexpected_attachment_is_not_published(self):
        self.enable_thinflex()
        self.existing = {"id": 42, "draft": True}
        self.add_asset("studiorender.dll", content=b"must not publish")
        with self.assertRaisesRegex(RuntimeError, "Unexpected draft attachment"):
            publish_release.publish()
        self.run.assert_not_called()
        self.assertTrue(self.existing["draft"])

    def test_published_collision_refused(self):
        self.existing = {"id": 42, "draft": False}
        with self.assertRaises(RuntimeError):
            publish_release.publish()
        self.run.assert_not_called()

    def test_draft_without_published_tag_resumes(self):
        self.existing = {"id": 42, "draft": True}
        self.add_asset("full.zip")
        with self.assertRaises(HTTPError) as missing_tag:
            self.read_api("repos/owner/repo/releases/tags/tag")
        self.assertEqual(missing_tag.exception.code, 404)
        publish_release.publish()
        commands = self.release_commands()
        self.assertEqual([command[2] for command in commands], ["upload", "edit"])
        self.assertNotIn("full.zip", [Path(name).name for name in commands[0][4:]])

    def test_release_list_pagination_finds_draft(self):
        self.other_releases = [
            {"id": 100 + index, "tag_name": f"other-{index}", "draft": False}
            for index in range(100)
        ]
        self.existing = {"id": 42, "draft": True}
        publish_release.publish()
        self.assertEqual([command[2] for command in self.release_commands()], ["upload", "edit"])
        self.api.assert_any_call("repos/owner/repo/releases?per_page=100&page=2")

    def test_duplicate_tags_across_release_pages_stop_before_writes(self):
        self.other_releases = [
            {"id": 100 + index, "tag_name": f"other-{index}", "draft": False}
            for index in range(100)
        ]
        self.other_releases[0] = {"id": 99, "tag_name": "tag", "draft": True}
        self.existing = {"id": 42, "draft": True}
        with self.assertRaisesRegex(RuntimeError, "Multiple releases"):
            publish_release.publish()
        self.run.assert_not_called()
        self.api.assert_any_call("repos/owner/repo/releases?per_page=100&page=2")

    def test_release_listing_failure_is_not_treated_as_absent(self):
        for status in (404, 503):
            with self.subTest(status=status):
                def fail_listing(path):
                    if "/releases?" in path:
                        raise HTTPError(path, status, "unavailable", {}, None)
                    return self.read_api(path)

                self.api.side_effect = fail_listing
                with self.assertRaises(HTTPError) as failure:
                    publish_release.publish()
                self.assertEqual(failure.exception.code, status)
                self.run.assert_not_called()

    def test_later_release_page_failure_does_not_use_partial_match(self):
        self.other_releases = [
            {"id": 100 + index, "tag_name": f"other-{index}", "draft": False}
            for index in range(100)
        ]
        self.other_releases[0] = {"id": 42, "tag_name": "tag", "draft": True}

        def fail_later_page(path):
            if path == "repos/owner/repo/releases?per_page=100&page=2":
                raise HTTPError(path, 503, "unavailable", {}, None)
            return self.read_api(path)

        self.api.side_effect = fail_later_page
        with self.assertRaises(HTTPError):
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
                for filename in command[4:5]:
                    self.add_asset(Path(filename).name)
                raise subprocess.CalledProcessError(1, command)
            return self.run_command(command, **kwargs)

        self.run.side_effect = fail_upload
        with self.assertRaises(subprocess.CalledProcessError):
            publish_release.publish()
        self.assertTrue(self.existing["draft"])
        self.assertEqual(len(self.assets), 1)
        self.run.reset_mock()
        self.run.side_effect = self.run_command
        publish_release.publish()
        commands = self.release_commands()
        self.assertEqual([command[2] for command in commands], ["upload", "edit"])
        self.assertEqual([Path(name).name for name in commands[0][4:]],
                         ["full.zip.sha256"])
        self.assertEqual(len(self.assets), 2)
        self.assertFalse(self.existing["draft"])

    def test_edit_failure_resumes_without_uploading_again(self):
        def fail_edit(command, **kwargs):
            if command[:3] == ["gh", "release", "edit"]:
                raise subprocess.CalledProcessError(1, command)
            return self.run_command(command, **kwargs)

        self.run.side_effect = fail_edit
        with self.assertRaises(subprocess.CalledProcessError):
            publish_release.publish()
        self.assertEqual(len(self.assets), 2)
        self.assertTrue(self.existing["draft"])
        self.run.reset_mock()
        self.run.side_effect = self.run_command
        publish_release.publish()
        self.assertEqual([command[2] for command in self.release_commands()], ["edit"])
        self.assertEqual(len(self.assets), 2)
        self.assertFalse(self.existing["draft"])

    def test_missing_digest_downloads_and_verifies_actual_content(self):
        self.existing = {"id": 42, "draft": True}
        self.add_asset("full.zip", digest=False)
        self.add_asset("full.zip.sha256", digest=False)
        publish_release.publish()
        downloads = [call.args[0] for call in self.run.call_args_list if call.args[0][1] == "api"]
        self.assertEqual(len(downloads), 2)
        self.assertEqual([command[2] for command in self.release_commands()], ["edit"])

    def test_same_size_different_content_is_refused_with_or_without_digest(self):
        self.existing = {"id": 42, "draft": True}
        for digest in (True, False):
            with self.subTest(digest=digest):
                self.assets.clear()
                self.run.reset_mock()
                original = Path("assets/full.zip.sha256").read_bytes()
                self.add_asset("full.zip.sha256", digest=digest, content=b"x" * len(original))
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

    def test_asset_list_pagination_rejects_unexpected_attachments_before_publication(self):
        self.existing = {"id": 42, "draft": True}
        for index in range(100):
            self.add_asset(f"unrelated-{index}.txt", content=b"unrelated")
        self.add_asset("full.zip")
        with self.assertRaisesRegex(RuntimeError, "Unexpected draft attachment"):
            publish_release.publish()
        self.run.assert_not_called()
        self.assertTrue(self.existing["draft"])
        self.api.assert_any_call("repos/owner/repo/releases/42/assets?per_page=100&page=2")


if __name__ == "__main__":
    unittest.main()
