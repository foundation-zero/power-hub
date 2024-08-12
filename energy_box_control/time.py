from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import cached_property
from time import time_ns

from energy_box_control.units import Second


@dataclass
class ProcessTime:
    step_size: timedelta
    step: int
    start: datetime

    @cached_property
    def timestamp(self) -> datetime:

        return self.start + timedelta(
            seconds=self.step * self.step_size.total_seconds()
        )

    @cached_property
    def step_seconds(self) -> Second:
        return self.step_size.total_seconds()


def time_ms() -> int:
    return time_ns() // 1_000_000

def ms_to_datetime(ms: int):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
