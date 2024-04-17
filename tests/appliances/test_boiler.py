from datetime import datetime, timedelta
from hypothesis import assume, example, given, reproduce_failure
from hypothesis.strategies import floats
from pytest import approx, fixture
from energy_box_control.appliances.base import ConnectionState
from energy_box_control.appliances.boiler import (
    Boiler,
    BoilerControl,
    BoilerPort,
    BoilerState,
)
from energy_box_control.time import ProcessTime

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
    temp_strat,
)
@example(20, 1, 1, 1, 1, 50, 20)
def test_boiler_heating(
    volume,
    heater_power,
    heat_loss,
    specific_heat_capacity_exchange,
    specific_heat_capacity_fill,
    boiler_temp,
    ambient_temp,
):

    boiler = Boiler(
        volume,
        heater_power,
        heat_loss,
        specific_heat_capacity_exchange,
        specific_heat_capacity_fill,
    )
    state, _ = boiler.simulate(
        {},
        BoilerState(boiler_temp, ambient_temperature=ambient_temp),
        BoilerControl(heater_on=True),
        ProcessTime(timedelta(seconds=1), 0, datetime.now()),
    )

    assert state.temperature == approx(
        boiler_temp
        + (heater_power - heat_loss * (boiler_temp > ambient_temp))
        / (volume * specific_heat_capacity_fill),
        abs=1e-6,
    )


@given(
    volume_strat,
    heat_capacity_strat,
    heat_capacity_strat,
    temp_strat,
    temp_strat,
    temp_strat,
)
@example(10, 1, 1, 10, 50, 20)
def test_boiler_exchange(
    volume,
    specific_heat_capacity_exchange,
    specific_heat_capacity_fill,
    exchange_in_temp,
    boiler_temp,
    ambient_temp,
):

    boiler = Boiler(
        volume,
        0,
        0,
        specific_heat_capacity_exchange,
        specific_heat_capacity_fill,
    )
    exchange_in_flow = (
        volume * specific_heat_capacity_fill / specific_heat_capacity_exchange
    )  # to have equal heat capacities
    state, _ = boiler.simulate(
        {
            BoilerPort.HEAT_EXCHANGE_IN: ConnectionState(
                exchange_in_flow, exchange_in_temp
            )
        },
        BoilerState(boiler_temp, ambient_temp),
        BoilerControl(heater_on=False),
        ProcessTime(timedelta(seconds=1), 0, datetime.now()),
    )
    assert state.temperature == approx((boiler_temp + exchange_in_temp) / 2, abs=1e-6)


@given(
    heat_capacity_strat,
    heat_capacity_strat,
    temp_strat,
    flow_strat,
    temp_strat,
    temp_strat,
)
@example(1, 1, 20, 1, 50, 20)
def test_boiler_fill(
    specific_heat_capacity_exchange,
    specific_heat_capacity_fill,
    fill_in_temp,
    fill_in_flow,
    boiler_temp,
    ambient_temp,
):
    assume(fill_in_flow > 0.5)

    boiler = Boiler(
        fill_in_flow,
        0,
        0,
        specific_heat_capacity_exchange,
        specific_heat_capacity_fill,
    )
    state, _ = boiler.simulate(
        {BoilerPort.FILL_IN: ConnectionState(fill_in_flow, fill_in_temp)},
        BoilerState(boiler_temp, ambient_temp),
        BoilerControl(heater_on=False),
        ProcessTime(timedelta(seconds=1), 0, datetime.now()),
    )
    assert state.temperature == approx((boiler_temp + fill_in_temp) / 2, abs=1e-6)


@fixture
def boiler():
    return Boiler(1, 1, 1, 1, 1)


@fixture
def simulation_time():
    return ProcessTime(timedelta(seconds=1), 0, datetime.now())


def test_boiler_heat_loss(boiler, simulation_time):

    state = BoilerState(50, 20)

    for _ in range(100):
        state, _ = boiler.simulate(
            {}, state, BoilerControl(heater_on=False), simulation_time
        )

    assert state.temperature == approx(20)


def test_boiler_double_step(boiler, simulation_time):
    state = BoilerState(50, 20)

    first_state, _ = boiler.simulate(
        {}, state, BoilerControl(heater_on=True), simulation_time
    )
    second_state, _ = boiler.simulate(
        {},
        first_state,
        BoilerControl(heater_on=True),
        ProcessTime(timedelta(seconds=1), 1, datetime.now()),
    )

    double_step_state, _ = boiler.simulate(
        {},
        state,
        BoilerControl(heater_on=True),
        ProcessTime(timedelta(seconds=2), 0, datetime.now()),
    )

    assert double_step_state == second_state
