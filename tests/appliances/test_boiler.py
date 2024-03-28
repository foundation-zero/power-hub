from hypothesis import assume, example, given, reproduce_failure
from hypothesis.strategies import floats
from pytest import approx
from energy_box_control.appliances.base import ConnectionState, ureg
from energy_box_control.appliances.boiler import (
    Boiler,
    BoilerControl,
    BoilerPort,
    BoilerState,
)
from pint.testing import assert_allclose


volume_strat = floats(1, 1e3, allow_nan=False)
temp_strat = floats(0, 150, allow_nan=False)
flow_strat = floats(0, 100, allow_nan=False)
heat_capacity_strat = floats(1, 1e5, allow_nan=False)
power_strat = floats(0, 1e6, allow_nan=False)


@given(
    volume_strat,
    power_strat,
    power_strat,
    heat_capacity_strat,
    heat_capacity_strat,
    temp_strat,
)
@example(20, 1, 1, 1, 1, 0)
def test_boiler_heating(
    volume,
    heater_power,
    heat_loss,
    specific_heat_capacity_exchange,
    specific_heat_capacity_fill,
    boiler_temp,
):

    boiler = Boiler(
        volume * ureg.liter,
        heater_power * ureg.watt,
        heat_loss * ureg.watt,
        specific_heat_capacity_exchange * (ureg.joule / (ureg.liter * ureg.kelvin)),
        specific_heat_capacity_fill * (ureg.joule / (ureg.liter * ureg.kelvin)),
    )
    state, _ = boiler.simulate(
        {}, BoilerState(boiler_temp * ureg.kelvin), BoilerControl(heater_on=True)
    )

    assert_allclose(
        state.temperature.to_base_units(),
        boiler_temp * ureg.kelvin
        + ((heater_power * ureg.watt - heat_loss * ureg.watt) * 1 * ureg.second)
        / (
            (volume * ureg.liter)
            * (specific_heat_capacity_fill * (ureg.joule / (ureg.liter * ureg.kelvin)))
        ),
        atol=1e-6,
    )


@given(
    volume_strat,
    heat_capacity_strat,
    heat_capacity_strat,
    temp_strat,
    temp_strat,
)
@example(10, 1, 1, 10, 20)
def test_boiler_exchange(
    volume,
    specific_heat_capacity_exchange,
    specific_heat_capacity_fill,
    exchange_in_temp,
    boiler_temp,
):

    boiler = Boiler(
        volume * ureg.liter,
        0 * ureg.watt,
        0 * ureg.watt,
        specific_heat_capacity_exchange * (ureg.joule / (ureg.liter * ureg.kelvin)),
        specific_heat_capacity_fill * (ureg.joule / (ureg.liter * ureg.kelvin)),
    )
    exchange_in_flow = (
        volume * specific_heat_capacity_fill / specific_heat_capacity_exchange
    )  # to have equal heat capacities
    state, _ = boiler.simulate(
        {
            BoilerPort.HEAT_EXCHANGE_IN: ConnectionState(
                exchange_in_flow,
                exchange_in_temp,
            )
        },
        BoilerState(boiler_temp * ureg.kelvin),
        BoilerControl(heater_on=False),
    )

    assert_allclose(
        state.temperature.to_base_units(),
        (boiler_temp * ureg.kelvin + exchange_in_temp * ureg.kelvin) / 2,
    )


@given(heat_capacity_strat, heat_capacity_strat, temp_strat, flow_strat, temp_strat)
@example(1, 1, 20, 1, 10)
def test_boiler_fill(
    specific_heat_capacity_exchange,
    specific_heat_capacity_fill,
    fill_in_temp,
    fill_in_flow,
    boiler_temp,
):
    assume(fill_in_flow > 0.5)

    boiler = Boiler(
        fill_in_flow * ureg.liter,
        0 * ureg.watt,
        0 * ureg.watt,
        specific_heat_capacity_exchange * (ureg.joule / (ureg.liter * ureg.kelvin)),
        specific_heat_capacity_fill * (ureg.joule / (ureg.liter * ureg.kelvin)),
    )
    state, _ = boiler.simulate(
        {BoilerPort.FILL_IN: ConnectionState(fill_in_flow, fill_in_temp)},
        BoilerState(boiler_temp * ureg.kelvin),
        BoilerControl(heater_on=False),
    )
    assert_allclose(
        state.temperature,
        (boiler_temp * ureg.kelvin + fill_in_temp * ureg.kelvin) / 2,
        atol=1e-6,
    )
