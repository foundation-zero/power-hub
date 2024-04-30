from dataclasses import dataclass
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceState,
    ConnectionState,
    Port,
)
from energy_box_control.time import ProcessTime


@dataclass(frozen=True, eq=True)
class WaterMakerState(ApplianceState):
    pass


class WaterMakerPort(Port):
    DESALINATED_OUT = "desalinated_out"
    BRINE_OUT = "brine_out"
    IN = "in"


@dataclass(frozen=True, eq=True)
class WaterMaker(Appliance[WaterMakerState, None, WaterMakerPort]):
    efficiency: float

    def simulate(
        self,
        inputs: dict[WaterMakerPort, ConnectionState],
        previous_state: WaterMakerState,
        control: None,
        simulation_time: ProcessTime,
    ) -> tuple[WaterMakerState, dict[WaterMakerPort, ConnectionState]]:
        return WaterMakerState(), {
            WaterMakerPort.DESALINATED_OUT: ConnectionState(
                inputs[WaterMakerPort.IN].flow * self.efficiency,
                inputs[WaterMakerPort.IN].temperature,
            )
        }
