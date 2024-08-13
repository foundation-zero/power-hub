from dataclasses import dataclass
from typing import Optional

from energy_box_control.appliances.base import (
    ThermalAppliance,
    ApplianceControl,
    ApplianceState,
    ThermalState,
    Port,
)
from energy_box_control.time import ProcessTime

from energy_box_control.units import LiterPerSecond, Watt


Ratio = float


@dataclass(frozen=True, eq=True)
class FrequencyPumpState(ApplianceState):
    pass


class FrequencyPumpPort(Port):
    IN = "in"
    OUT = "out"


@dataclass(frozen=True, eq=True)
class FrequencyPumpControl(ApplianceControl):
    on: bool
    frequency_ratio: Ratio


@dataclass(frozen=True, eq=True)
class FrequencyPump(
    ThermalAppliance[FrequencyPumpState, FrequencyPumpControl, FrequencyPumpPort]
):
    max_flow: LiterPerSecond
    rated_power_consumption: Watt

    def simulate(
        self,
        inputs: dict[FrequencyPumpPort, ThermalState],
        previous_state: FrequencyPumpState,
        control: Optional[FrequencyPumpControl],
        simulation_time: ProcessTime,
    ) -> tuple[FrequencyPumpState, dict[FrequencyPumpPort, ThermalState]]:
        input = inputs[FrequencyPumpPort.IN]
        return FrequencyPumpState(), {
            FrequencyPumpPort.OUT: ThermalState(
                (
                    self.max_flow * control.frequency_ratio
                    if (control and control.on)
                    else 0
                ),
                input.temperature,
            )
        }
