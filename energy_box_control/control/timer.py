from datetime import datetime, timedelta
from typing import Callable

from energy_box_control.appliances.base import ProcessTime


class Timer[T]:
    _last_run: None | datetime
    _last_value: T

    def __init__(self, interval: timedelta):
        self._interval = interval
        self._last_run = None

    def run(self, fn: Callable[[], T], time: ProcessTime) -> "tuple[Timer[T], T]":
        if self._last_run is None or (time.timestamp - self._last_run) >= (
            self._interval
        ):
            last_value = fn()
            timer = Timer[T](self._interval)
            timer._last_run = time.timestamp
            timer._last_value = last_value
            return timer, last_value
        else:
            return self, self._last_value
