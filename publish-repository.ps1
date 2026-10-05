param(
  [Parameter(Mandatory = $true)][string]$RepositoryUrl
)
$ErrorActionPreference = 'Stop'
if ($RepositoryUrl -notmatch '^https://github\.com/[A-Za-z0-9_.-]+/L4D2_Dxvk_32to64_Bridge-Nightlybuild(?:\.git)?$') {
  throw 'Use the HTTPS URL of the requested private Nightlybuild repository.'
}
function CheckedGit {
  param([string[]]$Arguments)
  & git @Arguments
  if ($LASTEXITCODE -ne 0) { throw 'Git command failed' }
}
Push-Location $PSScriptRoot
try {
  if (-not (Test-Path -LiteralPath '.git')) {
    CheckedGit @('init', '-b', 'main')
    CheckedGit @('add', '.')
    CheckedGit @('commit', '-m', 'Add automatic upstream Bridge release builds')
    CheckedGit @('remote', 'add', 'origin', $RepositoryUrl)
  } else {
    $remote = & git remote get-url origin
    if ($LASTEXITCODE -ne 0 -or $remote -ne $RepositoryUrl) { throw 'Existing remote differs; checkout preserved' }
  }
  CheckedGit @('push', '-u', 'origin', 'main')
} finally { Pop-Location }
