"""Telemetry sinks and delivery manager."""
from __future__ import annotations

import asyncio
import gzip
import http.client
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from .config import QUEUE_DIR, TelemetryConfig
from .schemas import HealthPayload, InventoryPayload


class TelemetrySink:
    name = "base"

    async def send(self, payload_type: str, payload: Dict[str, object], idempotency: str) -> bool:
        raise NotImplementedError


class LocalFileSink(TelemetrySink):
    name = "local"

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def send(self, payload_type: str, payload: Dict[str, object], idempotency: str) -> bool:
        path = self.base_dir / f"{payload_type}.jsonl"
        record = json.dumps({"id": idempotency, "payload": payload})
        await asyncio.to_thread(self._append, path, record)
        return True

    def _append(self, path: Path, record: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as fh:
            fh.write(record + "\n")


class AppsScriptSink(TelemetrySink):
    name = "apps_script"

    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def send(self, payload_type: str, payload: Dict[str, object], idempotency: str) -> bool:
        url = f"{self.base_url}/ingest"
        return await _post_gzip_json(url, payload, self.api_key, idempotency)

    async def fetch_watchlist(self) -> Dict[str, Dict[str, str]]:
        url = f"{self.base_url}/watchlist"
        data = await _get_json(url, self.api_key)
        return data.get("stores", {}) if isinstance(data, dict) else {}

    async def check_trigger(self, store: str) -> bool:
        url = f"{self.base_url}/trigger/{store}"
        data = await _get_json(url, self.api_key)
        if isinstance(data, dict) and data.get("refresh"):
            await _post_gzip_json(url, {"cleared": True}, self.api_key, f"clear-{store}")
            return True
        return False


class VigilixPlaceholderSink(TelemetrySink):
    name = "vigilix"

    async def send(self, payload_type: str, payload: Dict[str, object], idempotency: str) -> bool:
        # Placeholder acknowledges payload without network IO.
        return True


SINK_REGISTRY = {
    LocalFileSink.name: LocalFileSink,
    AppsScriptSink.name: AppsScriptSink,
    VigilixPlaceholderSink.name: VigilixPlaceholderSink,
}


class TelemetryManager:
    def __init__(self, config: TelemetryConfig) -> None:
        self.config = config
        self.sinks: List[TelemetrySink] = []
        self._queue = QueueStorage(QUEUE_DIR)
        for name in config.sinks:
            sink_cls = SINK_REGISTRY.get(name)
            if not sink_cls:
                continue
            if sink_cls is LocalFileSink:
                self.sinks.append(sink_cls(QUEUE_DIR / "sent"))
            elif sink_cls is AppsScriptSink:
                self.sinks.append(sink_cls(config.app_script.base_url, config.app_script.api_key))
            else:
                self.sinks.append(sink_cls())

    async def send_health(self, payload: HealthPayload) -> None:
        data = _serialize_health(payload)
        await self._send("health", data, payload.ts, payload.store)

    async def send_inventory(self, payload: InventoryPayload) -> None:
        data = _serialize_inventory(payload)
        await self._send("inventory", data, payload.ts, payload.store)

    async def _send(self, payload_type: str, payload: Dict[str, object], ts: datetime, store: str) -> None:
        idempotency = f"{payload_type}-{store}-{ts.isoformat()}"
        pending = await self._queue.load()
        for entry in list(pending):
            ok = await self._dispatch(entry["payload_type"], entry["payload"], entry["id"])
            if not ok:
                await self._queue.save(entry["payload_type"], entry["payload"], entry["id"])
        success = await self._dispatch(payload_type, payload, idempotency)
        if not success:
            await self._queue.save(payload_type, payload, idempotency)

    async def _dispatch(self, payload_type: str, payload: Dict[str, object], idempotency: str) -> bool:
        ok_any = False
        for sink in self.sinks:
            try:
                ok = await sink.send(payload_type, payload, idempotency)
            except Exception:
                ok = False
            ok_any = ok_any or ok
        return ok_any


class QueueStorage:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def load(self) -> List[Dict[str, object]]:
        return await asyncio.to_thread(self._load_sync)

    def _load_sync(self) -> List[Dict[str, object]]:
        items = []
        for path in sorted(self.base_dir.glob("queued-*.json")):
            try:
                data = json.loads(path.read_text())
            except Exception:
                path.unlink(missing_ok=True)
                continue
            items.append(data)
            path.unlink(missing_ok=True)
        return items

    async def save(self, payload_type: str, payload: Dict[str, object], idempotency: str) -> None:
        await asyncio.to_thread(self._save_sync, payload_type, payload, idempotency)

    def _save_sync(self, payload_type: str, payload: Dict[str, object], idempotency: str) -> None:
        safe_id = idempotency.replace(":", "_")
        path = self.base_dir / f"queued-{safe_id}.json"
        if path.exists():
            return
        record = {"payload_type": payload_type, "payload": payload, "id": idempotency}
        path.write_text(json.dumps(record))


def _serialize_health(payload: HealthPayload) -> Dict[str, object]:
    return {
        "ts": payload.ts.isoformat(),
        "store": payload.store,
        "targets": [asdict(target) for target in payload.targets],
    }


def _serialize_inventory(payload: InventoryPayload) -> Dict[str, object]:
    return {
        "ts": payload.ts.isoformat(),
        "store": payload.store,
        "bios": payload.bios,
        "system": payload.system,
        "printers": payload.printers,
        "monitor": payload.monitor,
        "nics": payload.nics,
    }


async def _post_gzip_json(url: str, payload: Dict[str, object], api_key: str, idem: str) -> bool:
    return await asyncio.to_thread(_post_sync, url, payload, api_key, idem)


def _post_sync(url: str, payload: Dict[str, object], api_key: str, idem: str) -> bool:
    try:
        conn, path = _build_connection(url)
        body = gzip.compress(json.dumps(payload).encode("utf-8"))
        headers = {
            "Content-Type": "application/json",
            "Content-Encoding": "gzip",
            "X-RDS-Key": api_key,
            "X-Idempotency-Key": idem,
        }
        conn.request("POST", path, body=body, headers=headers)
        response = conn.getresponse()
        return 200 <= response.status < 300
    except Exception:
        return False


def _get_json(url: str, api_key: str) -> Dict[str, object]:
    try:
        conn, path = _build_connection(url)
        conn.request("GET", path, headers={"X-RDS-Key": api_key})
        response = conn.getresponse()
        if response.status != 200:
            return {}
        data = response.read()
        if response.getheader("Content-Encoding") == "gzip":
            data = gzip.decompress(data)
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {}


def _build_connection(url: str) -> tuple[http.client.HTTPSConnection, str]:
    if not url.startswith("https://"):
        raise ValueError("Apps Script endpoint must be HTTPS")
    without_scheme = url[len("https://"):]
    host, _, path = without_scheme.partition("/")
    return http.client.HTTPSConnection(host, timeout=5), "/" + path


__all__ = [
    "TelemetryManager",
    "TelemetrySink",
    "LocalFileSink",
    "AppsScriptSink",
    "VigilixPlaceholderSink",
]
