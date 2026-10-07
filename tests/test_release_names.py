import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from release_names import classify

class Naming(unittest.TestCase):
    def test_nightly_has_no_version_dependency(self):
        def api(path):
            raise AssertionError("Naming must not query historical tags")
        row=classify(api,"repos/upstream","a"*40,"2026-10-05T00:00:00Z")
        self.assertEqual(row["release_tag"],"nightly-20261005-aaaaaaaa")
        self.assertEqual(row["title"],"nightly-20261005-aaaaaaaa")
        self.assertEqual(row["archive"],"l4d2-bridge-nightly-20261005-aaaaaaaa.zip")
    def test_invalid_date(self):
        with self.assertRaises(ValueError):
            classify(None,"repos/upstream","a"*40,"invalid")
if __name__=="__main__":
    unittest.main()
