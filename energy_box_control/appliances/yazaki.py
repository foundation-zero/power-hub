from dataclasses import dataclass
from typing import Tuple
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    ConnectionState,
    Port,
)

from scipy.interpolate import RegularGridInterpolator


class YazakiPort(Port):
    HOT_IN = "HOT_IN"
    HOT_OUT = "HOT_OUT"
    CHILLED_IN = "CHILLED_IN"
    CHILLED_OUT = "CHILLED_OUT"
    COOLING_IN = "COOLING_IN"
    COOLING_OUT = "COOLING_OUT"


@dataclass(frozen=True, eq=True)
class YazakiState(ApplianceState):
    efficiency: float


@dataclass(frozen=True, eq=True)
class YazakiControl(ApplianceControl):
    pass


@dataclass(frozen=True, eq=True)
class Yazaki(Appliance[YazakiState, YazakiControl, YazakiPort]):
    specific_heat_capacity_hot: float
    specific_heat_capacity_cooling: float
    specific_heat_capacity_chilled: float

    def simulate(
        self,
        inputs: dict[YazakiPort, ConnectionState],
        previous_state: YazakiState,
        control: YazakiControl,
    ) -> Tuple[YazakiState, dict[YazakiPort, ConnectionState]]:

        hot_in = inputs[YazakiPort.HOT_IN]
        cooling_in = inputs[YazakiPort.COOLING_IN]
        chilled_in = inputs[YazakiPort.CHILLED_IN]

        # Hot water: assuming flow of 1.2 l/s should lead to heat input of 25.1 kW at inlet temp of 88 and outlet temp of 83
        # Cooling water: assuming cooling water flow of 2.55 l/s should lead to heat rejection of 42.7 kW at inlet temp of 31 and outlet temp of 35
        # Chilled water: assuming chilled water flow of 0.77 l/s should lead to cooling capacity of 17.6 kW at inlet temp of 17.6 and outlet temp of 12.5

        # Here we will assume that the flows are close to optimal. We then use the lookup table (page 5,6 in https://drive.google.com/file/d/1-zn3pD88ZF3Z0rSOXOneaLs78x7psXdR/view?usp=sharing) to get cooling capacity from cooling water temp and hot water temp

        ref_temps_cooling: list[float] = [27, 29.5, 31, 32]
        ref_temps_heat: list[float] = [70, 80, 87, 95]
        cooling_capacity_values: list[list[float]] = [
            [10.0, 16.5, 21.0, 22.5],
            [7.0, 14.0, 18.0, 21],
            [6.0, 13.0, 17.5, 19.5],
            [4.0, 10.0, 15.0, 16],
        ]

        heat_input_values: list[list[float]] = [
            [12.5, 10, 9, 7],
            [21, 18, 17, 14],
            [30, 26, 25, 22.5],
            [37, 34, 32, 27.5],
        ]

        cooling_capacity = 1000 * float(
            RegularGridInterpolator(
                (ref_temps_cooling, ref_temps_heat), cooling_capacity_values
            )((cooling_in.temperature, hot_in.temperature))
        )
        heat_input = 1000 * float(
            RegularGridInterpolator(
                (ref_temps_cooling, ref_temps_heat), heat_input_values
            )((cooling_in.temperature, hot_in.temperature))
        )

        hot_temp_out = hot_in.temperature - heat_input / (
            hot_in.flow * self.specific_heat_capacity_hot
        )

        cooling_temp_out = cooling_in.temperature + (heat_input + cooling_capacity) / (
            cooling_in.flow * self.specific_heat_capacity_cooling
        )

        chilled_temp_out = chilled_in.temperature - cooling_capacity / (
            chilled_in.flow * self.specific_heat_capacity_chilled
        )

        efficiency = heat_input / cooling_capacity

        return YazakiState(efficiency), {
            YazakiPort.HOT_OUT: ConnectionState(
                inputs[YazakiPort.HOT_IN].flow, hot_temp_out
            ),
            YazakiPort.COOLING_OUT: ConnectionState(
                inputs[YazakiPort.COOLING_IN].flow, cooling_temp_out
            ),
            YazakiPort.CHILLED_OUT: ConnectionState(
                inputs[YazakiPort.CHILLED_IN].flow, chilled_temp_out
            ),
        }
