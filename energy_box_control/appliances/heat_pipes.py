from dataclasses import dataclass
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    Port,
)


@dataclass(frozen=True, eq=True)
class HeatPipesState(ApplianceState):
    pass


class HeatPipesPort(Port):
    IN = "IN"
    OUT = "OUT"


class HeatPipes(Appliance[HeatPipesState, ApplianceControl, HeatPipesPort]):
    pass
