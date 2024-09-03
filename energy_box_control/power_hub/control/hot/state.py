from dataclasses import dataclass
from energy_box_control.control.pid import Pid
from energy_box_control.control.state_machines import Context, State


class HotControlMode(State):
    WAITING_FOR_SUN = "waiting_for_sun"
    IDLE = "idle"
    PREPARE_HEAT_RESERVOIR = "prepare_heat_reservoir"
    HEAT_RESERVOIR = "heat_reservoir"
    PREPARE_HEAT_PCM = "prepare_heat_pcm"
    HEAT_PCM = "heat_pcm"


@dataclass
class HotControlState:
    context: Context
    control_mode: HotControlMode
    feedback_valve_controller: Pid
    hot_switch_valve_position: float
