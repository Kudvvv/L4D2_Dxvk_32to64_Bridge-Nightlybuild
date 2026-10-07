param(
  [Parameter(Mandatory=$true)][ValidateSet('no-bridge','bridge')][string]$Mode,
  [Parameter(Mandatory=$true)][string]$Label,
  [Parameter(Mandatory=$true)][string]$OutputDirectory,
  [ValidateRange(1,3600)][int]$Seconds=120,
  [ValidateRange(1,30)][int]$IntervalSeconds=1
)
$ErrorActionPreference='Stop'
$game=@(Get-Process -Name left4dead2 -ErrorAction SilentlyContinue)
$hostProcesses=@(Get-Process -Name L4D2Bridge64 -ErrorAction SilentlyContinue)
if ($game.Count -ne 1) { throw 'Start one L4D2 process and reach the test scene first.' }
if ($Mode -eq 'bridge' -and $hostProcesses.Count -ne 1) { throw 'Bridge mode requires one L4D2Bridge64 process.' }
if ($Mode -eq 'no-bridge' -and $hostProcesses.Count -ne 0) { throw 'Stop the Bridge Host before recording the no-bridge baseline.' }
$output=[IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $output) { throw 'Use a new output directory; existing results are preserved.' }
New-Item -ItemType Directory -Path $output | Out-Null
$targets=@($game[0])
if ($Mode -eq 'bridge') { $targets+=$hostProcesses[0] }
$csv=Join-Path $output 'process-metrics.csv'
$cores=[Environment]::ProcessorCount
if ($cores -le 0) { throw 'Unable to determine logical processor count.' }
$manifest=@{
  label=$Label; mode=$Mode; started_at=[DateTimeOffset]::Now.ToString('o');
  logical_processors=$cores; requested_seconds=$Seconds; interval_seconds=$IntervalSeconds;
  processes=@($targets | ForEach-Object { @{pid=$_.Id;name=$_.ProcessName} });
  notes='CPU percent is normalized to all logical processors. Process metrics are not FPS or client free virtual address space.';
  map='FILL IN'; scene_position_and_view='FILL IN'; gpu='FILL IN'; driver='FILL IN';
  game_build='FILL IN'; release_tag='FILL IN'; upstream_commit='FILL IN'; recipe_digest='FILL IN';
  backend_version_and_sha256='FILL IN'; mods_and_config_hashes='FILL IN'; resolution_and_quality='FILL IN'
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $output 'session.json') -Encoding utf8
$previous=@{}
$startTimes=@{}
foreach ($target in $targets) { $startTimes[$target.Id]=$target.StartTime }
$timer=[Diagnostics.Stopwatch]::StartNew()
while ($timer.Elapsed.TotalSeconds -lt $Seconds) {
  $rows=@()
  foreach ($original in $targets) {
    $role=if ($original.Id -eq $game[0].Id) {'game'} else {'host'}
    try {
      $process=Get-Process -Id $original.Id -ErrorAction Stop
      if ($process.StartTime -ne $startTimes[$original.Id]) { throw 'Target PID was reused; partial samples are preserved.' }
      $now=$timer.Elapsed.TotalSeconds
      $cpu=$process.TotalProcessorTime.TotalSeconds
      $percent=$null
      if ($previous.ContainsKey($process.Id)) {
        $delta=$now-$previous[$process.Id].time
        if ($delta -gt 0) { $percent=100*($cpu-$previous[$process.Id].cpu)/$delta/$cores }
      }
      $previous[$process.Id]=@{time=$now;cpu=$cpu}
      $rows+=[pscustomobject]@{time_utc=[DateTime]::UtcNow.ToString('o');elapsed_seconds=[Math]::Round($now,3);label=$Label;mode=$Mode;role=$role;pid=$process.Id;state='running';cpu_percent_machine=$percent;working_set_bytes=$process.WorkingSet64;private_bytes=$process.PrivateMemorySize64;handles=$process.HandleCount}
    } catch [Microsoft.PowerShell.Commands.ProcessCommandException] {
      $rows+=[pscustomobject]@{time_utc=[DateTime]::UtcNow.ToString('o');elapsed_seconds=[Math]::Round($timer.Elapsed.TotalSeconds,3);label=$Label;mode=$Mode;role=$role;pid=$original.Id;state='exited';cpu_percent_machine=$null;working_set_bytes=$null;private_bytes=$null;handles=$null}
      $rows | Export-Csv -LiteralPath $csv -NoTypeInformation -Append -Encoding utf8
      throw 'A target process exited. Partial results have been preserved.'
    }
  }
  $rows | Export-Csv -LiteralPath $csv -NoTypeInformation -Append -Encoding utf8
  Start-Sleep -Seconds $IntervalSeconds
}
Write-Output "Saved baseline to $output. Complete session.json and attach frame times and Bridge logs."
