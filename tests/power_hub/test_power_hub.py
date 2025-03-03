from datetime import datetime, time, timedelta, timezone
from functools import partial
from pandas import read_csv
from pytest import approx, fixture, mark
from energy_box_control.appliances import (
    HeatPipesPort,
)
from energy_box_control.appliances.base import ThermalState
from energy_box_control.appliances.boiler import BoilerPort
from energy_box_control.appliances.heat_exchanger import HeatExchangerPort
from energy_box_control.appliances.water_maker import (
    WaterMakerState,
    WaterMakerStatus,
)
from energy_box_control.appliances.yazaki import YazakiPort
from energy_box_control.power_hub import PowerHub
from dataclasses import replace

from energy_box_control.power_hub.control.control import (
    FreshWaterControlMode,
    control_power_hub,
    initial_control_all_off,
    no_control,
)
import energy_box_control.power_hub.components as phc
from energy_box_control.power_hub.control.cooling_supply.state import (
    CoolingSupplyControlMode,
)
from energy_box_control.power_hub.control.state import initial_control_state
from energy_box_control.time import ProcessTime
from tests.simulation.test_simulation import (
    SimulationFailure,
    SimulationSuccess,
    run_simulation,
)
from energy_box_control.power_hub.network import PowerHubSchedules
from energy_box_control.schedules import ConstSchedule, PeriodicSchedule
from energy_box_control.appliances.pcm import PcmPort


@fixture
def power_hub_const() -> PowerHub:
    return PowerHub.power_hub(
        PowerHubSchedules(
            ConstSchedule(phc.GLOBAL_IRRADIANCE),
            ConstSchedule(phc.AMBIENT_TEMPERATURE),
            ConstSchedule(phc.COOLING_DEMAND),
            ConstSchedule(phc.SEAWATER_TEMPERATURE),
            ConstSchedule(phc.FRESHWATER_TEMPERATURE),
            ConstSchedule(phc.WATER_DEMAND),
            ConstSchedule(phc.PERCENT_WATER_CAPTURED * phc.WATER_DEMAND),
        )
    )


@fixture
def min_max_temperature():
    return (0, 300)


def test_power_hub_step(power_hub_const):
    power_hub_const.simulate(
        power_hub_const.simple_initial_state(),
        no_control(power_hub_const),
    )


def test_power_hub_sensors(power_hub_const):

    next_state = power_hub_const.simulate(
        power_hub_const.simple_initial_state(), no_control(power_hub_const)
    )

    sensors = power_hub_const.sensors_from_state(next_state)
    assert (
        sensors.heat_pipes.output_temperature
        == next_state.connection(
            power_hub_const.heat_pipes, HeatPipesPort.OUT
        ).temperature
    )
    assert sensors.hot_reservoir.exchange_flow == approx(
        next_state.connection(
            power_hub_const.hot_reservoir, BoilerPort.HEAT_EXCHANGE_IN
        ).flow
    )
    assert sensors.cold_reservoir is not None


def test_derived_sensors(power_hub_const, min_max_temperature):

    control_values = no_control(power_hub_const)
    state = power_hub_const.simulate(
        power_hub_const.simple_initial_state(datetime.now()), control_values
    )

    for i in range(500):
        try:
            state = power_hub_const.simulate(state, control_values, min_max_temperature)
        except Exception as e:
            SimulationFailure(e, i, state)

        sensors = power_hub_const.sensors_from_state(state)

        assert sensors.pcm.discharge_input_temperature == approx(
            state.connection(power_hub_const.pcm, PcmPort.DISCHARGE_IN).temperature,
            abs=1e-4,
        )
        assert sensors.pcm.charge_flow == approx(
            state.connection(power_hub_const.pcm, PcmPort.CHARGE_IN).flow, abs=1e-4
        )
        assert sensors.pcm.discharge_output_temperature == approx(
            state.connection(power_hub_const.pcm, PcmPort.DISCHARGE_OUT).temperature,
            abs=1e-4,
        )

        sensors.chiller_switch_valve.position = phc.CHILLER_SWITCH_VALVE_YAZAKI_POSITION
        sensors.waste_switch_valve.position = phc.WASTE_SWITCH_VALVE_YAZAKI_POSITION
        assert sensors.yazaki.chilled_input_temperature == approx(
            state.connection(power_hub_const.yazaki, YazakiPort.CHILLED_IN).temperature,
            abs=1e-4,
        )

        assert sensors.yazaki.waste_input_temperature == approx(
            state.connection(power_hub_const.yazaki, YazakiPort.COOLING_IN).temperature,
            abs=1e-4,
        )


