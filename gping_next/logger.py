"""Logging utilities for GPING NEXT."""
from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .config import LOG_DIR
from .schemas import HealthPayload, TargetStatus


CSV_HEADER = ["timestamp", "target", "up", "code", "tcp_ms", "tls_ms", "http_ms", "note"]
JSON_HEADER = ["ts", "store", "targets"]


class DeltaLogger:
    """Write delta-only log files with periodic heartbeats."""

    def __init__(self, store: str, heartbeat: timedelta) -> None:
        self.store = store
        self.heartbeat = heartbeat
        self._last_status: Dict[str, TargetStatus] = {}
        self._last_written: Optional[datetime] = None

    def _log_paths(self, when: datetime) -> Dict[str, Path]:
        stamp = when.strftime("%m%d%Y")
        csv_path = LOG_DIR / f"GPing{stamp}.csv"
        json_path = LOG_DIR / f"GPing{stamp}.jsonl"
        return {"csv": csv_path, "json": json_path}

    def _write_csv_rows(self, csv_path: Path, rows: Iterable[List[str]]) -> None:
        existed = csv_path.exists()
        with csv_path.open("a", newline="") as fh:
            writer = csv.writer(fh)
            if not existed:
                writer.writerow(CSV_HEADER)
            for row in rows:
                writer.writerow(row)

    def _write_json(self, json_path: Path, payload: HealthPayload) -> None:
        record = {
            "ts": payload.ts.isoformat(),
            "store": payload.store,
            "targets": [asdict(t) for t in payload.targets],
        }
        with json_path.open("a") as fh:
            fh.write(json.dumps(record) + "\n")

    def should_emit(self, statuses: List[TargetStatus], now: datetime) -> bool:
        if self._last_written is None:
            return True
        if now - self._last_written >= self.heartbeat:
            return True
        for status in statuses:
            previous = self._last_status.get(status.name)
            if previous is None:
                return True
            if (
                previous.up != status.up
                or previous.code != status.code
                or previous.tcp_ms != status.tcp_ms
                or previous.tls_ms != status.tls_ms
                or previous.http_ms != status.http_ms
                or previous.note != status.note
            ):
                return True
        return False

    def record(self, payload: HealthPayload) -> None:
        now = payload.ts
        if not self.should_emit(payload.targets, now):
            return
        paths = self._log_paths(now)
        rows: List[List[str]] = []
        for status in payload.targets:
            rows.append(
                [
                    now.isoformat(),
                    status.name,
                    "1" if status.up else "0",
                    status.code,
                    f"{status.tcp_ms:.2f}" if status.tcp_ms is not None else "",
                    f"{status.tls_ms:.2f}" if status.tls_ms is not None else "",
                    f"{status.http_ms:.2f}" if status.http_ms is not None else "",
                    status.note or "",
                ]
            )
            self._last_status[status.name] = status
        self._write_csv_rows(paths["csv"], rows)
        self._write_json(paths["json"], payload)
        self._last_written = now
        self._cleanup(now)

    def _cleanup(self, now: datetime) -> None:
        horizon = now - timedelta(days=7)
        for path in LOG_DIR.glob("GPing*.csv"):
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            if mtime < horizon:
                path.unlink(missing_ok=True)
        for path in LOG_DIR.glob("GPing*.jsonl"):
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            if mtime < horizon:
                path.unlink(missing_ok=True)


__all__ = ["DeltaLogger"]
