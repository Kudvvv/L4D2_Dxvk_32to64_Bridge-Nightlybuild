"""Offline checks for branch HEAD tracking and safe retry/deduplication."""
import importlib.util
import os
import sys
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

spec = importlib.util.spec_from_file_location("detect", Path(__file__).parents[1] / "scripts/detect_release.py")
detect = importlib.util.module_from_spec(spec)
spec.loader.exec_module(detect)
SHA = "a" * 40


class HeadDetection(unittest.TestCase):
    def run_case(self, existing=None, failure=None, manual="", branch="main", force=False):
        calls = []
        def api(path):
            calls.append(path)
            if "/releases?" in path:
                return []
            if path == detect.UPSTREAM:
                return {"default_branch": branch}
            if "/commits/" in path:
                return {"sha": SHA, "commit": {"committer": {"date": "2026-10-05T00:00:00Z"}}}
            if failure:
                raise HTTPError(path, failure, "failure", {}, None)
            if existing is not None:
                return existing
            raise HTTPError(path, 404, "missing", {}, None)
        with patch.dict(os.environ, {"GITHUB_REPOSITORY": "owner/repo", "UPSTREAM_COMMIT": manual, "FORCE_REBUILD": str(force).lower()}), patch.object(detect, "api", api), patch.object(detect, "classify", return_value={"group":"untagged", "release_tag":"bridge-test"}):
            rows = detect.pending()
        return rows, calls

    def test_tracks_latest_default_branch(self):
        rows, calls = self.run_case()
        self.assertEqual(rows[0]["commit"], SHA)
        self.assertEqual(rows[0]["branch"], "main")
        self.assertIn(detect.UPSTREAM + "/commits/main", calls)
        self.assertFalse(any(p.startswith(detect.UPSTREAM + "/releases?") for p in calls))

    def test_default_branch_changes(self):
        rows, calls = self.run_case(branch="dev/bridge")
        self.assertEqual(rows[0]["branch"], "dev/bridge")
        self.assertIn(detect.UPSTREAM + "/commits/dev%2Fbridge", calls)

    def test_existing_success_skipped(self):
        self.assertEqual(self.run_case(existing={"draft": False})[0], [])

    def test_force_rebuild_bypasses_all_published_release_checks(self):
        rows, calls = self.run_case(existing={"draft": False}, force=True)
        self.assertEqual(rows[0]["commit"], SHA)
        self.assertFalse(any("/releases" in path for path in calls))

    def test_force_manual_commit(self):
        rows, calls = self.run_case(manual=SHA, force=True)
        self.assertEqual(rows[0]["branch"], "manual")

    def test_draft_retried(self):
        self.assertEqual(len(self.run_case(existing={"draft": True})[0]), 1)

    def test_api_failure_not_mistaken_for_new_commit(self):
        with self.assertRaises(HTTPError):
            self.run_case(failure=403)

    def test_manual_override(self):
        rows, calls = self.run_case(manual=SHA)
        self.assertEqual(rows[0]["branch"], "manual")
        self.assertNotIn(detect.UPSTREAM, calls)

    def test_invalid_manual_input(self):
        with self.assertRaises(ValueError):
            self.run_case(manual="main; echo unsafe")


if __name__ == "__main__":
    unittest.main()

