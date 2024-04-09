from dataclasses import dataclass
from energy_box_control.appliances import HeatPipes, HeatPipesPort
from energy_box_control.appliances.base import (
    Appliance,
    Celsius,
    LitersPerSecond,
    Watts,
    WattsPerMeterSquared,
)
from energy_box_control.appliances.boiler import Boiler, BoilerPort
from energy_box_control.appliances.chiller import Chiller, ChillerPort
from energy_box_control.appliances.pcm import Pcm, PcmPort
from energy_box_control.appliances.valve import Valve
from energy_box_control.appliances.yazaki import Yazaki, YazakiPort
from energy_box_control.sensors import (
    FromState,
    SensorContext,
    SensorType,
    WeatherSensors,
    sensor,
    sensors,
)


@sensors()
class HeatPipesSensors(FromState):
    spec: HeatPipes
    flow: LitersPerSecond = sensor(type=SensorType.FLOW, from_port=HeatPipesPort.IN)
    ambient_temperature: Celsius = sensor(from_weather=True)
    global_irradiance: WattsPerMeterSquared = sensor(from_weather=True)
    input_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=HeatPipesPort.IN
    )
    output_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=HeatPipesPort.OUT
    )

    @property
    def power(self) -> Watts:
        return (
            self.flow
            * (self.output_temperature - self.input_temperature)
            * self.spec.specific_heat_medium
        )


@sensors()
class PcmSensors(FromState):
    spec: Pcm
    charge_flow: LitersPerSecond = sensor(
        type=SensorType.FLOW, from_port=PcmPort.CHARGE_IN
    )
    charge_input_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=PcmPort.CHARGE_IN
    )
    charge_output_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=PcmPort.CHARGE_OUT
    )
    discharge_flow: LitersPerSecond = sensor(
        type=SensorType.FLOW, from_port=PcmPort.DISCHARGE_IN
    )
    discharge_input_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=PcmPort.DISCHARGE_IN
    )
    discharge_output_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=PcmPort.DISCHARGE_OUT
    )
    temperature: Celsius

    @property
    def state_of_charge(self) -> float:
        return float(self.temperature > self.spec.phase_change_temperature)


@sensors()
class YazakiSensors(FromState):
    spec: Yazaki
    hot_flow: LitersPerSecond = sensor(
        type=SensorType.FLOW, from_port=YazakiPort.HOT_IN
    )
    hot_input_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=YazakiPort.HOT_IN
    )
    hot_output_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=YazakiPort.HOT_OUT
    )

    cooling_flow: LitersPerSecond = sensor(
        type=SensorType.FLOW, from_port=YazakiPort.COOLING_IN
    )
    cooling_input_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=YazakiPort.COOLING_IN
    )
    cooling_output_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=YazakiPort.COOLING_OUT
    )

    chilled_flow: LitersPerSecond = sensor(
        type=SensorType.FLOW, from_port=YazakiPort.CHILLED_IN
    )
    chilled_input_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=YazakiPort.CHILLED_IN
    )
    chilled_output_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=YazakiPort.CHILLED_OUT
    )

    @property
    def efficiency(self) -> float:
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
    temperature: Celsius
    heat_exchange_flow: LitersPerSecond = sensor(
        type=SensorType.FLOW, from_port=BoilerPort.HEAT_EXCHANGE_IN
    )
    heat_exchange_in_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=BoilerPort.HEAT_EXCHANGE_IN
    )
    heat_exchange_out_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=BoilerPort.HEAT_EXCHANGE_OUT
    )

    fill_flow: LitersPerSecond = sensor(
        type=SensorType.FLOW, from_port=BoilerPort.FILL_IN
    )
    fill_in_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=BoilerPort.FILL_IN
    )
    fill_out_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=BoilerPort.FILL_OUT
    )


@sensors()
class ChillerSensors(FromState):
    spec: Chiller
    cooling_flow: LitersPerSecond = sensor(
        type=SensorType.FLOW, from_port=ChillerPort.COOLING_IN
    )
    cooling_input_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=ChillerPort.COOLING_IN
    )
    cooling_output_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=ChillerPort.COOLING_OUT
    )

    chilled_flow: LitersPerSecond = sensor(
        type=SensorType.FLOW, from_port=ChillerPort.CHILLED_IN
    )
    chilled_input_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=ChillerPort.CHILLED_IN
    )
    chilled_output_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=ChillerPort.CHILLED_OUT
    )


@sensors()
class ValveSensors(FromState):
    spec: Valve
    position: float


@dataclass
class PowerHubSensors:
    heat_pipes: HeatPipesSensors
    heat_pipes_valve: ValveSensors
    hot_reservoir_pcm_valve: ValveSensors
    hot_reservoir: BoilerSensors
    pcm: PcmSensors
    yazaki_hot_bypass_valve: ValveSensors
    yazaki: YazakiSensors
    chiller: ChillerSensors
    chiller_switch_valve: ValveSensors
    cold_reservoir: BoilerSensors
    yazaki_waste_bypass_valve: ValveSensors
    preheat_bypass_valve: ValveSensors
    preheat_reservoir: BoilerSensors
    waste_switch_valve: ValveSensors
    chiller_waste_bypass_valve: ValveSensors

    @staticmethod
    def context(weather: WeatherSensors) -> "SensorContext[PowerHubSensors]":
        return SensorContext(PowerHubSensors, weather)


SensorName = str
SensorValue = float | Celsius | LitersPerSecond | WattsPerMeterSquared


def get_sensor_values(
    sensor_name: SensorName, sensors: PowerHubSensors
) -> dict[SensorName, SensorValue]:
    return {
        sensor_item_name: sensor_item_value
        for sensor_item_name, sensor_item_value in getattr(
            sensors, sensor_name
        ).__dict__.items()
        if not issubclass(sensor_item_value.__class__, Appliance)
    }
