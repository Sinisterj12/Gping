"""Shared dataclasses for RDSIQ core."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


@dataclass(slots=True)
class TriggerState:
    unlocked_token: Optional[str] = None
    send_now: bool = False


@dataclass(slots=True)
class WatchMode:
    mode: str
    until: datetime


WatchMap = Dict[str, WatchMode]


__all__ = ["TriggerState", "WatchMode", "WatchMap"]
