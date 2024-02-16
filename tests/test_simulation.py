from hypothesis import assume, example, given
from hypothesis.strategies import floats
from pytest import approx

from energy_box_control.control import Control
from energy_box_control.simulation import (
    Boiler,
    BoilerPort,
    BoilerState,
    Source,
    ValveState,
)
from tests.networks import BoilerNetwork, BoilerValveNetwork

temp_strat = floats(0, 150, allow_nan=False)
flow_strat = floats(0, 100, allow_nan=False)
heat_capacity_strat = floats(1, 1e5, allow_nan=False)
power_strat = floats(0, 1e6, allow_nan=False)


@given(temp_strat, heat_capacity_strat, power_strat, heat_capacity_strat, temp_strat)
@example(20, 1, 1, 1, 10)
def test_simulate_heater_off(
    source_temp,
    boiler_heat_capacity,
    heater_power,
    specific_heat_capacity_input,
    boiler_temperature,
):
    network = BoilerNetwork(
        Source(0, source_temp),
        Boiler(boiler_heat_capacity, heater_power, 0, specific_heat_capacity_input),
        BoilerState(temperature=boiler_temperature),
    )

    state = network.initial_state()
    control = Control(heater_on=False)
    next_state = network.simulate(state, control)
    assert next_state.appliance(network.boiler).get().temperature == approx(
        boiler_temperature
    )


@given(temp_strat, heat_capacity_strat, power_strat, heat_capacity_strat)
@example(20, 1, 1, 1)
def test_simulate_heater_on(
    source_temp, boiler_heat_capacity, heater_power, specific_heat_capacity_input
):
    network = BoilerNetwork(
        Source(0, source_temp),
        Boiler(boiler_heat_capacity, heater_power, 0, specific_heat_capacity_input),
        BoilerState(temperature=0),
    )
    control = Control(heater_on=True)
    state_1 = network.simulate(network.initial_state(), control)
    assert state_1.appliance(network.boiler).get().temperature == approx(
        heater_power / boiler_heat_capacity
    )
    state_2 = network.simulate(state_1, control)
    assert state_2.appliance(network.boiler).get().temperature == approx(
        2 * heater_power / boiler_heat_capacity
    )


@given(flow_strat, temp_strat, heat_capacity_strat, power_strat, heat_capacity_strat)
@example(1, 20, 1, 1, 1)
def test_simulate_equal_temp(
    source_flow,
    test_temperature,
    boiler_heat_capacity,
    heater_power,
    specific_heat_capacity_input,
):
    network = BoilerNetwork(
        Source(source_flow, test_temperature),
        Boiler(boiler_heat_capacity, heater_power, 0, specific_heat_capacity_input),
        BoilerState(temperature=test_temperature),
    )
    control = Control(heater_on=False)
    next_state = network.simulate(network.initial_state(), control)
    assert next_state.appliance(network.boiler).get().temperature == approx(
        test_temperature
    )


@given(floats(0.1, 100, allow_nan=False), temp_strat, heat_capacity_strat, temp_strat)
@example(1, 20, 1, 10)
def test_simulate_equal_capacity(
    source_flow, source_temp, boiler_heat_capacity, boiler_temp
):

    network = BoilerNetwork(
        Source(source_flow, source_temp),
        Boiler(boiler_heat_capacity, 0, 0, boiler_heat_capacity / source_flow),
        BoilerState(temperature=boiler_temp),
    )
    control = Control(heater_on=False)
    next_state = network.simulate(network.initial_state(), control)
    assert next_state.appliance(network.boiler).get().temperature == approx(
        (source_temp + boiler_temp) / 2
    )


@given(
    temp_strat,
    heat_capacity_strat,
    power_strat,
    power_strat,
    heat_capacity_strat,
    temp_strat,
)
@example(20, 1, 2, 1, 1, 10)
def test_simulate_heat_loss(
    source_temp,
    boiler_heat_capacity,
    heater_power,
    boiler_heat_loss,
    specific_heat_capacity_input,
    boiler_temp,
):
    assume(boiler_heat_loss < heater_power)
    network = BoilerNetwork(
        Source(0, source_temp),
        Boiler(
            boiler_heat_capacity,
            heater_power,
            boiler_heat_loss,
            specific_heat_capacity_input,
        ),
        BoilerState(temperature=boiler_temp),
    )
    control = Control(heater_on=True)
    state_1 = network.simulate(network.initial_state(), control)
    assert state_1.appliance(network.boiler).get().temperature == approx(
        boiler_temp + (heater_power - boiler_heat_loss) / boiler_heat_capacity
    )


def test_valve():
    network = BoilerValveNetwork(
        Source(2, 100), Boiler(1, 0, 0, 1), BoilerState(temperature=0), ValveState(0.5)
    )
    control = Control(heater_on=True)
    state_1 = network.simulate(network.initial_state(), control)
    assert state_1.connection(network.boiler, BoilerPort.HEAT_EXCHANGE_IN).flow == 1.0
    assert state_1.appliance(network.boiler).get().temperature == 50
