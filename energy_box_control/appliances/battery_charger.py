from dataclasses import dataclass
from energy_box_control.appliances.base import ApplianceState
from energy_box_control.units import Watt


@dataclass(frozen=True, eq=True)
class BatteryChargerState(ApplianceState):
    state_of_charge: float
    charge_power: Watt
    discharge_power: Watt
