Param()

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$marker = Join-Path $root 'SENDNOW'
New-Item -Path $marker -ItemType File -Force | Out-Null
Write-Output 'Send-now trigger created.'
