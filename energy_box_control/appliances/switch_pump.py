from dataclasses import dataclass
from enum import Enum
from typing import Optional

from energy_box_control.appliances.base import (
    ThermalAppliance,
    ApplianceControl,
    ApplianceState,
    ThermalState,
    Port,
)
from energy_box_control.time import ProcessTime

from energy_box_control.units import Bar, LiterPerSecond, Watt

SwitchPumpAlarm = int  # CRE series alarm codes: https://drive.google.com/file/d/1I8lCpu8UkNt6YmGF5-MU4DgqCUPPA-BV/view?usp=drive_link
NO_ALARM = 0
DEFAULT_PRESSURE = 2.5


class SwitchPumpStatusBit(Enum):
    ON_OFF = 1 << 8


@dataclass(frozen=True, eq=True)
class SwitchPumpState(ApplianceState):
    pump_alarm: int = NO_ALARM
    pump_warning: int = NO_ALARM
    status: int = 0
    pressure: Bar = DEFAULT_PRESSURE


class SwitchPumpPort(Port):
    IN = "in"
    OUT = "out"


@dataclass(frozen=True, eq=True)
class SwitchPumpControl(ApplianceControl):
    on: bool


@dataclass(frozen=True, eq=True)
class SwitchPump(ThermalAppliance[SwitchPumpState, SwitchPumpControl, SwitchPumpPort]):
    flow: LiterPerSecond
    rated_power_consumption: Watt

    def simulate(
        self,
        inputs: dict[SwitchPumpPort, ThermalState],
        previous_state: SwitchPumpState,
        control: Optional[SwitchPumpControl],
        simulation_time: ProcessTime,
    ) -> tuple[SwitchPumpState, dict[SwitchPumpPort, ThermalState]]:
        input = inputs[SwitchPumpPort.IN]
        return SwitchPumpState(
            status=SwitchPumpStatusBit.ON_OFF.value if (control and control.on) else 0
        ), {
            SwitchPumpPort.OUT: ThermalState(
                self.flow if (control and control.on) else 0, input.temperature
            )
        }
