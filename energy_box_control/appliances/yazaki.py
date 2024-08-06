from dataclasses import dataclass
from energy_box_control.appliances.base import (
    ThermalAppliance,
    ApplianceControl,
    ApplianceState,
    ThermalState,
    Port,
)

import logging

from energy_box_control.time import ProcessTime
from energy_box_control.units import (
    Celsius,
    JoulePerLiterKelvin,
    KiloWatt,
    Watt,
)

LOGGER = logging.getLogger(__name__)

DEFAULT_PRESSURE = 2.5


class YazakiPort(Port):
    HOT_IN = "hot_in"
    HOT_OUT = "hot_out"
    CHILLED_IN = "chilled_in"
    CHILLED_OUT = "chilled_out"
    COOLING_IN = "cooling_in"
    COOLING_OUT = "cooling_out"


@dataclass(frozen=True, eq=True)
class YazakiState(ApplianceState):
    operation_status: bool = False
    error_status: bool = False


@dataclass(frozen=True, eq=True)
class YazakiControl(ApplianceControl):
    on: bool


@dataclass(frozen=True, eq=True)
class Yazaki(ThermalAppliance[YazakiState, YazakiControl, YazakiPort]):
    specific_heat_capacity_hot: JoulePerLiterKelvin
    specific_heat_capacity_cooling: JoulePerLiterKelvin
    specific_heat_capacity_chilled: JoulePerLiterKelvin

    def simulate(
        self,
        inputs: dict[YazakiPort, ThermalState],
        previous_state: YazakiState,
        control: YazakiControl,
        simulation_time: ProcessTime,
    ) -> tuple[YazakiState, dict[YazakiPort, ThermalState]]:
        if not control.on:
            return YazakiState(), {
                YazakiPort.HOT_OUT: inputs[YazakiPort.HOT_IN],
                YazakiPort.COOLING_OUT: inputs[YazakiPort.COOLING_IN],
                YazakiPort.CHILLED_OUT: inputs[YazakiPort.CHILLED_IN],
            }

        def _refs():
            from scipy.interpolate import RegularGridInterpolator

            @dataclass(frozen=True)
            class YazakiRefs:
                cooling_temps: list[Celsius]
                hot_temps: list[Celsius]
                cooling_capacity: list[list[KiloWatt]]
                heat_input: list[list[KiloWatt]]
                cooling_capacity_interpolator: RegularGridInterpolator
                heat_input_interpolator: RegularGridInterpolator

            _ref_temps_cooling: list[Celsius] = [27, 29.5, 31, 32]
            _ref_temps_hot: list[Celsius] = [70, 80, 87, 95]
            _cooling_capacity_values: list[list[KiloWatt]] = [
                [10.0, 16.5, 21.0, 22.5],
                [7.0, 14.0, 18.0, 21],
                [6.0, 13.0, 17.5, 19.5],
                [4.0, 10.0, 15.0, 16],
            ]

            _heat_input_values: list[list[KiloWatt]] = [
                [12.5, 21.0, 30.0, 37.0],
                [10.0, 18.0, 26.0, 34.0],
                [9.0, 17.0, 25.0, 32.0],
                [7.0, 14.0, 22.5, 27.5],
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

            return YazakiRefs(
                _ref_temps_cooling,
                _ref_temps_hot,
                _cooling_capacity_values,
                _heat_input_values,
                _cooling_capacity_interpolator,
                _heat_input_interpolator,
            )

        hot_in = inputs[YazakiPort.HOT_IN]
        cooling_in = inputs[YazakiPort.COOLING_IN]
        chilled_in = inputs[YazakiPort.CHILLED_IN]

        # Hot water: assuming flow of 1.2 l/s should lead to heat input of 25.1 kW at inlet temp of 88 and outlet temp of 83
        # Cooling water: assuming cooling water flow of 2.55 l/s should lead to heat rejection of 42.7 kW at inlet temp of 31 and outlet temp of 35
        # Chilled water: assuming chilled water flow of 0.77 l/s should lead to cooling capacity of 17.6 kW at inlet temp of 17.6 and outlet temp of 12.5

        # Here we will assume that the flows are close to optimal. We then use the lookup table (page 5,6 in https://drive.google.com/file/d/1-zn3pD88ZF3Z0rSOXOneaLs78x7psXdR/view?usp=sharing) to get cooling capacity from cooling water temp and hot water temp
        refs = _refs()
        if not min(refs.hot_temps) < hot_in.temperature < max(refs.hot_temps):
            logging.warning(
                f"Hot in temperature of {hot_in.temperature} outside of hot reference temperatures. All values are passed through without change"
            )
            hot_temp_out = hot_in.temperature
            cooling_temp_out = cooling_in.temperature
            chilled_temp_out = chilled_in.temperature

        else:
            cooling_capacity: Watt = 1000 * float(
                refs.cooling_capacity_interpolator(
                    (cooling_in.temperature, hot_in.temperature)
                )
            )
            heat_input: Watt = 1000 * float(
                refs.heat_input_interpolator(
                    (cooling_in.temperature, hot_in.temperature)
                )
            )

            if cooling_capacity <= 0 or heat_input <= 0:
                logging.warning(
                    f"No cooling capacity or heat input resulting from a cooling in temperature of {cooling_in.temperature} and hot in temperature of {hot_in.temperature} that are far outside the reference values"
                )
                cooling_capacity = 0
                heat_input = 0

            hot_temp_out = (
                hot_in.temperature
                - heat_input / (hot_in.flow * self.specific_heat_capacity_hot)
                if hot_in.flow > 0
                else hot_in.temperature
            )

            cooling_temp_out = (
                cooling_in.temperature
                + (heat_input + cooling_capacity)
                / (cooling_in.flow * self.specific_heat_capacity_cooling)
                if cooling_in.flow > 0
                else cooling_in.temperature
            )

            chilled_temp_out = (
                chilled_in.temperature
                - cooling_capacity
                / (chilled_in.flow * self.specific_heat_capacity_chilled)
                if chilled_in.flow > 0
                else chilled_in.temperature
            )

        return YazakiState(operation_status=True), {
            YazakiPort.HOT_OUT: ThermalState(
                inputs[YazakiPort.HOT_IN].flow, hot_temp_out
            ),
            YazakiPort.COOLING_OUT: ThermalState(
                inputs[YazakiPort.COOLING_IN].flow, cooling_temp_out
            ),
            YazakiPort.CHILLED_OUT: ThermalState(
                inputs[YazakiPort.CHILLED_IN].flow, chilled_temp_out
            ),
        }
