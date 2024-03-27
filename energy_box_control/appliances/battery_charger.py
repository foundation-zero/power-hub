from dataclasses import dataclass
from energy_box_control.appliances.base import ApplianceState


@dataclass(frozen=True, eq=True)
class BatteryChargerState(ApplianceState):
    state_of_charge: float
    charge_power: float
    discharge_power: float
