# GPING NEXT Architecture

## Overview
GPING NEXT is a headless async agent that performs proactive network probes, collects lightweight system inventory, and ships telemetry to multiple sinks. The runtime stays dormant between scheduled cadences to respect the <20 MB RAM / low CPU requirement.

## Package Layout
- `gping_next/core_runtime.py` – async orchestrator for probes, telemetry, watchlist cadence, and trigger handling.
- `gping_next/config.py` – configuration loader with safe defaults and directory provisioning.
- `gping_next/probes.py` – concurrent TCP/TLS/HTTP probes with ARP awareness for `l2_present_l3_blocked` classification.
- `gping_next/logger.py` – delta-only CSV + JSON logging and 7-day retention manager.
- `gping_next/telemetry.py` – pluggable sinks (Local, Apps Script, Vigilix placeholder) with durable queue + idempotency keys.
- `gping_next/policy.py` – cadence control, watchlist evaluation, refresh polling windows.
- `gping_next/web_local.py` – locked-by-default UI projection to a local JSON snapshot (no inbound ports).
- `gping_next/task_api.py` & `gping_next/intent_router.py` – extensible command/task routing scaffolding.
- `gping_next/inventory.py` – PowerShell CIM-based inventory with fail-soft fallbacks.

## Data Flow
1. **Probes**: `ProbeRunner` issues bounded-concurrency TCP connects, optional TLS handshake inspection, and optional HTTP HEAD requests.
2. **Logging**: `DeltaLogger` writes CSV + JSONL only when states change or on the 15-minute heartbeat.
3. **Telemetry**: `TelemetryManager` fan-outs payloads to configured sinks. Failures are spooled to `data/queue` with idempotency keys.
4. **Policy**: `CadencePolicy` shifts cadence to 5-minute watch mode based on Apps Script watchlist and enforces refresh polling SLA (≤60 s).
5. **UI**: When an `UNLOCK_*` trigger is present, `LocalUIBridge` renders the latest status summary for a local dashboard while preserving tooltips and last failure metadata.

## Extensibility
- Drop-in tasks via `TaskRegistry.register()`.
- Additional telemetry sinks can inherit `TelemetrySink` and be listed in `TelemetryConfig.sinks`.
- Inventory modules can be expanded by adding new PowerShell queries while keeping fail-soft semantics.
