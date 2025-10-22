"""Configuration loader for GPING NEXT."""
from __future__ import annotations

import json
import socket
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schemas import TargetSpec

CONFIG_FILE = Path("gping_next_config.json")
FIXME_FILE = Path("config.fixme.json")
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
class AgentConfig:
    store_id: str
    targets: List[TargetSpec]
    cadence: Cadence = field(default_factory=Cadence)
    telemetry: TelemetryConfig = field(default_factory=TelemetryConfig)


DEFAULT_TARGETS: List[TargetSpec] = [
    TargetSpec(name="gateway", host="192.168.1.1", port=443, use_tls=False),
    TargetSpec(name="isp", host="8.8.4.4", port=443, use_tls=False),
    TargetSpec(name="public", host="8.8.8.8", port=443, use_tls=False),
]


def _safe_store_id() -> str:
    try:
        return socket.gethostname().upper()
    except Exception:
        return "UNKNOWN-STORE"


def _parse_target(data: Dict[str, Any]) -> Optional[TargetSpec]:
    try:
        return TargetSpec(
            name=data["name"],
            host=data["host"],
            port=int(data.get("port", 443)),
            use_tls=bool(data.get("use_tls", True)),
            http_path=data.get("http_path"),
            sni=data.get("sni"),
            timeout=float(data.get("timeout", 3.0)),
        )
    except Exception:
        return None


def load_config() -> AgentConfig:
    store_id = _safe_store_id()
    targets = DEFAULT_TARGETS
    config_dict: Dict[str, Any] = {}
    if CONFIG_FILE.exists():
        try:
            config_dict = json.loads(CONFIG_FILE.read_text())
        except json.JSONDecodeError:
            FIXME_FILE.write_text(CONFIG_FILE.read_text())
        except Exception:
            pass
    if config_dict:
        if "store_id" in config_dict:
            store_id = str(config_dict.get("store_id") or store_id).strip() or store_id
        parsed_targets = [_parse_target(t) for t in config_dict.get("targets", [])]
        parsed_targets = [t for t in parsed_targets if t is not None]
        if parsed_targets:
            targets = parsed_targets
    DATA_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)
    QUEUE_DIR.mkdir(exist_ok=True)
    UI_DIR.mkdir(exist_ok=True)
    return AgentConfig(store_id=store_id, targets=targets)


__all__ = [
    "AgentConfig",
    "Cadence",
    "TelemetryConfig",
    "AppScriptConfig",
    "load_config",
    "CONFIG_FILE",
    "FIXME_FILE",
    "DATA_DIR",
    "LOG_DIR",
    "QUEUE_DIR",
    "UI_DIR",
]
