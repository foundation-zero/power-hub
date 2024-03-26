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
from energy_box_control.appliances.yazaki import Yazaki, YazakiControl, YazakiPort
from energy_box_control.network import NetworkControl
from energy_box_control.networks import BoilerNetwork, BoilerValveNetwork, YazakiNetwork

volume_strat = floats(1, 1e3, allow_nan=False)
temp_strat = floats(0, 150, allow_nan=False)
flow_strat = floats(0, 100, allow_nan=False)
heat_capacity_strat = floats(1, 1e5, allow_nan=False)
power_strat = floats(0, 1e6, allow_nan=False)


@given(
    temp_strat,
    volume_strat,
    power_strat,
    heat_capacity_strat,
    heat_capacity_strat,
    temp_strat,
)
@example(20, 1, 1, 1, 1, 10)
def test_simulate_heater_off(
    source_temp,
    volume,
    heater_power,
    specific_heat_capacity_exchange,
    specific_heat_capacity_fill,
    boiler_temperature,
):
    network = BoilerNetwork(
        Source(0, source_temp),
        Boiler(
            volume,
            heater_power,
            0,
            specific_heat_capacity_exchange,
            specific_heat_capacity_fill,
        ),
        BoilerState(temperature=boiler_temperature),
    )

    state = network.initial_state()
    next_state = network.simulate(state, network.heater_off())
    assert next_state.appliance(network.boiler).get().temperature == approx(
        boiler_temperature
    )


@given(
    temp_strat,
    volume_strat,
    power_strat,
    heat_capacity_strat,
    heat_capacity_strat,
)
@example(20, 1, 1, 1, 1)
def test_simulate_heater_on(
    source_temp,
    volume,
    heater_power,
    specific_heat_capacity_exchange,
    specific_heat_capacity_fill,
):
    network = BoilerNetwork(
        Source(0, source_temp),
        Boiler(
            volume,
            heater_power,
            0,
            specific_heat_capacity_exchange,
            specific_heat_capacity_fill,
        ),
        BoilerState(temperature=0),
    )

    boiler_heat_capacity = (
        network.boiler.volume * network.boiler.specific_heat_capacity_fill
    )

    control = network.heater_on()
    state_1 = network.simulate(network.initial_state(), control)
    assert state_1.appliance(network.boiler).get().temperature == approx(
        heater_power / boiler_heat_capacity
    )
    state_2 = network.simulate(state_1, control)
    assert state_2.appliance(network.boiler).get().temperature == approx(
        2 * heater_power / boiler_heat_capacity
    )


@given(
    flow_strat,
    temp_strat,
    volume_strat,
    power_strat,
    heat_capacity_strat,
    heat_capacity_strat,
)
@example(1, 20, 1, 1, 1, 1)
def test_simulate_equal_temp(
    source_flow,
    test_temperature,
    volume,
    heater_power,
    specific_heat_capacity_exchange,
    specific_heat_capacity_fill,
):
    network = BoilerNetwork(
        Source(source_flow, test_temperature),
        Boiler(
            volume,
            heater_power,
            0,
            specific_heat_capacity_exchange,
            specific_heat_capacity_fill,
        ),
        BoilerState(temperature=test_temperature),
    )
    control = network.heater_off()
    next_state = network.simulate(network.initial_state(), control)
    assert next_state.appliance(network.boiler).get().temperature == approx(
        test_temperature
    )


@given(floats(0.1, 100, allow_nan=False), temp_strat, heat_capacity_strat, temp_strat)
@example(1, 20, 1, 10)
def test_simulate_equal_capacity(
    source_flow, source_temp, specific_heat_capacity_fill, boiler_temp
):

    network = BoilerNetwork(
        Source(source_flow, source_temp),
        Boiler(
            source_flow, 0, 0, specific_heat_capacity_fill, specific_heat_capacity_fill
        ),
        BoilerState(temperature=boiler_temp),
    )
    control = network.heater_on()
    next_state = network.simulate(network.initial_state(), control)
    assert next_state.appliance(network.boiler).get().temperature == approx(
        (source_temp + boiler_temp) / 2
    )


@given(
    temp_strat,
    volume_strat,
    power_strat,
    power_strat,
    heat_capacity_strat,
    heat_capacity_strat,
    temp_strat,
)
@example(20, 1, 2, 1, 1, 1, 10)
def test_simulate_heat_loss(
    source_temp,
    volume,
    heater_power,
    boiler_heat_loss,
    specific_heat_capacity_exchange,
    specific_heat_capacity_fill,
    boiler_temp,
):
    assume(boiler_heat_loss < heater_power)
    network = BoilerNetwork(
        Source(0, source_temp),
        Boiler(
            volume,
            heater_power,
            boiler_heat_loss,
            specific_heat_capacity_exchange,
            specific_heat_capacity_fill,
        ),
        BoilerState(temperature=boiler_temp),
    )
    control = network.heater_on()
    state_1 = network.simulate(network.initial_state(), control)
    assert state_1.appliance(network.boiler).get().temperature == approx(
        boiler_temp
        + (heater_power - boiler_heat_loss) / (volume * specific_heat_capacity_fill)
    )


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


def test_yazaki():
    network = YazakiNetwork(
        Source(1.2, 88), Source(2.55, 31), Source(0.77, 17.6), Yazaki(4184, 4184, 4184)
    )

    control = network.control(network.yazaki).value(YazakiControl()).build()

    state_1 = network.simulate(network.initial_state(), control)

    assert state_1.connection(network.yazaki, YazakiPort.HOT_OUT).temperature == approx(
        83, abs=1
    )
    assert state_1.connection(
        network.yazaki, YazakiPort.COOLING_OUT
    ).temperature == approx(35, abs=1)
    assert state_1.connection(
        network.yazaki, YazakiPort.CHILLED_OUT
    ).temperature == approx(12.5, abs=1)
