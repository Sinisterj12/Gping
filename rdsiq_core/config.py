"""Shared configuration and runtime directories for RDSIQ."""
from __future__ import annotations

import json
import socket
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path("data")
LOG_DIR = DATA_DIR / "logs"
QUEUE_DIR = DATA_DIR / "queue"
UI_DIR = DATA_DIR / "ui"


@dataclass(slots=True)
class Cadence:
    normal: timedelta = timedelta(hours=1)
    watch: timedelta = timedelta(minutes=5)
    heartbeat: timedelta = timedelta(minutes=15)
    refresh_poll: timedelta = timedelta(seconds=45)


@dataclass(slots=True)
class AppScriptConfig:
    base_url: str = "https://script.google.com/macros/s/app-id"
    api_key: str = "demo-key"


@dataclass(slots=True)
class TelemetryConfig:
    sinks: List[str] = field(default_factory=lambda: ["local", "apps_script", "vigilix"])
    app_script: AppScriptConfig = field(default_factory=AppScriptConfig)


@dataclass(slots=True)
class FoundationConfig:
    store_id: str
    telemetry: TelemetryConfig = field(default_factory=TelemetryConfig)
    cadence: Cadence = field(default_factory=Cadence)
    modules: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


def ensure_runtime_dirs() -> None:
    """Create runtime directories if they are missing."""
    for path in (DATA_DIR, LOG_DIR, QUEUE_DIR, UI_DIR):
        path.mkdir(parents=True, exist_ok=True)


def load_foundation_config(path: Optional[Path] = None) -> FoundationConfig:
    """Load a lightweight configuration for the foundation agent."""
    path = path or Path("rdsiq_config.json")
    ensure_runtime_dirs()
    if not path.exists():
        return FoundationConfig(store_id=_safe_store_id())
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        path.with_suffix(".fixme.json").write_text(path.read_text(encoding="utf-8", errors="ignore"))
        return FoundationConfig(store_id=_safe_store_id())
    except Exception:
        return FoundationConfig(store_id=_safe_store_id())
    defaults_app = AppScriptConfig()
    defaults_cadence = Cadence()
    store = str(data.get("store_id") or "").strip() or _safe_store_id()
    telemetry_dict = data.get("telemetry") or {}
    sinks = telemetry_dict.get("sinks", ["local", "apps_script", "vigilix"])
    app_script_dict = telemetry_dict.get("app_script") or {}
    telemetry = TelemetryConfig(
        sinks=list(sinks),
        app_script=AppScriptConfig(
            base_url=str(app_script_dict.get("base_url") or defaults_app.base_url),
            api_key=str(app_script_dict.get("api_key") or defaults_app.api_key),
        ),
    )
    cadence_dict = data.get("cadence") or {}
    cadence = Cadence(
        normal=_parse_timedelta(cadence_dict.get("normal"), defaults_cadence.normal),
        watch=_parse_timedelta(cadence_dict.get("watch"), defaults_cadence.watch),
        heartbeat=_parse_timedelta(cadence_dict.get("heartbeat"), defaults_cadence.heartbeat),
        refresh_poll=_parse_timedelta(cadence_dict.get("refresh_poll"), defaults_cadence.refresh_poll),
    )
    metadata = data.get("metadata") or {}
    modules = [str(m).strip() for m in data.get("modules", []) if str(m).strip()]
    return FoundationConfig(store_id=store, telemetry=telemetry, cadence=cadence, modules=modules, metadata=metadata)


def _parse_timedelta(value: Any, default: timedelta) -> timedelta:
    if isinstance(value, (int, float)):
        return timedelta(seconds=float(value))
    if isinstance(value, dict):
        seconds = value.get("seconds")
        if seconds is not None:
            try:
                return timedelta(seconds=float(seconds))
            except (TypeError, ValueError):
                return default
    return default


def _safe_store_id() -> str:
    try:
        return socket.gethostname().upper()
    except Exception:
        return "UNKNOWN-STORE"


__all__ = [
    "Cadence",
    "AppScriptConfig",
    "TelemetryConfig",
    "FoundationConfig",
    "DATA_DIR",
    "LOG_DIR",
    "QUEUE_DIR",
    "UI_DIR",
    "ensure_runtime_dirs",
    "load_foundation_config",
]
