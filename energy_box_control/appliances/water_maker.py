from dataclasses import dataclass
from enum import Enum
from energy_box_control.appliances.base import (
    ApplianceState,
    Port,
    ThermalAppliance,
    ThermalState,
)
from energy_box_control.time import ProcessTime
from energy_box_control.units import LiterPerSecond


class WaterMakerStatus(Enum):
    PASSIVE = 0
    STANDBY = 1
    WATER_PRODUCTION = 2
    FLUSHING = 3


@dataclass(frozen=True, eq=True)
class WaterMakerState(ApplianceState):
    status: WaterMakerStatus
    tank_empty: bool = True


class WaterMakerPort(Port):
    DESALINATED_OUT = "desalinated_out"
    BRINE_OUT = "brine_out"
    IN = "in"


@dataclass(frozen=True, eq=True)
class WaterMaker(ThermalAppliance[WaterMakerState, None, WaterMakerPort]):
    production_flow: LiterPerSecond

    def simulate(
        self,
        inputs: dict[WaterMakerPort, ThermalState],
        previous_state: WaterMakerState,
        control: None,
        simulation_time: ProcessTime,
    ) -> tuple[WaterMakerState, dict[WaterMakerPort, ThermalState]]:

        return WaterMakerState(previous_state.status), {
            WaterMakerPort.DESALINATED_OUT: ThermalState(
                (
                    self.production_flow
                    if previous_state.status == WaterMakerStatus.WATER_PRODUCTION
                    else 0
                ),
                inputs[WaterMakerPort.IN].temperature,
            )
        }
