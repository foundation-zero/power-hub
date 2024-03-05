from energy_box_control.networks import ControlState
from power_hub import PowerHub

# TODO: dump network state every time step on MQTT


def run():
    times = 1000

    powerhub = PowerHub()
    state = powerhub.initial_state()
    sensors = powerhub.sensors(state)
    control_state = ControlState(50)
    for _ in range(times):
        new_control_state, control_values = powerhub.regulate(control_state, sensors)
        new_state = powerhub.simulate(state, control_values)
        control_state = new_control_state
        state = new_state
