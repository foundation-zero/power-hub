from dataclasses import dataclass
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceState,
    ConnectionState,
    Port,
)
from energy_box_control.schedules import Schedule
from energy_box_control.time import ProcessTime
from energy_box_control.units import Celsius, Liter


@dataclass(frozen=True, eq=True)
class WaterDemandState(ApplianceState):
    pass


class WaterDemandPort(Port):
    DEMAND_OUT = "demand_out"
    GREY_WATER_OUT = "grey_water_out"


@dataclass(frozen=True, eq=True)
class WaterDemand(Appliance[WaterDemandState, None, WaterDemandPort]):
    water_demand_flow_schedule: Schedule[Liter]
    water_demand_temperature_schedule: Schedule[Celsius]

    def simulate(
        self,
        inputs: dict[WaterDemandPort, ConnectionState],
        previous_state: WaterDemandState,
        control: None,
        simulation_time: ProcessTime,
    ) -> tuple[WaterDemandState, dict[WaterDemandPort, ConnectionState]]:

        return WaterDemandState(), {
            WaterDemandPort.DEMAND_OUT: ConnectionState(
                self.water_demand_flow_schedule.at(simulation_time),
                self.water_demand_temperature_schedule.at(simulation_time),
            ),
            WaterDemandPort.GREY_WATER_OUT: ConnectionState(
                self.water_demand_flow_schedule.at(simulation_time),
                self.water_demand_temperature_schedule.at(simulation_time),
            ),
        }
