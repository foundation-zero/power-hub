from dataclasses import dataclass
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceState,
    ConnectionState,
    JoulesPerLiterKelvin,
    Port,
    Seconds,
)


class HeatExchangerPort(Port):
    A_IN = "a_in"
    A_OUT = "a_out"
    B_IN = "b_in"
    B_OUT = "b_out"


@dataclass(frozen=True, eq=True)
class HeatExchanger(Appliance[ApplianceState, None, HeatExchangerPort]):
    specific_heat_capacity_A: JoulesPerLiterKelvin
    specific_heat_capacity_B: JoulesPerLiterKelvin

    # assuming a perfect heat exchange, reaching thermal equilibrium in every time step
    def simulate(
        self,
        inputs: dict[HeatExchangerPort, ConnectionState],
        previous_state: ApplianceState,
        control: None,
        step_size: Seconds,
    ) -> tuple[ApplianceState, dict[HeatExchangerPort, ConnectionState]]:

        heat_A = (
            inputs[HeatExchangerPort.A_IN].flow
            * step_size
            * inputs[HeatExchangerPort.A_IN].temperature
            * self.specific_heat_capacity_A
        )
        heat_B = (
            inputs[HeatExchangerPort.B_IN].flow
            * step_size
            * inputs[HeatExchangerPort.B_IN].temperature
            * self.specific_heat_capacity_B
        )

        equilibrium_temperature = (heat_A + heat_B) / (
            inputs[HeatExchangerPort.A_IN].flow
            * step_size
            * self.specific_heat_capacity_A
            + inputs[HeatExchangerPort.B_IN].flow
            * step_size
            * self.specific_heat_capacity_B
        )

        return ApplianceState(), {
            HeatExchangerPort.A_OUT: ConnectionState(
                inputs[HeatExchangerPort.A_IN].flow, equilibrium_temperature
            ),
            HeatExchangerPort.B_OUT: ConnectionState(
                inputs[HeatExchangerPort.B_IN].flow, equilibrium_temperature
            ),
        }
