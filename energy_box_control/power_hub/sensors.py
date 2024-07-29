from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, TYPE_CHECKING

from energy_box_control.appliances import HeatPipes, HeatPipesPort, SwitchPump
from energy_box_control.appliances.base import Port, ThermalState
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
from energy_box_control.network import AnyAppliance, NetworkState
from energy_box_control.power_hub.components import (
    CHILLER_SWITCH_VALVE_CHILLER_POSITION,
    CHILLER_SWITCH_VALVE_YAZAKI_POSITION,
    HOT_RESERVOIR_PCM_VALVE_PCM_POSITION,
    HOT_RESERVOIR_PCM_VALVE_RESERVOIR_POSITION,
    WASTE_SWITCH_VALVE_CHILLER_POSITION,
    WASTE_SWITCH_VALVE_YAZAKI_POSITION,
    PCM_ZERO_TEMPERATURE,
)

if TYPE_CHECKING:
    from energy_box_control.power_hub.network import PowerHub, PowerHubSchedules

from energy_box_control.schedules import Schedule
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
from energy_box_control.appliances.chiller import Chiller
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


def power_hub_sensor[T](resolver: "Callable[[PowerHub, NetworkState[PowerHub]], T]"):
    return sensor(resolver=resolver)


@sensors(from_appliance=False, eq=False)
class RH33Sensors(WithoutAppliance):
    hot_temperature: Celsius
    cold_temperature: Celsius
    delta_temperature: Celsius

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, RH33Sensors):
            return False
        return (
            self.cold_temperature == value.cold_temperature
            and self.delta_temperature == value.delta_temperature
            and self.hot_temperature == value.hot_temperature
        )


type TemperatureResolver = "tuple[Callable[[PowerHub], AnyAppliance], Port]"


def rh33(hot: TemperatureResolver, cold: TemperatureResolver) -> Any:
    hot_appliance, hot_port = hot
    cold_appliance, cold_port = cold

    @sensors(from_appliance=False, eq=False)
    class RH33(RH33Sensors):
        hot_temperature: Celsius = power_hub_sensor(
            lambda power_hub, state: state.connection(
                hot_appliance(power_hub),
                hot_port,
                ThermalState(float("nan"), float("nan")),
            ).temperature
        )
        cold_temperature: Celsius = power_hub_sensor(
            lambda power_hub, state: state.connection(
                cold_appliance(power_hub),
                cold_port,
                ThermalState(float("nan"), float("nan")),
            ).temperature
        )
        delta_temperature: Celsius = power_hub_sensor(
            lambda power_hub, state: state.connection(
                hot_appliance(power_hub),
                hot_port,
                ThermalState(float("nan"), float("nan")),
            ).temperature
            - state.connection(
                cold_appliance(power_hub),
                cold_port,
                ThermalState(float("nan"), float("nan")),
            ).temperature
        )

    return RH33


@sensors()
class HeatPipesSensors(FromState):
    spec: HeatPipes
    flow: LiterPerSecond = sensor(
        technical_name="FS-1001", type=SensorType.FLOW, from_port=HeatPipesPort.IN
    )
    rh33_heat_pipes: RH33Sensors

    @property
    def input_temperature(self) -> Celsius:
        return self.rh33_heat_pipes.cold_temperature

    @property
    def output_temperature(self) -> Celsius:
        return self.rh33_heat_pipes.hot_temperature

    @property
    def delta_temperature(self) -> Celsius:
        return self.rh33_heat_pipes.delta_temperature

    @property
    def power(self) -> Watt:
        return self.flow * self.delta_temperature * self.spec.specific_heat_medium


