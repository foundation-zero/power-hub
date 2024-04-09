from dataclasses import dataclass
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceState,
    Celsius,
    ConnectionState,
    JoulesPerLiterKelvin,
    MetersSquared,
    Port,
    Seconds,
    WattsPerMeterSquared,
)


@dataclass(frozen=True, eq=True)
class HeatPipesState(ApplianceState):
    mean_temperature: Celsius
    ambient_temperature: Celsius
    global_irradiance: WattsPerMeterSquared


class HeatPipesPort(Port):
    IN = "in"
    OUT = "out"


@dataclass(frozen=True, eq=True)
class HeatPipes(Appliance[HeatPipesState, None, HeatPipesPort]):
    optical_efficiency: float
    first_order_loss_coefficient: float
    second_order_loss_coefficient: float
    absorber_area: MetersSquared
    specific_heat_medium: JoulesPerLiterKelvin

    def simulate(
        self,
        inputs: dict[HeatPipesPort, ConnectionState],
        previous_state: HeatPipesState,
        control: None,
        step_size: Seconds,
    ) -> tuple[HeatPipesState, dict[HeatPipesPort, ConnectionState]]:

        input = inputs[HeatPipesPort.IN]

        dT = previous_state.mean_temperature - previous_state.ambient_temperature

        power = self.absorber_area * (
            previous_state.global_irradiance * self.optical_efficiency
            - self.first_order_loss_coefficient * dT
            - self.second_order_loss_coefficient * dT**2
        )

        temp_out = (
            input.temperature + power / (input.flow * self.specific_heat_medium)
            if input.flow > 0
            else input.temperature
        )

        new_state = HeatPipesState(
            (temp_out + input.temperature) / 2,
            previous_state.ambient_temperature,
            previous_state.global_irradiance,
        )

        return new_state, {HeatPipesPort.OUT: ConnectionState(input.flow, temp_out)}
