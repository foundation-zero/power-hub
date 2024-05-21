from dataclasses import dataclass
from energy_box_control.appliances.base import (
    ThermalAppliance,
    ApplianceState,
    ThermalState,
    Port,
)
from energy_box_control.schedules import Schedule
from energy_box_control.time import ProcessTime
from energy_box_control.units import Watt, WattPerMeterSquared, MeterSquared


@dataclass(frozen=True, eq=True)
class PVPanelState(ApplianceState):
    power: Watt


@dataclass(frozen=True, eq=True)
class PVPanel(ThermalAppliance[PVPanelState, None, Port]):
    global_irradiance_schedule: Schedule[WattPerMeterSquared]
    surface_area: MeterSquared
    efficiency: float

    def simulate(
        self,
        inputs: dict[Port, ThermalState],
        previous_state: PVPanelState,
        control: None,
        simulation_time: ProcessTime,
    ) -> tuple[PVPanelState, dict[Port, ThermalState]]:
        return (
            PVPanelState(
                self.global_irradiance_schedule.at(simulation_time)
                * self.surface_area
                * self.efficiency
            ),
            {},
        )
