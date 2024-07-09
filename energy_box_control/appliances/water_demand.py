from dataclasses import dataclass
from energy_box_control.appliances.base import (
    WaterAppliance,
    ApplianceState,
    WaterState,
    Port,
)
from energy_box_control.schedules import Schedule
from energy_box_control.time import ProcessTime
from energy_box_control.units import LiterPerSecond


@dataclass(frozen=True, eq=True)
class WaterDemandState(ApplianceState):
    pass


class WaterDemandPort(Port):
    OUT = "out"


@dataclass(frozen=True, eq=True)
class WaterDemand(WaterAppliance[WaterDemandState, None, WaterDemandPort]):
    water_demand_flow_schedule: Schedule[LiterPerSecond]

    def simulate(
        self,
        inputs: dict[WaterDemandPort, WaterState],
        previous_state: WaterDemandState,
        control: None,
        simulation_time: ProcessTime,
    ) -> tuple[WaterDemandState, dict[WaterDemandPort, WaterState]]:

        return WaterDemandState(), {
            WaterDemandPort.OUT: WaterState(
                self.water_demand_flow_schedule.at(simulation_time),
            )
        }
