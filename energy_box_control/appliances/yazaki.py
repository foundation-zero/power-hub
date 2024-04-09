from dataclasses import dataclass
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    Celsius,
    ConnectionState,
    JoulesPerLiterKelvin,
    KiloWatts,
    Port,
    Seconds,
    Watts,
)

from scipy.interpolate import RegularGridInterpolator
import logging

LOGGER = logging.getLogger(__name__)


class YazakiPort(Port):
    HOT_IN = "hot_in"
    HOT_OUT = "hot_out"
    CHILLED_IN = "chilled_in"
    CHILLED_OUT = "chilled_out"
    COOLING_IN = "cooling_in"
    COOLING_OUT = "cooling_out"


@dataclass(frozen=True, eq=True)
class YazakiState(ApplianceState):
    pass


@dataclass(frozen=True, eq=True)
class YazakiControl(ApplianceControl):
    pass


_ref_temps_cooling: list[Celsius] = [27, 29.5, 31, 32]
_ref_temps_hot: list[Celsius] = [70, 80, 87, 95]
_cooling_capacity_values: list[list[KiloWatts]] = [
    [10.0, 16.5, 21.0, 22.5],
    [7.0, 14.0, 18.0, 21],
    [6.0, 13.0, 17.5, 19.5],
    [4.0, 10.0, 15.0, 16],
]

_heat_input_values: list[list[KiloWatts]] = [
    [12.5, 10.0, 9.0, 7.0],
    [21.0, 18.0, 17.0, 14.0],
    [30.0, 26.0, 25.0, 22.5],
    [37.0, 34.0, 32.0, 27.5],
]

_cooling_capacity_interpolator = RegularGridInterpolator(
    (_ref_temps_cooling, _ref_temps_hot),
    _cooling_capacity_values,
    bounds_error=False,
    fill_value=None,
)

_heat_input_interpolator = RegularGridInterpolator(
    (_ref_temps_cooling, _ref_temps_hot),
    _heat_input_values,
    bounds_error=False,
    fill_value=None,
)


@dataclass(frozen=True, eq=True)
class Yazaki(Appliance[YazakiState, YazakiControl, YazakiPort]):
    specific_heat_capacity_hot: JoulesPerLiterKelvin
    specific_heat_capacity_cooling: JoulesPerLiterKelvin
    specific_heat_capacity_chilled: JoulesPerLiterKelvin

    def simulate(
        self,
        inputs: dict[YazakiPort, ConnectionState],
        previous_state: YazakiState,
        control: YazakiControl,
        step_size: Seconds,
    ) -> tuple[YazakiState, dict[YazakiPort, ConnectionState]]:

        hot_in = inputs[YazakiPort.HOT_IN]
        cooling_in = inputs[YazakiPort.COOLING_IN]
        chilled_in = inputs[YazakiPort.CHILLED_IN]

        # Hot water: assuming flow of 1.2 l/s should lead to heat input of 25.1 kW at inlet temp of 88 and outlet temp of 83
        # Cooling water: assuming cooling water flow of 2.55 l/s should lead to heat rejection of 42.7 kW at inlet temp of 31 and outlet temp of 35
        # Chilled water: assuming chilled water flow of 0.77 l/s should lead to cooling capacity of 17.6 kW at inlet temp of 17.6 and outlet temp of 12.5

        # Here we will assume that the flows are close to optimal. We then use the lookup table (page 5,6 in https://drive.google.com/file/d/1-zn3pD88ZF3Z0rSOXOneaLs78x7psXdR/view?usp=sharing) to get cooling capacity from cooling water temp and hot water temp

        if not min(_ref_temps_hot) < hot_in.temperature < max(_ref_temps_hot):
            logging.warning(
                f"Hot in temperature of {hot_in.temperature} outside of hot reference temperatures. All values are passed through without change"
            )
            hot_temp_out = hot_in.temperature
            cooling_temp_out = cooling_in.temperature
            chilled_temp_out = chilled_in.temperature

        else:
            cooling_capacity: Watts = 1000 * float(
                _cooling_capacity_interpolator(
                    (cooling_in.temperature, hot_in.temperature)
                )
            )
            heat_input: Watts = 1000 * float(
                _heat_input_interpolator((cooling_in.temperature, hot_in.temperature))
            )

            hot_temp_out = hot_in.temperature - heat_input / (
                hot_in.flow * step_size * self.specific_heat_capacity_hot
            )

            cooling_temp_out = cooling_in.temperature + (
                heat_input + cooling_capacity
            ) / (cooling_in.flow * step_size * self.specific_heat_capacity_cooling)

            chilled_temp_out = chilled_in.temperature - cooling_capacity / (
                chilled_in.flow * step_size * self.specific_heat_capacity_chilled
            )

        return YazakiState(), {
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