def test_power_hub_simulation_no_control(power_hub_const, min_max_temperature):

    result = run_simulation(
        power_hub_const,
        power_hub_const.simple_initial_state(step_size=timedelta()),
        initial_control_all_off(power_hub_const),
        None,
        None,
        min_max_temperature,
        500,
    )

    assert isinstance(result, SimulationSuccess)


@mark.skip(reason="test broke due to turning off water treatment")
@mark.parametrize("seconds", [1, 60])
def test_power_hub_simulation_control(power_hub_const, min_max_temperature, seconds):
    result = run_simulation(
        power_hub_const,
        power_hub_const.simple_initial_state(step_size=timedelta(seconds=seconds)),
        initial_control_all_off(power_hub_const),
        initial_control_state(),
        partial(control_power_hub, power_hub_const, survival_mode=False),
        min_max_temperature,
        500,
    )

    assert isinstance(result, SimulationSuccess)


@fixture
def schedules():
    return PowerHubSchedules.schedules_from_data()


@mark.skip(reason="test broke due to turning off water treatment")
@mark.parametrize("seconds", [1, 60])
def test_power_hub_simulation_data_schedule(
    power_hub_const, min_max_temperature, seconds, schedules
):
    schedule_start = schedules.ambient_temperature.schedule_start  # type: ignore
    result = run_simulation(
        power_hub_const,
        power_hub_const.simple_initial_state(
            schedule_start, timedelta(seconds=seconds)
        ),
        initial_control_all_off(power_hub_const),
        initial_control_state(),
        partial(control_power_hub, power_hub_const, survival_mode=False),
        min_max_temperature,
        100,
    )

    assert isinstance(result, SimulationSuccess)


@fixture
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
    schedule = PeriodicSchedule(
        schedules.global_irradiance.schedule_start,
        schedules.global_irradiance.period,
        tuple(range(0, len(data))),
    )
    time = schedules.global_irradiance.schedule_start + timedelta(hours=12)
    index = schedule.at(
        ProcessTime(
            timedelta(seconds=1),
            0,
            datetime(year, month, day, 12, tzinfo=timezone.utc),
        )
    )
    assert data.index[index].to_pydatetime().replace(tzinfo=timezone.utc).hour == 12


@fixture
def scheduled_power_hub(schedules):
    return PowerHub.power_hub(schedules)


@fixture
def state(scheduled_power_hub):
    return scheduled_power_hub.simple_initial_state(
        datetime.now(timezone.utc), timedelta(seconds=1)
    )


@fixture
def control_state():
    return initial_control_state()


@fixture
def control_values(scheduled_power_hub):
    return initial_control_all_off(scheduled_power_hub)


@fixture
def sensors(scheduled_power_hub, state):
    return scheduled_power_hub.sensors_from_state(state)


def test_cold_supply_schedule(
    scheduled_power_hub, state, control_state, control_values, sensors
):
    control_state.setpoints.cold_supply_outside_temperature_threshold = -100
    control_state.setpoints.cold_supply_enabled_time = replace(
        state.time, step=3
    ).timestamp.timetz()
    control_state.setpoints.cold_supply_disabled_time = replace(
        state.time, step=5
    ).timestamp.timetz()

    control_state, control_values = control_power_hub(
        scheduled_power_hub, control_state, sensors, state.time.timestamp, False
    )

    for i in range(1, 10):
        control_state, control_values = control_power_hub(
            scheduled_power_hub,
            control_state,
            sensors,
            replace(state.time, step=i).timestamp,
            False,
        )

        if i <= 3:
            assert (
                control_state.cooling_supply_control.control_mode
                == CoolingSupplyControlMode.DISABLED
            )

        if 3 < i <= 5:
            assert control_state.cooling_supply_control.control_mode in [
                CoolingSupplyControlMode.SUPPLY,
                CoolingSupplyControlMode.ENABLED_NO_SUPPLY,
            ]

        if i > 5:
            assert (
                control_state.cooling_supply_control.control_mode
                == CoolingSupplyControlMode.DISABLED
            )


