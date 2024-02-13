from dataclasses import dataclass

from energy_box_control.control import Control, Sensors


@dataclass
class BoilerState:
    temperature: float


@dataclass
class State:
    boiler_state: BoilerState

    def sensors(self) -> Sensors:
        return Sensors(self.boiler_state.temperature)


@dataclass
class Boiler:
    heat_capacity: float
    heater_power: float

    def simulate(self, previous_state: State, control: Control) -> State:
        return State(
            boiler_state=BoilerState(
                temperature=previous_state.boiler_state.temperature
                + (self.heater_power * control.heater_on / self.heat_capacity)
            )
        )


@dataclass
class Network:
    boiler: Boiler


def simulate(network: Network, previous_state: State, control: Control) -> State:
    return network.boiler.simulate(previous_state, control)
