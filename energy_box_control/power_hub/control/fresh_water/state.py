from dataclasses import dataclass
from energy_box_control.control.state_machines import Context, State


class FreshWaterControlMode(State):
    READY = "ready"
    FILTER_TANK = "filter_tank"


@dataclass
class FreshWaterControlState:
    context: Context
    control_mode: FreshWaterControlMode
