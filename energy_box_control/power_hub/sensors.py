from dataclasses import dataclass
from datetime import datetime

from energy_box_control.appliances import HeatPipes, HeatPipesPort, SwitchPump
from energy_box_control.appliances.containers import Containers, FanAlarm, FilterAlarm
from energy_box_control.appliances.electric_battery import BatteryAlarm, ElectricBattery
from energy_box_control.appliances.heat_exchanger import (
    HeatExchanger,
    HeatExchangerPort,
)

from energy_box_control.appliances.mix import MixPort

from energy_box_control.appliances.pv_panel import PVPanel
from energy_box_control.appliances.switch_pump import SwitchPumpAlarm, SwitchPumpPort
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

from energy_box_control.units import (
    Bar,
    Celsius,
    Joule,
    Liter,
    LiterPerSecond,
    Watt,
    WattPerMeterSquared,
)
from energy_box_control.appliances.boiler import Boiler, BoilerPort
from energy_box_control.appliances.chiller import Chiller, ChillerPort
from energy_box_control.appliances.pcm import Pcm, PcmPort
from energy_box_control.appliances.valve import Valve, ValvePort, ValveServiceInfo
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

    delta_t: Celsius = sensor(
        technical_name="RH33-heat-pipes",
        type=SensorType.DELTA_T,
        from_ports=[HeatPipesPort.IN, HeatPipesPort.OUT],
    )

    @property
    def power(self) -> Watt:
        power = self.flow * (self.delta_t) * self.spec.specific_heat_medium
        return power if self.output_temperature > self.input_temperature else -power


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

    discharge_delta_t: Celsius = sensor(
        technical_name="RH33-pcm-discharge",
        type=SensorType.DELTA_T,
        from_ports=[PcmPort.DISCHARGE_OUT, PcmPort.DISCHARGE_IN],
    )

    discharge_flow: LiterPerSecond = sensor(
        technical_name="FS-1003", type=SensorType.FLOW, from_port=PcmPort.DISCHARGE_IN
    )

    charge_delta_t: Celsius = sensor(
        technical_name="RH33-pcm-boiler",
        type=SensorType.DELTA_T,
        from_ports=[PcmPort.DISCHARGE_IN, PcmPort.DISCHARGE_OUT],
    )  # problem here as this RH33 will be duplicated in the hot reservoir

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
    def charge_pressure(self) -> Celsius:
        return (
            self.hot_switch_valve.pressure
            if self.hot_switch_valve.position == HOT_RESERVOIR_PCM_VALVE_PCM_POSITION
            else float("nan")
        )

    @property
    def charge_power(
        self,
    ) -> Watt:
        power = (
            self.charge_flow
            * (self.charge_delta_t)
            * self.spec.specific_heat_capacity_charge
        )
        return (
            power
            if self.charge_input_temperature > self.charge_output_temperature
            else -power
        )

    @property
    def discharge_power(
        self,
    ) -> Watt:
        power = (
            self.discharge_flow
            * (self.discharge_delta_t)
            * self.spec.specific_heat_capacity_discharge
        )
        return (
            power
            if self.discharge_output_temperature > self.discharge_output_temperature
            else -power
        )

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
    chilled_loop_pump: "SwitchPumpSensors"

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

    hot_delta_t: Celsius = sensor(
        technical_name="RH33-yazaki-hot",
        type=SensorType.DELTA_T,
        from_ports=[YazakiPort.HOT_IN, YazakiPort.HOT_OUT],
    )
    waste_delta_t: Celsius = sensor(
        technical_name="RH33-waste-heat",
        type=SensorType.DELTA_T,
        from_ports=[YazakiPort.COOLING_IN, YazakiPort.COOLING_OUT],
    )  # problem here as this sensor will be duplicated for electric chiller
    cooling_delta_t: Celsius = sensor(
        technical_name="RH33-chill",
        type=SensorType.DELTA_T,
        from_ports=[YazakiPort.COOLING_IN, YazakiPort.COOLING_OUT],
    )  # problem here as this sensor will be duplicated for electric chiller

    hot_pressure: LiterPerSecond = sensor(technical_name="PS-1001")

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
    def cooling_pressure(self) -> Bar:
        return (
            self.preheat_switch_valve.pressure
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
    def chilled_pressure(
        self,
    ) -> LiterPerSecond:
        return (
            self.chilled_loop_pump.pressure
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
            * (self.cooling_delta_t)
            * self.spec.specific_heat_capacity_cooling
        )
        return (
            (
                power
                if self.cooling_output_temperature > self.cooling_input_temperature
                else -power
            )
            if power == power
            else 0
        )

    @property
    def used_power(self) -> Watt:
        power = (
            self.hot_flow * (self.hot_delta_t) * self.spec.specific_heat_capacity_hot
        )
        return (
            power
            if self.hot_input_temperature > self.hot_output_temperature
            else -power
        )

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

    delta_t: Celsius = sensor(
        technical_name="RH33-heat-dump",
        type=SensorType.DELTA_T,
        from_ports=[HeatExchangerPort.A_IN, HeatExchangerPort.A_OUT],
    )

    @property
    def power(self) -> Watt:
        power = self.flow * (self.delta_t) * self.spec.specific_heat_capacity_A
        return power if self.input_temperature > self.output_temperature else -power


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

    exchange_delta_t: Celsius = sensor(
        technical_name="RH33-pcm-boiler",
        type=SensorType.DELTA_T,
        from_ports=[BoilerPort.HEAT_EXCHANGE_IN, BoilerPort.HEAT_EXCHANGE_OUT],
    )  ##duplicated in PCM

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
            * (self.exchange_delta_t)
            * self.spec.specific_heat_capacity_exchange
        )

        return (
            power
            if self.exchange_output_temperature > self.exchange_output_temperature
            else -power
        )

    @property
    def total_hot_water_power(
        self,
    ) -> (
        Watt
    ):  # power including preheat  --- for this, we need delta_t from the boiler and the preheat
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

    exchange_delta_t: Celsius = sensor(
        technical_name="RH33-preheat",
        type=SensorType.DELTA_T,
        from_ports=[BoilerPort.HEAT_EXCHANGE_IN, BoilerPort.HEAT_EXCHANGE_OUT],
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
            * (self.exchange_delta_t)
            * self.spec.specific_heat_capacity_exchange
        )
        return (
            power
            if self.exchange_output_temperature > self.exchange_input_temperature
            else -power
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

    fill_delta_t: Celsius = sensor(
        technical_name="RH33-cooling-demand",
        type=SensorType.DELTA_T,
        from_ports=[BoilerPort.FILL_IN, BoilerPort.FILL_OUT],
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

    exchange_delta_t: Celsius = sensor(
        technical_name="RH33-chill",
        type=SensorType.DELTA_T,
        from_ports=[BoilerPort.HEAT_EXCHANGE_IN, BoilerPort.HEAT_EXCHANGE_OUT],
    )

    @property
    def cooling_demand(self) -> Watt:
        power = (
            self.fill_flow * self.fill_delta_t * self.spec.specific_heat_capacity_fill
        )
        return (
            power
            if self.fill_input_temperature > self.fill_output_temperature
            else -power
        )

    @property
    def cooling_supply(self) -> Watt:
        power = (
            self.exchange_flow
            * self.exchange_delta_t
            * self.spec.specific_heat_capacity_exchange
        )
        return (
            power
            if self.exchange_input_temperature < self.fill_output_temperature
            else -power
        )


@sensors()
class ValveSensors(FromState):
    spec: Valve
    position: float = sensor()
    service_info: ValveServiceInfo = sensor()

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
        technical_name="FS-1011", type=SensorType.FLOW, from_port=ValvePort.AB
    )

    pressure: Bar = sensor(technical_name="PS-1003")


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

    pressure: Bar = sensor(technical_name="PS-1002")


@sensors()
class ChillerSensors(FromState):
    spec: Chiller
    chiller_switch_valve: "ChillerSwitchSensors"
    cold_reservoir: "ColdReservoirSensors"
    waste_switch_valve: "WasteSwitchSensors"
    preheat_switch_valve: "PreHeatSwitchSensors"

    cooling_delta_t: Celsius = sensor(
        technical_name="RH33-waste-heat",
        type=SensorType.DELTA_T,
        from_ports=[ChillerPort.COOLING_IN, ChillerPort.COOLING_OUT],
    )  # problem here as this sensor is duplicated for yazaki
    chilled_delta_t: Celsius = sensor(
        technical_name="RH33-chill",
        type=SensorType.DELTA_T,
        from_ports=[ChillerPort.COOLING_IN, ChillerPort.COOLING_OUT],
    )  # problem here as this sensor is duplicated for yazaki

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
            * self.chilled_delta_t
            * self.spec.specific_heat_capacity_chilled
        )
        return (
            (
                power
                if self.chilled_input_temperature > self.chilled_output_temperature
                else -power
            )
            if power == power
            else 0
        )

    @property
    def waste_heat(self) -> Watt:
        power = (
            self.cooling_flow
            * self.cooling_delta_t
            * self.spec.specific_heat_capacity_cooling
        )
        return (
            (
                power
                if self.cooling_output_temperature > self.cooling_input_temperature
                else -power
            )
            if power == power
            else 0
        )


