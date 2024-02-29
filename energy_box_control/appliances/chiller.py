from dataclasses import dataclass

from energy_box_control.appliances.base import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    ConnectionState,
    Port,
)


@dataclass(frozen=True, eq=True)
class ChillerState(ApplianceState):
    pass


class ChillerPort(Port):
    CHILLED_IN = "CHILLED_IN"
    CHILLED_OUT = "CHILLED_OUT"
    COOLING_IN = "COOLING_IN"
    COOLING_OUT = "COOLING_OUT"


@dataclass(frozen=True, eq=True)
class ChillerControl(ApplianceControl):
    pass


@dataclass(frozen=True, eq=True)
class Chiller(Appliance[ChillerState, ChillerControl, ChillerPort]):
    cooling_capacity: float
    specific_heat_capacity_chilled: float  # J / l K
    specific_heat_capacity_cooling: float  # J / l K

    def simulate(
        self,
        inputs: dict[ChillerPort, ConnectionState],
        previous_state: ChillerState,
        control: ChillerControl,
    ) -> tuple[ChillerState, dict[ChillerPort, ConnectionState]]:

        chilled_out_temp = inputs[
            ChillerPort.CHILLED_IN
        ].temperature - self.cooling_capacity / (
            self.specific_heat_capacity_chilled * inputs[ChillerPort.CHILLED_IN].flow
        )
        cooling_out_temp = inputs[
            ChillerPort.COOLING_IN
        ].temperature + self.cooling_capacity / (
            self.specific_heat_capacity_cooling * inputs[ChillerPort.COOLING_IN].flow
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
