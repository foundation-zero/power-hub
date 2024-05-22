from typing import TypedDict
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceState,
    Port,
    ThermalState,
    WaterState,
)
from energy_box_control.time import ProcessTime


class IgnoreTemperaturePort(Port):
    INPUT = "input"
    OUTPUT = "output"


class IgnoreTemperatureInput(TypedDict):
    input: ThermalState


class IgnoreTemperatureOutput(TypedDict):
    output: WaterState


class IgnoreTemperature(
    Appliance[
        ApplianceState,
        None,
        IgnoreTemperaturePort,
        IgnoreTemperatureInput,
        IgnoreTemperatureOutput,
    ]
):

    def simulate(
        self,
        inputs: IgnoreTemperatureInput,
        previous_state: ApplianceState,
        control: None,
        simulation_time: ProcessTime,
    ) -> tuple[ApplianceState, IgnoreTemperatureOutput]:
        return ApplianceState(), {
            IgnoreTemperaturePort.OUTPUT.value: WaterState(inputs["input"].flow)
        }
