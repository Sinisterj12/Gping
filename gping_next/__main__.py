"""CLI entrypoint for GPING NEXT."""
from __future__ import annotations

import argparse
import asyncio
import contextlib
import signal
from datetime import datetime

from .core_runtime import GPingNextAgent
from .config import load_config


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run the GPING NEXT agent")
    parser.add_argument("--once", action="store_true", help="Run a single probe cycle and exit")
    args = parser.parse_args()
    agent = GPingNextAgent(load_config())
    if args.once:
        await agent._gather_and_send(datetime.utcnow(), force_upload=True)  # type: ignore[attr-defined]
        return
    stop_event = asyncio.Event()

    def _handle_stop(*_: object) -> None:
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _handle_stop)
    runner = asyncio.create_task(agent.run_forever())
    await stop_event.wait()
    runner.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await runner


if __name__ == "__main__":
    asyncio.run(main())
