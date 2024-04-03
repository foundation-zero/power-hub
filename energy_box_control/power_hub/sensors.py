from dataclasses import dataclass
from energy_box_control.appliances import HeatPipes, HeatPipesPort
from energy_box_control.sensors import (
    FromState,
    SensorContext,
    WeatherSensors,
    sensor,
    sensors,
    Loop, # type: ignore because we're re-exporting it
)


@sensors()
class HeatPipesSensors(FromState):
    spec: HeatPipes
    flow: float = sensor(from_loop=True)
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


@dataclass
class PowerHubSensors:

    @staticmethod
    def context(weather: WeatherSensors) -> "SensorContext[PowerHubSensors]":
        return SensorContext(PowerHubSensors, weather)

    heat_pipes: HeatPipesSensors
