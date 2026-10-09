"""Stage the exact, previously validated ThinFlex engine repair."""
import hashlib
import json
from pathlib import Path
import stat

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_SHA256 = "3f5f5b0f539e8ad22bcfc4381be41571257c0c29e8061057682f9b8525ca7b85"
PATCHED_SHA256 = "03964dedcf8b7f4ebde24cd3d0738873d37c075a7a9b313dad001bb937f9d1b6"
MANIFEST_SHA256 = "148b66195b3db23356d9d3e9ec2243a65cfa9e331480b0e10cd32046f5aa8b73"
DLL_SIZE = 634672
ENGINE_FILES = ("bin/studiorender.dll", "ENGINE-PATCH.json", "licenses/Valve-engine-NOTICE.txt")


def read_regular(path):
    attributes = getattr(path.lstat(), "st_file_attributes", 0)
    if path.is_symlink() or attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
        raise ValueError(f"Linked engine input is not supported: {path.name}")
    return path.read_bytes()


def validate_engine_files(files):
    dll, record, notice = (files[name] for name in ENGINE_FILES)
    if len(dll) != DLL_SIZE or hashlib.sha256(dll).hexdigest() != PATCHED_SHA256:
        raise ValueError("Engine DLL differs from the exact validated ThinFlex repair")
    # Git checkout line endings do not affect the manifest's meaning.
    if hashlib.sha256(record.replace(b"\r\n", b"\n")).hexdigest() != MANIFEST_SHA256:
        raise ValueError("Engine manifest differs from the validated repair record")
    metadata = json.loads(record)
    if metadata["original_sha256"] != ORIGINAL_SHA256 or metadata["output_sha256"] != PATCHED_SHA256:
        raise ValueError("Engine repair identity mismatch")
    if not notice.strip():
        raise ValueError("Missing Valve engine attribution")
    return files


def source_engine_files(root=ROOT):
    files = dict(zip(ENGINE_FILES, (
        read_regular(root / "runtime/engine/studiorender.dll"),
        read_regular(root / "runtime/engine/studiorender.manifest.json"),
        read_regular(root / "licenses/Valve-engine-NOTICE.txt"),
    )))
    return validate_engine_files(files)


def staged_engine_files(source):
    return validate_engine_files({name: read_regular(source / name) for name in ENGINE_FILES})
