from functools import partial
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
from energy_box_control.appliances.yazaki import YazakiState
from energy_box_control.network import NetworkState
from energy_box_control.networks import ControlState
from energy_box_control.power_hub import PowerHub
from dataclasses import dataclass

from energy_box_control.power_hub.control import (
    control_power_hub,
    initial_control_state,
    no_control,
)
import energy_box_control.power_hub.power_hub_components as phc
from tests.test_simulation import SimulationSuccess, run_simulation
from energy_box_control.power_hub.network import PowerHubSchedules
from energy_box_control.schedules import ConstSchedule


@fixture
def power_hub() -> PowerHub:
    return PowerHub.power_hub(PowerHubSchedules(ConstSchedule(phc.GLOBAL_IRRADIANCE)))


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
    assert sensors.hot_reservoir.heat_exchange_flow == approx(
        next_state.connection(power_hub.hot_reservoir, BoilerPort.HEAT_EXCHANGE_IN).flow
    )
    assert sensors.cold_reservoir is not None


def test_derived_sensors(power_hub, min_max_temperature):

    result = run_simulation(
        power_hub,
        power_hub.simple_initial_state(),
        power_hub.no_control(),
        PowerHubControlState(),
        None,
        min_max_temperature,
        100,
    )

    state = result.state
    sensors = power_hub.sensors(state)

    assert sensors.pcm.discharge_input_temperature == approx(
        state.connection(power_hub.pcm, PcmPort.DISCHARGE_IN).temperature, abs=1e-4
    )

    assert sensors.pcm.charge_flow == approx(
        state.connection(power_hub.pcm, PcmPort.CHARGE_IN).flow, abs=1e-4
    )
    assert sensors.pcm.discharge_output_temperature == approx(
        state.connection(power_hub.pcm, PcmPort.DISCHARGE_OUT).temperature, abs=1e-4
    )


def test_power_hub_simulation_no_control(power_hub, min_max_temperature):

    result = run_simulation(
        power_hub,
        power_hub.simple_initial_state(),
        no_control(power_hub),
        initial_control_state(),
        None,
        min_max_temperature,
        5000,
    )

    assert isinstance(result, SimulationSuccess)


def test_power_hub_simulation_control(power_hub, min_max_temperature):
    result = run_simulation(
        power_hub,
        power_hub.simple_initial_state(),
        no_control(power_hub),
        initial_control_state(),
        partial(control_power_hub, power_hub),
        min_max_temperature,
    )

    assert isinstance(result, SimulationSuccess)
