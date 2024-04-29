from dataclasses import dataclass
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceState,
    ConnectionState,
    Port,
)
from energy_box_control.schedules import Schedule
from energy_box_control.time import ProcessTime
from energy_box_control.units import WattPerMeterSquared, Percentage, MeterSquared


@dataclass(frozen=True, eq=True)
class PVPanelState(ApplianceState):
    produced_power: float


class PVPanelPort(Port):
    OUT = "out"
    IN = "in"


@dataclass(frozen=True, eq=True)
class PVPanel(Appliance[PVPanelState, None, PVPanelPort]):
    global_irradiance_schedule: Schedule[WattPerMeterSquared]
    surface_area: MeterSquared
    efficiency: Percentage

    def simulate(
        self,
        inputs: dict[PVPanelPort, ConnectionState],
        previous_state: PVPanelState,
        control: None,
        simulation_time: ProcessTime,
    ) -> tuple[PVPanelState, dict[PVPanelPort, ConnectionState]]:
        return PVPanelState(
            self.global_irradiance_schedule.at(simulation_time)
            * self.surface_area
            * self.efficiency
        ), {
            PVPanelPort.OUT: ConnectionState(
                inputs[PVPanelPort.IN].flow, inputs[PVPanelPort.IN].temperature
            )
        }
