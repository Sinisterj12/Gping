Param()

$ErrorActionPreference = 'Stop'
$root = 'C:\rds\GPING'
$serviceName = 'GPING-NEXT'
if (Get-ScheduledTask -TaskName $serviceName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $serviceName -Confirm:$false | Out-Null
}
if (Test-Path $root) {
    Remove-Item -Path $root -Recurse -Force
}
Write-Output 'GPING NEXT removed.'
