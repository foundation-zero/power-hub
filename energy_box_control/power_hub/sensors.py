from dataclasses import dataclass
from energy_box_control.appliances import HeatPipes, HeatPipesPort
from energy_box_control.units import (
    Celsius,
    JoulePerLiterKelvin,
    LiterPerSecond,
    Watt,
    WattPerMeterSquared,
)
from energy_box_control.appliances.boiler import Boiler, BoilerPort
from energy_box_control.appliances.chiller import Chiller, ChillerPort
from energy_box_control.appliances.pcm import Pcm, PcmPort
from energy_box_control.appliances.valve import Valve
from energy_box_control.appliances.yazaki import Yazaki, YazakiPort
from energy_box_control.sensors import (
    FromState,
    SensorType,
    sensor,
    sensors,
    NetworkSensors,
)


@sensors()
class HeatPipesSensors(FromState):
    spec: HeatPipes
    flow: LiterPerSecond = sensor(type=SensorType.FLOW, from_port=HeatPipesPort.IN)
    ambient_temperature: Celsius = sensor(from_weather=True)
    global_irradiance: WattPerMeterSquared = sensor(from_weather=True)
    input_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=HeatPipesPort.IN
    )
    output_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=HeatPipesPort.OUT
    )

    @property
    def power(self) -> Watt:
        return (
            self.flow
            * (self.output_temperature - self.input_temperature)
            * self.spec.specific_heat_medium
        )


@sensors()
class PcmSensors(FromState):
    spec: Pcm
    charge_flow: LiterPerSecond = sensor(
        type=SensorType.FLOW, from_port=PcmPort.CHARGE_IN
    )
    charge_input_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=PcmPort.CHARGE_IN
    )
    charge_output_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=PcmPort.CHARGE_OUT
    )
    discharge_flow: LiterPerSecond = sensor(
        type=SensorType.FLOW, from_port=PcmPort.DISCHARGE_IN
    )
    discharge_input_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=PcmPort.DISCHARGE_IN
    )
    discharge_output_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=PcmPort.DISCHARGE_OUT
    )

    temperature: Celsius


@sensors()
class YazakiSensors(FromState):
    spec: Yazaki
    hot_flow: LiterPerSecond = sensor(type=SensorType.FLOW, from_port=YazakiPort.HOT_IN)
    hot_input_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=YazakiPort.HOT_IN
    )
    hot_output_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=YazakiPort.HOT_OUT
    )

    cooling_flow: LiterPerSecond = sensor(
        type=SensorType.FLOW, from_port=YazakiPort.COOLING_IN
    )
    cooling_input_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=YazakiPort.COOLING_IN
    )
    cooling_output_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=YazakiPort.COOLING_OUT
    )

    chilled_flow: LiterPerSecond = sensor(
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
        if self.chilled_input_temperature - self.chilled_output_temperature == 0:
            return 0
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
    heat_exchange_in_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=BoilerPort.HEAT_EXCHANGE_IN
    )
    heat_exchange_out_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=BoilerPort.HEAT_EXCHANGE_OUT
    )
    fill_in_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=BoilerPort.FILL_IN
    )
    fill_out_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=BoilerPort.FILL_OUT
    )


@sensors()
class ValveSensors(FromState):
    spec: Valve
    position: float


def derive_flow(
    power: Watt,
    valve: ValveSensors,
    temperature_in: Celsius,
    temperature_out: Celsius,
    specific_heat_capacity: JoulePerLiterKelvin,
    open_valve_state: float,
) -> LiterPerSecond:
    if not valve.position == open_valve_state:
        return 0
    return power / (abs(temperature_in - temperature_out) * specific_heat_capacity)


@sensors()
class HotReservoirSensors(BoilerSensors):
    fill_flow: LiterPerSecond = sensor(
        type=SensorType.FLOW, from_port=BoilerPort.FILL_IN
    )
    heat_pipes: HeatPipesSensors
    hot_reservoir_pcm_valve: ValveSensors

    @property
    def heat_exchange_flow(self) -> LiterPerSecond:
        return derive_flow(
            self.heat_pipes.power,
            self.hot_reservoir_pcm_valve,
            self.heat_exchange_in_temperature,
            self.heat_exchange_out_temperature,
            self.spec.specific_heat_capacity_exchange,
            1,
        )


@sensors()
class ChillerSensors(FromState):
    spec: Chiller
    cooling_flow: LiterPerSecond = sensor(
        type=SensorType.FLOW, from_port=ChillerPort.COOLING_IN
    )
    cooling_input_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=ChillerPort.COOLING_IN
    )
    cooling_output_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=ChillerPort.COOLING_OUT
    )

    chilled_flow: LiterPerSecond = sensor(
        type=SensorType.FLOW, from_port=ChillerPort.CHILLED_IN
    )
    chilled_input_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=ChillerPort.CHILLED_IN
    )
    chilled_output_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=ChillerPort.CHILLED_OUT
    )


@dataclass
class PowerHubSensors(NetworkSensors):
    heat_pipes: HeatPipesSensors
    heat_pipes_valve: ValveSensors
    hot_reservoir_pcm_valve: ValveSensors
    hot_reservoir: HotReservoirSensors
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


SensorName = str
SensorValue = float | Celsius | LiterPerSecond | WattPerMeterSquared


def get_sensor_values(
    sensor_name: SensorName, sensors: PowerHubSensors
) -> dict[SensorName, SensorValue]:
    attr = getattr(sensors, sensor_name)

    return {
        field: getattr(attr, field)
        for field in dir(attr)
        if field[0] != "_" and (type(getattr(attr, field)) in [float, int, bool])
    }
