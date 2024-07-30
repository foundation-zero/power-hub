from dataclasses import dataclass
from energy_box_control.appliances.base import (
    ApplianceControl,
    ApplianceState,
    Port,
    ThermalAppliance,
    ThermalState,
)
from energy_box_control.time import ProcessTime


@dataclass(frozen=True, eq=True)
class WaterMakerState(ApplianceState):
    on: bool


@dataclass(frozen=True, eq=True)
class WaterMakerControl(ApplianceControl):
    on: bool


class WaterMakerPort(Port):
    DESALINATED_OUT = "desalinated_out"
    BRINE_OUT = "brine_out"
    IN = "in"


@dataclass(frozen=True, eq=True)
class WaterMaker(ThermalAppliance[WaterMakerState, WaterMakerControl, WaterMakerPort]):
    efficiency: float

    def simulate(
        self,
        inputs: dict[WaterMakerPort, ThermalState],
        previous_state: WaterMakerState,
        control: WaterMakerControl,
        simulation_time: ProcessTime,
    ) -> tuple[WaterMakerState, dict[WaterMakerPort, ThermalState]]:

        on = control.on if control else previous_state.on

        return WaterMakerState(on), {
            WaterMakerPort.DESALINATED_OUT: ThermalState(
                inputs[WaterMakerPort.IN].flow * self.efficiency if on else 0,
                inputs[WaterMakerPort.IN].temperature,
            )
        }
