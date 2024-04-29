from dataclasses import dataclass
from datetime import datetime, timedelta
from math import floor
from typing import Protocol

from energy_box_control.time import ProcessTime


class Schedule[T](Protocol):
    def at(self, time: ProcessTime) -> T: ...


@dataclass(frozen=True)
class ConstSchedule[T](Schedule[T]):
    value: T

    def at(self, time: ProcessTime) -> T:
        return self.value


@dataclass(frozen=True)
class PeriodicSchedule[T](Schedule[T]):
    schedule_start: datetime
    period: timedelta
    values: tuple[T, ...]

    def at(self, time: ProcessTime) -> T:
        return self.values[
            floor(
                (((time.timestamp - self.schedule_start) / self.period) % 1)
                * len(self.values)
            )
        ]


@dataclass(frozen=True)
class GivenSchedule[T](Schedule[T]):
    schedule_start: datetime
    schedule_end: datetime
    values: tuple[T, ...]

    def at(self, time: ProcessTime) -> T:
        if not self.schedule_start <= time.timestamp <= self.schedule_end:
            raise ValueError(
                f"Time {time.timestamp.strftime('%d/%m/%Y %H:%M:%S')} is outside of given schedule {self}"
            )
        return self.values[
            floor(
                (
                    (
                        (time.timestamp - self.schedule_start)
                        / (self.schedule_end - self.schedule_start)
                    )
                )
                * len(self.values)
            )
        ]
