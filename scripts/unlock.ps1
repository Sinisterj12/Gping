Param(
    [Parameter(Mandatory=$true)]
    [string]$Token
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$marker = Join-Path $root "UNLOCK_$Token"
New-Item -Path $marker -ItemType File -Force | Out-Null
Write-Output "Unlock token $Token created."