@sensors()
class PcmSensors(FromState):
    spec: Pcm
    temperature: Celsius = sensor(technical_name="TS-1007")
    state_of_charge: float = sensor()
    rh33_pcm_discharge: RH33Sensors
    rh33_hot_storage: RH33Sensors
    hot_switch_valve: "HotSwitchSensors"

    @property
    def discharge_input_temperature(self) -> Celsius:
        return self.rh33_pcm_discharge.cold_temperature

    @property
    def discharge_output_temperature(self) -> Celsius:
        return self.rh33_pcm_discharge.hot_temperature

    @property
    def discharge_delta_temperature(self) -> Celsius:
        return self.rh33_pcm_discharge.delta_temperature

    discharge_flow: LiterPerSecond = sensor(
        technical_name="FS-1003", type=SensorType.FLOW, from_port=PcmPort.DISCHARGE_IN
    )

    @property
    def discharge_power(
        self,
    ) -> Watt:
        return (
            self.discharge_flow
            * self.discharge_delta_temperature
            * self.spec.specific_heat_capacity_discharge
        )

    @property
    def charge_input_temperature(self) -> Celsius:
        return (
            self.rh33_hot_storage.hot_temperature
            if self.hot_switch_valve.position == HOT_RESERVOIR_PCM_VALVE_PCM_POSITION
            else float("nan")
        )

    @property
    def charge_output_temperature(self) -> Celsius:
        return (
            self.rh33_hot_storage.cold_temperature
            if self.hot_switch_valve.position == HOT_RESERVOIR_PCM_VALVE_PCM_POSITION
            else float("nan")
        )

    @property
    def charge_delta_temperature(self) -> Celsius:
        return (
            self.rh33_hot_storage.delta_temperature
            if self.hot_switch_valve.position == HOT_RESERVOIR_PCM_VALVE_PCM_POSITION
            else float("nan")
        )

    @property
    def charge_flow(self) -> LiterPerSecond:
        return (
            self.hot_switch_valve.flow
            if self.hot_switch_valve.position == HOT_RESERVOIR_PCM_VALVE_PCM_POSITION
            else 0
        )

    @property
    def charge_power(
        self,
    ) -> Watt:
        return (
            self.charge_flow
            * self.charge_delta_temperature
            * self.spec.specific_heat_capacity_charge
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
    rh33_yazaki_hot: RH33Sensors
    rh33_waste: RH33Sensors
    rh33_chill: RH33Sensors
    chiller_switch_valve: "ChillerSwitchSensors"
    cold_reservoir: "ColdReservoirSensors"
    waste_mix: "WasteMixSensors"
    waste_switch_valve: "ValveSensors"
    chilled_loop_pump: "SwitchPumpSensors"
    waste_pressure_sensor: "PressureSensors"
    pcm_yazaki_pressure_sensor: "PressureSensors"

    hot_flow: LiterPerSecond = sensor(
        technical_name="FS-1004", type=SensorType.FLOW, from_port=YazakiPort.HOT_IN
    )

    @property
    def hot_input_temperature(self) -> Celsius:
        return self.rh33_yazaki_hot.hot_temperature

    @property
    def hot_output_temperature(self) -> Celsius:
        return self.rh33_yazaki_hot.cold_temperature

    @property
    def hot_delta_temperature(self) -> Celsius:
        return self.rh33_yazaki_hot.delta_temperature

    @property
    def used_power(self) -> Watt:
        return (
            self.hot_flow
            * self.hot_delta_temperature
            * self.spec.specific_heat_capacity_hot
        )

    @property
    def hot_pressure(self) -> Bar:
        return (
            self.pcm_yazaki_pressure_sensor.pressure
            if self.waste_switch_valve.position == WASTE_SWITCH_VALVE_YAZAKI_POSITION
            else 0
        )

    @property
    def waste_flow(self) -> LiterPerSecond:
        return (
            self.waste_mix.flow
            if self.waste_switch_valve.position == WASTE_SWITCH_VALVE_YAZAKI_POSITION
            else 0
        )

    @property
    def waste_input_temperature(self) -> Celsius:
        return (
            self.rh33_waste.cold_temperature
            if self.waste_switch_valve.position == WASTE_SWITCH_VALVE_YAZAKI_POSITION
            else float("nan")
        )

    @property
    def waste_output_temperature(self) -> Celsius:
        return (
            self.rh33_waste.hot_temperature
            if self.waste_switch_valve.position == WASTE_SWITCH_VALVE_YAZAKI_POSITION
            else float("nan")
        )

    @property
    def waste_delta_temperature(self) -> Celsius:
        return (
            self.rh33_waste.delta_temperature
            if self.waste_switch_valve.position == WASTE_SWITCH_VALVE_YAZAKI_POSITION
            else float("nan")
        )

    @property
    def waste_power(self) -> Watt:
        return (
            self.waste_flow
            * self.waste_delta_temperature
            * self.spec.specific_heat_capacity_cooling
        )

    @property
    def waste_pressure(self) -> Bar:
        return (
            self.waste_pressure_sensor.pressure
            if self.waste_switch_valve.position == WASTE_SWITCH_VALVE_YAZAKI_POSITION
            else 0
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
    def chilled_input_temperature(self) -> Celsius:
        return (
            self.rh33_chill.hot_temperature
            if self.chiller_switch_valve.position
            == CHILLER_SWITCH_VALVE_YAZAKI_POSITION
            else float("nan")
        )

    @property
    def chilled_output_temperature(
        self,
    ) -> Celsius:
        return (
            self.rh33_chill.cold_temperature
            if self.chiller_switch_valve.position
            == CHILLER_SWITCH_VALVE_YAZAKI_POSITION
            else float("nan")
        )

    @property
    def chilled_delta_temperature(
        self,
    ) -> Celsius:
        return (
            self.rh33_chill.delta_temperature
            if self.chiller_switch_valve.position
            == CHILLER_SWITCH_VALVE_YAZAKI_POSITION
            else float("nan")
        )

    @property
    def chill_power(self) -> Watt:
        return (
            self.chilled_flow
            * self.chilled_delta_temperature
            * self.spec.specific_heat_capacity_chilled
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
    def efficiency(self) -> float:
        return (
            self.chill_power / self.used_power if self.used_power > 0 else float("nan")
        )


@sensors()
class HeatExchangerSensors(FromState):
    spec: HeatExchanger
    rh33_heat_dump: RH33Sensors

    flow: LiterPerSecond = sensor(
        technical_name="FS-1009",
        type=SensorType.FLOW,
        from_port=HeatExchangerPort.A_OUT,
    )

    @property
    def input_temperature(self) -> Celsius:
        return self.rh33_heat_dump.hot_temperature

    @property
    def output_temperature(self) -> Celsius:
        return self.rh33_heat_dump.cold_temperature

    @property
    def delta_temperature(self) -> Celsius:
        return self.rh33_heat_dump.delta_temperature

    @property
    def power(self) -> Watt:
        return self.flow * self.delta_temperature * self.spec.specific_heat_capacity_A


@sensors()
class HotReservoirSensors(FromState):
    spec: Boiler
    temperature: Celsius = sensor(technical_name="TS-1043")
    rh33_hot_storage: RH33Sensors
    rh33_domestic_hot_water: RH33Sensors
    hot_switch_valve: "HotSwitchSensors"

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
            self.rh33_hot_storage.hot_temperature
            if self.hot_switch_valve.position
            == HOT_RESERVOIR_PCM_VALVE_RESERVOIR_POSITION
            else float("nan")
        )

    @property
    def exchange_output_temperature(self) -> Celsius:
        return (
            self.rh33_hot_storage.cold_temperature
            if self.hot_switch_valve.position
            == HOT_RESERVOIR_PCM_VALVE_RESERVOIR_POSITION
            else float("nan")
        )

    @property
    def exchange_delta_temperature(self) -> Celsius:
        return (
            self.rh33_hot_storage.delta_temperature
            if self.hot_switch_valve.position
            == HOT_RESERVOIR_PCM_VALVE_RESERVOIR_POSITION
            else float("nan")
        )

    @property
    def exchange_power(self) -> Watt:
        return (
            self.exchange_flow
            * self.exchange_delta_temperature
            * self.spec.specific_heat_capacity_exchange
        )

    fill_flow: LiterPerSecond = sensor(
        technical_name="FS-1010",
        type=SensorType.FLOW,
        from_port=BoilerPort.FILL_OUT,
    )

    @property
    def DHW_output_temperature(self) -> Celsius:
        return self.rh33_domestic_hot_water.hot_temperature

    @property
    def DHW_input_temperature(self) -> Celsius:  # before preheat
        return self.rh33_domestic_hot_water.cold_temperature

    @property
    def DHW_delta_temperature(self) -> Celsius:
        return self.rh33_domestic_hot_water.delta_temperature

    @property
    def DHW_power(self) -> Celsius:
        return (
            self.fill_flow
            * self.rh33_domestic_hot_water.delta_temperature
            * self.spec.specific_heat_capacity_fill
        )


@sensors()
class PreHeatSensors(FromState):
    spec: Boiler
    rh33_preheat: RH33Sensors
    rh33_domestic_hot_water: RH33Sensors
    temperature: Celsius = sensor(technical_name="TS-1039")

    @property
    def exchange_input_temperature(self) -> Celsius:
        return self.rh33_preheat.hot_temperature

    @property
    def exchange_output_temperature(self) -> Celsius:
        return self.rh33_preheat.cold_temperature

    @property
    def exchange_delta_temperature(self) -> Celsius:
        return self.rh33_preheat.delta_temperature


@sensors()
class ColdReservoirSensors(FromState):
    spec: Boiler
    temperature: Celsius = sensor(technical_name="TS-1025")
    rh33_chill: RH33Sensors
    rh33_cooling_demand: RH33Sensors

    fill_flow: LiterPerSecond = sensor(
        technical_name="FS-1005", type=SensorType.FLOW, from_port=BoilerPort.FILL_OUT
    )

    @property
    def fill_input_temperature(self) -> Celsius:
        return self.rh33_cooling_demand.hot_temperature

    @property
    def fill_output_temperature(self) -> Celsius:
        return self.rh33_cooling_demand.cold_temperature

    @property
    def fill_delta_temperature(self) -> Celsius:
        return self.rh33_cooling_demand.delta_temperature

    @property
    def cooling_demand(self) -> Watt:
        return (
            self.fill_flow
            * self.fill_delta_temperature
            * self.spec.specific_heat_capacity_fill
        )

    exchange_flow: LiterPerSecond = sensor(
        technical_name="FS-1006",
        type=SensorType.FLOW,
        from_port=BoilerPort.HEAT_EXCHANGE_IN,
    )

    @property
    def exchange_input_temperature(self) -> Celsius:
        return self.rh33_chill.cold_temperature

    @property
    def exchange_output_temperature(self) -> Celsius:
        return self.rh33_chill.hot_temperature

    @property
    def exchange_delta_temperature(self) -> Celsius:
        return self.rh33_chill.delta_temperature

    @property
    def cooling_supply(self) -> Watt:
        return (
            self.exchange_flow
            * self.exchange_delta_temperature
            * self.spec.specific_heat_capacity_exchange
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
    pass


@sensors()
class HotSwitchSensors(ValveSensors):
    flow: LiterPerSecond = sensor(
        technical_name="FS-1011", type=SensorType.FLOW, from_port=ValvePort.AB
    )


@sensors()
class WasteMixSensors:
    flow: LiterPerSecond = sensor(
        technical_name="FS-1012", type=SensorType.FLOW, from_port=MixPort.AB
    )


@sensors()
class ChillerSensors(FromState):
    spec: Chiller
    rh33_chill: RH33Sensors
    rh33_waste: RH33Sensors
    chiller_switch_valve: "ChillerSwitchSensors"
    cold_reservoir: "ColdReservoirSensors"
    waste_mix: "WasteMixSensors"
    waste_switch_valve: "ValveSensors"

    @property
    def waste_flow(self) -> LiterPerSecond:
        return (
            self.waste_mix.flow
            if self.waste_switch_valve.position == WASTE_SWITCH_VALVE_CHILLER_POSITION
            else 0
        )

    @property
    def waste_input_temperature(self) -> Celsius:
        return (
            self.rh33_waste.cold_temperature
            if self.waste_switch_valve.position == WASTE_SWITCH_VALVE_CHILLER_POSITION
            else float("nan")
        )

    @property
    def waste_output_temperature(self) -> Celsius:
        return (
            self.rh33_waste.hot_temperature
            if self.waste_switch_valve.position == WASTE_SWITCH_VALVE_CHILLER_POSITION
            else float("nan")
        )

    @property
    def waste_delta_temperature(self) -> Celsius:
        return (
            self.rh33_waste.delta_temperature
            if self.waste_switch_valve.position == WASTE_SWITCH_VALVE_CHILLER_POSITION
            else float("nan")
        )

    @property
    def waste_heat(self) -> Watt:
        return (
            self.waste_flow
            * self.waste_delta_temperature
            * self.spec.specific_heat_capacity_cooling
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
    def chilled_input_temperature(self) -> Celsius:
        return (
            self.rh33_chill.hot_temperature
            if self.chiller_switch_valve.position
            == CHILLER_SWITCH_VALVE_CHILLER_POSITION
            else float("nan")
        )

    @property
    def chilled_output_temperature(
        self,
    ) -> Celsius:
        return (
            self.rh33_chill.cold_temperature
            if self.chiller_switch_valve.position
            == CHILLER_SWITCH_VALVE_CHILLER_POSITION
            else float("nan")
        )

    @property
    def chilled_delta_temperature(
        self,
    ) -> Celsius:
        return (
            self.rh33_chill.delta_temperature
            if self.chiller_switch_valve.position
            == CHILLER_SWITCH_VALVE_CHILLER_POSITION
            else float("nan")
        )

    @property
    def chill_power(self) -> Watt:
        return (
            self.chilled_flow
            * self.chilled_delta_temperature
            * self.spec.specific_heat_capacity_chilled
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


def schedule_sensor(schedule: "Callable[[PowerHubSchedules], Schedule[Any]]") -> Any:
    return power_hub_sensor(
        lambda power_hub, state: schedule(power_hub.schedules).at(state.time)
    )


def const_resolver(value: Any) -> "Callable[[PowerHub, NetworkState[PowerHub]], Any]":
    return lambda _a, _b: value


@sensors(from_appliance=False)
class WeatherSensors(WithoutAppliance):
    ambient_temperature: Celsius = schedule_sensor(
        lambda schedules: schedules.ambient_temperature
    )
    global_irradiance: WattPerMeterSquared = schedule_sensor(
        lambda schedules: schedules.global_irradiance
    )
    alarm: int = sensor(type=SensorType.ALARM, resolver=const_resolver(0))


@sensors(from_appliance=False)
class PressureSensors(WithoutAppliance):
    pressure: Bar = sensor(type=SensorType.PRESSURE, resolver=const_resolver(2))


@dataclass
class PowerHubSensors(NetworkSensors):
    heat_pipes: HeatPipesSensors
    heat_pipes_valve: ValveSensors
    heat_pipes_power_hub_pump: SwitchPumpSensors
    heat_pipes_supply_box_pump: SwitchPumpSensors
    hot_switch_valve: HotSwitchSensors
    hot_reservoir: HotReservoirSensors
    pcm: PcmSensors
    yazaki_hot_bypass_valve: ValveSensors
    yazaki: YazakiSensors
    chiller: ChillerSensors
    chiller_switch_valve: ChillerSwitchSensors
    cold_reservoir: ColdReservoirSensors
    waste_bypass_valve: ValveSensors
    preheat_switch_valve: ValveSensors
    preheat_reservoir: PreHeatSensors
    waste_switch_valve: ValveSensors
    outboard_exchange: HeatExchangerSensors
    weather: WeatherSensors
    pcm_to_yazaki_pump: SwitchPumpSensors
    chilled_loop_pump: SwitchPumpSensors
    waste_pump: SwitchPumpSensors
    waste_mix: WasteMixSensors
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
    waste_pressure_sensor: PressureSensors
    pipes_pressure_sensor: PressureSensors
    pcm_yazaki_pressure_sensor: PressureSensors
    time: datetime

    rh33_pcm_discharge: RH33Sensors = rh33(
        (lambda power_hub: power_hub.pcm, PcmPort.DISCHARGE_OUT),
        (lambda power_hub: power_hub.pcm, PcmPort.DISCHARGE_IN),
    )
    rh33_preheat: RH33Sensors = rh33(
        (lambda power_hub: power_hub.preheat_reservoir, BoilerPort.HEAT_EXCHANGE_IN),
        (lambda power_hub: power_hub.preheat_reservoir, BoilerPort.HEAT_EXCHANGE_OUT),
    )
    rh33_domestic_hot_water: RH33Sensors = rh33(
        (lambda power_hub: power_hub.hot_reservoir, BoilerPort.FILL_OUT),
        (lambda power_hub: power_hub.preheat_reservoir, BoilerPort.FILL_IN),
    )
    rh33_heat_pipes: RH33Sensors = rh33(
        (lambda power_hub: power_hub.heat_pipes, HeatPipesPort.OUT),
        (lambda power_hub: power_hub.heat_pipes, HeatPipesPort.IN),
    )
    rh33_hot_storage: RH33Sensors = rh33(
        (lambda power_hub: power_hub.hot_switch_valve, ValvePort.AB),
        (lambda power_hub: power_hub.hot_mix, MixPort.AB),
    )
    rh33_yazaki_hot: RH33Sensors = rh33(
        (lambda power_hub: power_hub.yazaki, YazakiPort.HOT_IN),
        (lambda power_hub: power_hub.yazaki, YazakiPort.HOT_OUT),
    )
    rh33_waste: RH33Sensors = rh33(
        (lambda power_hub: power_hub.waste_mix, MixPort.AB),
        (lambda power_hub: power_hub.waste_switch_valve, ValvePort.AB),
    )
    rh33_chill: RH33Sensors = rh33(
        (lambda power_hub: power_hub.chiller_switch_valve, ValvePort.AB),
        (lambda power_hub: power_hub.chill_mix, MixPort.AB),
    )
    rh33_heat_dump: RH33Sensors = rh33(
        (lambda power_hub: power_hub.outboard_exchange, HeatExchangerPort.A_IN),
        (lambda power_hub: power_hub.outboard_exchange, HeatExchangerPort.A_OUT),
    )
    rh33_cooling_demand: RH33Sensors = rh33(
        (lambda power_hub: power_hub.cold_reservoir, BoilerPort.FILL_IN),
        (lambda power_hub: power_hub.cold_reservoir, BoilerPort.FILL_OUT),
    )


SensorName = str
SensorValue = float | Celsius | LiterPerSecond | WattPerMeterSquared


def sensor_values(
    sensor_name: SensorName, sensors: PowerHubSensors
) -> dict[SensorName, SensorValue]:
    sensor = getattr(sensors, sensor_name)

    return {field: getattr(sensor, field) for field in sensor_fields(type(sensor))}
