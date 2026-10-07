"""Advance the staged project version once per commit, including amend."""
import re
import subprocess
from pathlib import Path


def next_version(value):
    if not re.fullmatch(r"[0-9]+\.[0-9]+", value):
        raise ValueError("VERSION must use major.minor, for example 1.0")
    major, minor = map(int, value.split("."))
    return f"{major}.{minor + 1}"


def main():
    root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
    staged = subprocess.check_output(["git", "show", ":VERSION"], text=True).strip()
    current = (Path(root) / "VERSION").read_text().strip()
    if current != staged:
        raise RuntimeError("VERSION has unstaged changes; stage or restore it before committing")
    previous = subprocess.check_output(["git", "show", "HEAD:VERSION"], text=True).strip()
    # An explicitly staged next version is accepted without incrementing twice.
    desired = next_version(previous)
    if staged not in (previous, desired):
        raise ValueError(f"Expected VERSION {previous} or {desired}, got {staged}")
    (Path(root) / "VERSION").write_text(desired + "\n", encoding="ascii", newline="\n")
    subprocess.run(["git", "add", "--", "VERSION"], check=True)
    print(f"Project version: v{desired}")


if __name__ == "__main__":
    main()