@sensors()
class SwitchPumpSensors(FromState):
    spec: SwitchPump
    flow_out: LiterPerSecond = sensor(
        type=SensorType.FLOW, from_port=SwitchPumpPort.OUT
    )

    pump_1_alarm: SwitchPumpAlarm = sensor(type=SensorType.ALARM)
    pump_2_alarm: SwitchPumpAlarm = sensor(type=SensorType.ALARM)
    pressure: Bar = sensor()

    @property
    def electrical_power(self) -> Watt:
        return self.spec.electrical_power if self.flow_out > 0 else 0


@sensors()
class PVSensors(FromState):
    spec: PVPanel
    power: Watt = sensor()


@sensors()
class ElectricBatterySensors(FromState):
    spec: ElectricBattery
    voltage_battery_system: int = sensor()
    current_battery_system: int = sensor()
    power_battery_system: int = sensor()
    soc_battery_system: float = sensor()
    battery_alarm: int = sensor()
    battery_low_voltage_alarm: int = sensor()
    battery_high_voltage_alarm: int = sensor()
    battery_low_starter_voltage_alarm: int = sensor()
    battery_high_starter_voltage_alarm: int = sensor()
    battery_low_soc_alarm: BatteryAlarm = sensor(type=SensorType.ALARM)
    battery_low_temperature_alarm: BatteryAlarm = sensor(type=SensorType.ALARM)
    battery_high_temperature_alarm: BatteryAlarm = sensor(type=SensorType.ALARM)
    battery_mid_voltage_alarm: BatteryAlarm = sensor(type=SensorType.ALARM)
    battery_low_fused_voltage_alarm: BatteryAlarm = sensor(type=SensorType.ALARM)
    battery_high_fused_voltage_alarm: BatteryAlarm = sensor(type=SensorType.ALARM)
    battery_fuse_blown_alarm: BatteryAlarm = sensor(type=SensorType.ALARM)
    battery_high_internal_temperature_alarm: BatteryAlarm = sensor(
        type=SensorType.ALARM
    )
    battery_high_charge_current_alarm: BatteryAlarm = sensor(type=SensorType.ALARM)
    battery_high_discharge_current_alarm: BatteryAlarm = sensor(type=SensorType.ALARM)
    battery_cell_imbalance_alarm: BatteryAlarm = sensor(type=SensorType.ALARM)
    battery_internal_failure_alarm: BatteryAlarm = sensor(type=SensorType.ALARM)
    battery_high_charge_temperature_alarm: BatteryAlarm = sensor(type=SensorType.ALARM)
    battery_low_charge_temperature_alarm: BatteryAlarm = sensor(type=SensorType.ALARM)
    battery_low_cell_voltage_alarm: BatteryAlarm = sensor(type=SensorType.ALARM)
    battery_error: int = sensor()
    high_temperature_alarm: BatteryAlarm = sensor(type=SensorType.ALARM)
    high_battery_voltage_alarm: BatteryAlarm = sensor(type=SensorType.ALARM)
    high_ac_out_voltage_alarm: BatteryAlarm = sensor(type=SensorType.ALARM)
    low_temperature_alarm: BatteryAlarm = sensor(type=SensorType.ALARM)
    low_battery_voltage_alarm: BatteryAlarm = sensor(type=SensorType.ALARM)
    low_ac_out_voltage_alarm: BatteryAlarm = sensor(type=SensorType.ALARM)
    overload_alarm: BatteryAlarm = sensor(type=SensorType.ALARM)
    ripple_alarm: BatteryAlarm = sensor(type=SensorType.ALARM)
    low_batt_voltage_alarm: BatteryAlarm = sensor(type=SensorType.ALARM)
    high_batt_voltage_alarm: BatteryAlarm = sensor(type=SensorType.ALARM)


