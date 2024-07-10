from dataclasses import dataclass
from energy_box_control.appliances.base import (
    ThermalAppliance,
    ApplianceControl,
    ApplianceState,
    ThermalState,
    Port,
)
from energy_box_control.time import ProcessTime


@dataclass(frozen=True, eq=True)
class RH33State(ApplianceState):
    pass


@dataclass(frozen=True, eq=True)
class RH33Control(ApplianceControl):
    pass


class RH33Port(Port):
    IN = "in"
    OUT = "out"


@dataclass(eq=True, frozen=True)
class RH33(ThermalAppliance[RH33State, RH33Control, RH33Port]):

    def simulate(
        self,
        inputs: dict[RH33Port, ThermalState],
        previous_state: RH33State,
        control: RH33Control | None,
        simulation_time: ProcessTime,
    ) -> tuple[RH33State, dict[RH33Port, ThermalState]]:

        
        return RH33State(), {
            RH33Port.OUT: ThermalState(inputs[RH33Port.IN].flow, inputs[RH33Port.IN].temperature)
        }
        

