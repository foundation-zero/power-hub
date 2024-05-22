from dataclasses import dataclass
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceState,
    Port,
)
from energy_box_control.schedules import Schedule
from energy_box_control.time import ProcessTime
from energy_box_control.units import Watt, WattPerMeterSquared, MeterSquared


@dataclass(frozen=True, eq=True)
class PVPanelState(ApplianceState):
    power: Watt


@dataclass(frozen=True, eq=True)
class PVPanel(Appliance[PVPanelState, None, Port, dict[None, None], dict[None, None]]):
    global_irradiance_schedule: Schedule[WattPerMeterSquared]
    surface_area: MeterSquared
    efficiency: float

    def simulate(
        self,
        inputs: dict[None, None],
        previous_state: PVPanelState,
        control: None,
        simulation_time: ProcessTime,
    ) -> tuple[PVPanelState, dict[None, None]]:
        return (
            PVPanelState(
                self.global_irradiance_schedule.at(simulation_time)
                * self.surface_area
                * self.efficiency
            ),
            {},
        )
