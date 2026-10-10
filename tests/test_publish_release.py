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
        self.write_package("full.zip")
        self.enterContext(patch.dict(os.environ, {
            "RELEASE_TAG": "tag", "GITHUB_REPOSITORY": "owner/repo",
            "UPSTREAM_COMMIT": "a" * 40, "RECIPE_COMMIT": "b" * 40,
            "RECIPE_DIGEST": "c" * 64, "GITHUB_RUN_ID": "123",
            "THINFLEX_TEST": "false", "RELEASE_TITLE": "v1.0.6", "ARCHIVE_NAME": "full.zip",
        }))
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
        self.assertIn("keyou91", notes)
        self.assertIn("已修复的 `bin/studiorender.dll`", notes)
        self.assertIn("ENGINE-PATCH.json", notes)
        self.assertNotIn("tools/thinflex/ThinFlexPatch.exe", notes)
        self.assertEqual({asset["name"] for asset in self.assets}, {"full.zip", "full.zip.sha256"})

    def test_thinflex_publishes_one_full_package_with_explicit_limitations(self):
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
        for statement in ("已修复的 `bin/studiorender.dll`", "复制文件即可应用 ThinFlex 修复",
                          "无需运行补丁工具或安装 Python", "只提供一个完整 ZIP", "玩家包不包含补丁工具",
                          "须保留最初原版 DLL 备份", "未知版本应从临时解压目录移除 `bin/studiorender.dll`，仅更新 Bridge",
                          "10000 项扩为 65536 项", "2 MiB", "原数字签名失效",
                          "v1.0.10 ThinFlex 修复有效", "2026-10-10", "反馈未提供游玩时长及完整模型范围",
                          "完整合并 L4D2 原项目", "尚未进行游戏 FPS 对照", "optional/L4N/L4D2BridgePlugin.dll",
                          "L4N 2.51.0", "Starfell", "L4N-PAYLOAD.json", "请勿与其他类似整合项目混装",
                          "性能测试未安装 ThinFlex", "PERFORMANCE-2026-10-10.md",
                          "引擎 DLL 归属 Valve，不适用项目根目录 MIT 许可", "licenses/Valve-engine-NOTICE.txt",
                          "ENGINE-PATCH.json", "附件不包含玩家私有 dump",
                          "3f5f5b0f539e8ad22bcfc4381be41571257c0c29e8061057682f9b8525ca7b85",
                          "03964dedcf8b7f4ebde24cd3d0738873d37c075a7a9b313dad001bb937f9d1b6"):
            self.assertIn(statement, notes)
        self.assertLess(notes.index("复制文件即可应用 ThinFlex 修复"), notes.index("Upstream commit:"))
        self.assertNotIn("tools/thinflex", notes)
        self.assertNotIn("工具 BUILD.json", notes)
        self.assertNotIn("update 包", notes)
        self.assertNotIn("独立工具 ZIP", notes)

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
