from dataclasses import dataclass

from energy_box_control.appliances.base import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    Port,
)


@dataclass(frozen=True, eq=True)
class ChillerState(ApplianceState):
    pass


class ChillerPort(Port):
    CHILLED_IN = "CHILLED_IN"
    CHILLED_OUT = "CHILLED_OUT"
    COOLING_IN = "COOLING_IN"
    COOLING_OUT = "COOLING_OUT"


class Chiller(Appliance[ChillerState, ApplianceControl, ChillerPort]):
    pass
