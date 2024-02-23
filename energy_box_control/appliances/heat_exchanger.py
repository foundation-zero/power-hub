from dataclasses import dataclass
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    Port,
)


@dataclass(eq=True, frozen=True)
class HeatExchangerState(ApplianceState):
    pass


class HeatExchangerPort(Port):
    A_IN = "A_IN"
    A_OUT = "A_OUT"
    B_IN = "B_IN"
    B_OUT = "B_OUT"


class HeatExchanger(Appliance[HeatExchangerState, ApplianceControl, HeatExchangerPort]):
    pass
