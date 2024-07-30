from dataclasses import dataclass
from energy_box_control.appliances.base import (
    ThermalAppliance,
    ApplianceState,
    Port,
    ThermalState,
)
from energy_box_control.schedules import Schedule
from energy_box_control.time import ProcessTime
from energy_box_control.units import Celsius, LiterPerSecond


@dataclass(frozen=True, eq=True)
class WaterDemandState(ApplianceState):
    pass


class WaterDemandPort(Port):
    OUT = "out"


@dataclass(frozen=True, eq=True)
class WaterDemand(ThermalAppliance[WaterDemandState, None, WaterDemandPort]):
    water_demand_flow_schedule: Schedule[LiterPerSecond]
    freshwater_temperature_schedule: Schedule[Celsius]

    def simulate(
        self,
        inputs: dict[WaterDemandPort, ThermalState],
        previous_state: WaterDemandState,
        control: None,
        simulation_time: ProcessTime,
    ) -> tuple[WaterDemandState, dict[WaterDemandPort, ThermalState]]:

        return WaterDemandState(), {
            WaterDemandPort.OUT: ThermalState(
                self.water_demand_flow_schedule.at(simulation_time),
                self.freshwater_temperature_schedule.at(simulation_time),
            )
        }
