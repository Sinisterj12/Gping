"""Module registration helper to attach GPing to the RDSIQ foundation."""
from __future__ import annotations

from rdsiq_core.runtime import RDSIQCoreAgent

from .core_runtime import GPingNextAgent


def register(agent: RDSIQCoreAgent) -> None:
    """Attach the GPing module to a running foundation agent."""
    gping_agent = GPingNextAgent()

    # Mirror the GPing tasks onto the foundation registry.
    for key, metadata in gping_agent.tasks.all().items():
        agent.register_task(key, metadata)

    async def _runner() -> None:
        await gping_agent.run_forever()

    agent.schedule_task(_runner)
