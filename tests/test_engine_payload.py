"""Reject any engine payload other than the exact previously verified repair."""
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import engine_payload as engine


class EnginePayload(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.files = engine.source_engine_files()
        for name, data in self.files.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

    def test_exact_repair_and_manifest_round_trip(self):
        self.assertEqual(engine.staged_engine_files(self.root), self.files)

    def test_corrupt_truncated_and_different_engine_are_rejected(self):
        path = self.root / "bin/studiorender.dll"
        original = path.read_bytes()
        for modified in (original[:-1], bytes([original[0] ^ 1]) + original[1:], b"different engine"):
            with self.subTest(size=len(modified)):
                path.write_bytes(modified)
                with self.assertRaisesRegex(ValueError, "exact validated"):
                    engine.staged_engine_files(self.root)

    def test_record_tampering_rejected_and_line_endings_portable(self):
        path = self.root / "ENGINE-PATCH.json"
        record = path.read_bytes().replace(b"\r\n", b"\n")
        path.write_bytes(record.replace(b"\n", b"\r\n"))
        engine.staged_engine_files(self.root)
        path.write_bytes(record.replace(b'"game_validated": false', b'"game_validated": true'))
        with self.assertRaisesRegex(ValueError, "manifest differs"):
            engine.staged_engine_files(self.root)

    def test_notice_required_and_linked_engine_rejected(self):
        notice = self.root / "licenses/Valve-engine-NOTICE.txt"
        notice.write_bytes(b"")
        with self.assertRaisesRegex(ValueError, "attribution"):
            engine.staged_engine_files(self.root)
        notice.write_bytes(self.files["licenses/Valve-engine-NOTICE.txt"])
        target = self.root / "external.dll"
        source = self.root / "bin/studiorender.dll"
        shutil.move(source, target)
        try:
            source.symlink_to(target)
        except OSError as error:
            self.skipTest(f"Symlink unavailable: {error}")
        with self.assertRaisesRegex(ValueError, "Linked"):
            engine.staged_engine_files(self.root)


if __name__ == "__main__":
    unittest.main()
