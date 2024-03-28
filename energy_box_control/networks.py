# pyright: reportIncompatibleMethodOverride=true
from dataclasses import dataclass
from typing import Self
from energy_box_control.appliances.yazaki import Yazaki, YazakiPort, YazakiState
from energy_box_control.network import (
    Network,
    NetworkConnections,
    NetworkControl,
    NetworkState,
)
from energy_box_control.appliances import (
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
from energy_box_control.appliances.base import ureg
from pint import Quantity


@dataclass
class BoilerSensors:
    boiler_temperature: float | Quantity


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
            .build()
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
    ) -> tuple[(ControlState, NetworkControl[Self])]:
        heater_on = (
            sensors.boiler_temperature < control_state.boiler_setpoint * ureg.kelvin
        )

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
            .build()
        )

    def connections(self) -> NetworkConnections[Self]:
        source_to_valve = (
            self.connect(self.source)
            .at(SourcePort.OUTPUT)
            .to(self.valve)
            .at(ValvePort.AB)
        )

        valve_to_boiler = (
            source_to_valve.connect(self.valve)
            .at(ValvePort.A)
            .to(self.boiler)
            .at(BoilerPort.HEAT_EXCHANGE_IN)
        )

        return valve_to_boiler.build()


class YazakiNetwork(Network[None]):
    def __init__(
        self,
        hot_source: Source,
        cooling_source: Source,
        chilled_source: Source,
        yazaki: Yazaki,
    ):
        self.hot_source = hot_source
        self.cooling_source = cooling_source
        self.chilled_source = chilled_source
        self.yazaki = yazaki
        super().__init__()

    def initial_state(self) -> NetworkState[Self]:
        return (
            self.define_state(self.hot_source)
            .value(SourceState())
            .define_state(self.chilled_source)
            .value(SourceState())
            .define_state(self.cooling_source)
            .value(SourceState())
            .define_state(self.yazaki)
            .value(YazakiState(0))
            .build()
        )

    def connections(self) -> NetworkConnections[Self]:

        return (
            self.connect(self.hot_source)
            .at(SourcePort.OUTPUT)
            .to(self.yazaki)
            .at(YazakiPort.HOT_IN)
            .connect(self.chilled_source)
            .at(SourcePort.OUTPUT)
            .to(self.yazaki)
            .at(YazakiPort.CHILLED_IN)
            .connect(self.cooling_source)
            .at(SourcePort.OUTPUT)
            .to(self.yazaki)
            .at(YazakiPort.COOLING_IN)
            .build()
        )

    def sensors(self, state: NetworkState[Self]) -> None:
        return None
