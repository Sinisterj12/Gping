"""Local UI projection without exposing inbound ports."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from .config import UI_DIR


class LocalUIBridge:
    def __init__(self, ui_dir: Optional[Path] = None) -> None:
        self._token: Optional[str] = None
        self._ui_dir = ui_dir or UI_DIR
        self._path = self._ui_dir / "status.json"
        self.lock()

    def lock(self) -> None:
        self._token = None
        self._write({"locked": True})

    def unlock(self, token: str) -> None:
        self._token = token

    def is_unlocked(self) -> bool:
        return self._token is not None

    def publish(
        self,
        status_color: str,
        last_failure: Optional[str],
        last_upload: Optional[datetime],
        summary: Dict[str, str],
    ) -> None:
        if not self._token:
            self.lock()
            return
        payload = {
            "locked": False,
            "token": self._token,
            "status": status_color,
            "last_failure_reason": last_failure or "None recorded",
            "last_upload": last_upload.isoformat() if last_upload else None,
            "summary": summary,
            "tooltips": {
                "status": "Green steady means all clear",
                "send": "Uploads status to dashboard now",
                "check": "Runs current probes without delay",
            },
        }
        self._write(payload)

    def _write(self, payload: Dict[str, object]) -> None:
        self._ui_dir.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(payload, indent=2))


__all__ = ["LocalUIBridge"]
