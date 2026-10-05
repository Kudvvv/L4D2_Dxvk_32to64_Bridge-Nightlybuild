"""Create portable ZIP entries, including dot directories, without ./ prefixes."""
import argparse
from pathlib import Path
import zipfile


def archive(source, output):
    source = source.resolve()
    if output.resolve().is_relative_to(source):
        raise ValueError("Output must be outside the source directory")
    files = sorted(p for p in source.rglob("*") if p.is_file())
    if not files:
        raise ValueError("Source directory contains no files")
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as target:
        for path in files:
            if path.is_symlink():
                raise ValueError("Symlinks are not supported")
            target.write(path, path.relative_to(source).as_posix())
    with zipfile.ZipFile(output) as target:
        if target.testzip() is not None:
            raise ValueError("ZIP integrity check failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    archive(args.source, args.output)
