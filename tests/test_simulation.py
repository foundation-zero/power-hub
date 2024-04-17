from dataclasses import dataclass
from datetime import datetime, timedelta

from energy_box_control.appliances.base import ProcessTime
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
    steps,
):
    state = initial_state
    control_values = initial_control_values
    control_state = initial_control_state

    for i in range(steps):
        try:
            state = network.simulate(state, control_values, min_max_temperature)
        except Exception as e:
            return SimulationFailure(e, i, state)
        sensors = network.sensors_from_state(state)
        if control_function:
            control_state, control_values = control_function(
                control_state, sensors, state.time
            )
    return SimulationSuccess(state)


def test_simulation_time_timestamp():
    start = datetime(2023, 1, 1, 0, 0, 0)
    step_size = timedelta(days=1)
    step = 10
    simulation_time = ProcessTime(step_size, step, start)

    assert simulation_time.timestamp == datetime(2023, 1, 11, 0, 0, 0)
