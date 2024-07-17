from dataclasses import dataclass
from energy_box_control.appliances import HeatPipes, HeatPipesPort, SwitchPump
from energy_box_control.appliances.electric_battery import ElectricBattery
from energy_box_control.appliances.heat_exchanger import (
    HeatExchanger,
    HeatExchangerPort,
)

from energy_box_control.appliances.mix import MixPort

from energy_box_control.appliances.pv_panel import PVPanel
from energy_box_control.appliances.switch_pump import SwitchPumpPort
from energy_box_control.appliances.water_maker import WaterMaker, WaterMakerPort
from energy_box_control.appliances.water_tank import WaterTank, WaterTankPort
from energy_box_control.appliances.water_treatment import (
    WaterTreatment,
    WaterTreatmentPort,
)
from energy_box_control.power_hub.components import (
    CHILLER_SWITCH_VALVE_CHILLER_POSITION,
    CHILLER_SWITCH_VALVE_YAZAKI_POSITION,
    HOT_RESERVOIR_PCM_VALVE_PCM_POSITION,
    HOT_RESERVOIR_PCM_VALVE_RESERVOIR_POSITION,
    WASTE_SWITCH_VALVE_CHILLER_POSITION,
    WASTE_SWITCH_VALVE_YAZAKI_POSITION,
    PCM_ZERO_TEMPERATURE,
)

from datetime import datetime

