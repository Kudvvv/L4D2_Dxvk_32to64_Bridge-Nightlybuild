import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from release_names import classify

SHA = "a" * 40
class Naming(unittest.TestCase):
    def run_case(self, exact=False, tags=True):
        def api(path):
            if "/tags?" in path:
                return [{"name":"remix-1.5.2","commit":{"sha": SHA if exact else "b"*40}}] if tags and path.endswith("page=1") else []
            return {"status":"ahead","ahead_by":3}
        return classify(api,"repos/upstream",SHA,"2026-10-05T00:00:00Z")
    def test_tag(self):
        self.assertEqual(self.run_case(True)["kind"],"tag")
    def test_nightly(self):
        row=self.run_case()
        self.assertEqual(row["group"],"remix-1.5.2")
        self.assertEqual(row["distance"],3)
        self.assertEqual(row["archive"],"l4d2-bridge-remix-1.5.2-nightly-20261005-aaaaaaaa.zip")
    def test_untagged(self):
        self.assertEqual(self.run_case(tags=False)["group"],"untagged")
if __name__=="__main__":
    unittest.main()
