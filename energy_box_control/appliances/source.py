from dataclasses import dataclass
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceState,
    ConnectionState,
    Port,
)
from energy_box_control.units import Celsius, LiterPerSecond, Second


@dataclass(frozen=True, eq=True)
class SourceState(ApplianceState):
    pass


class SourcePort(Port):
    OUTPUT = "output"


@dataclass(frozen=True, eq=True)
class Source(Appliance[SourceState, None, SourcePort]):
    flow: LiterPerSecond
    temp: Celsius

    def simulate(
        self,
        inputs: dict[SourcePort, "ConnectionState"],
        previous_state: SourceState,
        control: None,
        step_size: Second,
    ) -> tuple[SourceState, dict[SourcePort, "ConnectionState"]]:
        return SourceState(), {SourcePort.OUTPUT: ConnectionState(self.flow, self.temp)}
