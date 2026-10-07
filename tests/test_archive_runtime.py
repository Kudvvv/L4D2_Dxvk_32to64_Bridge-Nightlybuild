import sys, tempfile, unittest, zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"scripts"))
from archive_runtime import runtime_archive, REQUIRED

class Packaging(unittest.TestCase):
    def test_update_pairs_bridge_and_preserves_user_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); source=root/"source"; source.mkdir()
            for name in REQUIRED+("UPSTREAM.json","licenses/Bridge-MIT.txt"):
                p=source/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(b"fixture")
            for name in ("bin/.l4d2bridge/ReShade.dll","bin/.l4d2bridge/resource-retention.db"):
                (source/name).write_bytes(b"user")
            for update in (False,True):
                output=root/("update.zip" if update else "full.zip")
                runtime_archive(source,output,update)
                with zipfile.ZipFile(output) as z:
                    names=set(z.namelist())
                    self.assertIn("d3d9.dll",names)
                    self.assertNotIn("bin/dxvk_d3d9.dll",names)
                    self.assertIn("bin/.l4d2bridge/L4D2Bridge64.exe",names)
                    self.assertIn("UPSTREAM.json",names)
                    for name in ("bin/.l4d2bridge/d3d9vk_x64.dll","bin/.l4d2bridge/bridge.conf"):
                        self.assertEqual(name in names,not update)
                    self.assertNotIn("bin/.l4d2bridge/ReShade.dll",names)
                    self.assertNotIn("bin/.l4d2bridge/resource-retention.db",names)
                with self.assertRaises(FileExistsError): runtime_archive(source,output,update)
