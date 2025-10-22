Param()

$ErrorActionPreference = 'Stop'
$root = 'C:\rds\GPING'
New-Item -ItemType Directory -Force -Path $root | Out-Null
Copy-Item -Path "$PSScriptRoot\..\*" -Destination $root -Recurse -Force
$serviceName = 'GPING-NEXT'
$pythonExe = Join-Path $root '.venv\\Scripts\\python.exe'
if (-not (Test-Path $pythonExe)) {
    Write-Output 'Python runtime expected via packaged environment.'
}
$task = New-ScheduledTaskAction -Execute $pythonExe -Argument ' -m gping_next'
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName $serviceName -Action $task -Trigger $trigger -RunLevel Highest -Force | Out-Null
Write-Output 'GPING NEXT installed.'
