from dataclasses import dataclass
from typing import Tuple
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    ConnectionState,
    Port,
)


class HeatExchangerPort(Port):
    A_IN = "A_IN"
    A_OUT = "A_OUT"
    B_IN = "B_IN"
    B_OUT = "B_OUT"


@dataclass(frozen=True, eq=True)
class HeatExchanger(Appliance[ApplianceState, ApplianceControl, HeatExchangerPort]):
    specific_heat_capacity_A: float  # TODO: make bus or connection property
    specific_heat_capacity_B: float  # TODO: make bus or connection property

    # assuming a perfect heat exchange, reaching thermal equilibrium in every time step #TODO: properly simulate heat exchange, which would require transfer coefficient or something similar
    def simulate(
        self,
        inputs: dict[HeatExchangerPort, ConnectionState],
        previous_state: ApplianceState,
        control: ApplianceControl,
    ) -> Tuple[ApplianceState, dict[HeatExchangerPort, ConnectionState]]:

        heat_A = (
            inputs[HeatExchangerPort.A_IN].flow
            * inputs[HeatExchangerPort.A_IN].temperature
            * self.specific_heat_capacity_A
        )
        heat_B = (
            inputs[HeatExchangerPort.B_IN].flow
            * inputs[HeatExchangerPort.B_IN].temperature
            * self.specific_heat_capacity_B
        )

        equilibrium_temperature = (heat_A + heat_B) / (
            inputs[HeatExchangerPort.A_IN].flow * self.specific_heat_capacity_A
            + inputs[HeatExchangerPort.B_IN].flow * self.specific_heat_capacity_B
        )

        return ApplianceState(), {
            HeatExchangerPort.A_IN: ConnectionState(
                inputs[HeatExchangerPort.A_IN].flow,
                inputs[HeatExchangerPort.A_IN].temperature,
            ),
            HeatExchangerPort.A_OUT: ConnectionState(
                inputs[HeatExchangerPort.A_IN].flow, equilibrium_temperature
            ),
            HeatExchangerPort.B_IN: ConnectionState(
                inputs[HeatExchangerPort.B_IN].flow,
                inputs[HeatExchangerPort.B_IN].temperature,
            ),
            HeatExchangerPort.B_OUT: ConnectionState(
                inputs[HeatExchangerPort.B_IN].flow, equilibrium_temperature
            ),
        }
