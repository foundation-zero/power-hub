from pytest import approx
from energy_box_control.logic import ControlState, control

from energy_box_control.simulation import Boiler, BoilerState, Network, State, simulate


def run(network, state, control_state, times):
    for _ in range(times):
        sensors = state.sensors()
        new_control_state, control_values = control(network, control_state, sensors)
        new_state = simulate(network, state, control_values)

        control_state = new_control_state
        state = new_state

    return state, control_state


def test_heater():
    network = Network(Boiler(10, 1))
    state = State(BoilerState(0))
    control_state = ControlState(50)

    state_1, new_control_state = run(network, state, control_state, 1000)

    assert state_1.boiler_state.temperature == approx(control_state.boiler_setpoint)

    state_2, new_control_state = run(network, state, control_state, 1000)
    assert state_2.boiler_state.temperature == state_2.boiler_state.temperature
