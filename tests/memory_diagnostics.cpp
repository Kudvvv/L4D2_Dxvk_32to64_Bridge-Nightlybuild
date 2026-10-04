#define NOMINMAX
#include "memory_diagnostics.h"
#include <fstream>
#include <iterator>
#include <limits>
#include <string>

int main(int argc, char** argv) {
  if (argc != 2) { return 1; }
  using namespace l4d2_memory;
  auto surface = allocate(4096, Kind::Surface, 64, 16, 21);
  auto vertex = allocate(8192, Kind::Vertex, 0, 0, 0, true);
  auto index = allocate(2048, Kind::Index);
  if (bytes[0] != 4096 || bytes[1] != 8192 || bytes[2] != 2048 ||
      objects[0] != 1 || objects[1] != 1 || objects[2] != 1) { return 2; }
  for (size_t i = 0; i < 8192; ++i) {
    if (vertex[i] != 0) { return 3; }
  }
  delete[] surface; released(4096, Kind::Surface);
  delete[] vertex; released(8192, Kind::Vertex);
  delete[] index; released(2048, Kind::Index);
  if (bytes[0] != 0 || bytes[1] != 0 || bytes[2] != 0 ||
      objects[0] != 0 || objects[1] != 0 || objects[2] != 0) { return 4; }
  bool failed = false;
  try {
    auto impossible = allocate(std::numeric_limits<size_t>::max(), Kind::Surface);
    delete[] impossible;
  } catch (const std::bad_alloc&) { failed = true; }
  if (!failed || bytes[0] != 0 || objects[0] != 0) { return 5; }
  sample(true, "test-final");
  std::ifstream file(argv[1]);
  const std::string text((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
  if (text.find("event=allocation-failed") == std::string::npos ||
      text.find("event=test-final") == std::string::npos ||
      text.find("scan_complete=1") == std::string::npos ||
      text.find("counters_valid=1") == std::string::npos) { return 6; }
  return 0;
}
