from dataclasses import dataclass
from typing import Tuple

from energy_box_control.network import NetworkControl
from energy_box_control.simulation import BoilerControl
from energy_box_control.networks import BoilerNetwork, BoilerSensors


@dataclass
class ControlState:
    boiler_setpoint: float


def control(
    network: BoilerNetwork, control_state: ControlState, sensors: BoilerSensors
) -> Tuple[(ControlState, NetworkControl[BoilerNetwork])]:

    heater_on = sensors.boiler_temperature < control_state.boiler_setpoint

    return (
        control_state,
        network.control(network.boiler)
        .value(BoilerControl(heater_on=heater_on))
        .build(),
    )


if __name__ == "__main__":
    print("hello world")
