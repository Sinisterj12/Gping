# RDSIQ Foundation + GPING NEXT

RDSIQ is the headless foundation that keeps remote teams in control of every POS or back-office host. It owns the cadence loop, trigger files, telemetry fan-out, task registry, and local status bridge so modules can bolt on without rewriting infrastructure.

GPING NEXT is the first production module riding on that foundation. It probes store, ISP, and public endpoints; captures inventory; and uploads health deltas so the ops center sees issues immediately, no remote desktop required.

---

## Why stores like it
- **Understands the outage**: Concurrent TCP/TLS/HTTP probes (with ARP hints) show whether the break is inside the store or out on the ISP side.
- **Stays quiet but available**: Runs headless with <20 MB idle RAM. A simple unlock file reveals a calm red/amber/green summary for on-site checks.
- **Keeps managers in sync**: Hourly health uploads, daily inventory, 15-minute heartbeats, and SENDNOW triggers feed Google Apps Script dashboards or Vigilix.
- **Survives rough networks**: Delta-only logging, durable offline queues, and watchlist-driven 5-minute bursts make it resilient when links flap.

---

## What you need before testing
1. **Python 3.11 and [uv](https://github.com/astral-sh/uv)** installed on the machine.
2. Outbound HTTPS access (no inbound ports required).
3. Optional: PowerShell on Windows for the inventory snapshot and helper scripts (Linux/macOS will fall back gracefully).

The foundation ships with safe defaults. To point at real telemetry endpoints or attach modules:

- Edit `rdsiq_config.json` to set the store id, telemetry sinks, and the modules list (e.g., `"gping_next.module"`).
- Tune `gping_next_config.json` for module-specific settings such as probe targets.

Keep the Apps Script base URL **without** `/exec`; both the foundation and GPing module append `/ingest` automatically.

```json
{
  "store_id": "KS-218",
  "targets": [
    {"name": "gateway", "host": "192.168.1.1", "port": 443, "use_tls": false},
    {"name": "isp", "host": "8.8.4.4", "port": 443, "use_tls": false},
    {"name": "public", "host": "8.8.8.8", "port": 443, "use_tls": false,
     "http_path": "/robots.txt", "timeout": 5.0}
  ]
}
```

If the JSON cannot be parsed, the agent copies it to `config.fixme.json` and continues with defaults so it never blocks monitoring.

---

## Quick automated live test
Run everything from PowerShell in the repo root:

```powershell
.\scripts\quick_live_test.ps1
```

- Ensures dependencies via `uv sync`, runs a baseline probe, forces a SENDNOW upload, unlocks the local status view, and guides you through the unplugged outage drill.
- Prints the latest JSON entries, queue status, and the unlocked `data/ui/status.json` snapshot.
- Re-locks the UI and removes helper files when finished.
- Use `-SkipOutage` if you can’t pull the cable right now, or `-SkipSync` when the environment is already provisioned.

---

## 5-minute smoke test (no coding required)
1. **Foundation heartbeat**
   ```bash
   uv run python -m rdsiq_core --once
   ```
   - Writes `data/ui/status.json` with a green “foundation-online” payload.
   - Confirms trigger handling, telemetry wiring, and queue storage paths are ready.

2. **Attach the GPing module**
   - Add `"gping_next.module"` to the `modules` list in `rdsiq_config.json`.
   - Run `uv run python -m rdsiq_core --once` again; the module registers and executes a health cycle.
   - Check `data/logs/GPingMMDDYYYY.csv` and `data/queue/sent/health.jsonl` for the emitted payload.

3. **Force an upload**
   - Windows PowerShell: `./scripts/sendnow.ps1`
   - macOS/Linux: `touch SENDNOW`
   - Rerun `uv run python -m rdsiq_core --once` (or `uv run python -m gping_next --once` if you prefer the standalone module). You should see a fresh line appended to the JSONL log with the current timestamp.

4. **Unlock the local status view (optional)**
   - Windows PowerShell: `./scripts/unlock.ps1 -Token demo`
   - macOS/Linux: `touch UNLOCK_demo`
   - Re-run the foundation. Inspect `data/ui/status.json` for:
     - `locked: false`
     - `status: green|amber|red`
     - `last_failure_reason`
     - Tooltips capped at 12 words (accessibility)

5. **Inspect the queue (simulated outage)**
   - Temporarily disconnect the machine or edit the config to point at an unreachable host.
   - Run `uv run python -m rdsiq_core --once`; a `queued-*.json` file should appear under `data/queue/`.
   - Restore connectivity and run the command again—the file disappears and `data/queue/sent/health.jsonl` grows.

6. **Run the automated checks**
   ```bash
   uv run pytest
   ```
   Pytest confirms logging cadence, watchlist policy behaviour, trigger handling, UI locks, queue dedupe, telemetry flushing, and more.

That’s it—the agent is ready for longer trials. When promoted to a service, use `./scripts/install.ps1` (idempotent) to register a startup task on Windows. `./scripts/uninstall.ps1` removes it safely.

---

## How it stays reliable on small-town networks
- **Bounded concurrency** keeps probes gentle on fragile links.
- **Error codes with ARP hints** (`l2_present_l3_blocked`, `tcp_timeout`, `tcp_refused`, etc.) point straight at wiring vs. upstream issues.
- **Watchlist cadence** drops to 5-minute loops until a specified date whenever Google Apps Script returns `"mode": "watch"` for the store.
- **Refresh-now triggers** are polled every 45 seconds so dashboards update within the 60 second SLA.
- **Heartbeat guarantee** writes a status line every 15 minutes, even when nothing changes.
- **Seven-day retention** automatically purges aged CSV and JSONL files to avoid manual cleanup.
- **Trigger files** (`SENDNOW`, `UNLOCK_<token>`) give techs and remote ops instant control without logging into the host.

---

## Repo tour
```
rdsiq_core/           # RDSIQ foundation runtime, shared telemetry, triggers, task/intent tooling
gping_next/           # GPing module built on the foundation (probes, logger, policy, UI bridge)
dashboard/apps_script # Google Apps Script stubs and README
scripts/              # PowerShell helpers (install, unlock, sendnow, uninstall)
docs/                 # Architecture, API contract, UX, constraints, ops, troubleshooting guides
tests/                # Pytest coverage for logging, policy, queue, UI, telemetry
```

### RDSIQ foundation quick start

- **Dry run:** `uv run python -m rdsiq_core --once` populates `data/ui/status.json` to confirm the base agent loop is healthy.
- **Continuous:** `uv run python -m rdsiq_core` keeps the foundation alive so modules can be attached dynamically.
- **Module wiring:** add module import paths to `rdsiq_config.json` (see `docs/MANDATORY_HARD_CONDITIONS.md`) and expose a `register(agent)` helper that uses the shared task/intent/telemetry APIs. The GPing module (`gping_next`) is the live example.

Additional documentation:
- `/docs/ARCH.md` – deep dive into the async design.
- `/docs/API.md` – Apps Script endpoints with curl samples.
- `/docs/CONSTRAINTS.md` – operational guardrails.
- `/docs/OPERATIONS.md` – repo map plus a 10-minute evaluation script.
- `/docs/TROUBLESHOOT.md` – quick fixes for common field issues.

---

## Next steps for deployment
1. Configure your Apps Script endpoint or Vigilix integration (stubs provided under `dashboard/apps_script/`).
2. Update `rdsiq_config.json` with the correct store id, telemetry sinks, and module list; adjust `gping_next_config.json` for probe targets.
3. Schedule the foundation (`python -m rdsiq_core`) with `scripts/install.ps1` on each Windows host (or adapt the same logic for other platforms).
4. Monitor `data/logs/`, `data/queue/`, and your dashboard during the first day to confirm watchlist cadence, SENDNOW triggers, and heartbeats behave as expected.

When you're satisfied, the project is ready for extended testing by your team-no extra coding required.
