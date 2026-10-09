"""Compare the native tool with the Python recipe using fabricated PE bytes only.

Normal unittest discovery skips native execution unless THINFLEX_NATIVE_TEST_EXE
and THINFLEX_NATIVE_PRODUCTION_EXE are set. The explicit runner requires both.
No game DLL, certificate or player evidence is read by this test suite.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import patch_studiorender_flex as flex
from test_patch_studiorender_flex import fabricated_pe


def fixture_header():
    original, certificates = fabricated_pe()
    return (
        "// Generated only from tests/test_patch_studiorender_flex.py fabricated_pe.\n"
        "// This header must never be used for the production tool.\n"
        f'#define THINFLEX_TEST_INPUT_SHA256 "{hashlib.sha256(original).hexdigest()}"\n'
        f'#define THINFLEX_TEST_CERT0_SHA256 "{certificates[0][2]}"\n'
        f'#define THINFLEX_TEST_CERT1_SHA256 "{certificates[1][2]}"\n'
    )


def _reverse_objects(value):
    if isinstance(value, dict):
        return {key: _reverse_objects(item) for key, item in reversed(list(value.items()))}
    if isinstance(value, list):
        return [_reverse_objects(item) for item in value]
    return value


@unittest.skipUnless(os.environ.get("THINFLEX_NATIVE_TEST_EXE") and
                     os.environ.get("THINFLEX_NATIVE_PRODUCTION_EXE"),
                     "Native tool paths are supplied by scripts/test_thinflex_native.ps1")
class NativeThinFlex(unittest.TestCase):
    def setUp(self):
        self.exe = Path(os.environ["THINFLEX_NATIVE_TEST_EXE"]).resolve(strict=True)
        self.production = Path(os.environ["THINFLEX_NATIVE_PRODUCTION_EXE"]).resolve(strict=True)
        self.assertNotEqual(self.exe, self.production, "Fixture and production builds must be distinct")
        self.directory = tempfile.TemporaryDirectory(prefix="thinflex-native-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = self.root / "original.dll"
        self.output = self.root / "experimental.dll"
        self.record = self.root / "experimental.json"
        self.original, certificates = fabricated_pe()
        self.source.write_bytes(self.original)
        self.addCleanup(patch.stopall)
        patch.object(flex, "EXPECTED_SHA256", hashlib.sha256(self.original).hexdigest()).start()
        patch.object(flex, "CERTIFICATES", certificates).start()
        self.expected, self.expected_manifest = flex.patch_image(
            self.original, experimental_engine_patch=True)

    def run_native(self, *args, success=True, production=False, fault=None, cwd=None):
        env = os.environ.copy()
        # The suite controls fault injection and cannot inherit another test's state.
        env.pop("THINFLEX_TEST_FAULT", None)
        if fault is not None:
            env["THINFLEX_TEST_FAULT"] = fault
        result = subprocess.run([str(self.production if production else self.exe),
                                 *map(str, args)], cwd=cwd, env=env,
                                capture_output=True, timeout=20)
        details = (result.stdout + result.stderr).decode("utf-8", errors="replace")
        if success:
            self.assertEqual(result.returncode, 0, details)
        else:
            self.assertNotEqual(result.returncode, 0, details)
            self.assertIn(result.returncode, (1, 2), "Tool crashed instead of rejecting input: " + details)
        self.assertEqual(self.source.read_bytes(), self.original, "Tool changed the input DLL")
        return result

    def create(self, **kwargs):
        return self.run_native("create", self.source, self.output, "--manifest", self.record,
                               "--experimental-engine-patch", **kwargs)

    def verify(self, **kwargs):
        return self.run_native("verify", self.source, self.output, self.record, **kwargs)

    def test_native_output_and_manifest_equal_reference_and_cross_verify(self):
        self.create()
        self.assertEqual(self.output.read_bytes(), self.expected)
        self.assertEqual(json.loads(self.record.read_text(encoding="utf-8")), self.expected_manifest)
        self.verify()
        self.assertEqual(flex.verify_copy(self.source, self.output, self.record), self.expected_manifest)
        self.output.unlink()
        self.record.unlink()
        flex.create_copy(self.source, self.output, self.record, experimental_engine_patch=True)
        self.verify()

    def test_default_manifest_and_unicode_paths(self):
        directory = self.root / "中文路径 é 汉字 🧪"
        directory.mkdir()
        source = directory / "原始 文件.dll"
        output = directory / "实验 副本.dll"
        source.write_bytes(self.original)
        record = output.with_name(output.name + ".manifest.json")
        self.run_native("create", source, output, "--experimental-engine-patch")
        self.run_native("verify", source, output, record)
        self.assertEqual(output.read_bytes(), self.expected)
        self.assertEqual(flex.verify_copy(source, output, record), self.expected_manifest)
        self.assertEqual(source.read_bytes(), self.original)

    def test_equivalent_json_object_order_whitespace_and_escapes(self):
        self.create()
        reordered = _reverse_objects(self.expected_manifest)
        variants = [
            json.dumps(reordered, separators=(",", ":")),
            " \r\n\t" + json.dumps(reordered, indent=4) + "\r\n\t ",
            json.dumps(reordered).replace("Thin", r"\u0054hin").replace("original", r"\u006friginal"),
            json.dumps(reordered).replace('"format_version": 1', '"format_version": 1.0')
                .replace('"pool_entries": 65536', '"pool_entries": 6.5536e4'),
        ]
        for encoded in variants:
            with self.subTest(prefix=encoded[:30]):
                self.record.write_text(encoded, encoding="utf-8", newline="")
                self.assertEqual(flex.verify_copy(self.source, self.output, self.record), self.expected_manifest)
                self.verify()

    def test_malformed_json_rejected_without_modifying_files(self):
        self.create()
        valid = self.record.read_bytes()
        malformed = [b"", b"{", b"[]", b"null", b"true", valid + b" trailing",
                     valid + valid, b'{"changes": [1,]}', b'{"bad": "\\q"}',
                     b'{"bad": "unterminated}', b'{"bad": "\x01"}',
                     b'{"bad": NaN}', b'{"bad": Infinity}', b'\xff\xfe{}',
                     b'{"bad": "\xff"}', b'{"bad": 01}', b'{"bad": 1e}',
                     b"[" * 500 + b"0" + b"]" * 500]
        for data in malformed:
            with self.subTest(data=data[:30]):
                self.record.write_bytes(data)
                self.verify(success=False)
                self.assertEqual(self.record.read_bytes(), data)
                self.assertEqual(self.output.read_bytes(), self.expected)

    def test_semantic_manifest_tampering_rejected(self):
        self.create()
        changes = [
            lambda value: value.update(game_validated=True),
            lambda value: value.update(output_sha256="0" * 64),
            lambda value: value.update(original_sha256="0" * 64),
            lambda value: value.update(pool_entries=10000),
            lambda value: value.update(extra="unrecognized"),
            lambda value: value.pop("warning"),
            lambda value: value["changes"].reverse(),
            lambda value: value["changes"][0].update(after_hex="00"),
        ]
        for index, change in enumerate(changes):
            with self.subTest(change=index):
                manifest = json.loads(json.dumps(self.expected_manifest))
                change(manifest)
                self.record.write_text(json.dumps(manifest), encoding="utf-8")
                self.verify(success=False)
                self.assertEqual(self.output.read_bytes(), self.expected)

    def test_modified_or_truncated_output_rejected(self):
        self.create()
        changed = bytearray(self.expected)
        changed[0x500] ^= 1
        for data in (bytes(changed), self.expected[:-1], self.expected + b"tampered", b""):
            with self.subTest(size=len(data)):
                self.output.write_bytes(data)
                self.verify(success=False)
                self.assertEqual(self.output.read_bytes(), data)

    def test_opt_in_and_argument_errors_create_nothing(self):
        for args in (("create", self.source, self.output),
                     ("create", self.source),
                     ("create", self.source, self.output, "--unknown"),
                     ("verify", self.source, self.output),
                     ("unknown-command",), ()):
            with self.subTest(args=args):
                self.run_native(*args, success=False)
                self.assertFalse(self.output.exists())
                self.assertFalse(self.record.exists())
        self.run_native("--help")
        self.run_native("create", "--help")
        self.run_native("verify", "--help")

    def test_production_rejects_fixture_even_with_test_environment(self):
        for fault in (None, "output_write", "manifest_race"):
            with self.subTest(fault=fault):
                self.create(production=True, success=False, fault=fault)
                self.assertFalse(self.output.exists())
                self.assertFalse(self.record.exists())
        self.create()
        self.verify(production=True, success=False)
        self.assertEqual(self.output.read_bytes(), self.expected)
        self.assertEqual(json.loads(self.record.read_text(encoding="utf-8")), self.expected_manifest)

    def test_unsupported_and_missing_sources_create_nothing(self):
        changed = bytearray(self.original)
        changed[0x500] ^= 1
        unknown = self.root / "unsupported.dll"
        for data in (bytes(changed), self.original[:-1], b"unsupported", b""):
            with self.subTest(size=len(data)):
                unknown.write_bytes(data)
                self.run_native("create", unknown, self.output, "--manifest", self.record,
                                "--experimental-engine-patch", success=False)
                self.assertEqual(unknown.read_bytes(), data)
                self.assertFalse(self.output.exists())
                self.assertFalse(self.record.exists())
        unknown.unlink()
        self.run_native("create", unknown, self.output, "--manifest", self.record,
                        "--experimental-engine-patch", success=False)
        self.assertFalse(self.output.exists())
        self.assertFalse(self.record.exists())

    def test_existing_output_or_manifest_preserved(self):
        for existing in (self.output, self.record):
            with self.subTest(existing=existing.name):
                existing.write_bytes(b"preserve existing file")
                self.create(success=False)
                self.assertEqual(existing.read_bytes(), b"preserve existing file")
                self.assertFalse((self.record if existing == self.output else self.output).exists())
                existing.unlink()
        self.output.mkdir()
        self.create(success=False)
        self.assertTrue(self.output.is_dir())
        self.assertFalse(self.record.exists())

    def test_same_and_normalized_paths_rejected(self):
        (self.root / "nested").mkdir()
        for source, output, record in (
                (self.source, self.source, self.record),
                (self.source, self.output, self.source),
                (self.source, self.output, self.output),
                (self.source, self.root / "nested" / ".." / "original.dll", self.record)):
            with self.subTest(source=source, output=output, record=record):
                self.run_native("create", source, output, "--manifest", record,
                                "--experimental-engine-patch", success=False)
                self.assertFalse(self.output.exists())
                self.assertFalse(self.record.exists())

    def test_partial_writes_remove_only_new_outputs(self):
        for fault in ("output_write", "manifest_write"):
            with self.subTest(fault=fault):
                self.create(success=False, fault=fault)
                self.assertFalse(self.output.exists())
                self.assertFalse(self.record.exists())

    def test_competing_creations_preserve_other_writer(self):
        for fault, competitor, missing in (("output_race", self.output, self.record),
                                           ("manifest_race", self.record, self.output)):
            with self.subTest(fault=fault):
                self.create(success=False, fault=fault)
                self.assertEqual(competitor.read_bytes(), b"competing writer\n")
                self.assertFalse(missing.exists())
                competitor.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path)
    parser.add_argument("--production-exe", type=Path)
    parser.add_argument("--write-fixture-header", type=Path)
    args = parser.parse_args()
    if args.write_fixture_header:
        args.write_fixture_header.write_text(fixture_header(), encoding="ascii", newline="\n")
        return 0
    if not args.exe or not args.production_exe:
        parser.error("--exe and --production-exe are required to execute native tests")
    os.environ["THINFLEX_NATIVE_TEST_EXE"] = str(args.exe.resolve(strict=True))
    os.environ["THINFLEX_NATIVE_PRODUCTION_EXE"] = str(args.production_exe.resolve(strict=True))
    # The module can also be discovered without native artifacts. The explicit
    # runner opts in only after resolving both executables, and must not skip.
    NativeThinFlex.__unittest_skip__ = False
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeThinFlex))
    return 0 if result.wasSuccessful() and not result.skipped else 1


if __name__ == "__main__":
    raise SystemExit(main())
