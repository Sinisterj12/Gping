"""Task registration API for RDSIQ."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable, Dict, Optional


TaskFn = Callable[[], Awaitable[None]]


@dataclass(slots=True)
class TaskMetadata:
    name: str
    label: str
    tooltip: str
    action: TaskFn


class TaskRegistry:
    def __init__(self) -> None:
        self._tasks: Dict[str, TaskMetadata] = {}

    def register(self, key: str, metadata: TaskMetadata) -> None:
        self._tasks[key] = metadata

    def get(self, key: str) -> Optional[TaskMetadata]:
        return self._tasks.get(key)

    async def run(self, key: str) -> bool:
        task = self.get(key)
        if not task:
            return False
        await task.action()
        return True

    def all(self) -> Dict[str, TaskMetadata]:
        return dict(self._tasks)


async def noop_task() -> None:
    return None


__all__ = ["TaskRegistry", "TaskMetadata", "TaskFn", "noop_task"]
