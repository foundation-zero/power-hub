from dataclasses import dataclass
from energy_box_control.appliances import HeatPipes, HeatPipesPort
from energy_box_control.appliances.boiler import Boiler, BoilerPort
from energy_box_control.appliances.pcm import Pcm, PcmPort
from energy_box_control.appliances.yazaki import Yazaki, YazakiPort
from energy_box_control.sensors import (
    FromState,
    SensorContext,
    WeatherSensors,
    sensor,
    sensors,
)


@sensors()
class HeatPipesSensors(FromState):
    spec: HeatPipes
    flow: float = sensor(flow=True, from_port=HeatPipesPort.IN)
    ambient_temperature: float = sensor(from_weather=True)
    global_irradiance: float = sensor(from_weather=True)
    input_temperature: float = sensor(temperature=True, from_port=HeatPipesPort.IN)
    output_temperature: float = sensor(temperature=True, from_port=HeatPipesPort.OUT)

    @property
    def power(self):
        return (
            self.flow
            * (self.output_temperature - self.input_temperature)
            * self.spec.specific_heat_medium
        )


@sensors()
class PcmSensors(FromState):
    spec: Pcm
    charge_flow: float = sensor(flow=True, from_port=PcmPort.CHARGE_IN)
    charge_input_temperature: float = sensor(
        temperature=True, from_port=PcmPort.CHARGE_IN
    )
    charge_output_temperature: float = sensor(
        temperature=True, from_port=PcmPort.CHARGE_OUT
    )
    discharge_flow: float = sensor(flow=True, from_port=PcmPort.DISCHARGE_IN)
    discharge_input_temperature: float = sensor(
        temperature=True, from_port=PcmPort.DISCHARGE_IN
    )
    discharge_output_temperature: float = sensor(
        temperature=True, from_port=PcmPort.DISCHARGE_OUT
    )
    temperature: float

    @property
    def state_of_charge(self):
        return float(self.temperature > self.spec.phase_change_temperature)


@sensors()
class YazakiSensors(FromState):
    spec: Yazaki
    hot_flow: float = sensor(flow=True, from_port=YazakiPort.HOT_IN)
    hot_input_temperature: float = sensor(temperature=True, from_port=YazakiPort.HOT_IN)
    hot_output_temperature: float = sensor(
        temperature=True, from_port=YazakiPort.HOT_OUT
    )

    cooling_flow: float = sensor(flow=True, from_port=YazakiPort.COOLING_IN)
    cooling_input_temperature: float = sensor(
        temperature=True, from_port=YazakiPort.COOLING_IN
    )
    cooling_output_temperature: float = sensor(
        temperature=True, from_port=YazakiPort.COOLING_OUT
    )

    chilled_flow: float = sensor(flow=True, from_port=YazakiPort.CHILLED_IN)
    chilled_input_temperature: float = sensor(
        temperature=True, from_port=YazakiPort.CHILLED_IN
    )
    chilled_output_temperature: float = sensor(
        temperature=True, from_port=YazakiPort.CHILLED_OUT
    )

    @property
    def efficiency(self):
        return (
            self.hot_flow
            * (self.hot_input_temperature - self.hot_output_temperature)
            * self.spec.specific_heat_capacity_hot
        ) / (
            self.chilled_flow
            * (self.chilled_input_temperature - self.chilled_output_temperature)
            * self.spec.specific_heat_capacity_chilled
        )


@sensors()
class BoilerSensors(FromState):
    spec: Boiler
    temperature: float
    heat_exchange_flow: float = sensor(flow=True, from_port=BoilerPort.HEAT_EXCHANGE_IN)
    heat_exchange_in_temperature: float = sensor(
        temperature=True, from_port=BoilerPort.HEAT_EXCHANGE_IN
    )
    heat_exchange_out_temperature: float = sensor(
        temperature=True, from_port=BoilerPort.HEAT_EXCHANGE_OUT
    )

    fill_flow: float = sensor(flow=True, from_port=BoilerPort.HEAT_EXCHANGE_IN)
    fill_in_temperature: float = sensor(
        temperature=True, from_port=BoilerPort.HEAT_EXCHANGE_IN
    )
    fill_out_temperature: float = sensor(
        temperature=True, from_port=BoilerPort.HEAT_EXCHANGE_OUT
    )


@dataclass
class PowerHubSensors:

    @staticmethod
    def context(weather: WeatherSensors) -> "SensorContext[PowerHubSensors]":
        return SensorContext(PowerHubSensors, weather)

    heat_pipes: HeatPipesSensors
    hot_reservoir: BoilerSensors
    pcm: PcmSensors
    yazaki: YazakiSensors
