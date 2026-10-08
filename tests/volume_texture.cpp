// SPDX-License-Identifier: MIT
// Regression harness for keyou91's PR #3; actual production methods are extracted at build time.
// Transport and format lookup are mocked. No GPU or game-rendering validation is claimed.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <d3d9.h>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <new>
#include <queue>
#include <limits>
#include <stdexcept>
#include <tuple>
#include <utility>
#include <vector>

void require(bool value, const char* message) { if (!value) throw std::runtime_error(message); }
namespace allocation {
bool failArray = false, failScalar = false, failQueueGrowth = false;
size_t liveArrays = 0, scalarFailures = 0;
}
// Exercise the real new[] and std::queue allocation sites without changing production code.
void* operator new(size_t size) {
  if (allocation::failScalar) { ++allocation::scalarFailures; throw std::bad_alloc(); }
  if (auto* memory = std::malloc(size ? size : 1)) { return memory; }
  throw std::bad_alloc();
}
void operator delete(void* memory) noexcept { std::free(memory); }
void operator delete(void* memory, size_t) noexcept { std::free(memory); }
void* operator new[](size_t size) {
  if (allocation::failArray) { throw std::bad_alloc(); }
  if (auto* memory = std::malloc(size ? size : 1)) {
    ++allocation::liveArrays;
    if (allocation::failQueueGrowth) { allocation::failScalar = true; }
    return memory;
  }
  throw std::bad_alloc();
}
void operator delete[](void* memory) noexcept {
  if (memory) { --allocation::liveArrays; }
  std::free(memory);
}
void operator delete[](void* memory, size_t) noexcept { ::operator delete[](memory); }

enum class TransportFault { None, Construct, Header, Payload, Finish };
TransportFault transportFault = TransportFault::None;
struct TransportFailure {};
bool benchmarkEnabled = false;
LARGE_INTEGER copyStart {};
LONGLONG copyTicks = 0;
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
  ClientMessage(uint32_t, uint32_t) {
    if (transportFault == TransportFault::Construct) { throw TransportFailure(); }
    ++capture.count;
  }
  void send_data(size_t size, const void* data) {
    if (!capture.boxSent) {
      if (transportFault == TransportFault::Header) { throw TransportFailure(); }
      require(size == sizeof(D3DBOX), "missing box header");
      std::memcpy(&capture.box, data, size); capture.boxSent = true; return;
    }
    if (transportFault == TransportFault::Payload) { throw TransportFailure(); }
    const auto p = static_cast<const uint8_t*>(data);
    capture.bytes.insert(capture.bytes.end(), p, p + size);
    capture.packets.push_back(size);
  }
  void send_data(DWORD flags) { capture.flags = flags; }
  void send_many(uint32_t a, uint32_t b, uint32_t c, uint32_t d) { capture.fields = {a,b,c,d}; }
  uint8_t* begin_data_blob(size_t size) {
    if (transportFault == TransportFault::Payload) { throw TransportFailure(); }
    capture.bytes.resize(size);
    if (benchmarkEnabled) { QueryPerformanceCounter(&copyStart); }
    return capture.bytes.data();
  }
  void end_data_blob() {
    if (benchmarkEnabled) {
      LARGE_INTEGER end {};
      QueryPerformanceCounter(&end);
      copyTicks += end.QuadPart - copyStart.QuadPart;
    }
    if (transportFault == TransportFault::Finish) { throw TransportFailure(); }
  }
};
struct Logger { static void err(const char*) {} };
#define LogFunctionCall() ((void)0)
#define BRIDGE_PARENT_DEVICE_LOCKGUARD() ((void)0)
class Direct3DVolume9_LSS {
#include "volume_lock_storage.h"
  D3DVOLUME_DESC m_desc {};
public:
  explicit Direct3DVolume9_LSS(D3DFORMAT format, UINT width=32, UINT height=16, UINT depth=8) {
    m_desc.Format = format; m_desc.Width = width; m_desc.Height = height; m_desc.Depth = depth;
  }
  uint32_t getId() const { return 7; }
  size_t pendingLocks() const { return m_lockInfoQueue.size(); }
  HRESULT LockBox(D3DLOCKED_BOX*, CONST D3DBOX*, DWORD);
  HRESULT UnlockBox();
  bool lock(D3DLOCKED_BOX&, const D3DBOX* const, const DWORD);
  void unlock();
  static D3DBOX resolveLockInfoBox(const D3DBOX* const, const D3DVOLUME_DESC&);
  static std::tuple<size_t,size_t,size_t> getBoxDimensions(const D3DBOX&);
};
#include "volume_methods.h"

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
  require(volume.LockBox(&locked, whole ? nullptr : &box, flags) == S_OK, "lock failed");
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
  require(volume.UnlockBox() == S_OK, "unlock failed");
  require(volume.UnlockBox() == S_OK, "extra unlock failed"); // Must not resend.
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

