param([ValidateSet('x86','x64')][string]$CompileArchitecture)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$source = Join-Path $repoRoot '.deps/dxvk-remix'
$testDir = Join-Path $repoRoot '.deps/volume-test'
New-Item -ItemType Directory -Force $testDir | Out-Null
if ($CompileArchitecture) {
  python "$PSScriptRoot/prepare_volume_test.py" $source "$testDir/volume_methods.h"
  if ($LASTEXITCODE -ne 0) { throw 'Volume test extraction failed' }
  . (Join-Path $source 'bridge/build_common.ps1')
  SetupVS -Platform $CompileArchitecture -VcVarsVer '14.29'
  Push-Location $testDir
  try {
    foreach ($mode in @('rows','blob')) {
      $options = @('/nologo','/std:c++17','/EHsc','/W4','/WX',"/I$testDir","$repoRoot/tests/volume_texture.cpp","/Fe:volume-$CompileArchitecture-$mode.exe")
      if ($mode -eq 'blob') { $options += '/DSEND_ALL_LOCK_DATA_AT_ONCE' }
      & cl.exe @options
      if ($LASTEXITCODE -ne 0) { throw "Volume test compilation failed: $CompileArchitecture/$mode" }
      & (Join-Path $testDir "volume-$CompileArchitecture-$mode.exe")
      if ($LASTEXITCODE -ne 0) { throw "Volume test failed: $CompileArchitecture/$mode" }
    }
    # The same test must reject the original block-count RowPitch bug.
    python "$PSScriptRoot/prepare_volume_test.py" $source "$testDir/volume_methods.h" --negative-control
    if ($LASTEXITCODE -ne 0) { throw 'Negative control extraction failed' }
    & cl.exe /nologo /std:c++17 /EHsc /W4 /WX /DSEND_ALL_LOCK_DATA_AT_ONCE "/I$testDir" "$repoRoot/tests/volume_texture.cpp" "/Fe:volume-$CompileArchitecture-negative.exe"
    if ($LASTEXITCODE -ne 0) { throw 'Negative control compilation failed' }
    & (Join-Path $testDir "volume-$CompileArchitecture-negative.exe")
    if ($LASTEXITCODE -eq 0) { throw 'Regression test failed to detect the old RowPitch bug' }
    python "$PSScriptRoot/prepare_volume_test.py" $source "$testDir/volume_methods.h"
    if ($LASTEXITCODE -ne 0) { throw 'Failed to restore actual volume methods' }
  } finally { Pop-Location }
} else {
  foreach ($arch in @('x86','x64')) {
    & powershell.exe -NoProfile -File $PSCommandPath -CompileArchitecture $arch
    if ($LASTEXITCODE -ne 0) { throw "Volume test failed: $arch" }
  }
}
