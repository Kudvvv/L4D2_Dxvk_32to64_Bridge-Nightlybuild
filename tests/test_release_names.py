import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from release_names import classify

class Naming(unittest.TestCase):
    def test_nightly_has_no_version_dependency(self):
        def api(path):
            raise AssertionError("Naming must not query historical tags")
        row=classify("a"*40,"2026-10-05T00:00:00Z","b"*64,"123",1)
        self.assertEqual(row["release_tag"],"nightly-20261005-aaaaaaaa-rbbbbbbbbbbbb-b123.1")
        self.assertEqual(row["title"],row["release_tag"])
        self.assertEqual(row["archive"],"l4d2-bridge-"+row["release_tag"]+".zip")
    def test_invalid_date(self):
        with self.assertRaises(ValueError):
            classify("a"*40,"invalid","b"*64,123,1)
    def test_rebuilds_and_attempts_are_distinct(self):
        tags={classify("a"*40,"2026-10-05T00:00:00Z","b"*64,run,attempt)["release_tag"] for run,attempt in [(123,1),(123,2),(124,1)]}
        self.assertEqual(len(tags),3)
if __name__=="__main__":
    unittest.main()
