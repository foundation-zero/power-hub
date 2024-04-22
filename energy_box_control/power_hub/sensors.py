from dataclasses import dataclass
from energy_box_control.appliances import HeatPipes, HeatPipesPort
from energy_box_control.appliances.heat_exchanger import (
    HeatExchanger,
    HeatExchangerPort,
)

from energy_box_control.appliances.mix import MixPort

from energy_box_control.power_hub.power_hub_components import (
    CHILLER_SWITCH_VALVE_CHILLER_POSITION,
    CHILLER_SWITCH_VALVE_YAZAKI_POSITION,
    HOT_RESERVOIR_PCM_VALVE_PCM_POSITION,
    HOT_RESERVOIR_PCM_VALVE_RESERVOIR_POSITION,
    WASTE_SWITCH_VALVE_CHILLER_POSITION,
    WASTE_SWITCH_VALVE_YAZAKI_POSITION,
)
from energy_box_control.units import (
    Celsius,
    LiterPerSecond,
    Watt,
    WattPerMeterSquared,
)
from energy_box_control.appliances.boiler import Boiler, BoilerPort
from energy_box_control.appliances.chiller import Chiller
from energy_box_control.appliances.pcm import Pcm, PcmPort
from energy_box_control.appliances.valve import Valve, ValvePort
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
    flow: LiterPerSecond = sensor(
        technical_name="FS-1001", type=SensorType.FLOW, from_port=HeatPipesPort.IN
    )
    input_temperature: Celsius = sensor(
        technical_name="TS-1001",
        type=SensorType.TEMPERATURE,
        from_port=HeatPipesPort.IN,
    )
    output_temperature: Celsius = sensor(
        technical_name="TS-1002",
        type=SensorType.TEMPERATURE,
        from_port=HeatPipesPort.OUT,
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
    temperature: Celsius = sensor(technical_name="TS-1007")
    hot_switch_valve: "HotSwitchSensors"
    hot_mix: "HotMixSensors"

    discharge_input_temperature: Celsius = sensor(
        technical_name="TS-1030",
        type=SensorType.TEMPERATURE,
        from_port=PcmPort.DISCHARGE_IN,
    )
    discharge_output_temperature: Celsius = sensor(
        technical_name="TS-1031",
        type=SensorType.TEMPERATURE,
        from_port=PcmPort.DISCHARGE_OUT,
    )

    discharge_flow: LiterPerSecond = sensor(
        technical_name="FS-1003", type=SensorType.FLOW, from_port=PcmPort.DISCHARGE_IN
    )

    @property
    def charge_flow(self) -> LiterPerSecond:
        return (
            self.hot_switch_valve.flow
            if self.hot_switch_valve.position == HOT_RESERVOIR_PCM_VALVE_PCM_POSITION
            else 0
        )

    @property
    def charge_input_temperature(self) -> Celsius:
        return (
            self.hot_switch_valve.input_temperature
            if self.hot_switch_valve.position == HOT_RESERVOIR_PCM_VALVE_PCM_POSITION
            else float("nan")
        )

    @property
    def charge_output_temperature(self) -> Celsius:
        return (
            self.hot_mix.output_temperature
            if self.hot_switch_valve.position == HOT_RESERVOIR_PCM_VALVE_PCM_POSITION
            else float("nan")
        )

    @property
    def charge_power(
        self,
    ) -> Watt:
        return (
            self.charge_flow
            * (self.charge_input_temperature - self.charge_output_temperature)
            * self.spec.specific_heat_capacity_charge
        )

    @property
    def discharge_power(
        self,
    ) -> Watt:
        return (
            self.discharge_flow
            * (self.discharge_output_temperature - self.discharge_input_temperature)
            * self.spec.specific_heat_capacity_discharge
        )

    @property
    def net_charge(self) -> Watt:
        return self.charge_power - self.discharge_power

    @property
    def charged(self) -> bool:
        return self.temperature > self.spec.phase_change_temperature

    @property
    def state_of_charge(self):
        return float(self.temperature > self.spec.phase_change_temperature)


@sensors()
class YazakiSensors(FromState):
    spec: Yazaki
    chiller_switch_valve: "ChillerSwitchSensors"
    cold_reservoir: "ColdReservoirSensors"
    waste_switch_valve: "WasteSwitchSensors"
    preheat_switch_valve: "PreHeatSwitchSensors"

    hot_flow: LiterPerSecond = sensor(
        technical_name="FS-1004", type=SensorType.FLOW, from_port=YazakiPort.HOT_IN
    )
    hot_input_temperature: Celsius = sensor(
        technical_name="TS-1010",
        type=SensorType.TEMPERATURE,
        from_port=YazakiPort.HOT_IN,
    )
    hot_output_temperature: Celsius = sensor(
        technical_name="TS-1011",
        type=SensorType.TEMPERATURE,
        from_port=YazakiPort.HOT_OUT,
    )

    @property
    def cooling_input_temperature(self) -> Celsius:
        return (
            self.waste_switch_valve.input_temperature
            if self.waste_switch_valve.position == WASTE_SWITCH_VALVE_YAZAKI_POSITION
            else float("nan")
        )

    @property
    def cooling_output_temperature(self) -> Celsius:
        return (
            self.preheat_switch_valve.input_temperature
            if self.waste_switch_valve.position == WASTE_SWITCH_VALVE_YAZAKI_POSITION
            else float("nan")
        )

    @property
    def cooling_flow(self) -> LiterPerSecond:
        return (
            self.preheat_switch_valve.input_flow
            if self.waste_switch_valve.position == WASTE_SWITCH_VALVE_YAZAKI_POSITION
            else 0
        )

    @property
    def chilled_input_temperature(self) -> Celsius:
        return (
            self.chiller_switch_valve.input_temperature
            if self.chiller_switch_valve.position
            == CHILLER_SWITCH_VALVE_YAZAKI_POSITION
            else float("nan")
        )

    @property
    def chilled_output_temperature(
        self,
    ) -> Celsius:
        return (
            self.cold_reservoir.exchange_input_temperature
            if self.chiller_switch_valve.position
            == CHILLER_SWITCH_VALVE_YAZAKI_POSITION
            else float("nan")
        )

    @property
    def chilled_flow(
        self,
    ) -> LiterPerSecond:
        return (
            self.cold_reservoir.exchange_flow
            if self.chiller_switch_valve.position
            == CHILLER_SWITCH_VALVE_YAZAKI_POSITION
            else 0
        )

    @property
    def cool_power(self) -> Watt:
        return (
            self.chilled_flow
            * (self.chilled_input_temperature - self.chilled_output_temperature)
            * self.spec.specific_heat_capacity_chilled
        )

    @property
    def waste_power(self) -> Watt:
        return (
            self.cooling_flow
            * (self.cooling_output_temperature - self.cooling_input_temperature)
            * self.spec.specific_heat_capacity_cooling
        )

    @property
    def used_power(self) -> Watt:
        return (
            self.hot_flow
            * (self.hot_input_temperature - self.hot_output_temperature)
            * self.spec.specific_heat_capacity_hot
        )

    @property
    def efficiency(self) -> float:
        return (
            self.used_power / self.cool_power if self.cool_power > 0 else float("nan")
        )


@sensors()
class HeatExchangerSensors(FromState):
    spec: HeatExchanger
    input_temperature: Celsius = sensor(
        technical_name="TS-1035",
        type=SensorType.TEMPERATURE,
        from_port=HeatExchangerPort.A_IN,
    )
    output_temperature: Celsius = sensor(
        technical_name="TS-1036",
        type=SensorType.TEMPERATURE,
        from_port=HeatExchangerPort.A_OUT,
    )
    flow: LiterPerSecond = sensor(
        technical_name="FS-1009",
        type=SensorType.FLOW,
        from_port=HeatExchangerPort.A_OUT,
    )

    @property
    def power(self) -> Watt:
        return (
            self.flow
            * (self.output_temperature - self.input_temperature)
            * self.spec.specific_heat_capacity_A
        )


@sensors()
class HotReservoirSensors(FromState):
    spec: Boiler
    temperature: Celsius = sensor(technical_name="TS-1043")
    hot_switch_valve: "HotSwitchSensors"
    hot_mix: "HotMixSensors"
    preheat_reservoir: "PreHeatSensors"

    fill_flow: LiterPerSecond = sensor(
        technical_name="FS-1010",
        type=SensorType.FLOW,
        from_port=BoilerPort.FILL_OUT,
    )

    fill_output_temperature: Celsius = sensor(
        technical_name="TS-1042",
        type=SensorType.TEMPERATURE,
        from_port=BoilerPort.FILL_OUT,
    )

    @property
    def fill_input_temperature(self) -> Celsius:
        return self.preheat_reservoir.temperature

    @property
    def fill_power(self) -> Watt:  # estimate taking internal temperature of preheat
        return (
            self.fill_flow
            * (self.fill_input_temperature - self.fill_output_temperature)
            * self.spec.specific_heat_capacity_exchange
        )

    @property
    def exchange_flow(self) -> LiterPerSecond:
        return (
            self.hot_switch_valve.flow
            if self.hot_switch_valve.position
            == HOT_RESERVOIR_PCM_VALVE_RESERVOIR_POSITION
            else 0
        )

    @property
    def exchange_input_temperature(self) -> Celsius:
        return (
            self.hot_switch_valve.input_temperature
            if self.hot_switch_valve.position
            == HOT_RESERVOIR_PCM_VALVE_RESERVOIR_POSITION
            else float("nan")
        )

    @property
    def exchange_output_temperature(self) -> Celsius:
        return (
            self.hot_mix.output_temperature
            if self.hot_switch_valve.position
            == HOT_RESERVOIR_PCM_VALVE_RESERVOIR_POSITION
            else float("nan")
        )

    @property
    def exchange_power(self) -> Watt:
        return (
            self.exchange_flow
            * (self.exchange_input_temperature - self.exchange_output_temperature)
            * self.spec.specific_heat_capacity_exchange
        )

    @property
    def total_heating_power(self) -> Watt:  # power including preheat
        return (
            self.fill_flow
            * (
                self.fill_output_temperature
                - self.preheat_reservoir.fill_input_temperature
            )
            * self.spec.specific_heat_capacity_fill
        )


@sensors()
class PreHeatSensors(FromState):
    spec: Boiler
    temperature: Celsius = sensor(technical_name="TS-1039")
    outboard_exchange: "HeatExchangerSensors"

    exchange_input_temperature: Celsius = sensor(
        technical_name="TS-1032",
        type=SensorType.TEMPERATURE,
        from_port=BoilerPort.HEAT_EXCHANGE_IN,
    )

    exchange_output_temperature: Celsius = sensor(
        technical_name="TS-1034",
        type=SensorType.TEMPERATURE,
        from_port=BoilerPort.HEAT_EXCHANGE_OUT,
    )

    fill_input_temperature: Celsius = sensor(
        technical_name="TS-1040",
        type=SensorType.TEMPERATURE,
        from_port=BoilerPort.FILL_IN,
    )

    @property
    def exchange_flow(self) -> LiterPerSecond:
        return self.outboard_exchange.flow

    @property
    def exchange_power(self) -> Watt:
        return (
            self.exchange_flow
            * (self.exchange_input_temperature - self.exchange_output_temperature)
            * self.spec.specific_heat_capacity_exchange
        )


@sensors()
class ColdReservoirSensors(FromState):
    spec: Boiler
    temperature: Celsius = sensor(technical_name="TS-1025")

    fill_flow: LiterPerSecond = sensor(
        technical_name="FS-1005", type=SensorType.FLOW, from_port=BoilerPort.FILL_IN
    )

    fill_input_temperature: Celsius = sensor(
        technical_name="TS-1026",
        type=SensorType.TEMPERATURE,
        from_port=BoilerPort.FILL_IN,
    )

    fill_output_temperature: Celsius = sensor(
        technical_name="TS-1027",
        type=SensorType.TEMPERATURE,
        from_port=BoilerPort.FILL_OUT,
    )

    exchange_flow: LiterPerSecond = sensor(
        technical_name="FS-1006",
        type=SensorType.FLOW,
        from_port=BoilerPort.HEAT_EXCHANGE_IN,
    )

    exchange_input_temperature: Celsius = sensor(
        technical_name="TS-1024",
        type=SensorType.TEMPERATURE,
        from_port=BoilerPort.HEAT_EXCHANGE_IN,
    )

    exchange_output_temperature: Celsius = sensor(
        technical_name="TS-1023",
        type=SensorType.TEMPERATURE,
        from_port=BoilerPort.HEAT_EXCHANGE_OUT,
    )

    @property
    def fill_power(self) -> Watt:
        return (
            self.fill_flow
            * (self.fill_input_temperature - self.fill_output_temperature)
            * self.spec.specific_heat_capacity_fill
        )

    @property
    def exchange_power(self) -> Watt:
        return (
            self.exchange_flow
            * (self.exchange_input_temperature - self.exchange_output_temperature)
            * self.spec.specific_heat_capacity_exchange
        )


@sensors()
class ValveSensors(FromState):
    spec: Valve
    position: float

    def in_position(self, position: float, diff: float = 0.05) -> bool:
        return abs(self.position - position) < diff


@sensors()
class ChillerSwitchSensors(ValveSensors):
    input_temperature: Celsius = sensor(
        technical_name="TS-1023", type=SensorType.TEMPERATURE, from_port=ValvePort.AB
    )


@sensors()
class HotSwitchSensors(ValveSensors):
    input_temperature: Celsius = sensor(
        technical_name="TS-1005", type=SensorType.TEMPERATURE, from_port=ValvePort.AB
    )

    flow: LiterPerSecond = sensor(
        technical_name="FS1011", type=SensorType.FLOW, from_port=ValvePort.AB
    )


@sensors()
class WasteSwitchSensors(ValveSensors):
    input_temperature: Celsius = sensor(
        technical_name="TS-1015", type=SensorType.TEMPERATURE, from_port=ValvePort.AB
    )


@sensors()
class HotMixSensors:
    output_temperature: Celsius = sensor(
        technical_name="TS-1006", type=SensorType.TEMPERATURE, from_port=MixPort.AB
    )


@sensors()
class PreHeatSwitchSensors(ValveSensors):
    input_temperature: Celsius = sensor(
        technical_name="TS-1014", type=SensorType.TEMPERATURE, from_port=ValvePort.AB
    )

    input_flow: LiterPerSecond = sensor(
        technical_name="FS-1012", type=SensorType.FLOW, from_port=ValvePort.AB
    )


@sensors()
class ChillerSensors(FromState):
    spec: Chiller
    chiller_switch_valve: "ChillerSwitchSensors"
    cold_reservoir: "ColdReservoirSensors"
    waste_switch_valve: "WasteSwitchSensors"
    preheat_switch_valve: "PreHeatSwitchSensors"

    @property
    def cooling_input_temperature(self) -> Celsius:
        return (
            self.waste_switch_valve.input_temperature
            if self.waste_switch_valve.position == WASTE_SWITCH_VALVE_CHILLER_POSITION
            else float("nan")
        )

    @property
    def cooling_output_temperature(self) -> Celsius:
        return (
            self.preheat_switch_valve.input_temperature
            if self.waste_switch_valve.position == WASTE_SWITCH_VALVE_CHILLER_POSITION
            else float("nan")
        )

    @property
    def cooling_flow(self) -> LiterPerSecond:
        return (
            self.preheat_switch_valve.input_flow
            if self.waste_switch_valve.position == WASTE_SWITCH_VALVE_CHILLER_POSITION
            else 0
        )

    @property
    def chilled_input_temperature(self) -> Celsius:
        return (
            self.chiller_switch_valve.input_temperature
            if self.chiller_switch_valve.position
            == CHILLER_SWITCH_VALVE_CHILLER_POSITION
            else float("nan")
        )

    @property
    def chilled_output_temperature(
        self,
    ) -> Celsius:
        return (
            self.cold_reservoir.exchange_input_temperature
            if self.chiller_switch_valve.position
            == CHILLER_SWITCH_VALVE_CHILLER_POSITION
            else float("nan")
        )

    @property
    def chilled_flow(
        self,
    ) -> LiterPerSecond:
        return (
            self.cold_reservoir.exchange_flow
            if self.chiller_switch_valve.position
            == CHILLER_SWITCH_VALVE_CHILLER_POSITION
            else 0
        )

    @property
    def cool_power(self) -> Watt:
        return (
            self.chilled_flow
            * (self.chilled_input_temperature - self.chilled_output_temperature)
            * self.spec.specific_heat_capacity_chilled
        )

    @property
    def waste_heat(self) -> Watt:
        return (
            self.cooling_flow
            * (self.cooling_output_temperature - self.cooling_input_temperature)
            * self.spec.specific_heat_capacity_cooling
        )


@dataclass
class WeatherSensors:
    ambient_temperature: Celsius
    global_irradiance: WattPerMeterSquared


@dataclass
class PowerHubSensors(NetworkSensors):
    heat_pipes: HeatPipesSensors
    heat_pipes_valve: ValveSensors
    hot_switch_valve: HotSwitchSensors
    hot_reservoir: HotReservoirSensors
    pcm: PcmSensors
    yazaki_hot_bypass_valve: ValveSensors
    yazaki: YazakiSensors
    chiller: ChillerSensors
    chiller_switch_valve: ChillerSwitchSensors
    cold_reservoir: ColdReservoirSensors
    waste_bypass_valve: WasteSwitchSensors
    preheat_switch_valve: PreHeatSwitchSensors
    preheat_reservoir: PreHeatSensors
    waste_switch_valve: WasteSwitchSensors
    outboard_exchange: HeatExchangerSensors
    hot_mix: HotMixSensors
    weather: WeatherSensors


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
