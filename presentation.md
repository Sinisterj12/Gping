# GPING NEXT – Presentation Guide

## What It Is
- Headless Python agent that watches gateway/ISP/public targets and logs every probe.
- Ships telemetry to Google Apps Script (demo) or Vigilix when configured, so you have remote visibility even if the store is offline.
- Local CSV/JSONL archives under `data/` for on-site audits; PowerShell script automates smoke and outage drills.

## User Flow
- Techs or automation drop trigger files (`SENDNOW`, `UNLOCK_<token>`) to force uploads or expose the local status snapshot.
- The agent runs continuously via `uv run python -m gping_next` or the Windows scheduled task (`scripts/install.ps1`).
- Loss of connectivity queues telemetry locally; once the WAN returns, the queue flushes automatically.
- Remote teams open the Google Sheet (Apps Script) to see incoming payloads in near real time; dashboards or Vigilix can consume the same feed.

## Tools & Interfaces
- **Local:** PowerShell helper `scripts/quick_live_test.ps1` for smoke/outage demos; `data/ui/status.json` shows R/A/G state when unlocked.
- **Remote:** Google Apps Script backing a Sheet tab (`health`) captures uploads today; production can swap in Vigilix or a web dashboard.
- **Config:** `gping_next_config.json` defines store id, targets, and telemetry endpoints. Defaults are safe placeholders.

## Talking Points
- Designed for grocery lanes with flaky networks: resilient queueing, short burst watchlist mode, forced SENDNOW telemetry for 60-second SLAs.
- Headless by default, so it survives restarts and runs unattended; GUI can be layered later if techs need live charts.
- Logs are structured (JSONL) so you can pipe into Data Studio or Vigilix without new ETL work.
- PowerShell installers allow RMM rollout; uninstall script leaves no residue.

## What’s Next
- Plug in real Apps Script URL/API key or Vigilix credentials.
- Optionally build a lightweight web dashboard (Data Studio/Looker or custom) on top of the same telemetry feed.
- Add store-specific targets in `gping_next_config.json` before field trials.
