from dataclasses import dataclass
from energy_box_control.control.state_machines import Context, State


class WaterTreatmentControlMode(State):
    RUN = "run"
    NO_RUN = "no_run"


@dataclass
class WaterTreatmentControlState:
    context: Context
    control_mode: WaterTreatmentControlMode
