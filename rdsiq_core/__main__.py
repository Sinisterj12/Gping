"""CLI entrypoint for the RDSIQ foundation agent."""
from __future__ import annotations

import argparse
import asyncio
import contextlib
import importlib
import signal
from datetime import datetime
from pathlib import Path
import sys

from .config import FoundationConfig, load_foundation_config
from .runtime import RDSIQCoreAgent
from .schemas import TriggerState


class FoundationAgent(RDSIQCoreAgent):
    def __init__(self, config: FoundationConfig) -> None:
        super().__init__(config.cadence, config.telemetry)
        self.config = config
        self._last_ping: datetime | None = None
        self._registered_modules: list[str] = []

    async def on_startup(self) -> None:
        summary = {
            "status": "foundation-online",
            "store": self.config.store_id,
            "modules": self._registered_modules or self.config.modules or ["none"],
        }
        self.ui.publish("green", None, None, summary)

    async def run_cycle(self, now: datetime, _triggers) -> None:
        self._last_ping = now
        if self._registered_modules:
            return
        summary = {
            "heartbeat": now.isoformat(),
            "store": self.config.store_id,
            "modules": "pending",
        }
        self.ui.publish("green", None, None, summary)

    async def on_send_now(self) -> None:
        if self._registered_modules:
            return
        summary = {
            "heartbeat": datetime.utcnow().isoformat(),
            "store": self.config.store_id,
            "modules": "triggered",
        }
        self.ui.publish("amber", None, None, summary)

    def note_module_registered(self, name: str) -> None:
        self._registered_modules.append(name)


def _register_modules(agent: FoundationAgent, modules: list[str]) -> None:
    for entry in modules:
        module_path, _, func_name = entry.partition(":")
        target = func_name or "register"
        try:
            module = importlib.import_module(module_path)
            register = getattr(module, target)
        except Exception as exc:
            print(f"[rdsiq_core] Failed to load module '{entry}': {exc}", file=sys.stderr)
            continue
        try:
            register(agent)
            agent.note_module_registered(entry)
            print(f"[rdsiq_core] Registered module '{entry}'")
        except Exception as exc:
            print(f"[rdsiq_core] Module '{entry}' raised during register(): {exc}", file=sys.stderr)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run the RDSIQ foundation agent")
    parser.add_argument("--once", action="store_true", help="Run a single loop and exit")
    parser.add_argument("--config", type=str, default=None, help="Optional path to rdsiq_config.json")
    args = parser.parse_args()

    if sys.platform.startswith("win"):
        with contextlib.suppress(AttributeError):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # type: ignore[attr-defined]

    config = load_foundation_config(None if args.config is None else Path(args.config))
    agent = FoundationAgent(config)
    _register_modules(agent, config.modules)

    if args.once:
        await agent.on_startup()
        await agent.run_cycle(datetime.utcnow(), TriggerState())
        return

    stop_event = asyncio.Event()

    def _handle_stop(*_: object) -> None:
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, _handle_stop)

    runner = asyncio.create_task(agent.run_forever())
    await stop_event.wait()
    runner.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await runner


if __name__ == "__main__":
    asyncio.run(main())
