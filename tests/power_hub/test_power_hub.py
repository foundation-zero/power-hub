from pytest import fixture
from energy_box_control.appliances import (
    BoilerControl,
    SwitchPumpControl,
    HeatPipesPort,
)
from energy_box_control.appliances.base import ApplianceState
from energy_box_control.appliances.boiler import BoilerState
from energy_box_control.appliances.chiller import ChillerState
from energy_box_control.appliances.heat_pipes import HeatPipesState
from energy_box_control.appliances.pcm import PcmState
from energy_box_control.appliances.source import SourceState
from energy_box_control.appliances.switch_pump import SwitchPumpState
from energy_box_control.appliances.valve import ValveState
from energy_box_control.appliances.yazaki import YazakiState
from energy_box_control.network import NetworkState
from energy_box_control.networks import ControlState
from energy_box_control.power_hub import PowerHub
from dataclasses import dataclass

from energy_box_control.power_hub.network import PowerHubControlState
import energy_box_control.power_hub.power_hub_components as phc
from tests.test_simulation import SimulationSuccess, run_simulation


@fixture
def power_hub() -> PowerHub:
    return PowerHub.power_hub()


@fixture
def min_max_temperature():
    return (0, 300)


def test_power_hub_step(power_hub):
    power_hub.simulate(
        power_hub.simple_initial_state(),
        power_hub.no_control(),
    )


def test_power_hub_sensors(power_hub):

    next_state = power_hub.simulate(
        power_hub.simple_initial_state(), power_hub.no_control()
    )

    sensors = power_hub.sensors(next_state)
    assert (
        sensors.heat_pipes.output_temperature
        == next_state.connection(power_hub.heat_pipes, HeatPipesPort.OUT).temperature
    )


def test_power_hub_simulation_no_control(power_hub, min_max_temperature):

    result = run_simulation(
        power_hub,
        power_hub.simple_initial_state(),
        power_hub.no_control(),
        PowerHubControlState(),
        None,
        min_max_temperature,
    )

    assert isinstance(result, SimulationSuccess)
