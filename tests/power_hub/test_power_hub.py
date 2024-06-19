from datetime import datetime, timedelta, timezone
from functools import partial
from pandas import read_csv
from pytest import approx, fixture, mark
import pytest
from energy_box_control.appliances import (
    HeatPipesPort,
)
from energy_box_control.appliances.boiler import BoilerPort
from energy_box_control.appliances.yazaki import YazakiPort
from energy_box_control.power_hub import PowerHub
from dataclasses import replace

from energy_box_control.power_hub.control import (
    WaterControlMode,
    control_power_hub,
    initial_control_all_off,
    initial_control_state,
    no_control,
)
import energy_box_control.power_hub.power_hub_components as phc
from energy_box_control.time import ProcessTime
from tests.test_simulation import SimulationFailure, SimulationSuccess, run_simulation
from energy_box_control.power_hub.network import PowerHubSchedules
from energy_box_control.schedules import ConstSchedule
from energy_box_control.appliances.pcm import PcmPort


@fixture
def power_hub() -> PowerHub:
    return PowerHub.power_hub(
        PowerHubSchedules(
            ConstSchedule(phc.GLOBAL_IRRADIANCE),
            ConstSchedule(phc.AMBIENT_TEMPERATURE),
            ConstSchedule(phc.COOLING_DEMAND),
            ConstSchedule(phc.SEAWATER_TEMPERATURE),
            ConstSchedule(phc.FRESHWATER_TEMPERATURE),
            ConstSchedule(phc.WATER_DEMAND),
        )
    )


@fixture
def min_max_temperature():
    return (0, 300)


def test_power_hub_step(power_hub):
    power_hub.simulate(
        power_hub.simple_initial_state(),
        no_control(power_hub),
    )


def test_power_hub_sensors(power_hub):

    next_state = power_hub.simulate(
        power_hub.simple_initial_state(), no_control(power_hub)
    )

    sensors = power_hub.sensors_from_state(next_state)
    assert (
        sensors.heat_pipes.output_temperature
        == next_state.connection(power_hub.heat_pipes, HeatPipesPort.OUT).temperature
    )
    assert sensors.hot_reservoir.exchange_flow == approx(
        next_state.connection(power_hub.hot_reservoir, BoilerPort.HEAT_EXCHANGE_IN).flow
    )
    assert sensors.cold_reservoir is not None


def test_derived_sensors(power_hub, min_max_temperature):

    state = power_hub.simple_initial_state(datetime.now())
    control_values = no_control(power_hub)

    for i in range(500):
        try:
            state = power_hub.simulate(state, control_values, min_max_temperature)
        except Exception as e:
            SimulationFailure(e, i, state)

        sensors = power_hub.sensors_from_state(state)

        assert sensors.pcm.discharge_input_temperature == approx(
            state.connection(power_hub.pcm, PcmPort.DISCHARGE_IN).temperature, abs=1e-4
        )
        assert sensors.pcm.charge_flow == approx(
            state.connection(power_hub.pcm, PcmPort.CHARGE_IN).flow, abs=1e-4
        )
        assert sensors.pcm.discharge_output_temperature == approx(
            state.connection(power_hub.pcm, PcmPort.DISCHARGE_OUT).temperature, abs=1e-4
        )

        assert sensors.yazaki.chilled_input_temperature == approx(
            state.connection(power_hub.yazaki, YazakiPort.CHILLED_IN).temperature,
            abs=1e-4,
        )

        assert sensors.yazaki.cooling_input_temperature == approx(
            state.connection(power_hub.yazaki, YazakiPort.COOLING_IN).temperature,
            abs=1e-4,
        )


def test_power_hub_simulation_no_control(power_hub, min_max_temperature):

    result = run_simulation(
        power_hub,
        power_hub.simple_initial_state(step_size=timedelta()),
        initial_control_all_off(power_hub),
        None,
        None,
        min_max_temperature,
        500,
    )

    assert isinstance(result, SimulationSuccess)


@mark.parametrize("seconds", [1, 60, 60 * 60, 60 * 60 * 24])
def test_power_hub_simulation_control(power_hub, min_max_temperature, seconds):
    result = run_simulation(
        power_hub,
        power_hub.simple_initial_state(step_size=timedelta(seconds=seconds)),
        initial_control_all_off(power_hub),
        initial_control_state(),
        partial(control_power_hub, power_hub),
        min_max_temperature,
        500,
    )

    assert isinstance(result, SimulationSuccess)


@pytest.fixture
def schedules():
    return PowerHubSchedules.schedules_from_data()


@mark.parametrize("seconds", [1, 60, 360])
def test_power_hub_simulation_data_schedule(min_max_temperature, seconds, schedules):

    power_hub = PowerHub.power_hub(schedules)

    schedule_start = schedules.ambient_temperature.schedule_start  # type: ignore
    result = run_simulation(
        power_hub,
        power_hub.simple_initial_state(schedule_start, timedelta(seconds=seconds)),
        initial_control_all_off(power_hub),
        initial_control_state(),
        partial(control_power_hub, power_hub),
        min_max_temperature,
        100,
    )

    assert isinstance(result, SimulationSuccess)