@sensors()
class WaterTankSensors(FromState):
    spec: WaterTank
    fill_ratio: Liter = sensor(technical_name="LS-5001")

    @property
    def fill(self) -> Liter:
        return self.fill_ratio * self.spec.capacity


@sensors()
class FreshWaterTankSensors(WaterTankSensors):

    water_demand_flow: LiterPerSecond = sensor(
        type=SensorType.FLOW, from_port=WaterTankPort.CONSUMPTION
    )
    secondary_flow_in: LiterPerSecond = sensor(
        type=SensorType.FLOW, from_port=WaterTankPort.IN_1
    )
    primary_flow_in: LiterPerSecond = sensor(
        type=SensorType.FLOW, from_port=WaterTankPort.IN_0
    )


@sensors()
class GreyWaterTankSensors(WaterTankSensors):

    water_demand_flow: LiterPerSecond = sensor(
        type=SensorType.FLOW, from_port=WaterTankPort.CONSUMPTION
    )

    primary_flow_in: LiterPerSecond = sensor(
        type=SensorType.FLOW, from_port=WaterTankPort.IN_0
    )


@sensors()
class WaterTreatmentSensors(FromState):
    spec: WaterTreatment

    out_flow: LiterPerSecond = sensor(
        technical_name="FS-4001", type=SensorType.FLOW, from_port=WaterTreatmentPort.OUT
    )


