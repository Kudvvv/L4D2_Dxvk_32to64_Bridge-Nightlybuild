# SPDX-License-Identifier: MIT
# Run each suite in a fresh process so x86/x64 MSVC environments cannot leak.
$ErrorActionPreference = 'Stop'
foreach ($suite in @('runtime_observation', 'pageblock_gc', 'exception_diagnostics',
    'device_reset', 'color_diagnostics', 'data_diagnostics', 'buffer_contract',
    'volume_layout', 'adapter_information', 'overlay_presenter', 'api_wait_diagnostics',
    'readback_recovery', 'x86_backend', 'data_ring_contract', 'ipc_api_failure',
    'ipc_transport')) {
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "test_$suite.ps1")
  if ($LASTEXITCODE -ne 0) { throw "Upstream native regression failed: $suite" }
}
foreach ($arch in @('x86', 'x64')) {
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'test_host_diagnostics.ps1') -Platform $arch
  if ($LASTEXITCODE -ne 0) { throw "Host diagnostic regression failed: $arch" }
}
$repoRoot = Split-Path $PSScriptRoot -Parent
if (!(Test-Path (Join-Path $repoRoot '.deps/dxvk-remix/bridge/src/client/buffer_shadow.h'))) {
  throw 'Prepared merged sources are required for runtime separation contracts'
}
& python -m unittest discover -s (Join-Path $repoRoot 'tests') -p test_runtime_separation.py
if ($LASTEXITCODE -ne 0) { throw 'Runtime separation contracts failed' }
& python -m unittest discover -s (Join-Path $repoRoot 'tests') -p test_install_color_diagnostics.py
if ($LASTEXITCODE -ne 0) { throw 'Temporary-directory color diagnostic installer tests failed' }
