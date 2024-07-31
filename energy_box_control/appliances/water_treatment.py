from dataclasses import dataclass
from energy_box_control.appliances.base import (
    ApplianceControl,
    ApplianceState,
    Port,
    ThermalAppliance,
    ThermalState,
)
from energy_box_control.schedules import Schedule
from energy_box_control.time import ProcessTime
from energy_box_control.units import Celsius, LiterPerSecond


@dataclass(frozen=True, eq=True)
class WaterTreatmentState(ApplianceState):
    on: bool


@dataclass(frozen=True, eq=True)
class WaterTreatmentControl(ApplianceControl):
    on: bool


class WaterTreatmentPort(Port):
    IN = "in"
    OUT = "out"


@dataclass(frozen=True, eq=True)
class WaterTreatment(
    ThermalAppliance[WaterTreatmentState, WaterTreatmentControl, WaterTreatmentPort]
):
    pump_flow: LiterPerSecond
    freshwater_temperature_schedule: Schedule[Celsius]

    def simulate(
        self,
        inputs: dict[WaterTreatmentPort, ThermalState],
        previous_state: WaterTreatmentState,
        control: WaterTreatmentControl,
        simulation_time: ProcessTime,
    ) -> tuple[WaterTreatmentState, dict[WaterTreatmentPort, ThermalState]]:

        on = control.on if control else previous_state.on

        return WaterTreatmentState(on), {
            WaterTreatmentPort.IN: ThermalState(
                self.pump_flow if on else 0,
                self.freshwater_temperature_schedule.at(simulation_time),
            ),
            WaterTreatmentPort.OUT: ThermalState(
                self.pump_flow if on else 0,
                self.freshwater_temperature_schedule.at(simulation_time),
            ),
        }
