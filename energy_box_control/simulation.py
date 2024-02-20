from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Tuple


@dataclass(frozen=True, eq=True)
class ApplianceState:
    pass


@dataclass(frozen=True, eq=True)
class ApplianceControl:
    pass


@dataclass(frozen=True, eq=True)
class Appliance[TState: ApplianceState, TControl: ApplianceControl, TPort: "Port"]:
    @abstractmethod
    def simulate(
        self,
        inputs: dict[TPort, "ConnectionState"],
        previous_state: TState,
        control: TControl,
    ) -> Tuple[TState, dict[TPort, "ConnectionState"]]: ...


@dataclass(frozen=True, eq=True)
class SourceState(ApplianceState):
    pass


class Port(Enum):
    pass


class SourcePort(Port):
    OUTPUT = "output"


@dataclass(frozen=True, eq=True)
class Source(Appliance[SourceState, ApplianceControl, SourcePort]):
    flow: float
    temp: float

    def simulate(
        self,
        inputs: dict[SourcePort, "ConnectionState"],
        previous_state: SourceState,
        control: ApplianceControl,
    ) -> Tuple[SourceState, dict[SourcePort, "ConnectionState"]]:
        return SourceState(), {SourcePort.OUTPUT: ConnectionState(self.flow, self.temp)}


@dataclass(frozen=True, eq=True)
class ConnectionState:
    flow: float
    temperature: float


@dataclass(frozen=True, eq=True)
class BoilerState(ApplianceState):
    temperature: float


class BoilerPort(Port):
    HEAT_EXCHANGE_IN = "HEAT_EXCHANGE_IN"
    HEAT_EXCHANGE_OUT = "HEAT_EXCHANGE_OUT"


@dataclass(frozen=True, eq=True)
class BoilerControl(ApplianceControl):
    heater_on: bool


@dataclass(frozen=True, eq=True)
class Boiler(Appliance[BoilerState, BoilerControl, BoilerPort]):
    heat_capacity: float  # TODO: split into volume & specific heat capacity
    heater_power: float  # TODO: power going into water. Define efficiency later
    heat_loss: float
    specific_heat_capacity_input: float  # J / l K #TODO: this should probably go into Connection or ConnectionState (as it varies with temp), and be in J / kg K

    # TODO: make temp dependent
    # heat_capacity_pipefluid = 3790  # J / (kg K) at 20C
    # density_pipefluid = 1.009  # kg / l at 20C
    # heat_capacity_water = 4184  # J / (kg K) at 20C
    # density_water = 0.997  # kg / l at 20C

    def simulate(
        self,
        inputs: dict[BoilerPort, ConnectionState],
        previous_state: BoilerState,
        control: BoilerControl,
    ) -> Tuple[BoilerState, dict[BoilerPort, ConnectionState]]:

        input = inputs[BoilerPort.HEAT_EXCHANGE_IN]

        # assuming a perfect heat exchange, reaching thermal equilibrium in every time step #TODO: properly simulate heat exchange, which would require transfer coefficient or something similar
        element_heat = self.heater_power * control.heater_on
        boiler_heat = self.heat_capacity * previous_state.temperature
        input_heat = input.flow * self.specific_heat_capacity_input * input.temperature

        equilibrium_temperature = (
            element_heat + boiler_heat + input_heat - self.heat_loss
        ) / (self.heat_capacity + input.flow * self.specific_heat_capacity_input)

        return BoilerState(
            temperature=equilibrium_temperature,
        ), {
            BoilerPort.HEAT_EXCHANGE_OUT: ConnectionState(
                input.flow, equilibrium_temperature
            )
        }


@dataclass(frozen=True, eq=True)
class ValveState(ApplianceState):
    position: float


class ValvePort(Port):
    A = "a"
    B = "b"
    AB = "ab"


@dataclass(eq=True, frozen=True)
class Valve(Appliance[ValveState, ApplianceControl, ValvePort]):

    def simulate(
        self,
        inputs: dict[ValvePort, ConnectionState],
        previous_state: ValveState,
        control: ApplianceControl,
    ) -> Tuple[ValveState, dict[ValvePort, ConnectionState]]:

        input = inputs[ValvePort.AB]

        return ValveState(
            previous_state.position,
        ), {
            ValvePort.A: ConnectionState(
                (1 - previous_state.position) * input.flow, input.temperature
            ),
            ValvePort.B: ConnectionState(
                previous_state.position * input.flow, input.temperature
            ),
        }
