from pytest import approx
from energy_box_control.control import Control
from energy_box_control.network import Network
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


def test_network():
    class MyNetwork(Network):
        source = Source(0, 1)
        valve = Valve()
        boiler = Boiler(1, 0, 0, 1)

        def initial_state(self):
            return (
                self.define_state(self.source)
                .value(SourceState())
                .define_state(self.valve)
                .value(ValveState(0.5))
                .define_state(self.boiler)
                .value(BoilerState(50))
                .build(self.connections())
            )

        def connections(self):
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

    my = MyNetwork()
    state = my.simulate(my.initial_state(), Control(heater_on=False))
    assert state.appliance(my.boiler).get().temperature == approx(50)
