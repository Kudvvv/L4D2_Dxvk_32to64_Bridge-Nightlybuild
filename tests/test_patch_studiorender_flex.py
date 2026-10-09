"""Offline tests use a fabricated PE; no Valve DLL or certificate is included."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import patch_studiorender_flex as flex


def fabricated_pe():
    data = bytearray(0x9AF30)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 0xE8)
    data[0xE8:0xEC] = b"PE\0\0"
    struct.pack_into("<HHIIIHH", data, 0xEC, 0x14C, 4, flex.EXPECTED_TIMESTAMP, 0, 0, 224, 0x2102)
    struct.pack_into("<H", data, 0x100, 0x10B)
    struct.pack_into("<II", data, 0x120, 0x1000, 0x200)
    struct.pack_into("<II", data, 0x138, 0x453000, 0x400)
    struct.pack_into("<I", data, 0x15C, 16)
    struct.pack_into("<II", data, 0x180, 0x98298, 0x2C98)
    sections = (
        (b".text", 510810, 4096, 510976, 1024, 0x60000020),
        (b".rdata", 49780, 516096, 50176, 512000, 0x40000040),
        (b".data", 3927756, 569344, 13312, 562176, 0xC0000040),
        (b".reloc", 36274, 4497408, 36352, 575488, 0x42000040),
    )
    for index, (name, size, rva, raw_size, raw, flags) in enumerate(sections):
        struct.pack_into("<8sIIIIIIHHI", data, 0x1E0 + index * 40, name, size, rva, raw_size, raw, 0, 0, 0, 0, flags)
    data[0x483:0x48D] = bytes.fromhex("81b93453070010270000")
    for rva in flex.ADD_RVAS:
        data[rva - 0xC00:rva - 0xC00 + 5] = bytes.fromhex("059a3a0000")
    certificates = []
    for offset, size, _ in flex.CERTIFICATES:
        struct.pack_into("<IHH", data, offset, size, 0x200, 2)
        certificates.append((offset, size, hashlib.sha256(data[offset:offset + size]).hexdigest()))
    return bytes(data), tuple(certificates)


class ExperimentalCopy(unittest.TestCase):
    def setUp(self):
        self.original, certificates = fabricated_pe()
        # Only synthetic test data is accepted inside this test process.
        self.addCleanup(patch.stopall)
        patch.object(flex, "EXPECTED_SHA256", hashlib.sha256(self.original).hexdigest()).start()
        patch.object(flex, "CERTIFICATES", certificates).start()

    def build(self, data=None):
        return flex.patch_image(self.original if data is None else data, experimental_engine_patch=True)

    def test_requires_opt_in_and_exact_input_hash(self):
        with self.assertRaisesRegex(ValueError, "opt-in"):
            flex.patch_image(self.original)
        modified = bytearray(self.original)
        modified[0x500] = 1
        with self.assertRaisesRegex(ValueError, "SHA256"):
            self.build(modified)

    def test_rejects_unknown_layout_and_certificate_bytes(self):
        for offset, value, message in (
            (0xEC, 0x64, "x86 PE"),
            (0x280, 1, "not empty"),
            (0x180, 0, "certificate directory"),
            (0x95610, 1, "certificate/overlay bytes"),
        ):
            with self.subTest(offset=offset):
                modified = bytearray(self.original)
                modified[offset] = value
                with self.assertRaisesRegex(ValueError, message):
                    flex._read_pe(modified)

    def test_checks_every_opcode_even_after_identity_validation(self):
        for rva in (0x1083, *flex.ADD_RVAS):
            with self.subTest(rva=rva):
                modified = bytearray(self.original)
                modified[rva - 0xC00] ^= 1
                # Isolate the secondary opcode guard, independently of SHA pinning.
                with patch.object(flex, "EXPECTED_SHA256", hashlib.sha256(modified).hexdigest()):
                    with self.assertRaisesRegex(ValueError, "instruction"):
                        self.build(modified)

    def test_adds_virtual_pool_preserves_overlay_and_records_all_edits(self):
        output, manifest = self.build()
        self.assertEqual(len(output), len(self.original))
        self.assertEqual(output[0x95600:], self.original[0x95600:])
        self.assertEqual(output[0x180:0x188], self.original[0x180:0x188])
        self.assertEqual(struct.unpack_from("<H", output, 0xEE)[0], 5)
        self.assertEqual(struct.unpack_from("<I", output, 0x138)[0], 0x653000)
        self.assertEqual(struct.unpack_from("<8sIIIIIIHHI", output, 0x280),
                         (b".cflex\0\0", 0x200000, 0x453000, 0, 0, 0, 0, 0, 0, 0xC0000080))
        covered = set()
        for change in manifest["changes"]:
            start, length = change["file_offset"], change["length"]
            self.assertEqual(self.original[start:start + length].hex(), change["before_hex"])
            self.assertEqual(output[start:start + length].hex(), change["after_hex"])
            covered.update(range(start, start + length))
        self.assertTrue(all(a == b or index in covered for index, (a, b) in enumerate(zip(self.original, output))))
        self.assertFalse(manifest["authenticode_signature_valid_after_patch"])
        self.assertFalse(manifest["game_validated"])

    def test_exclusive_copy_verify_and_tamper_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output, record = (root / name for name in ("input.dll", "output.dll", "output.json"))
            source.write_bytes(self.original)
            with self.assertRaisesRegex(ValueError, "distinct"):
                flex.create_copy(source, source, record, experimental_engine_patch=True)
            self.assertFalse(record.exists())
            manifest = flex.create_copy(source, output, record, experimental_engine_patch=True)
            self.assertEqual(manifest, flex.verify_copy(source, output, record))
            before = source.read_bytes(), output.read_bytes(), record.read_bytes()
            with self.assertRaises(FileExistsError):
                flex.create_copy(source, output, record, experimental_engine_patch=True)
            self.assertEqual(before, (source.read_bytes(), output.read_bytes(), record.read_bytes()))
            another_output = root / "another.dll"
            with self.assertRaises(FileExistsError):
                flex.create_copy(source, another_output, record, experimental_engine_patch=True)
            self.assertFalse(another_output.exists())
            output.write_bytes(before[1] + b"tampering")
            with self.assertRaisesRegex(ValueError, "Output bytes"):
                flex.verify_copy(source, output, record)
            output.write_bytes(before[1])
            altered = json.loads(before[2])
            altered["game_validated"] = True
            record.write_text(json.dumps(altered), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Manifest"):
                flex.verify_copy(source, output, record)
            self.assertEqual(source.read_bytes(), self.original)

    def test_failed_output_write_removes_only_new_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output, record = (root / name for name in ("input.dll", "output.dll", "output.json"))
            source.write_bytes(self.original)
            original_open = Path.open

            class InterruptedWriter:
                def __init__(self, handle):
                    self.handle = handle

                def __enter__(self):
                    self.handle.__enter__()
                    return self

                def __exit__(self, *args):
                    return self.handle.__exit__(*args)

                def write(self, data):
                    self.handle.write(data[:32])
                    raise OSError("simulated partial output write failure")

            def intercept(path, *args, **kwargs):
                handle = original_open(path, *args, **kwargs)
                return InterruptedWriter(handle) if path == output and args[0] == "xb" else handle

            with patch.object(Path, "open", intercept):
                with self.assertRaisesRegex(OSError, "partial output"):
                    flex.create_copy(source, output, record, experimental_engine_patch=True)
            self.assertFalse(output.exists())
            self.assertFalse(record.exists())
            self.assertEqual(source.read_bytes(), self.original)

    def test_failed_manifest_write_removes_only_new_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output, record = (root / name for name in ("input.dll", "output.dll", "output.json"))
            source.write_bytes(self.original)

            def interrupted_dump(value, handle, **kwargs):
                handle.write('{"partial":')
                raise OSError("simulated partial manifest write failure")

            with patch.object(flex.json, "dump", interrupted_dump):
                with self.assertRaisesRegex(OSError, "partial manifest"):
                    flex.create_copy(source, output, record, experimental_engine_patch=True)
            self.assertFalse(output.exists())
            self.assertFalse(record.exists())
            self.assertEqual(source.read_bytes(), self.original)

    def test_manifest_race_keeps_competitors_file_and_removes_new_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output, record = (root / name for name in ("input.dll", "output.dll", "output.json"))
            source.write_bytes(self.original)
            original_open = Path.open

            def intercept(path, *args, **kwargs):
                if path == record and args[0] == "x":
                    # Another writer wins after exists() checks, before our x-open.
                    with original_open(record, "x", encoding="utf-8") as competing:
                        competing.write("preserve the other writer's data")
                return original_open(path, *args, **kwargs)

            with patch.object(Path, "open", intercept):
                with self.assertRaises(FileExistsError):
                    flex.create_copy(source, output, record, experimental_engine_patch=True)
            self.assertFalse(output.exists())
            self.assertEqual(record.read_text(encoding="utf-8"), "preserve the other writer's data")
            self.assertEqual(source.read_bytes(), self.original)


if __name__ == "__main__":
    unittest.main()
