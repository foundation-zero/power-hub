from dataclasses import dataclass
from energy_box_control.appliances.base import (
    ApplianceState,
    Port,
    ThermalAppliance,
    ThermalState,
)
from energy_box_control.time import ProcessTime


@dataclass(frozen=True, eq=True)
class WaterMakerState(ApplianceState):
    on: bool


class WaterMakerPort(Port):
    DESALINATED_OUT = "desalinated_out"
    BRINE_OUT = "brine_out"
    IN = "in"


@dataclass(frozen=True, eq=True)
class WaterMaker(ThermalAppliance[WaterMakerState, None, WaterMakerPort]):
    efficiency: float

    def simulate(
        self,
        inputs: dict[WaterMakerPort, ThermalState],
        previous_state: WaterMakerState,
        control: None,
        simulation_time: ProcessTime,
    ) -> tuple[WaterMakerState, dict[WaterMakerPort, ThermalState]]:

        return WaterMakerState(previous_state.on), {
            WaterMakerPort.DESALINATED_OUT: ThermalState(
                (
                    inputs[WaterMakerPort.IN].flow * self.efficiency
                    if previous_state.on
                    else 0
                ),
                inputs[WaterMakerPort.IN].temperature,
            )
        }
