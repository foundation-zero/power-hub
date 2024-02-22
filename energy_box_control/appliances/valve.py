from dataclasses import dataclass
from typing import Tuple
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    ConnectionState,
    Port,
)


@dataclass(frozen=True, eq=True)
class ValveState(ApplianceState):
    position: float


class ValvePort(Port):
    A = "a"
    B = "b"
    AB = "ab"


@dataclass(eq=True, frozen=True)
class Valve(Appliance[ValveState, ApplianceControl, ValvePort]):

    def simulate(
        self,
        inputs: dict[ValvePort, ConnectionState],
        previous_state: ValveState,
        control: ApplianceControl,
    ) -> Tuple[ValveState, dict[ValvePort, ConnectionState]]:

        input = inputs[ValvePort.AB]

        return ValveState(
            previous_state.position,
        ), {
            ValvePort.A: ConnectionState(
                (1 - previous_state.position) * input.flow, input.temperature
            ),
            ValvePort.B: ConnectionState(
                previous_state.position * input.flow, input.temperature
            ),
        }
