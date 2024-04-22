from datetime import datetime, timedelta
from pytest import approx, fixture
from energy_box_control.appliances.base import ConnectionState
from energy_box_control.appliances import HeatPipes, HeatPipesState, HeatPipesPort
from energy_box_control.schedules import ConstSchedule
from energy_box_control.time import ProcessTime
from energy_box_control.units import *


@fixture
def simulation_time():
    return ProcessTime(timedelta(seconds=1), 0, datetime.now())


def test_equal_temps(simulation_time):
    heat_pipes = HeatPipes(0.50, 0.1, 0.1, 1, 1, ConstSchedule(1), ConstSchedule(10))
    _, outputs = heat_pipes.simulate(
        {
            HeatPipesPort.IN: ConnectionState(1, 10),
        },
        HeatPipesState(10),
        None,
        simulation_time,
    )
    assert outputs[HeatPipesPort.OUT].temperature == 10.5
    assert outputs[HeatPipesPort.OUT].flow == 1


def test_differential_temp(simulation_time):
    heat_pipes = HeatPipes(0.50, 0.1, 0.1, 1, 1, ConstSchedule(1), ConstSchedule(9))
    new_state, outputs = heat_pipes.simulate(
        {
            HeatPipesPort.IN: ConnectionState(1, 10),
        },
        HeatPipesState(10),
        None,
        simulation_time,
    )
    assert outputs[HeatPipesPort.OUT].temperature == 10.3
    assert outputs[HeatPipesPort.OUT].flow == 1
    assert new_state.mean_temperature == 10.15


@fixture
def hub_heat_pipes():
    return HeatPipes(
        0.767, 1.649, 0.006, 16.3, 3840 * 0.993, ConstSchedule(1000), ConstSchedule(20)
    )


def test_hub_stagnation_temp(hub_heat_pipes, simulation_time):
    inputs = {HeatPipesPort.IN: ConnectionState(1, 100)}
    pipes_state = HeatPipesState(100)

    temp_diff = None
    for _ in range(1000):
        pipes_state, outputs = hub_heat_pipes.simulate(
            inputs, pipes_state, None, simulation_time
        )
        temp_diff = (
            outputs[HeatPipesPort.OUT].temperature
            - inputs[HeatPipesPort.IN].temperature
        )

        inputs = {HeatPipesPort.IN: outputs[HeatPipesPort.OUT]}

    assert temp_diff == approx(0, abs=1e-4)
