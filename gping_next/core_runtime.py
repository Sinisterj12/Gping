"""Agent runtime for GPING NEXT."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Optional

from .config import AgentConfig, load_config
from .intent_router import Intent, IntentRouter
from .inventory import gather_inventory
from .logger import DeltaLogger
from .policy import CadencePolicy
from .probes import ProbeRunner
from .schemas import HealthPayload, TargetStatus
from .task_api import TaskMetadata, TaskRegistry
from .telemetry import AppsScriptSink, TelemetryManager
from .triggers import read_triggers
from .web_local import LocalUIBridge


class GPingNextAgent:
    def __init__(self, config: Optional[AgentConfig] = None) -> None:
        self.config = config or load_config()
        self.prober = ProbeRunner()
        self.logger = DeltaLogger(self.config.store_id, self.config.cadence.heartbeat)
        self.telemetry = TelemetryManager(self.config.telemetry)
        self.policy = CadencePolicy(self.config.cadence, self.config.store_id)
        self.ui = LocalUIBridge()
        self.tasks = TaskRegistry()
        self.intent_router = IntentRouter()
        self.last_failure: Optional[str] = None
        self.last_upload: Optional[datetime] = None
        self._register_default_tasks()
        self._inventory_sent: Optional[datetime] = None

    async def run_forever(self) -> None:
        await self._send_inventory_once()
        while True:
            now = datetime.utcnow()
            triggers = read_triggers()
            if triggers.unlocked_token:
                self.ui.unlock(triggers.unlocked_token)
            elif not self.ui.is_unlocked():
                self.ui.lock()
            if triggers.send_now:
                await self._gather_and_send(now, force_upload=True)
            if await self._maybe_refresh(now):
                now = datetime.utcnow()
            if self.policy.should_poll_watchlist(now):
                await self._update_watchlist(now)
            interval = self.policy.cadence_for(now)
            await self._gather_and_send(now)
            self.policy.clear_expired(datetime.utcnow())
            await asyncio.sleep(interval)

    async def _gather_and_send(self, now: datetime, force_upload: bool = False) -> None:
        statuses = await self.prober.probe_all(self.config.targets)
        payload = HealthPayload(ts=now, store=self.config.store_id, targets=statuses)
        should_upload = force_upload or self.logger.should_emit(statuses, now)
        self.logger.record(payload)
        if should_upload:
            await self.telemetry.send_health(payload)
            self.last_upload = datetime.utcnow()
        self._update_failure_status(statuses)
        self._update_ui(statuses)

    async def _send_inventory_once(self) -> None:
        if self._inventory_sent and (datetime.utcnow() - self._inventory_sent) < timedelta(hours=23):
            return
        payload = gather_inventory(self.config.store_id)
        await self.telemetry.send_inventory(payload)
        self._inventory_sent = datetime.utcnow()

    async def _maybe_refresh(self, now: datetime) -> bool:
        apps_sink = next((s for s in self.telemetry.sinks if isinstance(s, AppsScriptSink)), None)
        if not apps_sink:
            return False
        triggered = False
        if self.policy.should_poll_refresh(now):
            triggered = await apps_sink.check_trigger(self.config.store_id)
            if triggered:
                await self._gather_and_send(datetime.utcnow(), force_upload=True)
        return triggered

    async def _update_watchlist(self, now: datetime) -> None:
        apps_sink = next((s for s in self.telemetry.sinks if isinstance(s, AppsScriptSink)), None)
        if not apps_sink:
            return
        data = await apps_sink.fetch_watchlist()
        self.policy.update_watchlist(data, now)

    def _update_failure_status(self, statuses: list[TargetStatus]) -> None:
        for status in statuses:
            if not status.up:
                self.last_failure = f"{status.name}:{status.code}"
                return
        self.last_failure = None

    def _update_ui(self, statuses: list[TargetStatus]) -> None:
        color = "green"
        if any(status.code.startswith("http_4") for status in statuses):
            color = "amber"
        if any(not status.up for status in statuses):
            color = "red"
        summary = {
            status.name: ("up" if status.up else status.code)
            for status in statuses
        }
        self.ui.publish(color, self.last_failure, self.last_upload, summary)

    def _register_default_tasks(self) -> None:
        self.tasks.register(
            "check_internet",
            TaskMetadata(
                name="check_internet",
                label="Check Internet",
                tooltip="Runs current probes without delay",
                action=lambda: self._schedule_immediate_probe(),
            ),
        )
        self.tasks.register(
            "send_status",
            TaskMetadata(
                name="send_status",
                label="Send Status Now",
                tooltip="Uploads status to dashboard now",
                action=lambda: self._schedule_immediate_upload(),
            ),
        )
        self.intent_router.register(
            "check internet",
            Intent(name="check_internet", handler=lambda: None, description="Probe connectivity"),
        )

    def _schedule_immediate_probe(self) -> asyncio.Future:
        return asyncio.ensure_future(self._gather_and_send(datetime.utcnow(), force_upload=True))

    def _schedule_immediate_upload(self) -> asyncio.Future:
        return asyncio.ensure_future(self._gather_and_send(datetime.utcnow(), force_upload=True))

async def run() -> None:
    agent = GPingNextAgent()
    await agent.run_forever()


__all__ = ["GPingNextAgent", "run"]
