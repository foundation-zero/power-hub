from dataclasses import dataclass

from energy_box_control.appliances.base import (
    ThermalAppliance,
    ApplianceControl,
    ApplianceState,
    ThermalState,
    Port,
)
from energy_box_control.time import ProcessTime

from energy_box_control.units import Bar, LiterPerSecond, Watt


@dataclass(frozen=True, eq=True)
class SwitchPumpState(ApplianceState):
    # CRE series alarm codes: https://drive.google.com/file/d/1I8lCpu8UkNt6YmGF5-MU4DgqCUPPA-BV/view?usp=drive_link
    pump_1_alarm: int = 0
    pump_2_alarm: int = 0
    pressure: Bar = 100


class SwitchPumpPort(Port):
    IN = "in"
    OUT = "out"


@dataclass(frozen=True, eq=True)
class SwitchPumpControl(ApplianceControl):
    on: bool


@dataclass(frozen=True, eq=True)
class SwitchPump(ThermalAppliance[SwitchPumpState, SwitchPumpControl, SwitchPumpPort]):
    flow: LiterPerSecond
    electrical_power: Watt

    def simulate(
        self,
        inputs: dict[SwitchPumpPort, ThermalState],
        previous_state: SwitchPumpState,
        control: SwitchPumpControl,
        simulation_time: ProcessTime,
    ) -> tuple[SwitchPumpState, dict[SwitchPumpPort, ThermalState]]:
        input = inputs[SwitchPumpPort.IN]
        return SwitchPumpState(), {
            SwitchPumpPort.OUT: ThermalState(
                self.flow if control.on else 0, input.temperature
            )
        }
