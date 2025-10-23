"""Filesystem-based triggers shared across modules."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from .schemas import TriggerState

ROOT = Path(".")
SENDNOW_FILE = ROOT / "SENDNOW"
UNLOCK_PREFIX = "UNLOCK_"


def read_triggers() -> TriggerState:
    token = _consume_unlock()
    send_now = _consume_sendnow()
    return TriggerState(unlocked_token=token, send_now=send_now)


def _consume_sendnow() -> bool:
    if SENDNOW_FILE.exists():
        try:
            SENDNOW_FILE.unlink()
        finally:
            return True
    return False


def _consume_unlock() -> Optional[str]:
    for path in ROOT.iterdir():
        if path.is_file() and path.name.startswith(UNLOCK_PREFIX):
            token = path.name[len(UNLOCK_PREFIX) :]
            path.unlink(missing_ok=True)
            return token or "default"
    return None


__all__ = ["read_triggers", "TriggerState"]
