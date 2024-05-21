from dataclasses import dataclass
from energy_box_control.appliances.base import (
    ThermalAppliance,
    ApplianceState,
    ThermalState,
    Port,
)
from energy_box_control.schedules import Schedule
from energy_box_control.time import ProcessTime
from energy_box_control.units import Celsius, LiterPerSecond


@dataclass(frozen=True, eq=True)
class SourceState(ApplianceState):
    pass


class SourcePort(Port):
    OUTPUT = "output"


@dataclass(frozen=True, eq=True)
class Source(ThermalAppliance[SourceState, None, SourcePort]):
    flow: LiterPerSecond
    temperature_schedule: Schedule[Celsius]

    def simulate(
        self,
        inputs: dict[SourcePort, "ThermalState"],
        previous_state: SourceState,
        control: None,
        simulation_time: ProcessTime,
    ) -> tuple[SourceState, dict[SourcePort, "ThermalState"]]:
        return SourceState(), {
            SourcePort.OUTPUT: ThermalState(
                self.flow, self.temperature_schedule.at(simulation_time)
            )
        }
