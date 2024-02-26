from dataclasses import dataclass
from typing import Tuple
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    ConnectionState,
    Port,
)


@dataclass(frozen=True, eq=True)
class BoilerState(ApplianceState):
    temperature: float


class BoilerPort(Port):
    HEAT_EXCHANGE_IN = "HEAT_EXCHANGE_IN"
    HEAT_EXCHANGE_OUT = "HEAT_EXCHANGE_OUT"
    FILL_IN = "FILL_IN"
    FILL_OUT = "FILL_OUT"

@dataclass(frozen=True, eq=True)
class BoilerControl(ApplianceControl):
    heater_on: bool


@dataclass(frozen=True, eq=True)
class Boiler(Appliance[BoilerState, BoilerControl, BoilerPort]):
    heat_capacity_tank: float
    heater_power: float
    heat_loss: float
    specific_heat_capacity_exchange: float  # J / l K
    specific_heat_capacity_fill: float # J / l K
    
    def simulate(
        self,
        inputs: dict[BoilerPort, ConnectionState],
        previous_state: BoilerState,
        control: BoilerControl,
    ) -> Tuple[BoilerState, dict[BoilerPort, ConnectionState]]:

        # assuming a perfect heat exchange, reaching thermal equilibrium in every time step
        element_heat = self.heater_power * control.heater_on
        tank_heat = self.heat_capacity_tank * previous_state.temperature
        exchange_heat = inputs[BoilerPort.HEAT_EXCHANGE_IN].flow * self.specific_heat_capacity_exchange * inputs[BoilerPort.HEAT_EXCHANGE_IN].temperature
        fill_heat = inputs[BoilerPort.FILL_IN].flow * self.specific_heat_capacity_fill * inputs[BoilerPort.FILL_IN].temperature

        equilibrium_temperature = (
            element_heat + tank_heat + exchange_heat + fill_heat - self.heat_loss
        ) / (self.heat_capacity_tank + inputs[BoilerPort.HEAT_EXCHANGE_IN].flow * self.specific_heat_capacity_exchange + inputs[BoilerPort.FILL_IN].flow * self.specific_heat_capacity_fill)

        return BoilerState(
            temperature=equilibrium_temperature,
        ), {
            BoilerPort.HEAT_EXCHANGE_OUT: ConnectionState(
                inputs[BoilerPort.HEAT_EXCHANGE_OUT].flow, equilibrium_temperature
            ),
            BoilerPort.FILL_OUT: ConnectionState(
                inputs[BoilerPort.FILL_OUT].flow, equilibrium_temperature
            )
        }
