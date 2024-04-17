from dataclasses import dataclass

from energy_box_control.appliances.base import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    ConnectionState,
    Port,
    ProcessTime,
)
from energy_box_control.units import JoulePerLiterKelvin, Watt


@dataclass(frozen=True, eq=True)
class ChillerState(ApplianceState):
    pass


class ChillerPort(Port):
    CHILLED_IN = "chilled_in"
    CHILLED_OUT = "chilled_out"
    COOLING_IN = "cooling_in"
    COOLING_OUT = "cooling_out"


@dataclass(frozen=True, eq=True)
class ChillerControl(ApplianceControl):
    on: bool


@dataclass(frozen=True, eq=True)
class Chiller(Appliance[ChillerState, ChillerControl, ChillerPort]):
    cooling_capacity: Watt
    specific_heat_capacity_chilled: JoulePerLiterKelvin
    specific_heat_capacity_cooling: JoulePerLiterKelvin

    def simulate(
        self,
        inputs: dict[ChillerPort, ConnectionState],
        previous_state: ChillerState,
        control: ChillerControl,
        simulation_time: ProcessTime,
    ) -> tuple[ChillerState, dict[ChillerPort, ConnectionState]]:
        cooling_power = self.cooling_capacity if control.on else 0

        chilled_out_temp = (
            inputs[ChillerPort.CHILLED_IN].temperature
            - cooling_power
            / (
                self.specific_heat_capacity_chilled
                * inputs[ChillerPort.CHILLED_IN].flow
            )
            if inputs[ChillerPort.CHILLED_IN].flow > 0
            and inputs[ChillerPort.COOLING_IN].flow > 0
            else inputs[ChillerPort.CHILLED_IN].temperature
        )

        cooling_out_temp = (
            inputs[ChillerPort.COOLING_IN].temperature
            + cooling_power
            / (
                self.specific_heat_capacity_cooling
                * inputs[ChillerPort.COOLING_IN].flow
            )
            if inputs[ChillerPort.CHILLED_IN].flow > 0
            and inputs[ChillerPort.COOLING_IN].flow > 0
            else inputs[ChillerPort.COOLING_IN].temperature
        )

        return (
            ChillerState(),
            {
                ChillerPort.CHILLED_OUT: ConnectionState(
                    inputs[ChillerPort.CHILLED_IN].flow, chilled_out_temp
                ),
                ChillerPort.COOLING_OUT: ConnectionState(
                    inputs[ChillerPort.COOLING_IN].flow, cooling_out_temp
                ),
            },
        )
