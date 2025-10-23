"""Base runtime scaffolding for RDSIQ agents."""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional, Type

from .config import Cadence, TelemetryConfig, ensure_runtime_dirs
from .schemas import TriggerState
from .task_registry import TaskMetadata, TaskRegistry, TaskFn
from .intent_router import Intent, IntentRouter
from .telemetry import TelemetryManager
from .triggers import read_triggers
from .ui import LocalUIBridge


class RDSIQCoreAgent:
    """Base async agent loop with trigger handling and task registration."""

    def __init__(
        self,
        cadence: Cadence,
        telemetry: TelemetryConfig,
        telemetry_manager_cls: Optional[Type[TelemetryManager]] = None,
    ) -> None:
        ensure_runtime_dirs()
        self.cadence = cadence
        manager_cls = telemetry_manager_cls or TelemetryManager
        self.telemetry = manager_cls(telemetry)
        self.tasks = TaskRegistry()
        self.intent_router = IntentRouter()
        self.ui = LocalUIBridge()
        self.last_failure: Optional[str] = None
        self.last_upload: Optional[datetime] = None

    async def on_startup(self) -> None:
        """Hook for subclasses to perform async startup work."""

    async def run_forever(self) -> None:
        await self.on_startup()
        while True:
            now = datetime.utcnow()
            triggers = read_triggers()
            await self._handle_triggers(triggers)
            await self.run_cycle(now, triggers)
            interval = await self.next_interval(now, triggers)
            await asyncio.sleep(interval)

    async def run_cycle(self, now: datetime, triggers: TriggerState) -> None:
        """Perform a single iteration. Subclasses override."""
        raise NotImplementedError

    async def _handle_triggers(self, triggers: TriggerState) -> None:
        if triggers.unlocked_token:
            self.ui.unlock(triggers.unlocked_token)
        elif not self.ui.is_unlocked():
            self.ui.lock()
        if triggers.send_now:
            await self.on_send_now()

    async def on_send_now(self) -> None:
        """Hook executed when a SENDNOW trigger is consumed."""

    async def next_interval(self, now: datetime, _triggers: TriggerState) -> float:
        """Return seconds to wait until the next cycle."""
        return self.cadence.normal.total_seconds()

    def register_task(self, key: str, metadata: TaskMetadata) -> None:
        self.tasks.register(key, metadata)

    def register_intent(self, phrase: str, intent: Intent) -> None:
        self.intent_router.register(phrase, intent)

    def schedule_task(self, task_fn: TaskFn) -> asyncio.Future:
        return asyncio.ensure_future(task_fn())


__all__ = ["RDSIQCoreAgent"]