D3DLOCKED_BOX sentinelOutput() {
  return {123, 456, reinterpret_cast<void*>(static_cast<uintptr_t>(1))};
}
void requireEmptyOutput(const D3DLOCKED_BOX& output) {
  require(!output.pBits && output.RowPitch == 0 && output.SlicePitch == 0,
    "failed lock published or retained an output pointer");
}
void testAllocationFailuresAndDestruction() {
  const auto baseline = allocation::liveArrays;
  {
    Direct3DVolume9_LSS volume(D3DFMT_A8R8G8B8, 4, 4, 1);
    require(volume.LockBox(nullptr, nullptr, 0) == D3DERR_INVALIDCALL,
      "null output must return INVALIDCALL");
    auto locked = sentinelOutput();
    allocation::failArray = true;
    const auto result = volume.LockBox(&locked, nullptr, 0);
    allocation::failArray = false;
    require(result == E_OUTOFMEMORY, "buffer allocation failure escaped the HRESULT boundary");
    requireEmptyOutput(locked);
    require(volume.pendingLocks() == 0 && allocation::liveArrays == baseline,
      "buffer allocation failure changed ownership");

    // MSVC deque may allocate its first block lazily. Seed an owned lock before
    // failing growth, so the test also checks preservation of existing records.
    require(volume.LockBox(&locked, nullptr, 0) == S_OK, "could not seed the owning queue");
    bool growthFailed = false;
    for (unsigned attempt = 0; attempt < 1024; ++attempt) {
      locked = sentinelOutput();
      const auto previousLocks = volume.pendingLocks();
      const auto previousArrays = allocation::liveArrays;
      const auto previousFailures = allocation::scalarFailures;
      // new[] succeeds, then the next real std::queue heap allocation must fail.
      allocation::failQueueGrowth = true;
      const auto queued = volume.LockBox(&locked, nullptr, 0);
      allocation::failScalar = allocation::failQueueGrowth = false;
      if (FAILED(queued)) {
        require(allocation::scalarFailures > previousFailures,
          "queue case failed before exercising the scalar allocation fault");
        require(queued == E_OUTOFMEMORY, "queue growth failure escaped the HRESULT boundary");
        requireEmptyOutput(locked);
        require(volume.pendingLocks() == previousLocks && allocation::liveArrays == previousArrays,
          "queue failure leaked its temporary buffer or damaged older locks");
        growthFailed = true;
        break;
      }
      require(locked.pBits && allocation::liveArrays == previousArrays + 1,
        "successful queue insertion lost its buffer");
    }
    require(growthFailed, "the test did not reach a real std::queue growth allocation");
    require(volume.pendingLocks() > 0, "destruction case needs pending locks");
    // Destruction must free every queued buffer without requiring UnlockBox calls.
  }
  require(allocation::liveArrays == baseline, "destroying a locked volume leaked buffers");
  {
    Direct3DVolume9_LSS volume(D3DFMT_A8R8G8B8);
    D3DLOCKED_BOX locked {};
    require(volume.LockBox(&locked, nullptr, 0) == S_OK, "allocation failure poisoned later locks");
    std::memset(locked.pBits, 0x5a, static_cast<size_t>(locked.SlicePitch) * 8);
    capture = {};
    require(volume.UnlockBox() == S_OK, "lock after allocation failure could not unlock");
  }
  require(allocation::liveArrays == baseline, "successful recovery leaked its buffer");
}

