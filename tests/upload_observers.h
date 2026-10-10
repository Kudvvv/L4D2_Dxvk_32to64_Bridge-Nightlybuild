// SPDX-License-Identifier: MIT
// Narrow observer doubles for production upload extraction tests. They record
// every supplied byte so upload fast paths cannot silently skip enabled hashes.
#pragma once
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace l4d2_api_wait {
enum class Api { VolumeLockBox, VolumeUnlockBox, CreateVolumeTexture, CreateCubeTexture,
  CreateVertexBuffer, CreateIndexBuffer, CreateRenderTarget, CreateDepthStencilSurface,
  CreateOffscreenPlainSurface };
enum class Metric { ShadowRelease, Retention, UploadLocal, PayloadCopy, PayloadCopyHash };
struct ApiScope { explicit ApiScope(Api) {} };
struct Span { explicit Span(Metric) {} void finish() {} };
template<typename Work> auto backend(Work&& work) { return work(); }
}
namespace l4d2_color {
inline std::atomic<bool> enabled { false };
struct Digest {
  std::vector<uint8_t> bytes;
  void add(const void* data, size_t size) {
    const auto* first = static_cast<const uint8_t*>(data);
    bytes.insert(bytes.end(), first, first + size);
  }
};
inline std::vector<uint8_t> lastUpload;
template<typename... Args> void record(const char*, Args...) {}
struct Texture { uint32_t width, height, depth, levels, usage, format, pool, id; };
template<typename... Args> void texture(const char*, const Texture&, Args...) {}
enum class State { Reset };
template<typename... Args> void observe(Args...) {}
template<typename Format, typename Pitch, typename Slice>
void upload(uint32_t, uint32_t, const char*, uint32_t, Format, uint32_t, uint32_t,
            uint32_t, Pitch, Slice, const Digest& digest, HRESULT, HRESULT, bool valid) {
  if (enabled.load() && valid) { lastUpload = digest.bytes; }
}
}
namespace l4d2_data {
struct Temporary { explicit Temporary(uint64_t) {} };
enum class Kind { Vertex, Index };
struct Resource {
  template<typename... Args> void open(Args...) {}
  template<typename... Args> void lock(Args...) {}
  template<typename... Args> void unlock(Args...) {}
  void destroyLocked(size_t) {}
  template<typename... Args> void upload(Args...) {}
};
}
