from dataclasses import dataclass
from functools import cached_property

from energy_box_control.appliances.base import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    ConnectionState,
    Port,
    ProcessTime,
)
from energy_box_control.units import Celsius, JoulePerLiterKelvin, Liter, Watt


@dataclass(frozen=True, eq=True)
class BoilerState(ApplianceState):
    temperature: Celsius
    ambient_temperature: Celsius


class BoilerPort(Port):
    HEAT_EXCHANGE_IN = "heat_exchange_in"
    HEAT_EXCHANGE_OUT = "heat_exchange_out"
    FILL_IN = "fill_in"
    FILL_OUT = "fill_out"


@dataclass(frozen=True, eq=True)
class BoilerControl(ApplianceControl):
    heater_on: bool


@dataclass(frozen=True, eq=True)
class Boiler(Appliance[BoilerState, BoilerControl, BoilerPort]):
    volume: Liter
    heater_power: Watt
    heat_loss: Watt
    specific_heat_capacity_exchange: JoulePerLiterKelvin
    specific_heat_capacity_fill: JoulePerLiterKelvin

    @cached_property
    def tank_capacity(self):
        return self.volume * self.specific_heat_capacity_fill

    def simulate(
        self,
        inputs: dict[BoilerPort, ConnectionState],
        previous_state: BoilerState,
        control: BoilerControl,
        simulation_time: ProcessTime,
    ) -> tuple[BoilerState, dict[BoilerPort, ConnectionState]]:

        # assuming constant specific heat capacities with the temperature ranges
        # assuming a perfect heat exchange and mixing, reaching thermal equilibrium in every time step

        element_heat = (
            self.heater_power * simulation_time.step_seconds * control.heater_on
        )
        tank_heat = self.tank_capacity * previous_state.temperature

        if BoilerPort.HEAT_EXCHANGE_IN in inputs:
            exchange_capacity = (
                inputs[BoilerPort.HEAT_EXCHANGE_IN].flow
                * simulation_time.step_seconds
                * self.specific_heat_capacity_exchange
            )
            exchange_heat = (
                exchange_capacity * inputs[BoilerPort.HEAT_EXCHANGE_IN].temperature
            )
        else:
            exchange_capacity = 0
            exchange_heat = 0

        if BoilerPort.FILL_IN in inputs:
            fill_capacity = (
                inputs[BoilerPort.FILL_IN].flow
                * simulation_time.step_seconds
                * self.specific_heat_capacity_fill
            )
            fill_heat = fill_capacity * inputs[BoilerPort.FILL_IN].temperature

        else:
            fill_capacity = 0
            fill_heat = 0

        equilibrium_temperature = (
            element_heat
            + tank_heat
            + exchange_heat
            + fill_heat
            - (
                self.heat_loss
                * simulation_time.step_seconds
                * (previous_state.temperature > previous_state.ambient_temperature)
            )
        ) / (self.tank_capacity + exchange_capacity + fill_capacity)

        connection_states = {
            **(
                {
                    BoilerPort.HEAT_EXCHANGE_OUT: ConnectionState(
                        inputs[BoilerPort.HEAT_EXCHANGE_IN].flow,
                        equilibrium_temperature,
                    )
                }
                if BoilerPort.HEAT_EXCHANGE_IN in inputs
                else {}
            ),
            **(
                {
                    BoilerPort.FILL_OUT: ConnectionState(
                        inputs[BoilerPort.FILL_IN].flow, equilibrium_temperature
                    )
                }
                if BoilerPort.FILL_IN in inputs
                else {}
            ),
        }

        return (
            BoilerState(
                temperature=equilibrium_temperature,
                ambient_temperature=previous_state.ambient_temperature,
            ),
            connection_states,
        )
