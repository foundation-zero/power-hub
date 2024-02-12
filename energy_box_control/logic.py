from dataclasses import dataclass
from typing import Tuple
from energy_box_control.control import Control, Sensors

from energy_box_control.simulation import Network


@dataclass
class ControlState:
    boiler_setpoint: float


def control(
    network: Network, control_state: ControlState, sensors: Sensors
) -> Tuple[(ControlState, Control)]:

    heater_on = sensors.boiler_temperature < control_state.boiler_setpoint

    return (control_state, Control(heater_on=heater_on))


if __name__ == "__main__":
    print("hello world")
