from dataclasses import dataclass


@dataclass(frozen=True, eq=True)
class SimulationFailure:
    exception: Exception
    step: int


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
         
        state = network.simulate(state, control_values, min_max_temperature)
        sensors = network.sensors(state)
        if control_function:
            control_state, control_values = control_function(control_state, sensors)
    return state
