from datetime import timedelta
from time import monotonic_ns
from typing import Callable


class Timer:
    _last_run: None | float

    def __init__(self, interval: timedelta | float):
        self._interval = (
            interval.total_seconds() if isinstance(interval, timedelta) else interval
        )
        self._last_run = None

    def run(self, fn: Callable[[], None]) -> "Timer":
        now = monotonic_ns()
        if self._last_run is None or (now - self._last_run) >= (self._interval * 1e9):
            fn()
            timer = Timer(self._interval)
            timer._last_run = now
            return timer
        else:
            return self
