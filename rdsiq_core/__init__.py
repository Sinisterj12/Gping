"""RDSIQ core foundation package."""
from __future__ import annotations

from .config import (
    AppScriptConfig,
    Cadence,
    TelemetryConfig,
    DATA_DIR,
    LOG_DIR,
    QUEUE_DIR,
    UI_DIR,
    ensure_runtime_dirs,
)
from .intent_router import Intent, IntentRouter
from .runtime import RDSIQCoreAgent
from .schemas import TriggerState, WatchMode, WatchMap
from .task_registry import TaskMetadata, TaskRegistry, TaskFn, noop_task
from .telemetry import (
    AppsScriptSink,
    LocalFileSink,
    TelemetryManager,
    TelemetrySink,
    VigilixPlaceholderSink,
)
from .triggers import read_triggers
from .ui import LocalUIBridge

__all__ = [
    "AppScriptConfig",
    "AppsScriptSink",
    "Cadence",
    "DATA_DIR",
    "Intent",
    "IntentRouter",
    "LocalFileSink",
    "LocalUIBridge",
    "LOG_DIR",
    "RDSIQCoreAgent",
    "QUEUE_DIR",
    "TelemetryConfig",
    "TelemetryManager",
    "TelemetrySink",
    "TaskFn",
    "TaskMetadata",
    "TaskRegistry",
    "TriggerState",
    "UI_DIR",
    "VigilixPlaceholderSink",
    "WatchMap",
    "WatchMode",
    "ensure_runtime_dirs",
    "noop_task",
    "read_triggers",
]
