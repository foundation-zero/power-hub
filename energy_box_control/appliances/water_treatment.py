from dataclasses import dataclass
from energy_box_control.appliances.base import (
    ApplianceControl,
    WaterAppliance,
    ApplianceState,
    WaterState,
    Port,
)
from energy_box_control.time import ProcessTime
from energy_box_control.units import LiterPerSecond


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
class WaterTreatment(WaterAppliance[WaterTreatmentState, None, WaterTreatmentPort]):
    pump_flow: LiterPerSecond

    def simulate(
        self,
        inputs: dict[WaterTreatmentPort, WaterState],
        previous_state: WaterTreatmentState,
        control: WaterTreatmentControl | None,
        simulation_time: ProcessTime,
    ) -> tuple[WaterTreatmentState, dict[WaterTreatmentPort, WaterState]]:

        on = control.on if control else previous_state.on

        return WaterTreatmentState(on), {
            WaterTreatmentPort.IN: WaterState(self.pump_flow if on else 0),
            WaterTreatmentPort.OUT: WaterState(self.pump_flow if on else 0),
        }
