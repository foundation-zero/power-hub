from dataclasses import dataclass
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceState,
    ConnectionState,
    Port,
)
from energy_box_control.schedules import Schedule
from energy_box_control.time import ProcessTime
from energy_box_control.units import Watt, WattPerMeterSquared, Percentage, MeterSquared


@dataclass(frozen=True, eq=True)
class PVPanelState(ApplianceState):
    power: Watt


@dataclass(frozen=True, eq=True)
class PVPanel(Appliance[PVPanelState, None, Port]):
    global_irradiance_schedule: Schedule[WattPerMeterSquared]
    surface_area: MeterSquared
    efficiency: Percentage

    def simulate(
        self,
        inputs: dict[Port, ConnectionState],
        previous_state: PVPanelState,
        control: None,
        simulation_time: ProcessTime,
    ) -> tuple[PVPanelState, dict[Port, ConnectionState]]:
        return (
            PVPanelState(
                self.global_irradiance_schedule.at(simulation_time)
                * self.surface_area
                * self.efficiency
            ),
            {},
        )
