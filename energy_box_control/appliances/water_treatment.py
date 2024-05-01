from dataclasses import dataclass
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceState,
    ConnectionState,
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
class WaterTreatment(Appliance[WaterTreatmentState, None, WaterTreatmentPort]):
    efficiency: float

    def simulate(
        self,
        inputs: dict[WaterTreatmentPort, ConnectionState],
        previous_state: WaterTreatmentState,
        control: None,
        simulation_time: ProcessTime,
    ) -> tuple[WaterTreatmentState, dict[WaterTreatmentPort, ConnectionState]]:

        return WaterTreatmentState(), {
            WaterTreatmentPort.OUT: ConnectionState(
                inputs[WaterTreatmentPort.IN].flow * self.efficiency,
                inputs[WaterTreatmentPort.IN].temperature,
            )
        }
