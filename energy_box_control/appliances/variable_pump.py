from dataclasses import dataclass
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    ConnectionState,
    Port,
)


@dataclass(frozen=True, eq=True)
class VariablePumpState(ApplianceState):
    pass


class VariablePumpPort(Port):
    IN = "IN"
    OUT = "OUT"


@dataclass(frozen=True, eq=True)
class VariablePumpControl(ApplianceControl):
    on: bool
    requested_pressure: float


@dataclass(frozen=True, eq=True)
class VariablePump(Appliance[VariablePumpState, VariablePumpControl, VariablePumpPort]):
    min_pressure: float
    max_pressure: float
    min_flow: float
    max_flow: float

    def simulate(
        self,
        inputs: dict[VariablePumpPort, ConnectionState],
        previous_state: VariablePumpState,
        control: VariablePumpControl,
    ) -> tuple[VariablePumpState, dict[VariablePumpPort, ConnectionState]]:
        input = inputs[VariablePumpPort.IN]

        if not control.on:
            return VariablePumpState(), {
                VariablePumpPort.OUT: ConnectionState(0, input.temperature)
            }

        pressure = max(
            min(control.requested_pressure, self.max_pressure), self.min_pressure
        )
        ratio = (pressure - self.min_pressure) / (self.max_pressure - self.min_pressure)

        flow = self.min_flow + (self.max_flow - self.min_flow) * ratio

        return VariablePumpState(), {
            VariablePumpPort.OUT: ConnectionState(flow, input.temperature)
        }
