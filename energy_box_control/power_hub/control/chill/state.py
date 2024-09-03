from dataclasses import dataclass
from energy_box_control.control.pid import Pid
from energy_box_control.control.state_machines import Context, State


class ChillControlMode(State):
    NO_CHILL = "no_chill"
    PREPARE_YAZAKI_VALVES = "prepare_chill_yazaki"
    CHECK_YAZAKI_BOUNDS = "check_yazaki_bounds"
    CHILL_YAZAKI = "chill_yazaki"
    PREPARE_CHILLER_VALVES = "prepare_chill_chiller"
    CHILL_CHILLER = "chill_chiller"


@dataclass
class ChillControlState:
    context: Context
    control_mode: ChillControlMode
    yazaki_hot_feedback_valve_controller: Pid
    chiller_switch_valve_position: float
    waste_switch_valve_position: float
