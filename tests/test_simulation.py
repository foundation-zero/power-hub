from hypothesis import assume, given
from hypothesis.strategies import floats
from pytest import approx


from energy_box_control.simulation import (
    Network,
    Source,
    Boiler,
    NetworkState,
    BoilerState,
    SourceState,
)
from energy_box_control.control import Control

temp_float = floats(0, 150, allow_nan=False)
flow_float = floats(0, 100, allow_nan=False)
heat_capacity_float = floats(1, 1e5, allow_nan=False)
power_float = floats(0, 1e6, allow_nan=False)


@given(temp_float, heat_capacity_float, power_float, heat_capacity_float, temp_float)
def test_simulate_heater_off(
    source_temp,
    boiler_heat_capacity,
    heater_power,
    specific_heat_capacity_input,
    boiler_temperature,
):

    network = Network(
        Source(0, source_temp),
        Boiler(boiler_heat_capacity, heater_power, 0, specific_heat_capacity_input),
    )
    state = NetworkState(
        SourceState(inputs=[], outputs=[]),
        BoilerState(inputs=[], outputs=[], temperature=boiler_temperature),
    )
    control = Control(heater_on=False)
    next_state = network.simulate(state, control)
    assert next_state.boiler_state.temperature == approx(boiler_temperature)


@given(temp_float, heat_capacity_float, power_float, heat_capacity_float)
def test_simulate_heater_on(
    source_temp, boiler_heat_capacity, heater_power, specific_heat_capacity_input
):
    network = Network(
        Source(0, source_temp),
        Boiler(boiler_heat_capacity, heater_power, 0, specific_heat_capacity_input),
    )
    state = NetworkState(
        SourceState(inputs=[], outputs=[]),
        BoilerState(inputs=[], outputs=[], temperature=0),
    )
    control = Control(heater_on=True)
    state_1 = network.simulate(state, control)
    assert state_1.boiler_state.temperature == approx(
        heater_power / boiler_heat_capacity
    )
    state_2 = network.simulate(state_1, control)
    assert state_2.boiler_state.temperature == approx(
        2 * heater_power / boiler_heat_capacity
    )


@given(flow_float, temp_float, heat_capacity_float, power_float, heat_capacity_float)
def test_simulate_equal_temp(
    source_flow,
    test_temperature,
    boiler_heat_capacity,
    heater_power,
    specific_heat_capacity_input,
):
    network = Network(
        Source(source_flow, test_temperature),
        Boiler(boiler_heat_capacity, heater_power, 0, specific_heat_capacity_input),
    )
    state = NetworkState(
        SourceState(inputs=[], outputs=[]),
        BoilerState(inputs=[], outputs=[], temperature=test_temperature),
    )
    control = Control(heater_on=False)
    next_state = network.simulate(state, control)
    assert next_state.boiler_state.temperature == approx(test_temperature)


@given(floats(0.1, 100, allow_nan=False), temp_float, heat_capacity_float, temp_float)
def test_simulate_equal_capacity(
    source_flow, source_temp, boiler_heat_capacity, boiler_temp
):

    network = Network(
        Source(source_flow, source_temp),
        Boiler(boiler_heat_capacity, 0, 0, boiler_heat_capacity / source_flow),
    )

    state = NetworkState(
        SourceState(inputs=[], outputs=[]),
        BoilerState(inputs=[], outputs=[], temperature=boiler_temp),
    )
    control = Control(heater_on=False)
    next_state = network.simulate(state, control)
    assert next_state.boiler_state.temperature == approx(
        (source_temp + boiler_temp) / 2
    )


@given(
    temp_float,
    heat_capacity_float,
    power_float,
    power_float,
    heat_capacity_float,
    temp_float,
)
def test_simulate_heat_loss(
    source_temp,
    boiler_heat_capacity,
    heater_power,
    boiler_heat_loss,
    specific_heat_capacity_input,
    boiler_temp,
):
    network = Network(
        Source(0, source_temp),
        Boiler(
            boiler_heat_capacity,
            heater_power,
            boiler_heat_loss,
            specific_heat_capacity_input,
        ),
    )
    state = NetworkState(
        SourceState(inputs=[], outputs=[]),
        BoilerState(inputs=[], outputs=[], temperature=boiler_temp),
    )
    control = Control(heater_on=True)
    state_1 = network.simulate(state, control)
    assert state_1.boiler_state.temperature == approx(
        boiler_temp + (heater_power - boiler_heat_loss) / boiler_heat_capacity
    )
