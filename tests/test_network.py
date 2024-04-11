from datetime import datetime, timedelta
from typing import Self
from pytest import approx
from energy_box_control.appliances.base import ConnectionState, SimulationTime
from energy_box_control.network import (
    Network,
    NetworkConnections,
    NetworkFeedbacks,
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


def test_network():
    class MyNetwork(Network[None]):
        exchange_source = Source(0, 1)
        fill_source = Source(0, 1)
        valve = Valve()
        boiler = Boiler(1, 0, 0, 1, 1)

        def initial_state(self):
            return (
                self.define_state(self.exchange_source)
                .value(SourceState())
                .define_state(self.fill_source)
                .value(SourceState())
                .define_state(self.valve)
                .value(ValveState(0.5))
                .define_state(self.boiler)
                .value(BoilerState(50, 20))
                .build(SimulationTime(timedelta(seconds=1), 0, datetime.now()))
            )

        def connections(self):
            return (
                self.connect(self.exchange_source)
                .at(SourcePort.OUTPUT)
                .to(self.valve)
                .at(ValvePort.AB)
                .connect(self.fill_source)
                .at(SourcePort.OUTPUT)
                .to(self.boiler)
                .at(BoilerPort.FILL_IN)
                .connect(self.valve)
                .at(ValvePort.A)
                .to(self.boiler)
                .at(BoilerPort.HEAT_EXCHANGE_IN)
                .build()
            )

        def sensors_from_state(self, state: NetworkState[Self]) -> None:
            return None

    my = MyNetwork()
    control = my.control(my.boiler).value(BoilerControl(heater_on=False)).build()
    state = my.simulate(my.initial_state(), control)
    assert state.appliance(my.boiler).get().temperature == approx(50)


def test_circular_network():
    """Tests a circular network with just a boiler this in essence turns the flow through the heat exchanger into extra heat capacity"""

    class CircularNetwork(Network[None]):
        boiler = Boiler(99, 100, 0, 1, 1)

        def initial_state(self) -> NetworkState[Self]:
            return (
                self.define_state(self.boiler)
                .value(BoilerState(100, 20))
                .define_state(self.boiler)
                .at(BoilerPort.HEAT_EXCHANGE_OUT)
                .value(ConnectionState(1, 100))
                .build(SimulationTime(timedelta(seconds=1), 0, datetime.now()))
            )

        def connections(self) -> NetworkConnections[Self]:
            return NetworkConnections([])

        def feedback(self) -> NetworkFeedbacks[Self]:
            return (
                self.define_feedback(self.boiler)
                .at(BoilerPort.HEAT_EXCHANGE_OUT)
                .to(self.boiler)
                .at(BoilerPort.HEAT_EXCHANGE_IN)
                .build()
            )

        def sensors_from_state(self, state: NetworkState[Self]) -> None:
            return None

    circle = CircularNetwork()
    control = circle.control(circle.boiler).value(BoilerControl(heater_on=True)).build()
    state = circle.simulate(circle.initial_state(), control)
    assert (
        state.connection(circle.boiler, BoilerPort.HEAT_EXCHANGE_OUT).temperature == 101
    )
    assert state.appliance(circle.boiler).get().temperature == 101

    for _ in range(999):
        state = circle.simulate(state, control)

    assert (
        state.connection(circle.boiler, BoilerPort.HEAT_EXCHANGE_OUT).temperature
        == 1100
    )
    assert state.appliance(circle.boiler).get().temperature == 1100
