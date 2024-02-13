from energy_box_control.simulation import (
    Network,
    Source,
    Boiler,
    NetworkState,
    BoilerState,
    SourceState,
)
from energy_box_control.control import Control


def test_simulate_heater_off():
    network = Network(Source(0, 0), Boiler(1, 1, 0, 1))
    state = NetworkState(
        SourceState(inputs=[], outputs=[]),
        BoilerState(inputs=[], outputs=[], temperature=0.0),
    )
    control = Control(heater_on=False)
    next_state = network.simulate(state, control)
    assert next_state.boiler_state.temperature == 0.0


def test_simulate_heater_on():
    network = Network(Source(0, 0), Boiler(1, 1, 0, 1))
    state = NetworkState(
        SourceState(inputs=[], outputs=[]),
        BoilerState(inputs=[], outputs=[], temperature=0),
    )
    control = Control(heater_on=True)
    state_1 = network.simulate(state, control)
    assert state_1.boiler_state.temperature == 1.0
    state_2 = network.simulate(state_1, control)
    assert state_2.boiler_state.temperature == 2.0


def test_simulate_equal_temp(test_temperature=10):
    network = Network(Source(1, test_temperature), Boiler(1, 1, 0, 1))
    state = NetworkState(
        SourceState(inputs=[], outputs=[]),
        BoilerState(inputs=[], outputs=[], temperature=test_temperature),
    )
    control = Control(heater_on=False)
    next_state = network.simulate(state, control)
    assert next_state.boiler_state.temperature == test_temperature


def test_simulate_equal_capacity(
    source_temp=20, boiler_temp=10, source_flow=10, boiler_heat_capacity=30
):
    network = Network(
        Source(source_flow, source_temp),
        Boiler(boiler_heat_capacity, 1, 0, boiler_heat_capacity / source_flow),
    )
    state = NetworkState(
        SourceState(inputs=[], outputs=[]),
        BoilerState(inputs=[], outputs=[], temperature=boiler_temp),
    )
    control = Control(heater_on=False)
    next_state = network.simulate(state, control)
    assert next_state.boiler_state.temperature == (source_temp + boiler_temp) / 2


def test_simulate_heat_loss():
    network = Network(Source(0, 0), Boiler(1, 2, 1, 1))
    state = NetworkState(
        SourceState(inputs=[], outputs=[]),
        BoilerState(inputs=[], outputs=[], temperature=0),
    )
    control = Control(heater_on=True)
    state_1 = network.simulate(state, control)
    assert state_1.boiler_state.temperature == 1.0
    state_2 = network.simulate(state_1, control)
    assert state_2.boiler_state.temperature == 2.0
