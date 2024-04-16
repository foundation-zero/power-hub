from functools import partial
from numpy import power
from pytest import approx, fixture
from energy_box_control.appliances import (
    HeatPipesPort,
)
from energy_box_control.appliances.boiler import BoilerPort
from energy_box_control.power_hub import PowerHub
from dataclasses import dataclass

from energy_box_control.power_hub import control
from energy_box_control.power_hub.control import (
    PowerHubControlState,
    control_power_hub,
    initial_control_state,
    no_control,
)
import energy_box_control.power_hub.power_hub_components as phc
from tests.test_simulation import SimulationFailure, SimulationSuccess, run_simulation


@fixture
def power_hub() -> PowerHub:
    return PowerHub.power_hub()


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


def test_power_hub_simulation_no_control(power_hub, min_max_temperature):

    result = run_simulation(
        power_hub,
        power_hub.simple_initial_state(),
        no_control(power_hub),
        initial_control_state(),
        None,
        min_max_temperature,
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
