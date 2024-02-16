from dataclasses import dataclass
from typing import Self
from energy_box_control.network import Network, NetworkConnections, NetworkState
from energy_box_control.simulation import (
    Boiler,
    BoilerPort,
    BoilerState,
    Source,
    SourcePort,
    SourceState,
    Valve,
    ValvePort,
    ValveState,
)


@dataclass
class BoilerSensors:
    boiler_temperature: float


class BoilerNetwork(Network[BoilerSensors]):
    def __init__(self, source: Source, boiler: Boiler, boiler_state: BoilerState):
        self.source = source
        self.boiler = boiler
        self.boiler_state = boiler_state
        super().__init__()

    def initial_state(self) -> NetworkState[Self]:
        return (
            self.define_state(self.source)
            .value(SourceState())
            .define_state(self.boiler)
            .value(self.boiler_state)
            .build(self.connections())
        )

    def connections(self) -> NetworkConnections[Self]:
        return (
            self.connect(self.source)
            .at(SourcePort.OUTPUT)
            .to(self.boiler)
            .at(BoilerPort.HEAT_EXCHANGE_IN)
            .build()
        )

    def sensors(self, state: NetworkState[Self]) -> BoilerSensors:
        return BoilerSensors(state.appliance(self.boiler).get().temperature)


class BoilerValveNetwork(BoilerNetwork):
    def __init__(
        self,
        source: Source,
        boiler: Boiler,
        boiler_state: BoilerState,
        valve_state: ValveState,
    ):
        self.valve = Valve()
        self.valve_state = valve_state
        super().__init__(source, boiler, boiler_state)

    def initial_state(self) -> NetworkState[Self]:
        return (
            self.define_state(self.source)
            .value(SourceState())
            .define_state(self.valve)
            .value(self.valve_state)
            .define_state(self.boiler)
            .value(self.boiler_state)
            .build(self.connections())
        )

    def connections(self) -> NetworkConnections[Self]:
        return (
            self.connect(self.source)
            .at(SourcePort.OUTPUT)
            .to(self.valve)
            .at(ValvePort.AB)
            .connect(self.valve)
            .at(ValvePort.A)
            .to(self.boiler)
            .at(BoilerPort.HEAT_EXCHANGE_IN)
            .build()
        )
