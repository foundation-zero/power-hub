from dataclasses import dataclass
from energy_box_control.appliances.base import (
    ThermalAppliance,
    ThermalState,
    Port,
)
from energy_box_control.schedules import Schedule
from energy_box_control.time import ProcessTime
from energy_box_control.units import JoulePerLiterKelvin, Watt


class CoolingSinkPort(Port):
    INPUT = "input"
    OUTPUT = "output"


@dataclass(frozen=True, eq=True)
class CoolingSink(ThermalAppliance[None, None, CoolingSinkPort]):
    specific_heat_capacity: JoulePerLiterKelvin
    cooling_demand_schedule: Schedule[Watt]

    def simulate(
        self,
        inputs: dict[CoolingSinkPort, ThermalState],
        previous_state: None,
        control: None,
        simulation_time: ProcessTime,
    ) -> tuple[None, dict[CoolingSinkPort, ThermalState]]:

        output_temperature = (
            inputs[CoolingSinkPort.INPUT].temperature
            + (
                self.cooling_demand_schedule.at(simulation_time)
                / (inputs[CoolingSinkPort.INPUT].flow * self.specific_heat_capacity)
            )
            if inputs[CoolingSinkPort.INPUT].flow > 0
            else inputs[CoolingSinkPort.INPUT].temperature
        )

        return None, {
            CoolingSinkPort.OUTPUT: ThermalState(
                inputs[CoolingSinkPort.INPUT].flow, output_temperature
            )
        }
