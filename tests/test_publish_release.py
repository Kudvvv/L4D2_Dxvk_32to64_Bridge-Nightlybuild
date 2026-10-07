import hashlib, os, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).parents[1]/"scripts"))
import publish_release

class Publishing(unittest.TestCase):
    def run_fixture(self, existing=None, bad_checksum=False):
        with tempfile.TemporaryDirectory() as directory:
            previous=Path.cwd(); os.chdir(directory)
            try:
                Path("assets").mkdir()
                for name in ("full.zip","update.zip"):
                    p=Path("assets")/name; p.write_bytes(b"archive")
                    digest="0"*64 if bad_checksum else hashlib.sha256(p.read_bytes()).hexdigest()
                    Path(str(p)+".sha256").write_text(f"{digest}  {name}\n",encoding="ascii")
                def api(path):
                    if existing is not None: return existing
                    raise HTTPError(path,404,"missing",{},None)
                env={"RELEASE_TAG":"tag","GITHUB_REPOSITORY":"owner/repo","UPSTREAM_COMMIT":"a"*40,"RECIPE_COMMIT":"b"*40,"RECIPE_DIGEST":"c"*64,"GITHUB_RUN_ID":"123"}
                with patch.dict(os.environ,env),patch.object(publish_release,"api",api),patch.object(publish_release.subprocess,"run") as run:
                    publish_release.publish()
                    return [call.args[0] for call in run.call_args_list],Path("notes.md").read_text(encoding="utf-8")
            finally: os.chdir(previous)
    def test_new_release_uploads_without_replacement(self):
        commands,notes=self.run_fixture()
        self.assertEqual([c[2] for c in commands],["create","upload","edit"])
        self.assertFalse(any("--clobber" in c for c in commands))
        self.assertIn("Recipe digest: "+"c"*64,notes)
        self.assertIn("keyou91",notes)
    def test_published_collision_refused(self):
        with self.assertRaises(RuntimeError): self.run_fixture({"draft":False})
    def test_bad_checksum_refused(self):
        with self.assertRaises(ValueError): self.run_fixture(bad_checksum=True)
