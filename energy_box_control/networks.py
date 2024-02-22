from dataclasses import dataclass
from typing import Self, Tuple
from energy_box_control.network import (
    ControlBuilder,
    Network,
    NetworkConnections,
    NetworkControl,
    NetworkState,
)
from energy_box_control.simulation import (
    Boiler,
    BoilerControl,
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


@dataclass
class ControlState:
    boiler_setpoint: float


class BoilerNetwork(Network[BoilerSensors]):
    def __init__(self, source: Source, boiler: Boiler, boiler_state: BoilerState):
        self.source = source
        self.boiler = boiler
        self.boiler_state = boiler_state
        super().__init__()

    def heater_off(self) -> NetworkControl[Self]:
        return self.control(self.boiler).value(BoilerControl(heater_on=False)).build()

    def heater_on(self) -> NetworkControl[Self]:
        return self.control(self.boiler).value(BoilerControl(heater_on=True)).build()

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

    def regulate(
        self, control_state: ControlState, sensors: BoilerSensors
    ) -> Tuple[(ControlState, NetworkControl[Self])]:
        heater_on = sensors.boiler_temperature < control_state.boiler_setpoint

        return (
            control_state,
            self.control(self.boiler).value(BoilerControl(heater_on=heater_on)).build(),
        )


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
