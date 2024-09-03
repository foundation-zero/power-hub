from dataclasses import dataclass
from energy_box_control.control.state_machines import Context, State


class CoolingSupplyControlMode(State):
    SUPPLY = "supply"
    NO_SUPPLY = "no_supply"


@dataclass
class CoolingSupplyControlState:
    context: Context
    control_mode: CoolingSupplyControlMode
