from dataclasses import dataclass
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceState,
    ConnectionState,
    Port,
)
from energy_box_control.schedules import Schedule
from energy_box_control.time import ProcessTime
from energy_box_control.units import (
    JoulePerLiterKelvin,
    MeterSquared,
    WattPerMeterSquared,
    Celsius,
)


@dataclass(frozen=True, eq=True)
class HeatPipesState(ApplianceState):
    mean_temperature: Celsius


class HeatPipesPort(Port):
    IN = "in"
    OUT = "out"


@dataclass(frozen=True, eq=True)
class HeatPipes(Appliance[HeatPipesState, None, HeatPipesPort]):
    optical_efficiency: float
    first_order_loss_coefficient: float
    second_order_loss_coefficient: float
    absorber_area: MeterSquared
    specific_heat_medium: JoulePerLiterKelvin
    global_irradiance_schedule: Schedule[WattPerMeterSquared]
    ambient_temperature_schedule: Schedule[Celsius]

    def simulate(
        self,
        inputs: dict[HeatPipesPort, ConnectionState],
        previous_state: HeatPipesState,
        control: None,
        simulation_time: ProcessTime,
    ) -> tuple[HeatPipesState, dict[HeatPipesPort, ConnectionState]]:

        input = inputs[HeatPipesPort.IN]

        dT = previous_state.mean_temperature - self.ambient_temperature_schedule.at(
            simulation_time
        )

        power = self.absorber_area * (
            self.global_irradiance_schedule.at(simulation_time)
            * self.optical_efficiency
            - self.first_order_loss_coefficient * dT
            - self.second_order_loss_coefficient * dT**2
        )

        temp_out = (
            input.temperature + power / (input.flow * self.specific_heat_medium)
            if input.flow > 0
            else input.temperature
        )

        new_state = HeatPipesState((temp_out + input.temperature) / 2)

        return new_state, {HeatPipesPort.OUT: ConnectionState(input.flow, temp_out)}
