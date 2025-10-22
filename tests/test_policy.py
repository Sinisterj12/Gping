from datetime import datetime, timedelta

from gping_next.config import Cadence
from gping_next.policy import CadencePolicy


def test_watchlist_adjusts_cadence():
    cadence = Cadence(normal=timedelta(hours=1), watch=timedelta(minutes=5))
    policy = CadencePolicy(cadence, "STORE")
    now = datetime(2024, 1, 1, 12, 0, 0)
    assert policy.cadence_for(now) == cadence.normal.total_seconds()
    policy.update_watchlist({"STORE": {"mode": "watch", "until": "2024-01-01T12:20:00"}}, now)
    assert policy.cadence_for(now) == cadence.watch.total_seconds()
    policy.clear_expired(datetime(2024, 1, 1, 12, 30, 0))
    assert policy.cadence_for(now) == cadence.normal.total_seconds()
