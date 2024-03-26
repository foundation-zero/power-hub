from dataclasses import dataclass
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
    volume: float  # l
    heater_power: float  # W
    heat_loss: float  # W
    specific_heat_capacity_exchange: float  # J / l K
    specific_heat_capacity_fill: float  # J / l K

    def simulate(
        self,
        inputs: dict[BoilerPort, ConnectionState],
        previous_state: BoilerState,
        control: BoilerControl,
    ) -> tuple[BoilerState, dict[BoilerPort, ConnectionState]]:

        # assuming constant specific heat capacities with the temperature ranges
        # assuming a perfect heat exchange and mixing, reaching thermal equilibrium in every time step
        tank_capacity = self.volume * self.specific_heat_capacity_fill

        element_heat = self.heater_power * control.heater_on
        tank_heat = tank_capacity * previous_state.temperature

        if BoilerPort.HEAT_EXCHANGE_IN in inputs:
            exchange_capacity = (
                inputs[BoilerPort.HEAT_EXCHANGE_IN].flow
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
                inputs[BoilerPort.FILL_IN].flow * self.specific_heat_capacity_fill
            )
            fill_heat = fill_capacity * inputs[BoilerPort.FILL_IN].temperature

        else:
            fill_capacity = 0
            fill_heat = 0

        equilibrium_temperature = (
            element_heat + tank_heat + exchange_heat + fill_heat - self.heat_loss
        ) / (tank_capacity + exchange_capacity + fill_capacity)

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
            ),
            connection_states,
        )
