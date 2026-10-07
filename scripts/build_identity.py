"""Fingerprint inputs that affect binaries, packages, or their validation."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT_DIRS = ("patches", "config", "scripts", "tests", "licenses", ".github/workflows")
INPUT_FILES = ("VERSION", "LICENSE", "THIRD_PARTY.md")


def recipe_digest(root=ROOT):
    paths = [root / name for name in INPUT_FILES]
    for name in INPUT_DIRS:
        paths.extend(p for p in (root / name).rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts
                     and p.suffix not in (".pyc", ".pyo"))
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda p: p.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        data = path.read_bytes()
        if path.suffix != ".patch" and b"\0" not in data:
            data = data.replace(b"\r\n", b"\n")
        digest.update(len(relative).to_bytes(8, "little") + relative)
        digest.update(len(data).to_bytes(8, "little") + data)
    return digest.hexdigest()