from energy_box_control.units import (
    BatteryAlarm,
    Celsius,
    Joule,
    Liter,
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
    WithoutAppliance,
    SensorType,
    sensor,
    sensor_fields,
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
        power = (
            self.flow
            * (self.output_temperature - self.input_temperature)
            * self.spec.specific_heat_medium
        )
        return power if power == power else 0


@sensors()
class PcmSensors(FromState):
    spec: Pcm
    temperature: Celsius = sensor(technical_name="TS-1007")
    state_of_charge: float = sensor()
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
        power = (
            self.charge_flow
            * (self.charge_input_temperature - self.charge_output_temperature)
            * self.spec.specific_heat_capacity_charge
        )
        return power if power == power else 0

    @property
    def discharge_power(
        self,
    ) -> Watt:
        power = (
            self.discharge_flow
            * (self.discharge_output_temperature - self.discharge_input_temperature)
            * self.spec.specific_heat_capacity_discharge
        )
        return power if power == power else 0

    @property
    def net_charge(self) -> Watt:
        return self.charge_power - self.discharge_power

    @property
    def charged(self) -> bool:
        return self.temperature > self.spec.phase_change_temperature

    @property
    def heat(self) -> Joule:
        return (
            self.spec.sensible_capacity * (self.temperature - PCM_ZERO_TEMPERATURE)
            + self.spec.latent_heat * self.state_of_charge
        )


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
    def chill_power(self) -> Watt:
        power = (
            self.chilled_flow
            * (self.chilled_output_temperature - self.chilled_input_temperature)
            * self.spec.specific_heat_capacity_chilled
        )
        return power if power == power else 0

    @property
    def waste_power(self) -> Watt:
        power = (
            self.cooling_flow
            * (self.cooling_output_temperature - self.cooling_input_temperature)
            * self.spec.specific_heat_capacity_cooling
        )
        return power if power == power else 0

    @property
    def used_power(self) -> Watt:
        power = (
            self.hot_flow
            * (self.hot_input_temperature - self.hot_output_temperature)
            * self.spec.specific_heat_capacity_hot
        )
        return power if power == power else 0

    @property
    def efficiency(self) -> float:
        return (
            -self.chill_power / self.used_power if self.used_power > 0 else float("nan")
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
        power = (
            self.flow
            * (self.input_temperature - self.output_temperature)
            * self.spec.specific_heat_capacity_A
        )
        return power if power == power else 0


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
        return (
            self.preheat_reservoir.temperature if self.fill_flow > 0 else float("nan")
        )

    @property
    def fill_power(self) -> Watt:  # estimate taking internal temperature of preheat
        power = (
            self.fill_flow
            * (self.fill_input_temperature - self.fill_output_temperature)
            * self.spec.specific_heat_capacity_exchange
        )
        return power if power == power else 0

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
        power = (
            self.exchange_flow
            * (self.exchange_input_temperature - self.exchange_output_temperature)
            * self.spec.specific_heat_capacity_exchange
        )

        return power if power == power else 0

    @property
    def total_heating_power(self) -> Watt:  # power including preheat
        power = (
            self.fill_flow
            * (
                self.fill_output_temperature
                - self.preheat_reservoir.fill_input_temperature
            )
            * self.spec.specific_heat_capacity_fill
        )
        return power if power == power else 0


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
        power = (
            self.exchange_flow
            * (self.exchange_input_temperature - self.exchange_output_temperature)
            * self.spec.specific_heat_capacity_exchange
        )
        return power if power == power else 0


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
        power = (
            self.fill_flow
            * (self.fill_input_temperature - self.fill_output_temperature)
            * self.spec.specific_heat_capacity_fill
        )
        return power if power == power else 0

    @property
    def exchange_power(self) -> Watt:
        power = (
            self.exchange_flow
            * (self.exchange_input_temperature - self.exchange_output_temperature)
            * self.spec.specific_heat_capacity_exchange
        )
        return power if power == power else 0


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
    def chill_power(self) -> Watt:
        power = (
            self.chilled_flow
            * (self.chilled_output_temperature - self.chilled_input_temperature)
            * self.spec.specific_heat_capacity_chilled
        )
        return power if power == power else 0

    @property
    def waste_heat(self) -> Watt:
        power = (
            self.cooling_flow
            * (self.cooling_output_temperature - self.cooling_input_temperature)
            * self.spec.specific_heat_capacity_cooling
        )
        return power if power == power else 0


@sensors()
class SwitchPumpSensors(FromState):
    spec: SwitchPump
    flow_out: LiterPerSecond = sensor(
        type=SensorType.FLOW, from_port=SwitchPumpPort.OUT
    )

    @property
    def electrical_power(self) -> Watt:
        return self.spec.electrical_power if self.flow_out > 0 else 0


@sensors()
class PVSensors(FromState):
    spec: PVPanel
    power: Watt


@sensors()
class ElectricBatterySensors(FromState):
    spec: ElectricBattery
    voltage_battery_system: int
    current_battery_system: int
    power_battery_system: int
    soc_battery_system: float
    battery_alarm: int
    battery_low_voltage_alarm: int
    battery_high_voltage_alarm: int
    battery_low_starter_voltage_alarm: int
    battery_high_starter_voltage_alarm: int
    battery_low_soc_alarm: BatteryAlarm
    battery_low_temperature_alarm: BatteryAlarm
    battery_high_temperature_alarm: BatteryAlarm
    battery_mid_voltage_alarm: BatteryAlarm
    battery_low_fused_voltage_alarm: BatteryAlarm
    battery_high_fused_voltage_alarm: BatteryAlarm
    battery_fuse_blown_alarm: BatteryAlarm
    battery_high_internal_temperature_alarm: BatteryAlarm
    battery_high_charge_current_alarm: BatteryAlarm
    battery_high_discharge_current_alarm: BatteryAlarm
    battery_cell_imbalance_alarm: BatteryAlarm
    battery_internal_failure_alarm: BatteryAlarm
    battery_high_charge_temperature_alarm: BatteryAlarm
    battery_low_charge_temperature_alarm: BatteryAlarm
    battery_low_cell_voltage_alarm: BatteryAlarm
    battery_error: int
    high_temperature_alarm: BatteryAlarm
    high_battery_voltage_alarm: BatteryAlarm
    high_ac_out_voltage_alarm: BatteryAlarm
    low_temperature_alarm: BatteryAlarm
    low_battery_voltage_alarm: BatteryAlarm
    low_ac_out_voltage_alarm: BatteryAlarm
    overload_alarm: BatteryAlarm
    ripple_alarm: BatteryAlarm
    low_batt_voltage_alarm: BatteryAlarm
    high_batt_voltage_alarm: BatteryAlarm


@sensors()
class FreshWaterTankSensors(FromState):
    spec: WaterTank
    fill: Liter = sensor(technical_name="LS-5001")
    water_demand_flow: LiterPerSecond = sensor(
        type=SensorType.FLOW, from_port=WaterTankPort.CONSUMPTION
    )
    secondary_flow_in: LiterPerSecond = sensor(
        type=SensorType.FLOW, from_port=WaterTankPort.IN_1
    )
    primary_flow_in: LiterPerSecond = sensor(
        type=SensorType.FLOW, from_port=WaterTankPort.IN_0
    )

    @property
    def percentage_fill(self) -> float:
        return self.fill / self.spec.capacity


@sensors()
class GreyWaterTankSensors(FromState):
    spec: WaterTank
    fill: Liter = sensor(technical_name="LS-3001")

    water_demand_flow: LiterPerSecond = sensor(
        type=SensorType.FLOW, from_port=WaterTankPort.CONSUMPTION
    )

    primary_flow_in: LiterPerSecond = sensor(
        type=SensorType.FLOW, from_port=WaterTankPort.IN_0
    )

    @property
    def percentage_fill(self) -> float:
        return self.fill / self.spec.capacity


@sensors()
class WaterTreatmentSensors(FromState):
    spec: WaterTreatment

    out_flow: LiterPerSecond = sensor(
        technical_name="FS-4001", type=SensorType.FLOW, from_port=WaterTreatmentPort.OUT
    )


@sensors()
class WaterMakerSensors(FromState):
    spec: WaterMaker
    on: bool
    out_flow: LiterPerSecond = sensor(
        type=SensorType.FLOW, from_port=WaterMakerPort.DESALINATED_OUT
    )


@sensors(from_appliance=False)
class WeatherSensors(WithoutAppliance):
    ambient_temperature: Celsius
    global_irradiance: WattPerMeterSquared
    alarm: int


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
    heat_pipes_power_hub_pump: SwitchPumpSensors
    heat_pipes_supply_box_pump: SwitchPumpSensors
    pcm_to_yazaki_pump: SwitchPumpSensors
    chilled_loop_pump: SwitchPumpSensors
    waste_pump: SwitchPumpSensors
    hot_water_pump: SwitchPumpSensors
    outboard_pump: SwitchPumpSensors
    cooling_demand_pump: SwitchPumpSensors
    pv_panel: PVSensors
    electric_battery: ElectricBatterySensors
    fresh_water_tank: FreshWaterTankSensors
    grey_water_tank: GreyWaterTankSensors
    water_treatment: WaterTreatmentSensors
    water_maker: WaterMakerSensors
    time: datetime


SensorName = str
SensorValue = float | Celsius | LiterPerSecond | WattPerMeterSquared


def sensor_values(
    sensor_name: SensorName, sensors: PowerHubSensors
) -> dict[SensorName, SensorValue]:
    sensor = getattr(sensors, sensor_name)

    return {field: getattr(sensor, field) for field in sensor_fields(type(sensor))}
