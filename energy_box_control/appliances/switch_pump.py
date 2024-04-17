from dataclasses import dataclass

from energy_box_control.appliances.base import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    ConnectionState,
    Port,
)
from energy_box_control.time import ProcessTime


@dataclass(frozen=True, eq=True)
class SwitchPumpState(ApplianceState):
    pass


class SwitchPumpPort(Port):
    IN = "in"
    OUT = "out"


@dataclass(frozen=True, eq=True)
class SwitchPumpControl(ApplianceControl):
    on: bool


@dataclass(frozen=True, eq=True)
class SwitchPump(Appliance[SwitchPumpState, SwitchPumpControl, SwitchPumpPort]):
    flow: float

    def simulate(
        self,
        inputs: dict[SwitchPumpPort, ConnectionState],
        previous_state: SwitchPumpState,
        control: SwitchPumpControl,
        simulation_time: ProcessTime,
    ) -> tuple[SwitchPumpState, dict[SwitchPumpPort, ConnectionState]]:
        input = inputs[SwitchPumpPort.IN]
        return SwitchPumpState(), {
            SwitchPumpPort.OUT: ConnectionState(
                self.flow if control.on else 0, input.temperature
            )
        }
