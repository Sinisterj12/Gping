"""GPING NEXT telemetry wrappers built on the RDSIQ core manager."""
from __future__ import annotations

from dataclasses import asdict
from typing import Dict

from rdsiq_core.config import QUEUE_DIR as CORE_QUEUE_DIR
from rdsiq_core.telemetry import (
    AppsScriptSink,
    LocalFileSink,
    QueueStorage,
    SINK_REGISTRY,
    TelemetryManager as BaseTelemetryManager,
    TelemetrySink,
    VigilixPlaceholderSink,
)

from .schemas import HealthPayload, InventoryPayload


QUEUE_DIR = CORE_QUEUE_DIR


class TelemetryManager(BaseTelemetryManager):
    def __init__(self, config) -> None:
        super().__init__(config, queue_dir=QUEUE_DIR)

    async def send_health(self, payload: HealthPayload) -> None:
        data = _serialize_health(payload)
        await self.send_payload("health", data, payload.ts, payload.store)

    async def send_inventory(self, payload: InventoryPayload) -> None:
        data = _serialize_inventory(payload)
        await self.send_payload("inventory", data, payload.ts, payload.store)


def _serialize_health(payload: HealthPayload) -> Dict[str, object]:
    return {
        "ts": payload.ts.isoformat(),
        "store": payload.store,
        "targets": [asdict(target) for target in payload.targets],
    }


def _serialize_inventory(payload: InventoryPayload) -> Dict[str, object]:
    return {
        "ts": payload.ts.isoformat(),
        "store": payload.store,
        "bios": payload.bios,
        "system": payload.system,
        "printers": payload.printers,
        "monitor": payload.monitor,
        "nics": payload.nics,
    }


__all__ = [
    "TelemetryManager",
    "TelemetrySink",
    "LocalFileSink",
    "AppsScriptSink",
    "VigilixPlaceholderSink",
    "QueueStorage",
    "SINK_REGISTRY",
    "QUEUE_DIR",
]
