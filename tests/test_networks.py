from pytest import approx

from energy_box_control.appliances import Boiler, BoilerState, Source
from energy_box_control.networks import BoilerNetwork, ControlState
from energy_box_control.appliances.base import ureg
from pint.testing import assert_allclose


def run(network: BoilerNetwork, state, control_state, times):
    for _ in range(times):
        sensors = network.sensors(state)
        new_control_state, control_values = network.regulate(control_state, sensors)
        new_state = network.simulate(state, control_values)

        control_state = new_control_state
        state = new_state

    return state, control_state


def test_heater():
    network = BoilerNetwork(
        Source(0, 0),
        Boiler(
            10 * ureg.liter,
            1 * ureg.watt,
            0 * ureg.watt,
            0 * (ureg.joule / (ureg.liter * ureg.kelvin)),
            1 * (ureg.joule / (ureg.liter * ureg.kelvin)),
        ),
        BoilerState(0 * ureg.kelvin),
    )
    control_state = ControlState(50)

    state_1, new_control_state = run(
        network, network.initial_state(), control_state, 1000
    )

    assert_allclose(
        state_1.appliance(network.boiler).get().temperature.to_base_units(),
        control_state.boiler_setpoint * ureg.kelvin,
    )

    state_2, new_control_state = run(network, state_1, control_state, 1000)

    assert_allclose(
        state_1.appliance(network.boiler).get().temperature.to_base_units(),
        state_2.appliance(network.boiler).get().temperature.to_base_units(),
    )
