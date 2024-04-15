from datetime import timedelta
from time import monotonic_ns
from typing import Callable


class Timer[T]:
    _last_run: None | float
    _last_value: T

    def __init__(self, interval: timedelta | float):
        self._interval = (
            interval.total_seconds() if isinstance(interval, timedelta) else interval
        )
        self._last_run = None

    def run(self, fn: Callable[[], T]) -> "tuple[Timer[T], T]":
        now = monotonic_ns()
        if self._last_run is None or (now - self._last_run) >= (self._interval * 1e9):
            last_value = fn()
            timer = Timer[T](self._interval)
            timer._last_run = now
            timer._last_value = last_value
            return timer, last_value
        else:
            return self, self._last_value
