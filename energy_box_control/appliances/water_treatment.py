from dataclasses import dataclass
from energy_box_control.appliances.base import (
    WaterAppliance,
    ApplianceState,
    WaterState,
    Port,
)
from energy_box_control.time import ProcessTime


@dataclass(frozen=True, eq=True)
class WaterTreatmentState(ApplianceState):
    pass


class WaterTreatmentPort(Port):
    IN = "in"
    OUT = "out"


@dataclass(frozen=True, eq=True)
class WaterTreatment(WaterAppliance[WaterTreatmentState, None, WaterTreatmentPort]):
    efficiency: float

    def simulate(
        self,
        inputs: dict[WaterTreatmentPort, WaterState],
        previous_state: WaterTreatmentState,
        control: None,
        simulation_time: ProcessTime,
    ) -> tuple[WaterTreatmentState, dict[WaterTreatmentPort, WaterState]]:

        return WaterTreatmentState(), {
            WaterTreatmentPort.OUT: WaterState(
                inputs[WaterTreatmentPort.IN].flow * self.efficiency,
            )
        }
