"""Cadence and policy helpers."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from .config import Cadence


class CadencePolicy:
    def __init__(self, cadence: Cadence, store: str) -> None:
        self.cadence = cadence
        self.store = store
        self._watch_until: Optional[datetime] = None
        self._last_watch_check: Optional[datetime] = None
        self._last_refresh_poll: Optional[datetime] = None

    def update_watchlist(self, watch_data: Dict[str, Dict[str, str]], now: datetime) -> None:
        self._last_watch_check = now
        store_entry = watch_data.get(self.store)
        if not store_entry:
            self._watch_until = None
            return
        until_str = store_entry.get("until")
        if not until_str:
            self._watch_until = None
            return
        try:
            until = datetime.fromisoformat(until_str)
        except ValueError:
            self._watch_until = None
            return
        if until < now:
            self._watch_until = None
        else:
            self._watch_until = until

    def cadence_for(self, now: datetime) -> float:
        if self._watch_until and now < self._watch_until:
            return self.cadence.watch.total_seconds()
        return self.cadence.normal.total_seconds()

    def should_poll_watchlist(self, now: datetime) -> bool:
        if self._last_watch_check is None:
            return True
        return (now - self._last_watch_check) >= self.cadence.normal

    def should_poll_refresh(self, now: datetime) -> bool:
        if self._last_refresh_poll is None:
            self._last_refresh_poll = now
            return True
        if (now - self._last_refresh_poll) >= self.cadence.refresh_poll:
            self._last_refresh_poll = now
            return True
        return False

    def clear_expired(self, now: datetime) -> None:
        if self._watch_until and now >= self._watch_until:
            self._watch_until = None


__all__ = ["CadencePolicy"]