def test_water_filter(
    scheduled_power_hub, state, control_state, control_values, sensors
):

    control_state, control_values = control_power_hub(
        scheduled_power_hub, control_state, sensors, state.time.timestamp, False
    )

    state = scheduled_power_hub.simulate(state, control_values)
    sensors = scheduled_power_hub.sensors_from_state(state)

    assert control_state.setpoints.filter_water_tank == False
    assert (
        control_values.appliance(scheduled_power_hub.water_filter_bypass_valve)
        .get()
        .position
        == phc.WATER_FILTER_BYPASS_VALVE_CONSUMPTION_POSITION
    )
    assert control_state.fresh_water_control.control_mode == FreshWaterControlMode.READY

    control_state.setpoints.filter_water_tank = True

    control_state, control_values = control_power_hub(
        scheduled_power_hub,
        control_state,
        sensors,
        state.time.timestamp,
        False,
    )

    assert (
        control_values.appliance(scheduled_power_hub.water_filter_bypass_valve)
        .get()
        .position
        == phc.WATER_FILTER_BYPASS_VALVE_FILTER_POSITION
    )
    assert (
        control_state.fresh_water_control.control_mode
        == FreshWaterControlMode.FILTER_TANK
    )


@mark.parametrize(
    "heat_dump_out_temperature, water_maker_on, outboard_pump_on",
    [
        (10, WaterMakerStatus.WATER_PRODUCTION.value, True),
        (35, WaterMakerStatus.WATER_PRODUCTION.value, True),
        (10, WaterMakerStatus.STANDBY.value, False),
    ],
)
def test_waste_pump_water_maker_on(
    scheduled_power_hub,
    state,
    control_state,
    control_values,
    sensors,
    heat_dump_out_temperature,
    water_maker_on,
    outboard_pump_on,
):
    state = (
        scheduled_power_hub.simulate(state, control_values)
        .replace_signal(
            scheduled_power_hub.outboard_exchange,
            HeatExchangerPort.A_OUT,
            ThermalState(0, heat_dump_out_temperature),
        )
        .replace_state(
            scheduled_power_hub.water_maker,
            WaterMakerState(water_maker_on),
        )
    )
    sensors = scheduled_power_hub.sensors_from_state(state)

    control_state, control_values = control_power_hub(
        scheduled_power_hub, control_state, sensors, state.time.timestamp, False
    )

    # 5 minutes pass
    control_state, control_values = control_power_hub(
        scheduled_power_hub,
        control_state,
        sensors,
        state.time.timestamp + timedelta(minutes=5),
        False,
    )

    assert (
        control_values.appliance(scheduled_power_hub.outboard_pump).get().on
        == outboard_pump_on
    )


@mark.skip(reason="test broke due to turning off water treatment")
def test_water_treatment(
    scheduled_power_hub, state, control_state, control_values, sensors
):

    control_state, control_values = control_power_hub(
        scheduled_power_hub, control_state, sensors, state.time.timestamp, False
    )

    state = scheduled_power_hub.simulate(state, control_values)
    sensors = scheduled_power_hub.sensors_from_state(state)

    sensors.grey_water_tank.fill_ratio = 0.95

    control_state, control_values = control_power_hub(
        scheduled_power_hub, control_state, sensors, state.time.timestamp, False
    )

    assert (
        control_values.appliance(scheduled_power_hub.water_treatment).get().on == True
    )

    sensors.grey_water_tank.fill_ratio = 0.09

    control_state, control_values = control_power_hub(
        scheduled_power_hub, control_state, sensors, state.time.timestamp, False
    )

    assert (
        control_values.appliance(scheduled_power_hub.water_treatment).get().on == False
    )


def test_technical_water_control(
    scheduled_power_hub, state, control_state, control_values, sensors
):

    control_state, control_values = control_power_hub(
        scheduled_power_hub, control_state, sensors, state.time.timestamp, False
    )

    state = scheduled_power_hub.simulate(state, control_values)
    sensors = scheduled_power_hub.sensors_from_state(state)

    sensors.technical_water_tank.fill_ratio = 0

    control_state, control_values = control_power_hub(
        scheduled_power_hub, control_state, sensors, state.time.timestamp, False
    )

    assert (
        control_values.appliance(scheduled_power_hub.technical_water_regulator)
        .get()
        .position
        == phc.TECHNICAL_WATER_REGULATOR_OPEN_POSITION
    )

    sensors.grey_water_tank.fill_ratio = 0.09

    control_state, control_values = control_power_hub(
        scheduled_power_hub, control_state, sensors, state.time.timestamp, False
    )

    assert (
        control_values.appliance(scheduled_power_hub.water_treatment).get().on == False
    )
