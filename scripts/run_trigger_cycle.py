"""Run a single agent cycle after consuming trigger files."""
from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gping_next.core_runtime import GPingNextAgent  # noqa: E402
from gping_next.config import load_config  # noqa: E402
from gping_next.triggers import read_triggers  # noqa: E402


async def main() -> None:
    agent = GPingNextAgent(load_config())
    triggers = read_triggers()
    if triggers.unlocked_token:
        agent.ui.unlock(triggers.unlocked_token)
    await agent._gather_and_send(datetime.utcnow(), force_upload=True)  # type: ignore[attr-defined]


if __name__ == "__main__":
    asyncio.run(main())
