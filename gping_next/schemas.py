"""Data schemas for GPING NEXT."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass(slots=True)
class TargetSpec:
    name: str
    host: str
    port: int = 443
    use_tls: bool = True
    http_path: Optional[str] = None
    sni: Optional[str] = None
    timeout: float = 3.0


@dataclass(slots=True)
class TargetStatus:
    name: str
    up: bool
    code: str
    tcp_ms: Optional[float] = None
    tls_ms: Optional[float] = None
    http_ms: Optional[float] = None
    note: Optional[str] = None


@dataclass(slots=True)
class HealthPayload:
    ts: datetime
    store: str
    targets: List[TargetStatus]


@dataclass(slots=True)
class InventoryPayload:
    ts: datetime
    store: str
    bios: Dict[str, Optional[str]]
    system: Dict[str, Optional[str]]
    printers: List[Dict[str, Optional[str]]] = field(default_factory=list)
    monitor: Dict[str, Optional[str]] = field(default_factory=dict)
    nics: List[Dict[str, Optional[str]]] = field(default_factory=list)


@dataclass(slots=True)
class TriggerState:
    unlocked_token: Optional[str] = None
    send_now: bool = False


@dataclass(slots=True)
class WatchMode:
    mode: str
    until: datetime


WatchMap = Dict[str, WatchMode]
