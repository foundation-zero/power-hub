from dataclasses import dataclass
from datetime import datetime, timedelta
from math import floor
from typing import Protocol

from energy_box_control.appliances.base import SimulationTime


class Schedule[T](Protocol):
    def at(self, simulation_time: SimulationTime) -> T: ...


@dataclass(frozen=True)
class ConstSchedule[T](Schedule[T]):
    value: T

    def at(self, simulation_time: SimulationTime) -> T:
        return self.value


@dataclass(frozen=True)
class PeriodicSchedule[T](Schedule[T]):
    schedule_start: datetime
    period: timedelta
    values: list[T]

    def at(self, simulation_time: SimulationTime) -> T:
        return self.values[
            floor(
                (((simulation_time.timestamp - self.schedule_start) / self.period) % 1)
                * len(self.values)
            )
        ]


@dataclass
class GivenSchedule[T](Schedule[T]):
    schedule_start: datetime
    schedule_end: datetime
    values: list[T]

    def at(self, simulation_time: SimulationTime) -> T:
        if not self.schedule_start < simulation_time.timestamp < self.schedule_end:
            raise ValueError(
                f"Time {simulation_time.timestamp.strftime('%d/%m/%Y %H:%M:%S')} is outside of given schedule"
            )
        return self.values[
            floor(
                (
                    (
                        (simulation_time.timestamp - self.schedule_start)
                        / (self.schedule_end - self.schedule_start)
                    )
                    % 1
                )
                * len(self.values)
            )
        ]
