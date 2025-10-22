from datetime import datetime, timedelta
from pathlib import Path

from gping_next.logger import DeltaLogger
from gping_next.schemas import HealthPayload, TargetStatus


def make_payload(ts: datetime, up: bool) -> HealthPayload:
    return HealthPayload(
        ts=ts,
        store="TEST",
        targets=[
            TargetStatus(name="target", up=up, code="success" if up else "tcp_timeout"),
        ],
    )


def test_delta_logger_emits_on_change(tmp_path, monkeypatch):
    monkeypatch.setattr("gping_next.logger.LOG_DIR", tmp_path)
    logger = DeltaLogger("TEST", timedelta(minutes=15))
    now = datetime(2024, 1, 1, 12, 0, 0)
    logger.record(make_payload(now, True))
    later = now + timedelta(minutes=5)
    logger.record(make_payload(later, True))
    later2 = now + timedelta(minutes=16)
    logger.record(make_payload(later2, True))
    csv_path = next(tmp_path.glob("GPing*.csv"))
    lines = csv_path.read_text().strip().splitlines()
    assert len(lines) == 3  # header + 2 entries (initial + heartbeat)
