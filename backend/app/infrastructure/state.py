from __future__ import annotations


class RuntimeState:
    def __init__(self, state) -> None:
        self._state = state

    def get(self, key: str, default=None):
        return getattr(self._state, key, default)

    def set(self, key: str, value) -> None:
        setattr(self._state, key, value)
