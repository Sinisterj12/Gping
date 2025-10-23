"""Compatibility layer exposing the shared LocalUIBridge with GPing defaults."""
from __future__ import annotations

from rdsiq_core.config import UI_DIR as CORE_UI_DIR
from rdsiq_core.ui import LocalUIBridge as CoreLocalUIBridge

UI_DIR = CORE_UI_DIR


class LocalUIBridge(CoreLocalUIBridge):
    def __init__(self) -> None:
        super().__init__(UI_DIR)


__all__ = ["LocalUIBridge", "UI_DIR"]
