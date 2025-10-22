# Operations Runbook

## Repo Map
```
/ gping_next/           # Agent source (async runtime, probes, telemetry, UI bridge)
/ dashboard/apps_script # Apps Script stubs for ingest/watchlist/trigger
/ docs/                 # Architecture, API, UX, constraints, ops, troubleshooting references
/ scripts/              # PowerShell deployment helpers (install/unlock/sendnow/uninstall)
/ tests/                # Pytest coverage for logging, policy, triggers, queue, UI
```

## 10-Minute Evaluation Steps
1. `uv run python -m gping_next --once` – perform a single probe cycle, verify CSV + JSONL output under `data/logs/`.
2. Touch `SENDNOW` and rerun `uv run python -m gping_next --once` – confirm immediate upload recorded in `data/queue/sent/health.jsonl`.
3. Create `UNLOCK_demo` and rerun – inspect `data/ui/status.json` for unlocked payload with R/A/G state and last failure reason.
4. Run `uv run pytest` – ensure unit checks for logging, policy cadence, queue dedupe, UI locks, and trigger handling pass.
5. Review `data/queue` after removing network (simulate by editing config) – confirm offline queue files appear and flush after next successful run.
