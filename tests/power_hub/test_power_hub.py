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
import energy_box_control.power_hub.powerhub_components as phc
from tests.simulation import SimulationSuccess, run_simulation


@fixture
def powerhub() -> PowerHub:
    return PowerHub.powerhub()


# @fixture
# def simple_initial_state(powerhub):
#     return powerhub.simple_initial_state()

# @fixture
# def no_control(powerhub):
#     return powerhub.no_control()


@fixture
def min_max_temperature():
    return (0, 300)


def test_powerhub_step(powerhub):
    powerhub.simulate(
        powerhub.simple_initial_state(),
        powerhub.no_control(),
    )


def test_powerhub_sensors(powerhub):

    next_state = powerhub.simulate(
        powerhub.simple_initial_state(), powerhub.no_control()
    )

    sensors = powerhub.sensors(next_state)
    assert (
        sensors.heat_pipes.output_temperature
        == next_state.connection(powerhub.heat_pipes, HeatPipesPort.OUT).temperature
    )


def test_powerhub_simulation_no_control(powerhub, min_max_temperature):

    result = run_simulation(
        powerhub,
        powerhub.simple_initial_state(),
        powerhub.no_control(),
        PowerHubControlState(),
        None,
        min_max_temperature,
    )

    assert type(result) == SimulationSuccess
