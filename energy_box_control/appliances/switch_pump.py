from dataclasses import dataclass

from energy_box_control.appliances.base import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    ConnectionState,
    Port,
)


@dataclass(frozen=True, eq=True)
class SwitchPumpState(ApplianceState):
    pass


class SwitchPumpPort(Port):
    IN = "IN"
    OUT = "OUT"


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
    ) -> tuple[SwitchPumpState, dict[SwitchPumpPort, ConnectionState]]:
        input = inputs[SwitchPumpPort.IN]
        return SwitchPumpState(), {
            SwitchPumpPort.OUT: ConnectionState(
                self.flow if control.on else 0, input.temperature
            )
        }
