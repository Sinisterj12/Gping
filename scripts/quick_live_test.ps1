Param(
    [switch]$SkipSync,
    [switch]$SkipOutage
)

$ErrorActionPreference = 'Stop'
$root = Resolve-Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) '..')
$rootPath = $root.ProviderPath
Set-Location -Path $rootPath

function Invoke-Uv {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )
    & uv @Args
    if ($LASTEXITCODE -ne 0) {
        throw "uv $($Args -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Run-AgentOnce {
    param(
        [string]$Label
    )
    Write-Host ""
    Write-Host ">>> $Label" -ForegroundColor Cyan
    Invoke-Uv -Args @('run', 'python', '-m', 'gping_next', '--once')
}

function Run-AgentWithTriggers {
    param(
        [string]$Label
    )
    Write-Host ""
    Write-Host ">>> $Label" -ForegroundColor Cyan
    Invoke-Uv -Args @('run', 'python', 'scripts/run_trigger_cycle.py')
}

function Show-LatestLogSummary {
    $log = Get-ChildItem -Path (Join-Path $root 'data/logs') -Filter 'GPing*.jsonl' -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if (-not $log) {
        Write-Host "No JSONL log found yet." -ForegroundColor Yellow
        return
    }
    Write-Host "Latest log: $($log.Name)" -ForegroundColor Yellow
    $tail = Get-Content -Path $log.FullName | Select-Object -Last 1
    if ($tail) {
        Write-Host $tail
    }
}

function Show-QueueStatus {
    $queueDir = Join-Path $root 'data/queue'
    $queued = Get-ChildItem -Path $queueDir -Filter 'queued-*.json' -ErrorAction SilentlyContinue
    $sent = Get-ChildItem -Path (Join-Path $queueDir 'sent') -Filter '*.jsonl' -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($queued) {
        Write-Host "Queued files pending upload: $($queued.Count)" -ForegroundColor Red
    } else {
        Write-Host "No queued files pending upload." -ForegroundColor Green
    }
    if ($sent) {
        Write-Host "Latest uploaded log: $($sent.Name) @ $($sent.LastWriteTime.ToString('u'))"
    } else {
        Write-Host "No uploaded logs yet."
    }
}

function Show-UIStatus {
    $uiFile = Join-Path $root 'data/ui/status.json'
    if (-not (Test-Path $uiFile)) {
        Write-Host "UI status file not created yet." -ForegroundColor Yellow
        return
    }
    Write-Host "UI snapshot:"
    Get-Content -Path $uiFile | Write-Host
}

Write-Host "=== GPING NEXT Quick Live Test ===" -ForegroundColor Green
Write-Host "Root: $rootPath"

if (-not $SkipSync) {
    Write-Host "Step 0: Ensuring dependencies (uv sync)..." -ForegroundColor Yellow
    Invoke-Uv -Args @('sync')
}

Run-AgentOnce -Label 'Baseline probe (online)'
Show-LatestLogSummary
Show-QueueStatus

Write-Host ""
Write-Host "Step 2: Force telemetry send (SENDNOW trigger)" -ForegroundColor Yellow
New-Item -Path (Join-Path $root 'SENDNOW') -ItemType File -Force | Out-Null
Run-AgentOnce -Label 'Forced upload cycle'
Show-QueueStatus

Write-Host ""
Write-Host "Step 3: Unlock local status view (UNLOCK_demo)" -ForegroundColor Yellow
$unlockPath = Join-Path $root 'UNLOCK_demo'
New-Item -Path $unlockPath -ItemType File -Force | Out-Null
Run-AgentWithTriggers -Label 'Unlocked status cycle'
Show-UIStatus
Remove-Item -Path $unlockPath -Force -ErrorAction SilentlyContinue

if (-not $SkipOutage) {
    Write-Host ""
    Write-Host "Step 4: Live outage drill" -ForegroundColor Yellow
    Read-Host "Disconnect network (pull cable or disable NIC), then press ENTER to capture offline run"
    Run-AgentOnce -Label 'Offline capture'
    Show-LatestLogSummary
    Show-QueueStatus

    Read-Host "Reconnect network, wait 5 seconds, then press ENTER to flush queued uploads"
    Run-AgentOnce -Label 'Recovery capture'
    Show-LatestLogSummary
    Show-QueueStatus
} else {
    Write-Host ""
    Write-Host "Step 4: Live outage drill (skipped)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Cleanup: re-locking UI and removing helper files" -ForegroundColor Yellow
Invoke-Uv -Args @('run', 'python', '-c', 'from gping_next.web_local import LocalUIBridge; LocalUIBridge().lock()')
Remove-Item -Path (Join-Path $root 'SENDNOW') -Force -ErrorAction SilentlyContinue
Remove-Item -Path (Join-Path $root 'UNLOCK_*') -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Finished. Review outputs above; logs remain under data/logs/ for audit." -ForegroundColor Green
