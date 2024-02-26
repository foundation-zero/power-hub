from dataclasses import dataclass
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    ConnectionState,
    Port,
)


@dataclass(frozen=True, eq=True)
class SourceState(ApplianceState):
    pass


class SourcePort(Port):
    OUTPUT = "output"


@dataclass(frozen=True, eq=True)
class Source(Appliance[SourceState, ApplianceControl, SourcePort]):
    flow: float
    temp: float

    def simulate(
        self,
        inputs: dict[SourcePort, "ConnectionState"],
        previous_state: SourceState,
        control: ApplianceControl,
    ) -> tuple[SourceState, dict[SourcePort, "ConnectionState"]]:
        return SourceState(), {SourcePort.OUTPUT: ConnectionState(self.flow, self.temp)}
