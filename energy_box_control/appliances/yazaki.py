from dataclasses import dataclass
from typing import Tuple
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    ConnectionState,
    Port,
)


class YazakiPort(Port):
    HOT_IN = "HOT_IN"
    HOT_OUT = "HOT_OUT"
    CHILLED_IN = "CHILLED_IN"
    CHILLED_OUT = "CHILLED_OUT"
    COOLING_IN = "COOLING_IN"
    COOLING_OUT = "COOLING_OUT"


@dataclass(frozen=True, eq=True)
class YazakiState(ApplianceState):
    pass


@dataclass(frozen=True, eq=True)
class YazakiControl(ApplianceControl):
    pass


@dataclass(frozen=True, eq=True)
class Yazaki(Appliance[YazakiState, YazakiControl, YazakiPort]):
    cooling_capacity: float
    specific_heat_capacity_hot: float
    specific_heat_capacity_cold: float
    COP: float

    def simulate(
        self,
        inputs: dict[YazakiPort, ConnectionState],
        previous_state: YazakiState,
        control: YazakiControl,
    ) -> Tuple[YazakiState, dict[YazakiPort, ConnectionState]]:

        hot_in = inputs[YazakiPort.HOT_IN]
        
        ##Some lookup table, e.g. https://drive.google.com/file/d/1-zn3pD88ZF3Z0rSOXOneaLs78x7psXdR/view?usp=sharing
        hot_power = hot_in.flow * hot_in.temperature * self.specific_heat_capacity_hot
        cooling_power = self.COP * hot_power

        chilled_temp = inputs[YazakiPort.CHILLED_IN].temperature - cooling_power / (
            inputs[YazakiPort.CHILLED_IN].flow * self.specific_heat_capacity_cold
        )

        return YazakiState(), {
            YazakiPort.CHILLED_OUT: ConnectionState(
                inputs[YazakiPort.CHILLED_IN].flow, chilled_temp
            )
        }
