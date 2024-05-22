from dataclasses import dataclass
from energy_box_control.appliances.base import (
    ThermalAppliance,
    ApplianceControl,
    ApplianceState,
    ThermalState,
    Port,
)
from energy_box_control.time import ProcessTime


@dataclass(frozen=True, eq=True)
class ValveState(ApplianceState):
    position: float


@dataclass(frozen=True, eq=True)
class ValveControl(ApplianceControl):
    position: float

    @staticmethod
    def a_position() -> float:
        return 0.0

    @staticmethod
    def b_position() -> float:
        return 1.0


class ValvePort(Port):
    A = "a"
    B = "b"
    AB = "ab"


@dataclass(eq=True, frozen=True)
class Valve(ThermalAppliance[ValveState, ValveControl, ValvePort]):

    def simulate(
        self,
        inputs: dict[ValvePort, ThermalState],
        previous_state: ValveState,
        control: ValveControl | None,
        simulation_time: ProcessTime,
    ) -> tuple[ValveState, dict[ValvePort, ThermalState]]:

        input = inputs[ValvePort.AB]
        position = control.position if control else previous_state.position

        return ValveState(
            position,
        ), {
            ValvePort.A: ThermalState((1 - position) * input.flow, input.temperature),
            ValvePort.B: ThermalState(position * input.flow, input.temperature),
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
