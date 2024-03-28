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

from energy_box_control.appliances.base import ureg
from pint.testing import assert_allclose

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
            volume * ureg.liter,
            heater_power * ureg.watt,
            0 * ureg.watt,
            specific_heat_capacity_exchange * (ureg.joule / (ureg.liter * ureg.kelvin)),
            specific_heat_capacity_fill * (ureg.joule / (ureg.liter * ureg.kelvin)),
        ),
        BoilerState(temperature=boiler_temperature * ureg.kelvin),
    )

    state = network.initial_state()
    next_state = network.simulate(state, network.heater_off())
    assert_allclose(
        next_state.appliance(network.boiler).get().temperature.to_base_units(),
        boiler_temperature * ureg.kelvin,
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
            volume * ureg.liter,
            heater_power * ureg.watt,
            0 * ureg.watt,
            specific_heat_capacity_exchange * (ureg.joule / (ureg.liter * ureg.kelvin)),
            specific_heat_capacity_fill * (ureg.joule / (ureg.liter * ureg.kelvin)),
        ),
        BoilerState(temperature=0 * ureg.kelvin),
    )

    boiler_heat_capacity = (
        network.boiler.volume * network.boiler.specific_heat_capacity_fill
    )

    control = network.heater_on()
    state_1 = network.simulate(network.initial_state(), control)

    assert_allclose(
        state_1.appliance(network.boiler).get().temperature.to_base_units(),
        (
            (((heater_power * ureg.watt) / boiler_heat_capacity)) * 1 * ureg.second
        ).to_base_units(),
        atol=1e-6,
    )
    state_2 = network.simulate(state_1, control)

    assert_allclose(
        state_2.appliance(network.boiler).get().temperature.to_base_units(),
        (
            ((2 * heater_power * ureg.watt) / boiler_heat_capacity) * 1 * ureg.second
        ).to_base_units(),
        atol=1e-6,
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
            volume * ureg.liter,
            heater_power * ureg.watt,
            0 * ureg.watt,
            specific_heat_capacity_exchange * (ureg.joule / (ureg.liter * ureg.kelvin)),
            specific_heat_capacity_fill * (ureg.joule / (ureg.liter * ureg.kelvin)),
        ),
        BoilerState(temperature=test_temperature * ureg.kelvin),
    )
    control = network.heater_off()
    next_state = network.simulate(network.initial_state(), control)

    assert_allclose(
        next_state.appliance(network.boiler).get().temperature.to_base_units(),
        test_temperature * ureg.kelvin,
    )


@given(floats(0.1, 100, allow_nan=False), temp_strat, heat_capacity_strat, temp_strat)
@example(1, 20, 1, 10)
def test_simulate_equal_capacity(
    source_flow, source_temp, specific_heat_capacity_fill, boiler_temp
):

    network = BoilerNetwork(
        Source(source_flow, source_temp),
        Boiler(
            source_flow * ureg.liter,
            0 * ureg.watt,
            0 * ureg.watt,
            specific_heat_capacity_fill * (ureg.joule / (ureg.liter * ureg.kelvin)),
            specific_heat_capacity_fill * (ureg.joule / (ureg.liter * ureg.kelvin)),
        ),
        BoilerState(temperature=boiler_temp * ureg.kelvin),
    )
    control = network.heater_on()
    next_state = network.simulate(network.initial_state(), control)
    assert_allclose(
        next_state.appliance(network.boiler).get().temperature.to_base_units(),
        (source_temp * ureg.kelvin + boiler_temp * ureg.kelvin) / 2,
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
            volume * ureg.liter,
            heater_power * ureg.watt,
            boiler_heat_loss * ureg.watt,
            specific_heat_capacity_exchange * (ureg.joule / (ureg.liter * ureg.kelvin)),
            specific_heat_capacity_fill * (ureg.joule / (ureg.liter * ureg.kelvin)),
        ),
        BoilerState(temperature=boiler_temp * ureg.kelvin),
    )
    control = network.heater_on()
    state_1 = network.simulate(network.initial_state(), control)

    assert_allclose(
        state_1.appliance(network.boiler).get().temperature.to_base_units(),
        (
            boiler_temp * ureg.kelvin
            + (
                (heater_power * ureg.watt - boiler_heat_loss * ureg.watt)
                * 1
                * ureg.second
            )
            / (
                (volume * ureg.liter)
                * (
                    specific_heat_capacity_fill
                    * (ureg.joule / (ureg.liter * ureg.kelvin))
                )
            )
        ).to_base_units(),
    )


def test_valve():
    network = BoilerValveNetwork(
        Source(2, 100),
        Boiler(
            1 * ureg.liter,
            0 * ureg.watt,
            0 * ureg.watt,
            1 * (ureg.joule / (ureg.liter * ureg.kelvin)),
            1 * (ureg.joule / (ureg.liter * ureg.kelvin)),
        ),
        BoilerState(temperature=0 * ureg.kelvin),
        ValveState(0.5),
    )
    control = network.heater_on()
    state_1 = network.simulate(network.initial_state(), control)
    assert state_1.connection(network.boiler, BoilerPort.HEAT_EXCHANGE_IN).flow == 1.0

    assert_allclose(
        state_1.appliance(network.boiler).get().temperature.to_base_units(),
        50 * ureg.kelvin,
    )
