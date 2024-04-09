from dataclasses import dataclass
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    ConnectionState,
    Port,
    Seconds,
)


@dataclass(frozen=True, eq=True)
class ValveState(ApplianceState):
    position: float


@dataclass(frozen=True, eq=True)
class ValveControl(ApplianceControl):
    position: float


class ValvePort(Port):
    A = "a"
    B = "b"
    AB = "ab"


@dataclass(eq=True, frozen=True)
class Valve(Appliance[ValveState, ValveControl, ValvePort]):

    def simulate(
        self,
        inputs: dict[ValvePort, ConnectionState],
        previous_state: ValveState,
        control: ValveControl | None,
        step_size: Seconds,
    ) -> tuple[ValveState, dict[ValvePort, ConnectionState]]:

        input = inputs[ValvePort.AB]
        position = control.position if control else previous_state.position

        return ValveState(
            position,
        ), {
            ValvePort.A: ConnectionState(
                (1 - position) * input.flow, input.temperature
            ),
            ValvePort.B: ConnectionState(position * input.flow, input.temperature),
        }


def dummy_bypass_valve_temperature_control(
    position: float,
    setpoint_temperature: float,
    sensor_temperature: float,
    reversed: bool = False,
) -> float:

    # reversed means that increasing position lowers the temperature
    if sensor_temperature < setpoint_temperature:
        return min(position + 0.1, 1) if not reversed else max(position - 0.1, 0)
    elif sensor_temperature > setpoint_temperature:
        return max(position - 0.1, 0) if not reversed else min(position + 0.1, 1)
    else:
        return position
