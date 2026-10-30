"""Limitador de intentos de autenticación en memoria.

Suficiente para una instancia. En despliegues con varias réplicas debe sustituirse
por Redis o el limitador del reverse proxy; se documenta en SECURITY.md.
"""

from __future__ import annotations

import threading
import time
from collections import deque


class SlidingWindowLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            bucket = self._events.setdefault(key, deque())
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self.max_requests:
                return False
            bucket.append(now)
            if len(self._events) > 20_000:
                self._prune(cutoff)
            return True

    def reset(self, key: str) -> None:
        with self._lock:
            self._events.pop(key, None)

    def _prune(self, cutoff: float) -> None:
        for item_key in list(self._events):
            bucket = self._events[item_key]
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if not bucket:
                self._events.pop(item_key, None)
