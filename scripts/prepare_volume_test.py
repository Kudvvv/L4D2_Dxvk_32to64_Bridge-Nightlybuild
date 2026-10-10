"""Extract actual volume lock/upload methods for a mocked-transport native test."""
import argparse
from pathlib import Path


def prepare(source, output, negative_control=False, copy_reference=False, payload_negative_control=False):
    path = source / "bridge/src/client/d3d9_volume.cpp"
    text = path.read_text(encoding="utf-8")
    start = text.index("HRESULT Direct3DVolume9_LSS::LockBox(")
    # Include the public HRESULT boundary and actual owning lock records.
    methods = text[start:]
    if methods.count("Direct3DVolume9_LSS::") != 5:
        raise ValueError("Volume methods changed; update the test harness")
    layout = (source / "bridge/src/util/volume_layout.h").read_text(encoding="utf-8")
    if negative_control:
        needle = "static_cast<INT>(storage.rowBytes)"
        if layout.count(needle) != 1:
            raise ValueError("Cannot create the old-pitch negative control")
        layout = layout.replace(needle, "static_cast<INT>(storage.columns)")
    if payload_negative_control:
        needle = "  if (bytes > (std::numeric_limits<uint32_t>::max)() - 4u) { return false; }\n"
        if layout.count(needle) != 1:
            raise ValueError("Cannot create the missing-payload-bound negative control")
        layout = layout.replace(needle, "")
    if copy_reference:
        needle = "        memcpy(blobPacketPtr, lockedVolume.pBits, layout.bytes);"
        if methods.count(needle) != 1:
            raise ValueError("Cannot restore the original row-copy path")
        # Both variants keep exactly the same ownership and transport code.
        methods = methods.replace(needle, """        l4d2_volume::visitRows(lockedVolume.pBits, lockedVolume.RowPitch, lockedVolume.SlicePitch, layout,
          [&](const uint8_t* row, uint32_t rowBytes) {
            memcpy(blobPacketPtr, row, rowBytes);
            blobPacketPtr += rowBytes;
          });""")
    header = path.with_suffix(".h").read_text(encoding="utf-8")
    begin = "  struct LockInfo {"
    end = "  std::queue<LockInfo> m_lockInfoQueue;"
    if header.count(begin) != 1 or header.count(end) != 1:
        raise ValueError("Volume lock storage changed; update the harness")
    storage = header[header.index(begin):header.index(end) + len(end)]
    notices = text[:text.index('#include "pch.h"')]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(notices + methods, encoding="utf-8", newline="\n")
    output.with_name("volume_layout.h").write_text(layout, encoding="utf-8", newline="\n")
    output.with_name("volume_lock_storage.h").write_text(
        notices + storage + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    control = parser.add_mutually_exclusive_group()
    control.add_argument("--negative-control", action="store_true")
    control.add_argument("--payload-negative-control", action="store_true")
    control.add_argument("--copy-reference", action="store_true")
    args = parser.parse_args()
    prepare(args.source, args.output, args.negative_control, args.copy_reference,
            args.payload_negative_control)
