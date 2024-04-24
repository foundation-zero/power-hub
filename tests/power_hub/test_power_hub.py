from datetime import datetime, timedelta
from functools import partial
from hypothesis import example
from numpy import power
from pytest import approx, fixture
from energy_box_control.appliances import (
    HeatPipesPort,
)
from energy_box_control.appliances.base import ApplianceState
from energy_box_control.appliances.boiler import BoilerPort, BoilerState
from energy_box_control.appliances.chiller import ChillerState
from energy_box_control.appliances.heat_pipes import HeatPipesState
from energy_box_control.appliances.pcm import PcmPort, PcmState
from energy_box_control.appliances.source import SourceState
from energy_box_control.appliances.switch_pump import SwitchPumpState
from energy_box_control.appliances.valve import ValveState
from energy_box_control.appliances.yazaki import YazakiPort, YazakiState
from energy_box_control.network import NetworkState
from energy_box_control.networks import ControlState
from energy_box_control.power_hub import PowerHub
from dataclasses import dataclass

from energy_box_control.power_hub.control import (
    PowerHubControlState,
    control_power_hub,
    initial_control_state,
    no_control,
)
import energy_box_control.power_hub.power_hub_components as phc
from tests.test_simulation import SimulationFailure, SimulationSuccess, run_simulation
from energy_box_control.power_hub.network import PowerHubSchedules
from energy_box_control.schedules import ConstSchedule


@fixture
def power_hub() -> PowerHub:
    return PowerHub.power_hub(
        PowerHubSchedules(
            ConstSchedule(phc.GLOBAL_IRRADIANCE),
            ConstSchedule(phc.AMBIENT_TEMPERATURE),
            ConstSchedule(phc.COOLING_DEMAND),
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
        no_control(power_hub),
        None,
        None,
        min_max_temperature,
        500,
    )

    assert isinstance(result, SimulationSuccess)


def test_power_hub_simulation_control(power_hub, min_max_temperature):

    for seconds in [1, 60, 60 * 60, 60 * 60 * 24]:

        result = run_simulation(
            power_hub,
            power_hub.simple_initial_state(step_size=timedelta(seconds=seconds)),
            no_control(power_hub),
            initial_control_state(),
            partial(control_power_hub, power_hub),
            min_max_temperature,
            500,
        )

        assert isinstance(result, SimulationSuccess)