@pytest.fixture
def data():
    return read_csv(
        "energy_box_control/power_hub/powerhub_simulation_schedules_Jun_Oct_TMY.csv",
        index_col=0,
        parse_dates=True,
    )


def test_power_hub_schedules_from_data(schedules, data):
    hour = 4
    assert (
        schedules.global_irradiance.at(
            ProcessTime(
                timedelta(hours=1),
                0,
                schedules.global_irradiance.schedule_start + timedelta(hours=hour),  # type: ignore
            )
        )
        == data["Global Horizontal Radiation"].iloc[hour]
    )


@mark.parametrize("year", [2000, 2008, 2024])
@mark.parametrize("month", [1, 6, 11])
@mark.parametrize("day", [11, 18, 25])
def test_schedules_from_data_extrapolation(year, month, day, schedules, data):
    assert (
        schedules.ambient_temperature.at(
            ProcessTime(
                timedelta(seconds=1),
                0,
                datetime(year, month, day, 12, tzinfo=timezone.utc),
            )
        )
        >= data.between_time("12:00", "12:00")["Dry Bulb Temperature"].min()
    )


@mark.parametrize("year", [2000, 2008, 2024])
@mark.parametrize("month", [1, 6, 11])
@mark.parametrize("day", [11, 18, 25])
def test_schedule_hours(year, month, day, schedules, data):
    index = schedules.global_irradiance._get_index(
        ProcessTime(
            timedelta(seconds=1),
            0,
            datetime(year, month, day, 12, tzinfo=timezone.utc),
        )
    )
    assert data.index[index].to_pydatetime().replace(tzinfo=timezone.utc).hour == 12


def test_water_filter_trigger(power_hub, min_max_temperature, schedules):

    power_hub = PowerHub.power_hub(schedules)
    state = power_hub.simple_initial_state(
        datetime.now(timezone.utc), timedelta(seconds=1)
    )
    control_state = initial_control_state()
    control_values = initial_control_all_off(power_hub)

    sensors = power_hub.sensors_from_state(state)

    control_state, control_values = control_power_hub(
        power_hub, control_state, sensors, state.time.timestamp
    )

    control_state.setpoints.trigger_filter_water_tank = replace(
        state.time, step=10
    ).timestamp

    for i in range(31 * 60):
        control_state, control_values = control_power_hub(
            power_hub, control_state, sensors, replace(state.time, step=i).timestamp
        )

        if i == 1:
            assert control_values.appliance(power_hub.water_filter_bypass_valve).get().position == phc.WATER_FILTER_BYPASS_VALVE_CONSUMPTION_POSITION  # type: ignore
            assert control_state.water_control.control_mode == WaterControlMode.READY

        if i == 11:
            assert control_values.appliance(power_hub.water_filter_bypass_valve).get().position == phc.WATER_FILTER_BYPASS_VALVE_FILTER_POSITION  # type: ignore
            assert (
                control_state.water_control.control_mode == WaterControlMode.FILTER_TANK
            )

        if i == 12 + 30 * 60:
            assert control_values.appliance(power_hub.water_filter_bypass_valve).get().position == phc.WATER_FILTER_BYPASS_VALVE_CONSUMPTION_POSITION  # type: ignore
            assert control_state.water_control.control_mode == WaterControlMode.READY


def test_water_filter_stop(power_hub, min_max_temperature, schedules):

    power_hub = PowerHub.power_hub(schedules)
    state = power_hub.simple_initial_state(
        datetime.now(timezone.utc), timedelta(seconds=1)
    )
    control_state = initial_control_state()
    control_values = initial_control_all_off(power_hub)

    sensors = power_hub.sensors_from_state(state)

    control_state, control_values = control_power_hub(
        power_hub, control_state, sensors, state.time.timestamp
    )

    control_state.setpoints.trigger_filter_water_tank = replace(
        state.time, step=10
    ).timestamp
    control_state.setpoints.stop_filter_water_tank = replace(
        state.time, step=12
    ).timestamp

    for i in range(31 * 60):
        control_state, control_values = control_power_hub(
            power_hub, control_state, sensors, replace(state.time, step=i).timestamp
        )

        if i == 11:
            assert (
                control_values.appliance(power_hub.water_filter_bypass_valve)
                .get()
                .position
                == phc.WATER_FILTER_BYPASS_VALVE_FILTER_POSITION
            )
            assert (
                control_state.water_control.control_mode == WaterControlMode.FILTER_TANK
            )

        if i == 13:
            assert (
                control_values.appliance(power_hub.water_filter_bypass_valve)
                .get()
                .position
                == phc.WATER_FILTER_BYPASS_VALVE_CONSUMPTION_POSITION
            )
            assert control_state.water_control.control_mode == WaterControlMode.READY
