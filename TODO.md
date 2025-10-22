# GPING NEXT TODO

## ✅ Done
- Headless agent cleaned up; legacy GUI artifacts removed.
- `gping_next_config.json` template in repo root (reminder: omit `/exec` in Apps Script URL).
- PowerShell helper `scripts/quick_live_test.ps1` automates baseline, SENDNOW, unlock, and outage validation.
- Documentation refreshed (`README.md`, `docs/LIVE_TEST.md`, `presentation.md`) to cover workflow and presentation talking points.

## ⏭️ In Progress
- Finalize Google Apps Script deployment with public access so telemetry reaches the `health` sheet (current tests still get HTTP 401).
- Confirm manual `uv run python manual_post.py` returns `True` once the script accepts requests.

## 🎯 Next Up
- Decide whether to stay on Google Sheets or stand up a dedicated dashboard (Looker Studio/Vigilix) using the same Apps Script feed.
- Add store-specific targets and credentials in `gping_next_config.json` before field rollout.
- Package Windows startup service via `scripts/install.ps1` after telemetry endpoint is verified.