@sensors()
class WaterMakerSensors(FromState):
    spec: WaterMaker
    on: bool = sensor()
    out_flow: LiterPerSecond = sensor(
        type=SensorType.FLOW, from_port=WaterMakerPort.DESALINATED_OUT
    )


@sensors()
class ContainersSensors(FromState):
    spec: Containers
    simulator_storage_co2: float = sensor(type=SensorType.CO2)
    simulator_storage_humidity: float = sensor(type=SensorType.HUMIDITY)
    simulator_storage_temperature: Celsius = sensor(type=SensorType.TEMPERATURE)
    simulator_storage_ventilation_error: FanAlarm = sensor(type=SensorType.ALARM)
    simulator_storage_ventilation_filter_status: FilterAlarm = sensor(
        type=SensorType.REPLACE_FILTER_ALARM
    )
    office_co2: float = sensor(type=SensorType.CO2)
    office_humidity: float = sensor(type=SensorType.HUMIDITY)
    office_temperature: Celsius = sensor(type=SensorType.TEMPERATURE)
    office_ventilation_error: FanAlarm = sensor(type=SensorType.ALARM)
    office_ventilation_filter_status: FilterAlarm = sensor(
        type=SensorType.REPLACE_FILTER_ALARM
    )
    kitchen_co2: float = sensor(type=SensorType.CO2)
    kitchen_humidity: float = sensor(type=SensorType.HUMIDITY)
    kitchen_temperature: Celsius = sensor(type=SensorType.TEMPERATURE)
    sanitary_temperature: Celsius = sensor(type=SensorType.TEMPERATURE)
    kitchen_ventilation_error: FanAlarm = sensor(type=SensorType.ALARM)
    kitchen_ventilation_filter_status: FilterAlarm = sensor(
        type=SensorType.REPLACE_FILTER_ALARM
    )
    power_hub_humidity: float = sensor(type=SensorType.HUMIDITY)
    power_hub_temperature: Celsius = sensor(type=SensorType.TEMPERATURE)
    supply_box_humidity: float = sensor(type=SensorType.HUMIDITY)
    supply_box_temperature: Celsius = sensor(type=SensorType.TEMPERATURE)


@sensors(from_appliance=False)
class WeatherSensors(WithoutAppliance):
    ambient_temperature: Celsius
    global_irradiance: WattPerMeterSquared
    alarm: int = sensor(type=SensorType.ALARM)


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
    black_water_tank: WaterTankSensors
    technical_water_tank: WaterTankSensors
    water_treatment: WaterTreatmentSensors
    water_maker: WaterMakerSensors
    containers: ContainersSensors
    time: datetime


SensorName = str
SensorValue = float | Celsius | LiterPerSecond | WattPerMeterSquared


def sensor_values(
    sensor_name: SensorName, sensors: PowerHubSensors
) -> dict[SensorName, SensorValue]:
    sensor = getattr(sensors, sensor_name)

    return {field: getattr(sensor, field) for field in sensor_fields(type(sensor))}
