// SPDX-License-Identifier: MIT
// Regression harness for keyou91's PR #3; actual production methods are extracted at build time.
// Transport and format lookup are mocked. No GPU or game-rendering validation is claimed.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <d3d9.h>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <queue>
#include <limits>
#include <stdexcept>
#include <tuple>
#include <vector>

void require(bool value, const char* message) { if (!value) throw std::runtime_error(message); }
namespace bridge_util {
uint32_t getBlockSize(D3DFORMAT f) { return f == D3DFMT_DXT1 || f == D3DFMT_DXT5 ? 4u : 1u; }
uint32_t getBytesFromFormat(D3DFORMAT f) {
  if (f == D3DFMT_DXT1) return 8;
  if (f == D3DFMT_DXT5) return 16;
  if (f == D3DFMT_UNKNOWN) return 0;
  require(f == D3DFMT_A8R8G8B8, "unsupported test format"); return 4;
}
}
namespace Commands { constexpr uint32_t IDirect3DVolume9_UnlockBox = 1; }
struct Capture {
  uint32_t count = 0, flags = 0;
  D3DBOX box {};
  std::array<uint32_t,4> fields {};
  std::vector<uint8_t> bytes;
  std::vector<size_t> packets;
  bool boxSent = false;
} capture;
struct ClientMessage {
  ClientMessage(uint32_t, uint32_t) { ++capture.count; }
  void send_data(size_t size, const void* data) {
    if (!capture.boxSent) {
      require(size == sizeof(D3DBOX), "missing box header");
      std::memcpy(&capture.box, data, size); capture.boxSent = true; return;
    }
    const auto p = static_cast<const uint8_t*>(data);
    capture.bytes.insert(capture.bytes.end(), p, p + size);
    capture.packets.push_back(size);
  }
  void send_data(DWORD flags) { capture.flags = flags; }
  void send_many(uint32_t a, uint32_t b, uint32_t c, uint32_t d) { capture.fields = {a,b,c,d}; }
  uint8_t* begin_data_blob(size_t size) { capture.bytes.resize(size); return capture.bytes.data(); }
  void end_data_blob() {}
};
class Direct3DVolume9_LSS {
  struct LockInfo { D3DLOCKED_BOX lockedVolume; D3DBOX box; DWORD flags; };
  std::queue<LockInfo> m_lockInfoQueue;
  D3DVOLUME_DESC m_desc {};
public:
  explicit Direct3DVolume9_LSS(D3DFORMAT format, UINT width=32, UINT height=16, UINT depth=8) {
    m_desc.Format = format; m_desc.Width = width; m_desc.Height = height; m_desc.Depth = depth;
  }
  uint32_t getId() const { return 7; }
  bool lock(D3DLOCKED_BOX&, const D3DBOX* const, const DWORD);
  void unlock();
  static D3DBOX resolveLockInfoBox(const D3DBOX* const, const D3DVOLUME_DESC&);
  static std::tuple<size_t,size_t,size_t> getBoxDimensions(const D3DBOX&);
};
#pragma warning(push)
// Production defines totalSize for the blob path; row mode intentionally leaves it unused.
#pragma warning(disable:4189)
#include "volume_methods.h"
#pragma warning(pop)

