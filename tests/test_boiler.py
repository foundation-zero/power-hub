from hypothesis import assume, example, given
from hypothesis.strategies import floats
from pytest import approx
from energy_box_control.appliances.base import ConnectionState
from energy_box_control.appliances.boiler import (
    Boiler,
    BoilerControl,
    BoilerPort,
    BoilerState,
)


temp_strat = floats(0, 150, allow_nan=False)
flow_strat = floats(0, 100, allow_nan=False)
heat_capacity_strat = floats(1, 1e5, allow_nan=False)
power_strat = floats(0, 1e6, allow_nan=False)


@given(
    heat_capacity_strat,
    power_strat,
    power_strat,
    heat_capacity_strat,
    heat_capacity_strat,
    temp_strat,
)
@example(20, 1, 1, 1, 1, 0)
def test_boiler_heating(
    heat_capacity_tank,
    heater_power,
    heat_loss,
    specific_heat_capacity_exchange,
    specific_heat_capacity_fill,
    boiler_temp,
):

    boiler = Boiler(
        heat_capacity_tank,
        heater_power,
        heat_loss,
        specific_heat_capacity_exchange,
        specific_heat_capacity_fill,
    )
    state, _ = boiler.simulate(
        {}, BoilerState(boiler_temp), BoilerControl(heater_on=True)
    )

    assert state.temperature == approx(
        boiler_temp + (heater_power - heat_loss) / heat_capacity_tank
    )


@given(
    heat_capacity_strat,
    heat_capacity_strat,
    heat_capacity_strat,
    temp_strat,
    temp_strat,
)
@example(10, 1, 1, 10, 20)
def test_boiler_exchange(
    heat_capacity_tank,
    specific_heat_capacity_exchange,
    specific_heat_capacity_fill,
    exchange_in_temp,
    boiler_temp,
):

    boiler = Boiler(
        heat_capacity_tank,
        0,
        0,
        specific_heat_capacity_exchange,
        specific_heat_capacity_fill,
    )
    exchange_in_flow = (
        heat_capacity_tank / specific_heat_capacity_exchange
    )  # to have equal heat capacities
    state, _ = boiler.simulate(
        {
            BoilerPort.HEAT_EXCHANGE_IN: ConnectionState(
                exchange_in_flow, exchange_in_temp
            )
        },
        BoilerState(boiler_temp),
        BoilerControl(heater_on=False),
    )
    assert state.temperature == approx((boiler_temp + exchange_in_temp) / 2)


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
    heat_capacity_tank = (
        specific_heat_capacity_fill * fill_in_flow
    )  # equal heat capacities
    boiler = Boiler(
        heat_capacity_tank,
        0,
        0,
        specific_heat_capacity_exchange,
        specific_heat_capacity_fill,
    )
    state, _ = boiler.simulate(
        {BoilerPort.FILL_IN: ConnectionState(fill_in_flow, fill_in_temp)},
        BoilerState(boiler_temp),
        BoilerControl(heater_on=False),
    )
    assert state.temperature == approx((boiler_temp + fill_in_temp) / 2)
