# Operations Runbook

## Repo Map
```
/ rdsiq_core/           # RDSIQ foundation (cadence loop, telemetry, triggers, task/intent registry, UI bridge)
/ gping_next/           # GPing module riding on the foundation (probes, logger, policy, inventory)
/ dashboard/apps_script # Apps Script stubs for ingest/watchlist/trigger
/ docs/                 # Architecture, API, UX, constraints, ops, troubleshooting references
/ scripts/              # PowerShell deployment helpers (install/unlock/sendnow/uninstall)
/ tests/                # Pytest coverage for logging, policy, triggers, queue, UI
```

## 10-Minute Evaluation Steps
1. `uv run python -m rdsiq_core --once` – confirm the foundation writes `data/ui/status.json` and that telemetry directories exist.
2. Add `"gping_next.module"` to `rdsiq_config.json`, then rerun `uv run python -m rdsiq_core --once` – verify GPing logs appear under `data/logs/` and telemetry hits `data/queue/sent/health.jsonl`.
3. Touch `SENDNOW` (or run `./scripts/sendnow.ps1`) and rerun the foundation – confirm immediate uploads are recorded.
4. Create `UNLOCK_demo` and rerun – inspect `data/ui/status.json` for an unlocked payload with R/A/G status and last failure reason.
5. Run `uv run pytest` – ensure unit checks for logging, cadence policy, queue dedupe, UI locks, and trigger handling pass.
6. Simulate an outage (unplug network or point targets to an invalid host) and rerun – confirm offline queue files appear, then reconnect and rerun to watch them flush.
