"""Validate the exact user-provided L4N distribution and approved configuration preset."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat

ROOT = Path(__file__).resolve().parents[1]
VERSION = "2.51.0"
AUTHOR = "Starfell"
SOURCE_ARCHIVE_SHA256 = "5a530a24ee0e8a3014ab99df35e22279e410bed1a1f4cca1a08c2eb058eb0d4c"
# Canonical JSON digest pins both the file list and its provenance. Text checkout
# line endings and formatting may differ without altering the recorded identity.
MANIFEST_SHA256 = "794da288f160facaaef9259ccf8e9b53c8a5f1027adfc6c5de7de398b9228fe1"
MANIFEST_NAME = "L4N-PAYLOAD.json"
NOTICE_NAME = "licenses/L4N-NOTICE.txt"
FILE_COUNT = 78
TOTAL_SIZE = 23232626


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate L4N manifest key: {key}")
        result[key] = value
    return result


def manifest_metadata(data):
    metadata = json.loads(data, object_pairs_hook=_unique_object)
    normalized = json.dumps(metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if hashlib.sha256(normalized).hexdigest() != MANIFEST_SHA256:
        raise ValueError("L4N manifest differs from the approved distribution and preset")
    if (metadata["version"] != VERSION or metadata["author"] != AUTHOR
            or metadata["source_archive_sha256"] != SOURCE_ARCHIVE_SHA256):
        raise ValueError("L4N origin identity mismatch")
    entries = metadata["files"]
    if len(entries) != FILE_COUNT or sum(entry["size"] for entry in entries.values()) != TOTAL_SIZE:
        raise ValueError("L4N payload file count or total size mismatch")
    folded = set()
    for name in entries:
        path = PurePosixPath(name)
        if (path.is_absolute() or path.as_posix() != name or ".." in path.parts
                or "\\" in name or ":" in name or "\0" in name
                or name.casefold() in folded):
            raise ValueError(f"Invalid L4N payload path: {name}")
        folded.add(name.casefold())
    return metadata


def _check_unlinked(path, boundary):
    current = path
    while True:
        attributes = getattr(current.lstat(), "st_file_attributes", 0)
        if current.is_symlink() or attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
            raise ValueError(f"Linked L4N input is not supported: {path}")
        if current == boundary:
            break
        if current == current.parent:
            raise ValueError("L4N input escaped its root")
        current = current.parent


def _read_regular(path, boundary):
    _check_unlinked(path, boundary)
    if not path.is_file():
        raise ValueError(f"Not a regular L4N file: {path}")
    return path.read_bytes()


def validate_l4n_files(files):
    metadata = manifest_metadata(files[MANIFEST_NAME])
    expected = set(metadata["files"]) | {MANIFEST_NAME, NOTICE_NAME}
    if set(files) != expected:
        raise ValueError("Unexpected or missing L4N payload files")
    for name, entry in metadata["files"].items():
        data = files[name]
        if len(data) != entry["size"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError(f"L4N payload differs from its verified source: {name}")
    if b"Starfell" not in files[NOTICE_NAME]:
        raise ValueError("Missing L4N author credit: Starfell")
    return files


def source_l4n_files(root=ROOT):
    root = Path(root).absolute()
    record = _read_regular(root / "runtime/l4n/manifest.json", root)
    metadata = manifest_metadata(record)
    payload = root / "runtime/l4n/payload"
    _check_unlinked(payload, root)
    actual = set()
    for path in payload.rglob("*"):
        _check_unlinked(path, payload)
        if path.is_file():
            actual.add(path.relative_to(payload).as_posix())
    if actual != set(metadata["files"]):
        raise ValueError("Unexpected or missing source L4N payload files")
    files = {name: _read_regular(payload / name, payload) for name in metadata["files"]}
    files[MANIFEST_NAME] = record
    files[NOTICE_NAME] = _read_regular(root / NOTICE_NAME, root)
    return validate_l4n_files(files)


def staged_l4n_files(source):
    source = Path(source).absolute()
    record = _read_regular(source / MANIFEST_NAME, source)
    metadata = manifest_metadata(record)
    files = {name: _read_regular(source / name, source) for name in metadata["files"]}
    files[MANIFEST_NAME] = record
    files[NOTICE_NAME] = _read_regular(source / NOTICE_NAME, source)
    return validate_l4n_files(files)
