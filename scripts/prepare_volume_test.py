"""Extract actual volume lock/upload methods for a mocked-transport native test."""
import argparse
from pathlib import Path


def prepare(source, output, negative_control=False):
    path = source / "bridge/src/client/d3d9_volume.cpp"
    text = path.read_text(encoding="utf-8")
    start = text.index("bool Direct3DVolume9_LSS::lock(")
    # The final four methods are self-contained; fail rather than silently test a copy.
    methods = text[start:]
    if methods.count("Direct3DVolume9_LSS::") != 4:
        raise ValueError("Volume methods changed; update the test harness")
    if negative_control:
        needle = "lockedVolume.RowPitch = rowStride * bytesPerPixel;"
        if methods.count(needle) != 1:
            raise ValueError("Cannot create the old-pitch negative control")
        methods = methods.replace(needle, "lockedVolume.RowPitch = rowStride;")
    notices = text[:text.index('#include "pch.h"')]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(notices + methods, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--negative-control", action="store_true")
    args = parser.parse_args()
    prepare(args.source, args.output,args.negative_control)
