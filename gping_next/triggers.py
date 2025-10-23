"""Compatibility layer exposing trigger helpers for GPING NEXT."""
from __future__ import annotations

from rdsiq_core.triggers import TriggerState, read_triggers

__all__ = ["read_triggers", "TriggerState"]
