from dataclasses import dataclass
from energy_box_control.control.state_machines import Context, State


class CoolingSupplyControlMode(State):
    DISABLED = "disabled"
    ENABLED_NO_SUPPLY = "enabled_no_supply"
    SUPPLY = "supply"


@dataclass
class CoolingSupplyControlState:
    context: Context
    control_mode: CoolingSupplyControlMode
