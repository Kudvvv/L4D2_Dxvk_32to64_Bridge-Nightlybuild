"""Offline checks for release tracking, duplicate detection and API failures."""
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

spec = importlib.util.spec_from_file_location("detect", Path(__file__).parents[1] / "scripts/detect_release.py")
detect = importlib.util.module_from_spec(spec)
spec.loader.exec_module(detect)


class ReleaseDetection(unittest.TestCase):
    def run_case(self, releases, existing=None, failure=None):
        def api(path):
            if "releases?" in path:
                return releases if path.endswith("&page=1") else []
            if "/commits/" in path:
                return {"sha": "a" * 40}
            if failure:
                raise HTTPError(path, failure, "failure", {}, None)
            if existing:
                return existing
            raise HTTPError(path, 404, "missing", {}, None)
        with patch.dict(os.environ, {"GITHUB_REPOSITORY": "owner/repo"}), patch.object(detect, "api", api):
            return detect.pending()

    def test_bootstrap_and_skip_historical(self):
        self.assertEqual([r["tag"] for r in self.run_case([
            release("v2", "2026-09-01T00:00:00Z"), release("v1", "2025-01-01T00:00:00Z")])], ["v2"])

    def test_missed_releases_and_prerelease(self):
        rows = self.run_case([release("rc", prerelease=True), release("v3"), release("v2")])
        self.assertEqual([r["tag"] for r in rows], ["v2", "v3"])

    def test_existing_and_draft_retry(self):
        self.assertEqual(self.run_case([release("v1")], {"draft": False}), [])
        self.assertEqual(len(self.run_case([release("v1")], {"draft": True})), 1)

    def test_api_failures_are_not_missing_releases(self):
        with self.assertRaises(HTTPError):
            self.run_case([release("v1")], failure=403)


def release(tag, date="2026-10-05T01:00:00Z", prerelease=False):
    return {"tag_name": tag, "published_at": date, "draft": False, "prerelease": prerelease}


if __name__ == "__main__":
    unittest.main()
