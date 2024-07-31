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


class WaterMakerTankStatus(Enum):
    FULL = 0
    EMPTY = 1


class WaterMakerStatus(Enum):
    PASSIVE = 0
    STANDBY = 1
    WATER_PRODUCTION = 2
    FLUSHING = 3


@dataclass(frozen=True, eq=True)
class WaterMakerState(ApplianceState):
    system_status: int
    tank_status: int


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

        system_status = (
            WaterMakerStatus.WATER_PRODUCTION.value
            if previous_state.tank_status == WaterMakerTankStatus.EMPTY.value
            else WaterMakerStatus.STANDBY.value
        )

        return WaterMakerState(system_status, previous_state.tank_status), {
            WaterMakerPort.DESALINATED_OUT: ThermalState(
                (
                    self.production_flow
                    if system_status == WaterMakerStatus.WATER_PRODUCTION.value
                    else 0
                ),
                inputs[WaterMakerPort.IN].temperature,
            )
        }
