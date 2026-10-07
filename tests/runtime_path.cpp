// SPDX-License-Identifier: MIT
#include "runtime_path.h"
#include <chrono>
#include <stdexcept>
#include <cstdio>
int main() {
  const auto root = std::filesystem::temp_directory_path() /
    ("l4d2-runtime-path-" + std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
  try {
    std::filesystem::create_directories(root / "bin" / ".l4d2bridge");
    if (l4d2_paths::runtimeBase(root,".l4d2bridge") != root / "bin") throw std::runtime_error("root DLL path");
    if (l4d2_paths::runtimeBase(root / "bin",".l4d2bridge") != root / "bin") throw std::runtime_error("vulkan DLL path");
    std::filesystem::remove_all(root / "bin");
    std::filesystem::create_directories(root / ".l4d2bridge");
    if (l4d2_paths::runtimeBase(root,".l4d2bridge") != root) throw std::runtime_error("sibling runtime fallback");
    std::filesystem::remove_all(root);
    std::puts("PASS: root d3d9 and bin dxvk_d3d9 share the configured runtime directory");
    return 0;
  } catch (const std::exception& e) {
    std::fprintf(stderr,"%s\n",e.what()); std::filesystem::remove_all(root); return 1;
  }
}
