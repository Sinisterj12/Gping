import asyncio
from datetime import datetime

from gping_next.config import TelemetryConfig
from gping_next.schemas import HealthPayload, TargetStatus
from gping_next.telemetry import TelemetryManager


def test_offline_queue_flushes_when_connection_returns(tmp_path, monkeypatch):
    async def scenario() -> None:
        monkeypatch.setattr("gping_next.telemetry.QUEUE_DIR", tmp_path)
        manager = TelemetryManager(TelemetryConfig(sinks=["local"]))
        sink = manager.sinks[0]
        original_send = sink.send

        async def fail_once(payload_type, payload, idem):
            sink.send = original_send
            return False

        sink.send = fail_once  # type: ignore[assignment]

        payload1 = HealthPayload(
            ts=datetime(2024, 1, 1, 12, 0, 0),
            store="STORE",
            targets=[TargetStatus(name="gateway", up=False, code="tcp_timeout")],
        )
        await manager.send_health(payload1)
        queued = list(tmp_path.glob("queued-*.json"))
        assert len(queued) == 1

        payload2 = HealthPayload(
            ts=datetime(2024, 1, 1, 12, 5, 0),
            store="STORE",
            targets=[TargetStatus(name="gateway", up=True, code="success")],
        )
        await manager.send_health(payload2)

        assert not list(tmp_path.glob("queued-*.json"))
        sent_file = tmp_path / "sent" / "health.jsonl"
        assert sent_file.exists()
        contents = sent_file.read_text().strip().splitlines()
        # One line for the flushed payload and one for the latest send
        assert len(contents) == 2

    asyncio.run(scenario())
