# Live Test Guide

### Quick Start
- Run `.\scripts\quick_live_test.ps1` from the repo root (default runs `uv sync` for you).  
- Follow the prompts. The script handles baseline probes, SENDNOW uploads, UI unlock, and prompts exactly when to unplug or reconnect the network.
- When finished, it re-locks the UI and removes helper files so the working tree stays clean.
- If you use the Google Apps Script sink, set `telemetry.app_script.base_url` to the deployment URL **without** `/exec`; the agent appends `/ingest` on its own.

### What Happens
```
Baseline ──> SENDNOW upload ──> UNLOCK demo ──╮
                                             │
                                 unplug ↴    │
                             Offline cycle ──┼─> Recovery cycle ──> Cleanup
                                 replug ↱    │
```
- During the offline cycle, watch `data/queue/` for new `queued-*.json` files.
- Recovery flushes the queue and appends to `data/queue/sent/health.jsonl`.
- Every run prints the most recent JSONL entry so you can copy/paste into status reports.

### Optional Flags
- Use `.\scripts\quick_live_test.ps1 -SkipSync` if dependencies are already installed.
- To run the agent manually at any point:  
  - Continuous loop: `uv run python -m gping_next` (Ctrl+C to stop).  
  - Single cycle: `uv run python -m gping_next --once`.

Keep this guide and `AGENTS.md` handy when you brief others; the script output mirrors the operational checklist in `docs/OPERATIONS.md`.
