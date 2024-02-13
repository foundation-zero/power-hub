from dataclasses import dataclass
from abc import abstractmethod
from typing import TypeVar

from energy_box_control.control import Control, Sensors


@dataclass
class ApplianceState:
    inputs: "list[ConnectionState]"
    outputs: "list[ConnectionState]"


TState = TypeVar("TState", bound="ApplianceState")


@dataclass
class Appliance[TState]:

    @abstractmethod
    def state(self, network_state: "NetworkState") -> ApplianceState: ...

    @abstractmethod
    def simulate(
        self,
        inputs: "list[ConnectionState]",
        previous_state: TState,
        control: Control,
    ) -> TState: ...


@dataclass
class SourceState(ApplianceState):
    pass


@dataclass
class Source(Appliance[SourceState]):
    flow: float
    temp: float

    def state(self, network_state: "NetworkState") -> SourceState:
        return network_state.source_state

    def simulate(
        self,
        inputs: "list[ConnectionState]",
        previous_state: SourceState,
        control: Control,
    ) -> SourceState:
        return SourceState(inputs=[], outputs=[ConnectionState(self.flow, self.temp)])


@dataclass
class NetworkState:
    source_state: SourceState
    boiler_state: "BoilerState"

    def sensors(self) -> Sensors:
        return Sensors(self.boiler_state.temperature)


@dataclass
class ConnectionState:
    flow: float
    temperature: float


@dataclass
class BoilerState(ApplianceState):
    temperature: float


@dataclass
class Boiler(Appliance[BoilerState]):
    heat_capacity: float  # TODO: split into volume & specific heat capacity
    heater_power: float  # TODO: power going into water. Define efficiency later
    heat_loss: float
    specific_heat_capacity_input: float  # J / l K #TODO: this should probably go into Connection or ConnectionState (as it varies with temp), and be in J / kg K

    # TODO: make temp dependent
    # heat_capacity_pipefluid = 3790  # J / (kg K) at 20C
    # density_pipefluid = 1.009  # kg / l at 20C
    # heat_capacity_water = 4184  # J / (kg K) at 20C
    # density_water = 0.997  # kg / l at 20C

    def state(self, network_state: NetworkState) -> BoilerState:
        return network_state.boiler_state

    def simulate(
        self,
        inputs: list[ConnectionState],
        previous_state: BoilerState,
        control: Control,
    ) -> BoilerState:

        (input,) = inputs

        # assuming a perfect heat exchange, reaching thermal equilibrium in every time step #TODO: properly simulate heat exchange, which would require transfer coefficient or something similar
        element_heat = self.heater_power * control.heater_on
        boiler_heat = self.heat_capacity * previous_state.temperature
        input_heat = input.flow * self.specific_heat_capacity_input * input.temperature

        equilibrium_temperature = (
            element_heat + boiler_heat + input_heat - self.heat_loss
        ) / (self.heat_capacity + input.flow * self.specific_heat_capacity_input)

        return BoilerState(
            inputs=inputs,
            temperature=equilibrium_temperature,
            outputs=[ConnectionState(input.flow, equilibrium_temperature)],
        )


@dataclass
class Network:
    source: Source
    boiler: Boiler

    def simulate(self, previous_state: NetworkState, control: Control) -> NetworkState:
        source_state = self.source.state(previous_state)
        new_source_state = self.source.simulate([], source_state, control)
        boiler_state = self.boiler.state(previous_state)
        new_boiler_state = self.boiler.simulate(
            new_source_state.outputs, boiler_state, control
        )

        return NetworkState(
            source_state=new_source_state, boiler_state=new_boiler_state
        )
