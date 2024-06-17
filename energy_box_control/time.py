from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import cached_property

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
