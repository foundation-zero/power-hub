from dataclasses import dataclass
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceState,
    ConnectionState,
    Port,
    SimulationTime,
)
from energy_box_control.units import JoulePerLiterKelvin, Watt


class CoolingSinkPort(Port):
    INPUT = "input"
    OUTPUT = "output"


@dataclass(frozen=True, eq=True)
class CoolingSink(Appliance[ApplianceState, None, CoolingSinkPort]):
    power: Watt
    specific_heat_capacity: JoulePerLiterKelvin

    def simulate(
        self,
        inputs: dict[CoolingSinkPort, ConnectionState],
        previous_state: ApplianceState,
        control: None,
        simulation_time: SimulationTime,
    ) -> tuple[ApplianceState, dict[CoolingSinkPort, ConnectionState]]:

        output_temperature = (
            inputs[CoolingSinkPort.INPUT].temperature
            + (
                self.power
                / (inputs[CoolingSinkPort.INPUT].flow * self.specific_heat_capacity)
            )
            if inputs[CoolingSinkPort.INPUT].flow > 0
            else inputs[CoolingSinkPort.INPUT].temperature
        )

        return ApplianceState(), {
            CoolingSinkPort.OUTPUT: ConnectionState(
                inputs[CoolingSinkPort.INPUT].flow, output_temperature
            )
        }
