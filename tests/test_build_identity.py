import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"scripts"))
from build_identity import recipe_digest, INPUT_FILES

class Identity(unittest.TestCase):
    def test_runtime_inputs_change_identity_but_docs_and_line_endings_do_not(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for name in INPUT_FILES:
                (root/name).parent.mkdir(parents=True, exist_ok=True)
                (root/name).write_bytes(b"test\n")
            (root/"config").mkdir(); config=root/"config/backend.json"
            config.write_bytes(b"one\n"); before=recipe_digest(root)
            config.write_bytes(b"one\r\n"); self.assertEqual(before,recipe_digest(root))
            (root/"README.md").write_bytes(b"docs"); self.assertEqual(before,recipe_digest(root))
            config.write_bytes(b"two\n"); self.assertNotEqual(before,recipe_digest(root))
            before=recipe_digest(root); (root/"patches").mkdir()
            (root/"patches/new.patch").write_bytes(b"patch\n"); self.assertNotEqual(before,recipe_digest(root))
            before=recipe_digest(root)
            (root/"docs/THINFLEX-TEST-README.txt").write_bytes(b"installation correction\n")
            self.assertNotEqual(before,recipe_digest(root))
