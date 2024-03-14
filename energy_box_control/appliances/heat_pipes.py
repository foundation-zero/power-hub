from dataclasses import dataclass
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceState,
    ConnectionState,
    Port,
)


@dataclass(frozen=True, eq=True)
class HeatPipesState(ApplianceState):
    mean_temperature: float  # C
    ambient_temperature: float  # C
    global_irradiance: float  # W/m2


class HeatPipesPort(Port):
    IN = "in"
    OUT = "out"


@dataclass(frozen=True, eq=True)
class HeatPipes(Appliance[HeatPipesState, None, HeatPipesPort]):
    optical_efficiency: float  #
    first_order_loss_coefficient: float  # W/m2K
    second_order_loss_coefficient: float  #  W/m2K2
    absorber_area: float  # m2
    specific_heat_medium: float  # J/lK

    def simulate(
        self,
        inputs: dict[HeatPipesPort, ConnectionState],
        previous_state: HeatPipesState,
        control: None,
    ) -> tuple[HeatPipesState, dict[HeatPipesPort, ConnectionState]]:
        input = inputs[HeatPipesPort.IN]

        dT = previous_state.mean_temperature - previous_state.ambient_temperature

        efficiency = (
            self.optical_efficiency
            - (
                self.first_order_loss_coefficient * dT
                + self.second_order_loss_coefficient * dT**2
            )
            / previous_state.global_irradiance
        )

        power = previous_state.global_irradiance * efficiency / 100

        temp_out = input.temperature + power / (input.flow * self.specific_heat_medium)

        new_state = HeatPipesState(
            (temp_out + input.temperature) / 2,
            previous_state.ambient_temperature,
            previous_state.global_irradiance,
        )

        return new_state, {HeatPipesPort.OUT: ConnectionState(input.flow, temp_out)}
