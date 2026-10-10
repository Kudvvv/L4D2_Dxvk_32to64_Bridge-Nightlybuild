"""Exercise the actual installer against temporary game/package directories only."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == "nt", "Requires Windows PowerShell; mandatory in Windows CI")
class ColorInstaller(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.package = self.root / "package"
        self.game = self.root / "game"
        self.script = self.package / "scripts/install_color_diagnostics.ps1"
        self.script.parent.mkdir(parents=True)
        shutil.copy2(ROOT / "scripts/install_color_diagnostics.ps1", self.script)
        self.game.mkdir()
        (self.game / "left4dead2.exe").write_bytes(b"non-executable test fixture")
        self.files = {"bin/d3d9.dll": b"new client fixture",
                      "bin/.l4d2bridge/L4D2Bridge32.exe": b"new host32 fixture",
                      "bin/.l4d2bridge/L4D2Bridge64.exe": b"new host64 fixture"}
        for relative, data in self.files.items():
            path = self.package / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        (self.package / "SHA256.json").write_text(json.dumps({name: hashlib.sha256(data).hexdigest()
                                                             for name, data in self.files.items()}))
        self.config = self.game / "bin/.l4d2bridge/bridge.conf"
        self.config.parent.mkdir(parents=True)
        self.config.write_bytes(b"customSetting = preserve\r\nclient.colorDiagnostics = False\r\n")

    def snapshot(self):
        return {path.relative_to(self.game).as_posix(): path.read_bytes()
                for path in self.game.rglob("*") if path.is_file()}

    def run_installer(self):
        # Mask only process discovery: no real game paths/processes are consulted.
        runner = self.root / "run.ps1"
        runner.write_text("param($Installer, $Game)\n$ErrorActionPreference = 'Stop'\nfunction Get-Process {}\n& $Installer -GameDirectory $Game\n",
                          encoding="utf-8")
        # Python may inherit PowerShell 7's module path; Windows PowerShell must
        # initialize its own built-in modules instead of importing that path.
        environment = {key: value for key, value in os.environ.items() if key.upper() != "PSMODULEPATH"}
        return subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                               str(runner), str(self.script), str(self.game)], capture_output=True, env=environment)

    def test_both_client_names_preserve_the_installed_name_and_configuration(self):
        for name in ("d3d9.dll", "dxvk_d3d9.dll"):
            with self.subTest(name=name):
                client = self.game / "bin" / name
                client.write_bytes(b"old client")
                result = self.run_installer()
                self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
                self.assertEqual(client.read_bytes(), b"new client fixture")
                other = "dxvk_d3d9.dll" if name == "d3d9.dll" else "d3d9.dll"
                self.assertFalse((client.parent / other).exists())
                self.assertIn("customSetting = preserve", self.config.read_text())
                self.assertIn("client.colorDiagnostics = True", self.config.read_text())
                self.assertTrue(any(path.read_bytes() == b"old client" for path in
                                    (self.config.parent / "backups").rglob(name)))
                client.unlink()
                shutil.rmtree(self.config.parent / "backups")

    def test_ambiguous_clients_and_bad_manifest_make_no_changes(self):
        for name in ("d3d9.dll", "dxvk_d3d9.dll"):
            (self.game / "bin" / name).write_bytes(b"preserve installed proxy")
        before = self.snapshot()
        self.assertNotEqual(self.run_installer().returncode, 0)
        self.assertEqual(before, self.snapshot())
        (self.game / "bin/dxvk_d3d9.dll").unlink()
        (self.package / "bin/d3d9.dll").write_bytes(b"tampered package")
        before = self.snapshot()
        self.assertNotEqual(self.run_installer().returncode, 0)
        self.assertEqual(before, self.snapshot())


if __name__ == "__main__":
    unittest.main()