void testTransportExceptions() {
  const auto baseline = allocation::liveArrays;
  for (const auto fault : {TransportFault::Construct, TransportFault::Header,
                          TransportFault::Payload, TransportFault::Finish}) {
#ifndef SEND_ALL_LOCK_DATA_AT_ONCE
    if (fault == TransportFault::Finish) { continue; }
#endif
    Direct3DVolume9_LSS volume(D3DFMT_A8R8G8B8);
    D3DLOCKED_BOX locked {};
    require(volume.LockBox(&locked, nullptr, 0) == S_OK, "transport case could not lock");
    std::memset(locked.pBits, 0x6b, static_cast<size_t>(locked.SlicePitch) * 8);
    capture = {};
    transportFault = fault;
    bool caught = false;
    try { volume.UnlockBox(); } catch (const TransportFailure&) { caught = true; }
    transportFault = TransportFault::None;
    require(caught, "transport fault was not exercised");
    require(allocation::liveArrays == baseline && volume.pendingLocks() == 0,
      "transport exception leaked or retained the consumed lock");
    const auto commands = capture.count;
    require(volume.UnlockBox() == S_OK && capture.count == commands,
      "a failed transport left the same lock queued for retransmission");
  }
}

#ifdef SEND_ALL_LOCK_DATA_AT_ONCE
void runCopyBenchmark(const char* variant, const char* round) {
  struct Case { UINT width, height, depth, iterations; };
  LARGE_INTEGER frequency {};
  require(QueryPerformanceFrequency(&frequency) != FALSE, "performance clock unavailable");
  for (const auto item : {Case{32, 32, 16, 512}, Case{128, 64, 16, 128}, Case{256, 128, 16, 64}}) {
    const size_t size = static_cast<size_t>(item.width) * item.height * item.depth * 4;
    std::vector<uint8_t> expected(size);
    for (size_t i = 0; i < size; ++i) { expected[i] = static_cast<uint8_t>((i * 13 + i / 4096) & 255); }
    Direct3DVolume9_LSS volume(D3DFMT_A8R8G8B8, item.width, item.height, item.depth);
    capture = {};
    capture.bytes.resize(size);
    copyTicks = 0;
    // Allocation, initialization, transport setup and byte verification are outside
    // the timed interval, which begins after reserving the destination blob.
    for (UINT iteration = 0; iteration < item.iterations + 8; ++iteration) {
      expected[(static_cast<size_t>(iteration) * 997) % size] ^= static_cast<uint8_t>(iteration + 1);
      D3DLOCKED_BOX locked {};
      require(volume.LockBox(&locked, nullptr, 0) == S_OK, "benchmark lock failed");
      std::memcpy(locked.pBits, expected.data(), size);
      capture.boxSent = false;
      benchmarkEnabled = iteration >= 8;
      require(volume.UnlockBox() == S_OK, "benchmark unlock failed");
      benchmarkEnabled = false;
      require(capture.bytes == expected, "benchmark changed copied bytes");
    }
    require(capture.count == item.iterations + 8, "benchmark omitted an upload");
    const double microseconds = static_cast<double>(copyTicks) * 1000000.0 /
      static_cast<double>(frequency.QuadPart);
    std::printf("volume-copy variant=%s round=%s bytes=%zu iterations=%u copy_total_us=%.3f copy_us_per_iteration=%.3f\n",
      variant, round, size, item.iterations, microseconds, microseconds / item.iterations);
  }
  std::puts("Copy-only CPU microbenchmark; allocation, GPU work and game FPS are not measured.");
}
#endif

int main(int argc, char** argv) {
  try {
#ifdef SEND_ALL_LOCK_DATA_AT_ONCE
    if (argc == 4 && std::strcmp(argv[1], "--benchmark") == 0) {
      runCopyBenchmark(argv[2], argv[3]);
      return 0;
    }
#else
    (void)argc;
    (void)argv;
#endif
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
    rejected = sentinelOutput();
    require(normal.LockBox(&rejected, &invalid, 0) == E_FAIL, "invalid box HRESULT changed");
    requireEmptyOutput(rejected);
    testAllocationFailuresAndDestruction();
    testTransportExceptions();
    require(allocation::liveArrays == 0, "volume test leaked temporary buffers");
    std::puts("PASS: actual volume LockBox/UnlockBox and owning lock records; byte pitches, LUT contents, compressed/partial/tiny volumes, readonly, wire fields, allocation/queue/transport failures and locked destruction");
    return 0;
  } catch (const std::exception& e) { std::fprintf(stderr,"%s\n",e.what()); return 1; }
}
