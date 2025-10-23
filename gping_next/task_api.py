"""Compatibility layer for GPING NEXT task registry."""
from __future__ import annotations

from rdsiq_core.task_registry import TaskFn, TaskMetadata, TaskRegistry, noop_task

__all__ = ["TaskRegistry", "TaskMetadata", "TaskFn", "noop_task"]
