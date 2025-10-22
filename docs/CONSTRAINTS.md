# Operational Constraints

- Outbound HTTPS only. The agent never opens inbound ports; local UI is a JSON snapshot gated by unlock tokens.
- Headless by default: no pop-ups or tray icons. Unlock triggers only enable local inspection.
- Resource budget: idle footprint <20 MB RAM with near-zero CPU by sleeping between async cadences.
- Logging strategy: delta-only entries with a 15-minute heartbeat, purged after seven days.
- Triggers: filesystem flags `SENDNOW` and `UNLOCK_*` control uploads and UI availability.
- Cadence: hourly baseline, 5-minute watch mode until the provided date, and automatic reversion once expired.
- Refresh-now SLA: Apps Script trigger polling occurs every ≤45 s so dashboards reflect changes within 60 s.
- Secrets: no credentials stored at rest; headers/presigned URLs handle auth. All payloads redact PII fields by omission.
