from dataclasses import dataclass

from energy_box_control.appliances.base import (
    Appliance,
    ApplianceState,
    ConnectionState,
    JoulesPerLiterKelvin,
    Port,
    Seconds,
    Watts,
)


@dataclass(frozen=True, eq=True)
class ChillerState(ApplianceState):
    pass


class ChillerPort(Port):
    CHILLED_IN = "chilled_in"
    CHILLED_OUT = "chilled_out"
    COOLING_IN = "cooling_in"
    COOLING_OUT = "cooling_out"


@dataclass(frozen=True, eq=True)
class Chiller(Appliance[ChillerState, None, ChillerPort]):
    cooling_capacity: Watts
    specific_heat_capacity_chilled: JoulesPerLiterKelvin
    specific_heat_capacity_cooling: JoulesPerLiterKelvin

    def simulate(
        self,
        inputs: dict[ChillerPort, ConnectionState],
        previous_state: ChillerState,
        control: None,
        step_size: Seconds,
    ) -> tuple[ChillerState, dict[ChillerPort, ConnectionState]]:

        chilled_out_temp = (
            inputs[ChillerPort.CHILLED_IN].temperature
            - self.cooling_capacity
            / (
                self.specific_heat_capacity_chilled
                * inputs[ChillerPort.CHILLED_IN].flow
                * step_size
            )
            if inputs[ChillerPort.CHILLED_IN].flow > 0
            else inputs[ChillerPort.CHILLED_IN].temperature
        )

        cooling_out_temp = (
            inputs[ChillerPort.COOLING_IN].temperature
            + self.cooling_capacity
            / (
                self.specific_heat_capacity_cooling
                * inputs[ChillerPort.COOLING_IN].flow
                * step_size
            )
            if inputs[ChillerPort.COOLING_IN].flow > 0
            else inputs[ChillerPort.COOLING_IN].temperature
        )

        return (
            ChillerState(),
            {
                ChillerPort.CHILLED_OUT: ConnectionState(
                    inputs[ChillerPort.CHILLED_IN].flow * step_size, chilled_out_temp
                ),
                ChillerPort.COOLING_OUT: ConnectionState(
                    inputs[ChillerPort.COOLING_IN].flow * step_size, cooling_out_temp
                ),
            },
        )
