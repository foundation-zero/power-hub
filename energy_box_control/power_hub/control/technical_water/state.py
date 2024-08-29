from dataclasses import dataclass
from energy_box_control.control.state_machines import Context, State


class TechnicalWaterControlMode(State):
    FILL_FROM_FRESH = "fill_from_fresh"
    NO_FILL_FROM_FRESH = "no_fill_from_fresh"


@dataclass
class TechnicalWaterControlState:
    context: Context
    control_mode: TechnicalWaterControlMode
