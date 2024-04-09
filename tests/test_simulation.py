from dataclasses import dataclass
from datetime import datetime, timedelta

from energy_box_control.appliances.base import SimulationTime
from energy_box_control.network import NetworkState


@dataclass(frozen=True, eq=True)
class SimulationSuccess:
    state: NetworkState


@dataclass(frozen=True, eq=True)
class SimulationFailure:
    exception: Exception
    step: int
    state: NetworkState


def run_simulation(
    network,
    initial_state,
    initial_control_values,
    initial_control_state,
    control_function,
    min_max_temperature,
):
    state = initial_state
    control_values = initial_control_values
    control_state = initial_control_state

    for i in range(500):
        try:
            state = network.simulate(state, control_values, min_max_temperature)
        except Exception as e:
            return SimulationFailure(e, i, state)
        sensors = network.sensors(state)
        if control_function:
            control_state, control_values = control_function(control_state, sensors)
    return SimulationSuccess(state)


def test_simulationtime():

    start = datetime(2023, 1, 1, 0, 0, 0)
    step_size = timedelta(days=1)
    step = 10
    simulationtime = SimulationTime(step_size, step, start)

    assert simulationtime.timestamp == datetime(2023, 1, 11, 0, 0, 0)
