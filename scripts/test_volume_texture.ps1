param(
  [ValidateSet('x86','x64')][string]$CompileArchitecture,
  [switch]$Benchmark
)
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
    if ($Benchmark) {
      foreach ($variant in @('optimized','row-reference')) {
        $extractOptions = @("$PSScriptRoot/prepare_volume_test.py", $source, "$testDir/volume_methods.h")
        if ($variant -eq 'row-reference') { $extractOptions += '--copy-reference' }
        python @extractOptions
        if ($LASTEXITCODE -ne 0) { throw "Volume copy extraction failed: $variant" }
        # Identical harness and optimization flags; only the production copy path differs.
        & cl.exe /nologo /std:c++17 /EHsc /W4 /WX /O2 /DSEND_ALL_LOCK_DATA_AT_ONCE "/I$testDir" "$repoRoot/tests/volume_texture.cpp" "/Fe:volume-copy-$CompileArchitecture-$variant.exe"
        if ($LASTEXITCODE -ne 0) { throw "Volume copy benchmark compilation failed: $variant" }
        & (Join-Path $testDir "volume-copy-$CompileArchitecture-$variant.exe")
        if ($LASTEXITCODE -ne 0) { throw "Volume copy benchmark correctness checks failed: $variant" }
      }
      python "$PSScriptRoot/prepare_volume_test.py" $source "$testDir/volume_methods.h"
      if ($LASTEXITCODE -ne 0) { throw 'Failed to restore actual volume methods' }
      $results = @()
      for ($round = 1; $round -le 5; ++$round) {
        $variants = if ($round % 2) { @('row-reference','optimized') } else { @('optimized','row-reference') }
        foreach ($variant in $variants) {
          $lines = & (Join-Path $testDir "volume-copy-$CompileArchitecture-$variant.exe") --benchmark $variant $round
          if ($LASTEXITCODE -ne 0) { throw "Volume copy benchmark failed: $variant/$round" }
          foreach ($line in $lines) {
            Write-Output $line
            if ($line -match '^volume-copy variant=(\S+) round=(\d+) bytes=(\d+) iterations=(\d+) copy_total_us=([\d.]+) copy_us_per_iteration=([\d.]+)$') {
              $results += [pscustomobject]@{
                architecture = $CompileArchitecture; variant = $Matches[1]; round = [int]$Matches[2];
                bytes = [long]$Matches[3]; iterations = [int]$Matches[4];
                copy_total_us = [double]::Parse($Matches[5], [cultureinfo]::InvariantCulture);
                copy_us_per_iteration = [double]::Parse($Matches[6], [cultureinfo]::InvariantCulture)
              }
            }
          }
        }
      }
      if ($results.Count -ne 30) { throw 'Volume copy benchmark produced incomplete measurements' }
      $results | Export-Csv -LiteralPath (Join-Path $testDir "volume-copy-$CompileArchitecture.csv") -NoTypeInformation -Encoding utf8
      $results | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $testDir "volume-copy-$CompileArchitecture.json") -Encoding utf8
      return
    }
    & cl.exe /nologo /std:c++17 /EHsc /W4 /WX "/I$source/bridge/src/util" "$repoRoot/tests/runtime_path.cpp" "/Fe:runtime-path-$CompileArchitecture.exe"
    if ($LASTEXITCODE -ne 0) { throw 'Runtime path test compilation failed' }
    & (Join-Path $testDir "runtime-path-$CompileArchitecture.exe")
    if ($LASTEXITCODE -ne 0) { throw 'Runtime path test failed' }
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
    $childOptions = @('-NoProfile', '-File', $PSCommandPath, '-CompileArchitecture', $arch)
    if ($Benchmark) { $childOptions += '-Benchmark' }
    & powershell.exe @childOptions
    if ($LASTEXITCODE -ne 0) { throw "Volume test failed: $arch" }
  }
}
