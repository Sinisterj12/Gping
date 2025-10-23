# RDSIQ Ops Platform – Presentation Guide

## What It Is
- **RDSIQ Foundation:** Headless base agent that remote teams trigger from the office. It owns the cadence loop, trigger files, telemetry pipeline, task registry, and local status bridge so modules hot-swap without touching infrastructure.
- **GPING NEXT Module:** Default plug-in that probes gateway/ISP/public targets, captures inventory, and streams health deltas back to the dashboard without opening NetSupport or RDP.
- **Why it matters:** Remote technicians stay in their chairs—no file transfers, no manual script babysitting—yet they still see live store conditions and queue fixes instantly.

## Operator Flow (Desk Perspective)
1. Log into the internal dashboard (Vigilix/Sheets today, future web UI).
2. Pick a store; choose a task (e.g., “Connectivity Pulse” or “Cleanup Driver Cache”) registered with the foundation.
3. RDSIQ executes the module locally, logs to `data/logs/`, queues telemetry under `data/queue/`, and mirrors R/A/G state to `data/ui/status.json`.
4. Results and recommendations show up on the dashboard within seconds—no remote desktop session required.

## Tools & Interfaces
- **Foundation CLI:** `uv run python -m rdsiq_core` (service loop) or `--once` for spot checks; modules declared in `rdsiq_config.json`.
- **Module Examples:** `gping_next` (network health & inventory), future cleaners, package installers, or script runners that register via `register(agent)`.
- **Automation Script:** `scripts/quick_live_test.ps1` drives full smoke/outage drills end-to-end for demo or QA.
- **Telemetry:** Google Apps Script stub today; Vigilix placeholder sink already wired; swap in other sinks by extending `rdsiq_core.telemetry`.

## Talking Points
- Built for remote ops teams, not on-site techs—eliminates repetitive NetSupport sessions and manual .ps1 transfers.
- Modular by design: once the foundation is live, new tools are just another Python module hooking the shared task registry.
- Resilient in rough networks thanks to delta logging, durable queue, SENDNOW triggers, and watchlist cadence control.
- Uses placeholders only (`KS-218`, demo keys); no production secrets in the repo.

## What’s Next
1. Publish real Apps Script or Vigilix credentials to the secure config channel and update `rdsiq_config.json`.
2. Finish the dashboard card that calls foundation tasks (start with GPing actions).
3. Prioritise the next module (e.g., Drive Cleanup, Log Collection, Package Push) and register it through the same interface.
