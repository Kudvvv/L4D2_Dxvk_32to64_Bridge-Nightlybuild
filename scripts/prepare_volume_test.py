"""Extract actual volume lock/upload methods for a mocked-transport native test."""
import argparse
from pathlib import Path


def prepare(source, output, negative_control=False, copy_reference=False):
    path = source / "bridge/src/client/d3d9_volume.cpp"
    text = path.read_text(encoding="utf-8")
    start = text.index("HRESULT Direct3DVolume9_LSS::LockBox(")
    # Include the public HRESULT boundary and actual owning lock records.
    methods = text[start:]
    if methods.count("Direct3DVolume9_LSS::") != 6:
        raise ValueError("Volume methods changed; update the test harness")
    if negative_control:
        needle = "pending.RowPitch = static_cast<INT>(rowPitch);"
        if methods.count(needle) != 1:
            raise ValueError("Cannot create the old-pitch negative control")
        methods = methods.replace(needle, "pending.RowPitch = static_cast<INT>(rowStride);")
    if copy_reference:
        needle = "      memcpy(blobPacketPtr, lockedVolume.pBits, totalSize);"
        if methods.count(needle) != 1:
            raise ValueError("Cannot restore the original row-copy path")
        # Both variants keep exactly the same ownership and transport code.
        methods = methods.replace(needle, """      const auto rowSize = static_cast<size_t>(lockedVolume.RowPitch);
      for (uint32_t z = 0; z < depth; z++) {
        for (uint32_t y = 0; y < rows; y++) {
          auto ptr = static_cast<uint8_t*>(lockedVolume.pBits) +
            y * lockedVolume.RowPitch + z * lockedVolume.SlicePitch;
          memcpy(blobPacketPtr, ptr, rowSize);
          blobPacketPtr += rowSize;
        }
      }""")
    header = path.with_suffix(".h").read_text(encoding="utf-8")
    begin = "  struct LockInfo {"
    end = "  std::queue<LockInfo> m_lockInfoQueue;"
    if header.count(begin) != 1 or header.count(end) != 1:
        raise ValueError("Volume lock storage changed; update the harness")
    storage = header[header.index(begin):header.index(end) + len(end)]
    notices = text[:text.index('#include "pch.h"')]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(notices + methods, encoding="utf-8", newline="\n")
    output.with_name("volume_lock_storage.h").write_text(
        notices + storage + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    control = parser.add_mutually_exclusive_group()
    control.add_argument("--negative-control", action="store_true")
    control.add_argument("--copy-reference", action="store_true")
    args = parser.parse_args()
    prepare(args.source, args.output, args.negative_control, args.copy_reference)
