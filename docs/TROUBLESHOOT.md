# Troubleshooting Checklist

| Symptom | Checks | Resolution |
| --- | --- | --- |
| No logs generated | Ensure `data/logs/` exists and timestamps are current. | Delete stale CSVs and rerun `uv run python -m gping_next --once` to rehydrate. |
| Heartbeat missing | Confirm agent stayed online >15 minutes. | Restart service; heartbeat fires when cadence elapses. |
| Watch mode never activates | Inspect `/docs/API.md` curl examples to verify Apps Script returns store entry. | Validate watchlist JSON includes `until` in ISO format. |
| Refresh-now ignored | Check `data/queue` for stuck payloads and confirm HTTPS endpoint reachable. | Clear queue, verify firewall allows outbound 443. |
| UI never unlocks | Confirm `UNLOCK_*` file name matches token and that status JSON updates. | Regenerate unlock token using `scripts/unlock.ps1 -Token <value>`. |
| Frequent dropouts on old wiring | Look for repeated `l2_present_l3_blocked` or `tcp_timeout` codes plus ARP hints in logs. | Switch the store to watch mode via `/watchlist`, run `SENDNOW` after cable reseat, and review local wiring before escalating to ISP. |