void run(D3DFORMAT format, D3DBOX box, bool whole, DWORD flags) {
  capture = {};
  Direct3DVolume9_LSS volume(format);
  if (whole) box = {0,0,32,16,0,8};
  const uint32_t block = bridge_util::getBlockSize(format);
  const uint32_t bytes = bridge_util::getBytesFromFormat(format);
  const uint32_t cols = (box.Right - box.Left + block - 1) / block;
  const uint32_t rows = (box.Bottom - box.Top + block - 1) / block;
  const uint32_t depth = box.Back - box.Front;
  const size_t rowBytes = static_cast<size_t>(cols) * bytes;
  const size_t sliceBytes = rowBytes * rows;
  D3DLOCKED_BOX locked {};
  require(volume.lock(locked, whole ? nullptr : &box, flags), "lock failed");
  require(static_cast<size_t>(locked.RowPitch) == rowBytes, "RowPitch must be bytes");
  require(static_cast<size_t>(locked.SlicePitch) == sliceBytes, "SlicePitch must be bytes");
  std::vector<uint8_t> expected(sliceBytes * depth);
  for (size_t z = 0; z < depth; ++z) for (size_t y = 0; y < rows; ++y) {
    auto* row = static_cast<uint8_t*>(locked.pBits) + z * locked.SlicePitch + y * locked.RowPitch;
    for (size_t x = 0; x < rowBytes; ++x) {
      const auto value = static_cast<uint8_t>((z * 67 + y * 13 + x) & 255);
      row[x] = value; expected[z * sliceBytes + y * rowBytes + x] = value;
    }
  }
  volume.unlock();
  volume.unlock(); // Extra unlock must not resend.
  if (flags & D3DLOCK_READONLY) { require(capture.count == 0, "readonly upload"); return; }
  require(capture.count == 1, "upload count");
  require(capture.fields == std::array<uint32_t,4>{bytes,cols,rows,depth}, "wire fields must remain block counts");
  require(std::memcmp(&capture.box, &box, sizeof(box)) == 0, "partial box changed");
  require(capture.flags == flags && capture.bytes == expected, "upload data overlaps or truncates");
#ifndef SEND_ALL_LOCK_DATA_AT_ONCE
  require(capture.packets.size() == static_cast<size_t>(rows) * depth, "row packet count");
  for (auto size : capture.packets) require(size == rowBytes, "row packet bytes");
#endif
  // Simulate Host writes into padded destination pitches, with guard bytes.
  const size_t hostRow = rowBytes + 8, hostSlice = hostRow * rows + 16;
  std::vector<uint8_t> target(hostSlice * depth + 32, 0xcd), reference = target;
  for (size_t z = 0; z < depth; ++z) for (size_t y = 0; y < rows; ++y) {
    const size_t offset = 16 + z * hostSlice + y * hostRow;
    std::memcpy(target.data() + offset, capture.bytes.data() + z * sliceBytes + y * rowBytes, rowBytes);
    std::memcpy(reference.data() + offset, expected.data() + z * sliceBytes + y * rowBytes, rowBytes);
  }
  require(target == reference, "host layout or guards corrupted");
}
int main() {
  try {
    for (auto format : {D3DFMT_A8R8G8B8,D3DFMT_DXT1,D3DFMT_DXT5}) {
      run(format, {}, true, 0);
      run(format, {4,4,11,9,2,5}, false, 0);
      run(format, {0,0,1,1,0,1}, false, D3DLOCK_DISCARD);
      run(format, {0,0,4,4,0,2}, false, D3DLOCK_READONLY);
    }
    D3DLOCKED_BOX rejected {};
    Direct3DVolume9_LSS unsupported(D3DFMT_UNKNOWN);
    require(!unsupported.lock(rejected,nullptr,0), "unsupported format must fail");
    Direct3DVolume9_LSS huge(D3DFMT_A8R8G8B8,0xffffffffu,0xffffffffu,8);
    require(!huge.lock(rejected,nullptr,0), "overflowing pitch must fail before allocation");
    Direct3DVolume9_LSS hugeCompressed(D3DFMT_DXT1,0xffffffffu,0xffffffffu,8);
    require(!hugeCompressed.lock(rejected,nullptr,0), "compressed dimension overflow must fail");
    Direct3DVolume9_LSS normal(D3DFMT_A8R8G8B8);
    const D3DBOX invalid {8,0,4,4,0,1};
    require(!normal.lock(rejected,&invalid,0), "invalid box must fail");
    std::puts("PASS: actual volume lock/upload methods; byte pitches, LUT contents, compressed/partial/tiny volumes, readonly and wire fields");
    return 0;
  } catch (const std::exception& e) { std::fprintf(stderr,"%s\n",e.what()); return 1; }
}
