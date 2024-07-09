from dataclasses import dataclass
from energy_box_control.appliances.base import (
    ApplianceControl,
    WaterAppliance,
    ApplianceState,
    WaterState,
    Port,
)
from energy_box_control.time import ProcessTime
from energy_box_control.units import LiterPerSecond


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
class WaterMaker(WaterAppliance[WaterMakerState, None, WaterMakerPort]):
    efficiency: float
    pump_flow: LiterPerSecond

    def simulate(
        self,
        inputs: dict[WaterMakerPort, WaterState],
        previous_state: WaterMakerState,
        control: WaterMakerControl | None,
        simulation_time: ProcessTime,
    ) -> tuple[WaterMakerState, dict[WaterMakerPort, WaterState]]:

        on = control.on if control else previous_state.on

        return WaterMakerState(on), {
            WaterMakerPort.DESALINATED_OUT: WaterState(
                inputs[WaterMakerPort.IN].flow * self.efficiency if on else 0
            )
        }
