from pytest import approx

from energy_box_control.logic import ControlState, control
from energy_box_control.network import Network
from energy_box_control.simulation import Boiler, BoilerState, Source
from tests.networks import BoilerNetwork


def run(network: Network, state, control_state, times):
    for _ in range(times):
        sensors = network.sensors(state)
        new_control_state, control_values = control(network, control_state, sensors)
        new_state = network.simulate(state, control_values)

        control_state = new_control_state
        state = new_state

    return state, control_state


def test_heater():
    network = BoilerNetwork(Source(0, 0), Boiler(10, 1, 0, 0), BoilerState(0))
    control_state = ControlState(50)

    state_1, new_control_state = run(
        network, network.initial_state(), control_state, 1000
    )

    assert state_1.appliance(network.boiler).get().temperature == approx(
        control_state.boiler_setpoint
    )

    state_2, new_control_state = run(network, state_1, control_state, 1000)
    assert (
        state_1.appliance(network.boiler).get().temperature
        == state_2.appliance(network.boiler).get().temperature
    )
