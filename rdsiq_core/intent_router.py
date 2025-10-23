"""Keyword-based intent routing for RDSIQ commands."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional


@dataclass(slots=True)
class Intent:
    name: str
    handler: Callable[[], None]
    description: str


class IntentRouter:
    def __init__(self) -> None:
        self._commands: Dict[str, Intent] = {}

    def register(self, phrase: str, intent: Intent) -> None:
        self._commands[phrase.lower()] = intent

    def route(self, text: str) -> Optional[Intent]:
        text = text.strip().lower()
        for key, intent in self._commands.items():
            if key in text:
                return intent
        return None


__all__ = ["IntentRouter", "Intent"]
