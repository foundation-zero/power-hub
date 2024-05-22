from dataclasses import dataclass
from energy_box_control.appliances.base import (
    ThermalAppliance,
    ApplianceState,
    ThermalState,
    Port,
)
from energy_box_control.time import ProcessTime
from energy_box_control.units import JoulePerLiterKelvin


class HeatExchangerPort(Port):
    A_IN = "a_in"
    A_OUT = "a_out"
    B_IN = "b_in"
    B_OUT = "b_out"


@dataclass(frozen=True, eq=True)
class HeatExchanger(ThermalAppliance[ApplianceState, None, HeatExchangerPort]):
    specific_heat_capacity_A: JoulePerLiterKelvin
    specific_heat_capacity_B: JoulePerLiterKelvin

    # assuming a perfect heat exchange, reaching thermal equilibrium in every time step
    def simulate(
        self,
        inputs: dict[HeatExchangerPort, ThermalState],
        previous_state: ApplianceState,
        control: None,
        simulation_time: ProcessTime,
    ) -> tuple[ApplianceState, dict[HeatExchangerPort, ThermalState]]:

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

        if (
            inputs[HeatExchangerPort.A_IN].flow == 0
            or inputs[HeatExchangerPort.B_IN].flow == 0
        ):
            return ApplianceState(), {
                HeatExchangerPort.A_OUT: ThermalState(
                    inputs[HeatExchangerPort.A_IN].flow,
                    inputs[HeatExchangerPort.A_IN].temperature,
                ),
                HeatExchangerPort.B_OUT: ThermalState(
                    inputs[HeatExchangerPort.B_IN].flow,
                    inputs[HeatExchangerPort.B_IN].temperature,
                ),
            }

        equilibrium_temperature = (heat_A + heat_B) / (
            inputs[HeatExchangerPort.A_IN].flow * self.specific_heat_capacity_A
            + inputs[HeatExchangerPort.B_IN].flow * self.specific_heat_capacity_B
        )

        return ApplianceState(), {
            HeatExchangerPort.A_OUT: ThermalState(
                inputs[HeatExchangerPort.A_IN].flow,
                equilibrium_temperature,
            ),
            HeatExchangerPort.B_OUT: ThermalState(
                inputs[HeatExchangerPort.B_IN].flow,
                equilibrium_temperature,
            ),
        }
