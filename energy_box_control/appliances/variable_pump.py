from dataclasses import dataclass
from energy_box_control.appliances.base import (
    ThermalAppliance,
    ApplianceControl,
    ApplianceState,
    ThermalState,
    Port,
)
from energy_box_control.time import ProcessTime
from energy_box_control.units import LiterPerSecond


@dataclass(frozen=True, eq=True)
class VariablePumpState(ApplianceState):
    pass


class VariablePumpPort(Port):
    IN = "in"
    OUT = "out"


@dataclass(frozen=True, eq=True)
class VariablePumpControl(ApplianceControl):
    on: bool
    requested_pressure: float


@dataclass(frozen=True, eq=True)
class VariablePump(
    ThermalAppliance[VariablePumpState, VariablePumpControl, VariablePumpPort]
):
    min_pressure: float
    max_pressure: float
    min_flow: LiterPerSecond
    max_flow: LiterPerSecond

    def simulate(
        self,
        inputs: dict[VariablePumpPort, ThermalState],
        previous_state: VariablePumpState,
        control: VariablePumpControl,
        simulation_time: ProcessTime,
    ) -> tuple[VariablePumpState, dict[VariablePumpPort, ThermalState]]:
        input = inputs[VariablePumpPort.IN]

        if not control.on:
            return VariablePumpState(), {
                VariablePumpPort.OUT: ThermalState(0, input.temperature)
            }

        pressure = max(
            min(control.requested_pressure, self.max_pressure), self.min_pressure
        )
        ratio = (pressure - self.min_pressure) / (self.max_pressure - self.min_pressure)

        flow = self.min_flow + (self.max_flow - self.min_flow) * ratio

        return VariablePumpState(), {
            VariablePumpPort.OUT: ThermalState(flow, input.temperature)
        }
