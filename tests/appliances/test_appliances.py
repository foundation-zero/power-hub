from hypothesis import assume, example, given
from hypothesis.strategies import floats
from pytest import approx

from energy_box_control.appliances import (
    Boiler,
    BoilerPort,
    BoilerState,
    Source,
    ValveState,
)

from energy_box_control.networks import BoilerNetwork, BoilerValveNetwork

volume_strat = floats(1, 1e3, allow_nan=False)
temp_strat = floats(0, 150, allow_nan=False)
flow_strat = floats(0, 100, allow_nan=False)
heat_capacity_strat = floats(1, 1e5, allow_nan=False)
power_strat = floats(0, 1e6, allow_nan=False)


def test_valve():
    network = BoilerValveNetwork(
        Source(2, 100),
        Boiler(1, 0, 0, 1, 1),
        BoilerState(temperature=0),
        ValveState(0.5),
    )
    control = network.heater_on()
    state_1 = network.simulate(network.initial_state(), control)
    assert state_1.connection(network.boiler, BoilerPort.HEAT_EXCHANGE_IN).flow == 1.0
    assert state_1.appliance(network.boiler).get().temperature == 50
