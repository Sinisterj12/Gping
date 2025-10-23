# Live Test Guide

### Quick Start
- Run `.\scripts\quick_live_test.ps1` from the repo root (it runs `uv sync` for you).  
- Follow the prompts. The script boots the RDSIQ foundation, registers modules (GPing by default), forces SENDNOW uploads, unlocks the UI, and tells you exactly when to unplug or reconnect the network.
- When finished, it re-locks the UI, clears helper files, and leaves the working tree clean.
- If you use the Google Apps Script sink, set `telemetry.app_script.base_url` to the deployment URL **without** `/exec`; the agent appends `/ingest` on its own.

### What Happens
```
Foundation check → Module cycle → SENDNOW upload → UNLOCK demo
                                              │
                               unplug ?       │
                           Offline cycle ───▶ Recovery cycle ───▶ Cleanup
                               replug ?       │
```
- During the offline cycle, watch `data/queue/` for new `queued-*.json` files.
- Recovery flushes the queue and appends to `data/queue/sent/health.jsonl`.
- Each run prints the most recent JSONL entry so you can copy/paste into status reports.

### Optional Flags
- Use `.\scripts\quick_live_test.ps1 -SkipSync` if dependencies are already installed.
- To run manually at any point:  
  - Foundation continuous loop: `uv run python -m rdsiq_core` (Ctrl+C to stop).  
  - Foundation single cycle: `uv run python -m rdsiq_core --once`.  
  - Standalone GPing cycle (bypassing the foundation) stays available via `uv run python -m gping_next --once`.

Keep this guide and `AGENTS.md` handy when you brief others; the script output mirrors the operational checklist in `docs/OPERATIONS.md`.
