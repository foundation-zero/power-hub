from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, TYPE_CHECKING, Optional

from energy_box_control.appliances import HeatPipes, HeatPipesPort, SwitchPump
from energy_box_control.appliances.base import (
    Port,
    ThermalState,
)
from energy_box_control.appliances.containers import Containers, FanAlarm, FilterAlarm
from energy_box_control.appliances.electrical import BatteryAlarm, Electrical
from energy_box_control.appliances.heat_exchanger import (
    HeatExchanger,
    HeatExchangerPort,
)

from energy_box_control.appliances.mix import MixPort

from energy_box_control.appliances.pv_panel import PVPanel
from energy_box_control.appliances.switch_pump import SwitchPumpAlarm
from energy_box_control.appliances.water_maker import (
    WaterMaker,
    WaterMakerPort,
)
from energy_box_control.appliances.water_tank import WaterTank
from energy_box_control.appliances.water_treatment import (
    WaterTreatment,
    WaterTreatmentPort,
)
from energy_box_control.network import AnyAppliance, NetworkState
from energy_box_control.power_hub.components import (
    CHILLER_SWITCH_VALVE_CHILLER_POSITION,
    CHILLER_SWITCH_VALVE_YAZAKI_POSITION,
    FRESHWATER_TEMPERATURE,
    HOT_RESERVOIR_PCM_VALVE_PCM_POSITION,
    HOT_RESERVOIR_PCM_VALVE_RESERVOIR_POSITION,
    WASTE_SWITCH_VALVE_CHILLER_POSITION,
    WASTE_SWITCH_VALVE_YAZAKI_POSITION,
    PCM_ZERO_TEMPERATURE,
    DEFAULT_PRESSURE,
)

if TYPE_CHECKING:
    from energy_box_control.power_hub.network import PowerHub, PowerHubSchedules

from energy_box_control.schedules import Schedule
from energy_box_control.units import (
    Ampere,
    Bar,
    Celsius,
    Hours,
    Joule,
    Liter,
    LiterPerSecond,
    Ppm,
    Percentage,
    Volt,
    Watt,
    WattPerMeterSquared,
)
from energy_box_control.appliances.boiler import Boiler, BoilerPort
from energy_box_control.appliances.chiller import Chiller, ChillerFaultCode
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


def const_resolver(value: Any) -> "Callable[[PowerHub, NetworkState[PowerHub]], Any]":
    return lambda _a, _b: value


def power_hub_sensor[
    T
](
    technical_name: Optional[str],
    type: Optional[SensorType],
    resolver: "Callable[[PowerHub, NetworkState[PowerHub]], T]",
):
    return sensor(technical_name=technical_name, type=type, resolver=resolver)


FlowServiceInfo = int


@sensors(from_appliance=False, eq=False)
class FlowSensors(WithoutAppliance):
    flow: LiterPerSecond
    temperature: Celsius
    glycol_concentration: Percentage
    total_volume: Liter
    service_info: FlowServiceInfo

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, FlowSensors):
            return False
        return self.flow == value.flow


type FlowResolver = "tuple[Callable[[PowerHub], AnyAppliance], Port]"


def flow_sensor(
    resolver: FlowResolver, technical_name: Optional[str], address: Optional[str] = None
) -> Any:

    appliance, port = resolver

    @sensors(from_appliance=False, eq=False)
    class Flow(FlowSensors):
        flow: LiterPerSecond = power_hub_sensor(
            technical_name,
            SensorType.FLOW,
            lambda power_hub, state: state.connection(
                appliance(power_hub), port, ThermalState(float("nan"), float("nan"))
            ).flow,
        )
        temperature: Celsius = power_hub_sensor(
            None,
            SensorType.TEMPERATURE,
            lambda power_hub, state: state.connection(
                appliance(power_hub), port, ThermalState(float("nan"), float("nan"))
            ).temperature,
        )
        glycol_concentration: Percentage = sensor(resolver=const_resolver(0))
        total_volume: Liter = sensor(resolver=const_resolver(0))
        service_info: FlowServiceInfo = sensor(
            type=SensorType.INFO, resolver=const_resolver(0)
        )

    return Flow


def flow_sensor_not_simulated(
    technical_name: Optional[str], address: Optional[str] = None
) -> Any:
    @sensors(from_appliance=False, eq=False)
    class NotSimulatedFlow(FlowSensors):
        flow: LiterPerSecond = sensor(
            technical_name=technical_name,
            type=SensorType.FLOW,
            resolver=const_resolver(0),
        )
        temperature: Celsius = sensor(
            technical_name=None,
            type=SensorType.TEMPERATURE,
            resolver=const_resolver(FRESHWATER_TEMPERATURE),
        )
        glycol_concentration: Percentage = sensor(resolver=const_resolver(0))
        total_volume: Liter = sensor(resolver=const_resolver(0))
        service_info: FlowServiceInfo = sensor(
            technical_name=None, type=SensorType.INFO, resolver=const_resolver(0)
        )

    return NotSimulatedFlow


RH33Alarm = int


@sensors(from_appliance=False, eq=False)
class RH33Sensors(WithoutAppliance):
    hot_temperature: Celsius
    cold_temperature: Celsius
    delta_temperature: Celsius
    status: RH33Alarm

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, RH33Sensors):
            return False
        return (
            self.cold_temperature == value.cold_temperature
            and self.delta_temperature == value.delta_temperature
            and self.hot_temperature == value.hot_temperature
        )


type TemperatureResolver = "tuple[Callable[[PowerHub], AnyAppliance], Port]"


def rh33(
    hot: TemperatureResolver,
    cold: TemperatureResolver,
    hot_technical_name: Optional[str],
    cold_technical_name: Optional[str],
    delta_technical_name: Optional[str],
) -> Any:
    hot_appliance, hot_port = hot
    cold_appliance, cold_port = cold

    @sensors(from_appliance=False, eq=False)
    class RH33(RH33Sensors):
        hot_temperature: Celsius = power_hub_sensor(
            hot_technical_name,
            SensorType.TEMPERATURE,
            lambda power_hub, state: state.connection(
                hot_appliance(power_hub),
                hot_port,
                ThermalState(float("nan"), float("nan")),
            ).temperature,
        )
        cold_temperature: Celsius = power_hub_sensor(
            cold_technical_name,
            SensorType.TEMPERATURE,
            lambda power_hub, state: state.connection(
                cold_appliance(power_hub),
                cold_port,
                ThermalState(float("nan"), float("nan")),
            ).temperature,
        )
        delta_temperature: Celsius = power_hub_sensor(
            delta_technical_name,
            SensorType.DELTA_T,
            lambda power_hub, state: state.connection(
                hot_appliance(power_hub),
                hot_port,
                ThermalState(float("nan"), float("nan")),
            ).temperature
            - state.connection(
                cold_appliance(power_hub),
                cold_port,
                ThermalState(float("nan"), float("nan")),
            ).temperature,
        )
        status: RH33Alarm = sensor(resolver=const_resolver(0))

    return RH33


@sensors()
class HeatPipesSensors(FromState):
    spec: HeatPipes
    rh33_heat_pipes: RH33Sensors
    heat_pipes_flow_sensor: FlowSensors

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
        return (
            self.heat_pipes_flow_sensor.flow
            * self.delta_temperature
            * self.spec.specific_heat_medium
        )


@sensors()
class PcmSensors(FromState):
    spec: Pcm
    temperature: Celsius = sensor(technical_name="TS-1007")
    rh33_pcm_discharge: RH33Sensors
    rh33_hot_storage: RH33Sensors
    hot_switch_valve: "ValveSensors"
    pcm_discharge_flow_sensor: FlowSensors
    hot_storage_flow_sensor: FlowSensors

    @property
    def discharge_input_temperature(self) -> Celsius:
        return self.rh33_pcm_discharge.cold_temperature

    @property
    def discharge_output_temperature(self) -> Celsius:
        return self.rh33_pcm_discharge.hot_temperature

    @property
    def discharge_delta_temperature(self) -> Celsius:
        return self.rh33_pcm_discharge.delta_temperature

    @property
    def discharge_flow(self) -> LiterPerSecond:
        return self.pcm_discharge_flow_sensor.flow

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
            self.hot_storage_flow_sensor.flow
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
    def state_of_charge(self) -> float:
        # TODO: improve this based on reality
        return 1 if self.charged else 0

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
    waste_switch_valve: "ValveSensors"
    chilled_loop_pump: "PressuredPumpSensors"
    waste_pressure_sensor: "PressureSensors"
    pcm_yazaki_pressure_sensor: "PressureSensors"
    yazaki_hot_flow_sensor: "FlowSensors"
    waste_flow_sensor: "FlowSensors"
    chilled_flow_sensor: "FlowSensors"

    @property
    def hot_flow(self) -> LiterPerSecond:
        return self.yazaki_hot_flow_sensor.flow

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
            self.waste_flow_sensor.flow
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
            self.chilled_flow_sensor.flow
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
    heat_dump_flow_sensor: FlowSensors

    @property
    def flow(self) -> LiterPerSecond:
        return self.heat_dump_flow_sensor.flow

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
    hot_storage_flow_sensor: FlowSensors
    domestic_hot_water_flow_sensor: FlowSensors
    hot_switch_valve: "ValveSensors"

    @property
    def exchange_flow(self) -> LiterPerSecond:
        return (
            self.hot_storage_flow_sensor.flow
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

    @property
    def fill_flow(self) -> LiterPerSecond:
        return self.domestic_hot_water_flow_sensor.flow

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
    chilled_flow_sensor: FlowSensors
    cooling_demand_flow_sensor: FlowSensors

    @property
    def fill_flow(self) -> LiterPerSecond:
        return self.cooling_demand_flow_sensor.flow

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

    @property
    def exchange_flow(self) -> LiterPerSecond:
        return self.chilled_flow_sensor.flow

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


# from https://drive.google.com/file/d/1NCEg1okokmtj-2J-3ZsKRvVXCTlQC4ao/view
# index is aligned with bit position for that code
CHILLER_FAULTS = [
    ["AAA"],
    ["A01"],
    ["A02"],
    ["A09"],
    ["A10"],
    ["INIT"],
    ["A15"],
    ["A20"],
    ["A21"],
    ["A22"],
    ["A23"],
    ["A24"],
    ["A25"],
    ["A26"],
    ["A27"],
    ["A28"],
    [f"A{err}" for err in range(30, 55)],
]


@sensors()
class ChillerSensors(FromState):
    spec: Chiller
    rh33_chill: RH33Sensors
    rh33_waste: RH33Sensors
    fault_code: ChillerFaultCode = sensor(type=SensorType.ALARM)
    chiller_switch_valve: "ChillerSwitchSensors"
    cold_reservoir: "ColdReservoirSensors"
    waste_switch_valve: "ValveSensors"
    waste_flow_sensor: FlowSensors
    chilled_flow_sensor: FlowSensors
    chilled_loop_pump: "PressuredPumpSensors"
    waste_pressure_sensor: "PressureSensors"

    @property
    def waste_flow(self) -> LiterPerSecond:
        return (
            self.waste_flow_sensor.flow
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
            self.chilled_flow_sensor.flow
            if self.chiller_switch_valve.position
            == CHILLER_SWITCH_VALVE_CHILLER_POSITION
            else 0
        )

    @property
    def waste_pressure(self) -> Celsius:
        return (
            self.waste_pressure_sensor.pressure
            if self.waste_switch_valve.position == WASTE_SWITCH_VALVE_CHILLER_POSITION
            else float("nan")
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
    def chilled_pressure(
        self,
    ) -> LiterPerSecond:
        return (
            self.chilled_loop_pump.pressure
            if self.chiller_switch_valve.position
            == CHILLER_SWITCH_VALVE_CHILLER_POSITION
            else 0
        )

    @property
    def chill_power(self) -> Watt:
        return (
            self.chilled_flow
            * self.chilled_delta_temperature
            * self.spec.specific_heat_capacity_chilled
        )

    def faults(self) -> list[str]:
        return [
            fault
            for index, faults in enumerate(CHILLER_FAULTS)
            if self.fault_code & (1 << index)
            for fault in faults
        ]


@sensors()
class SwitchPumpSensors(FromState):
    spec: SwitchPump
    on: bool = sensor()

    @property
    def electrical_power(self) -> Watt:
        return self.spec.electrical_power if self.on else 0


@sensors()
class SmartPumpSensors(SwitchPumpSensors):
    pump_1_alarm: SwitchPumpAlarm = sensor(type=SensorType.ALARM)
    pump_1_communication_fault: SwitchPumpAlarm = sensor(type=SensorType.ALARM)


@sensors()
class PressuredPumpSensors(SmartPumpSensors):
    pressure: Bar = sensor()


@sensors()
class PVSensors(FromState):
    spec: PVPanel
    power: Watt = sensor()


@sensors()
class ElectricalSensors(FromState):
    spec: Electrical
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
    estop_active: bool = sensor(type=SensorType.BOOL)
    office_voltage_L1: Volt = sensor(type=SensorType.VOLTAGE)
    office_current_L1: Ampere = sensor(type=SensorType.CURRENT)
    office_power_L1: Watt = sensor(type=SensorType.POWER)
    office_voltage_L2: Volt = sensor(type=SensorType.VOLTAGE)
    office_current_L2: Ampere = sensor(type=SensorType.CURRENT)
    office_power_L2: Watt = sensor(type=SensorType.POWER)
    office_voltage_L3: Volt = sensor(type=SensorType.VOLTAGE)
    office_current_L3: Ampere = sensor(type=SensorType.CURRENT)
    office_power_L3: Watt = sensor(type=SensorType.POWER)
    workshop_voltage_L1: Volt = sensor(type=SensorType.VOLTAGE)
    workshop_current_L1: Ampere = sensor(type=SensorType.CURRENT)
    workshop_power_L1: Watt = sensor(type=SensorType.POWER)
    workshop_voltage_L2: Volt = sensor(type=SensorType.VOLTAGE)
    workshop_current_L2: Ampere = sensor(type=SensorType.CURRENT)
    workshop_power_L2: Watt = sensor(type=SensorType.POWER)
    workshop_voltage_L3: Volt = sensor(type=SensorType.VOLTAGE)
    workshop_current_L3: Ampere = sensor(type=SensorType.CURRENT)
    workshop_power_L3: Watt = sensor(type=SensorType.POWER)
    sim_room_storage_voltage_L1: Volt = sensor(type=SensorType.VOLTAGE)
    sim_room_storage_current_L1: Ampere = sensor(type=SensorType.CURRENT)
    sim_room_storage_power_L1: Watt = sensor(type=SensorType.POWER)
    sim_room_storage_voltage_L2: Volt = sensor(type=SensorType.VOLTAGE)
    sim_room_storage_current_L2: Ampere = sensor(type=SensorType.CURRENT)
    sim_room_storage_power_L2: Watt = sensor(type=SensorType.POWER)
    sim_room_storage_voltage_L3: Volt = sensor(type=SensorType.VOLTAGE)
    sim_room_storage_current_L3: Ampere = sensor(type=SensorType.CURRENT)
    sim_room_storage_power_L3: Watt = sensor(type=SensorType.POWER)
    kitchen_sanitary_voltage_L1: Volt = sensor(type=SensorType.VOLTAGE)
    kitchen_sanitary_current_L1: Ampere = sensor(type=SensorType.CURRENT)
    kitchen_sanitary_power_L1: Watt = sensor(type=SensorType.POWER)
    kitchen_sanitary_voltage_L2: Volt = sensor(type=SensorType.VOLTAGE)
    kitchen_sanitary_current_L2: Ampere = sensor(type=SensorType.CURRENT)
    kitchen_sanitary_power_L2: Watt = sensor(type=SensorType.POWER)
    kitchen_sanitary_voltage_L3: Volt = sensor(type=SensorType.VOLTAGE)
    kitchen_sanitary_current_L3: Ampere = sensor(type=SensorType.CURRENT)
    kitchen_sanitary_power_L3: Watt = sensor(type=SensorType.POWER)
    kitchen_sanitary_voltage_L1: Volt = sensor(type=SensorType.VOLTAGE)
    kitchen_sanitary_current_L1: Ampere = sensor(type=SensorType.CURRENT)
    kitchen_sanitary_power_L1: Watt = sensor(type=SensorType.POWER)
    kitchen_sanitary_voltage_L2: Volt = sensor(type=SensorType.VOLTAGE)
    kitchen_sanitary_current_L2: Ampere = sensor(type=SensorType.CURRENT)
    kitchen_sanitary_power_L2: Watt = sensor(type=SensorType.POWER)
    kitchen_sanitary_voltage_L3: Volt = sensor(type=SensorType.VOLTAGE)
    kitchen_sanitary_current_L3: Ampere = sensor(type=SensorType.CURRENT)
    kitchen_sanitary_power_L3: Watt = sensor(type=SensorType.POWER)
    supply_box_voltage_L1: Volt = sensor(type=SensorType.VOLTAGE)
    supply_box_current_L1: Ampere = sensor(type=SensorType.CURRENT)
    supply_box_power_L1: Watt = sensor(type=SensorType.POWER)
    supply_box_voltage_L2: Volt = sensor(type=SensorType.VOLTAGE)
    supply_box_current_L2: Ampere = sensor(type=SensorType.CURRENT)
    supply_box_power_L2: Watt = sensor(type=SensorType.POWER)
    supply_box_voltage_L3: Volt = sensor(type=SensorType.VOLTAGE)
    supply_box_current_L3: Ampere = sensor(type=SensorType.CURRENT)
    supply_box_power_L3: Watt = sensor(type=SensorType.POWER)
    center_1_voltage_L1: Volt = sensor(type=SensorType.VOLTAGE)
    center_1_current_L1: Ampere = sensor(type=SensorType.CURRENT)
    center_1_power_L1: Watt = sensor(type=SensorType.POWER)
    center_1_voltage_L2: Volt = sensor(type=SensorType.VOLTAGE)
    center_1_current_L2: Ampere = sensor(type=SensorType.CURRENT)
    center_1_power_L2: Watt = sensor(type=SensorType.POWER)
    center_1_voltage_L3: Volt = sensor(type=SensorType.VOLTAGE)
    center_1_current_L3: Ampere = sensor(type=SensorType.CURRENT)
    center_1_power_L3: Watt = sensor(type=SensorType.POWER)
    center_2_voltage_L1: Volt = sensor(type=SensorType.VOLTAGE)
    center_2_current_L1: Ampere = sensor(type=SensorType.CURRENT)
    center_2_power_L1: Watt = sensor(type=SensorType.POWER)
    center_2_voltage_L2: Volt = sensor(type=SensorType.VOLTAGE)
    center_2_current_L2: Ampere = sensor(type=SensorType.CURRENT)
    center_2_power_L2: Watt = sensor(type=SensorType.POWER)
    center_2_voltage_L3: Volt = sensor(type=SensorType.VOLTAGE)
    center_2_current_L3: Ampere = sensor(type=SensorType.CURRENT)
    center_2_power_L3: Watt = sensor(type=SensorType.POWER)
    thermo_cabinet_voltage_L1: Volt = sensor(type=SensorType.VOLTAGE)
    thermo_cabinet_current_L1: Ampere = sensor(type=SensorType.CURRENT)
    thermo_cabinet_power_L1: Watt = sensor(type=SensorType.POWER)
    thermo_cabinet_voltage_L2: Volt = sensor(type=SensorType.VOLTAGE)
    thermo_cabinet_current_L2: Ampere = sensor(type=SensorType.CURRENT)
    thermo_cabinet_power_L2: Watt = sensor(type=SensorType.POWER)
    thermo_cabinet_voltage_L3: Volt = sensor(type=SensorType.VOLTAGE)
    thermo_cabinet_current_L3: Ampere = sensor(type=SensorType.CURRENT)
    thermo_cabinet_power_L3: Watt = sensor(type=SensorType.POWER)


@sensors()
class WaterTankSensors(FromState):
    spec: WaterTank
    fill_ratio: float = sensor()

    @property
    def fill(self) -> Liter:
        return self.fill_ratio * self.spec.capacity


@sensors()
class FreshWaterTankSensors(WaterTankSensors):
    water_maker: "WaterMakerSensors"
    fill_ratio: float = sensor(technical_name="LS-5001", type=SensorType.LEVEL)
    fresh_to_kitchen_flow_sensor: FlowSensors
    fresh_to_technical_flow_sensor: FlowSensors

    @property
    def fill_flow(self) -> LiterPerSecond:
        return self.water_maker.production_flow

    @property
    def flow_to_kitchen(self) -> LiterPerSecond:
        return self.fresh_to_kitchen_flow_sensor.flow

    @property
    def flow_to_technical(self) -> LiterPerSecond:
        return self.fresh_to_technical_flow_sensor.flow

    @property
    def water_demand_flow(self) -> LiterPerSecond:
        return self.flow_to_kitchen + self.flow_to_technical


@sensors(from_appliance=False)
class TechnicalWaterSensors(WithoutAppliance):
    fill_ratio: float = sensor(technical_name="LS-4001", type=SensorType.LEVEL)
    technical_to_wash_off: FlowSensors
    technical_to_sanitary: FlowSensors

    def flow_to_sanitary(self) -> LiterPerSecond:
        return self.technical_to_sanitary.flow

    def flow_to_wash_off(self) -> LiterPerSecond:
        return self.technical_to_wash_off.flow


@sensors()
class GreyWaterTankSensors(WaterTankSensors):
    fill_ratio: float = sensor(technical_name="LS-3001", type=SensorType.FLOW)


@sensors()
class WaterTreatmentSensors(FromState):
    spec: WaterTreatment
    treated_water_flow_sensor: FlowSensors

    @property
    def out_flow(self) -> LiterPerSecond:
        return self.treated_water_flow_sensor.flow


@sensors()
class WaterMakerSensors(FromState):
    spec: WaterMaker
    production_flow: LiterPerSecond = sensor(
        type=SensorType.FLOW, from_port=WaterMakerPort.DESALINATED_OUT
    )
    tank_empty: bool = sensor(type=SensorType.BOOL)
    status: int = sensor(SensorType.INFO)
    error: int = sensor(type=SensorType.ALARM, resolver=const_resolver(0))
    warning: int = sensor(type=SensorType.ALARM, resolver=const_resolver(0))
    last_error_id: int = sensor(resolver=const_resolver(0))
    last_warning_id: int = sensor(resolver=const_resolver(0))
    feed_pressure: Bar = sensor(resolver=const_resolver(0))
    membrane_pressure: Bar = sensor(resolver=const_resolver(0))
    cumulative_operation_time: Hours = sensor(resolver=const_resolver(0))
    salinity: Ppm = sensor(resolver=const_resolver(0))
    time_to_service: float = sensor(resolver=const_resolver(0))
    total_water_production: Liter = sensor(resolver=const_resolver(0))
    current_water_production: Liter = sensor(resolver=const_resolver(0))


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
        None,
        None,
        lambda power_hub, state: schedule(power_hub.schedules).at(state.time),
    )


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
    pressure: Bar = sensor(
        type=SensorType.PRESSURE, resolver=const_resolver(DEFAULT_PRESSURE)
    )


def describe(technical_name: str, address: Optional[str] = None) -> Any:
    return field(metadata={"technical_name": technical_name, "address": address})


@dataclass
class PowerHubSensors(NetworkSensors):
    time: datetime

    heat_pipes: HeatPipesSensors = describe("W-1001")
    heat_pipes_valve: ValveSensors = describe("CV-1006", "35k10/4")
    heat_pipes_power_hub_pump: SwitchPumpSensors = describe("P-1008", "35k17/1")
    heat_pipes_supply_box_pump: SwitchPumpSensors = describe("P-1009", "11k11/0")
    hot_switch_valve: ValveSensors = describe("CV-1001", "35k10/1")
    hot_reservoir: HotReservoirSensors = describe("W-1002")
    pcm: PcmSensors = describe("W-1003")
    yazaki_hot_bypass_valve: ValveSensors = describe("CV-1010", "35k10/7")
    yazaki: YazakiSensors = describe("W-1005", "35k10/8")
    chiller: ChillerSensors = describe("W-1009")
    chiller_switch_valve: ChillerSwitchSensors = describe("CV-1008", "35k10/6")
    cold_reservoir: ColdReservoirSensors = describe("W-1006")
    waste_bypass_valve: ValveSensors = describe("CV-1004", "35k10/3")
    preheat_switch_valve: ValveSensors = describe("CV-1003", "35k10/2")
    preheat_reservoir: PreHeatSensors = describe("W-1008")
    waste_switch_valve: ValveSensors = describe("CV-1007", "35k10/5")
    outboard_exchange: HeatExchangerSensors = describe("W-1007")
    weather: WeatherSensors = describe("WSC-11", "35k10/10")
    pcm_to_yazaki_pump: PressuredPumpSensors = describe("P-1003", "35k10/11")
    chilled_loop_pump: PressuredPumpSensors = describe("P-1005", "35k10/13")
    waste_pump: SmartPumpSensors = describe("P-1004", "35k10/12")
    hot_water_pump: SwitchPumpSensors = describe("simulation-only")
    outboard_pump: SwitchPumpSensors = describe("P-1002", "35k17/0, 35k16/0")
    cooling_demand_pump: PressuredPumpSensors = describe("P-1007", "192.168.1.46")
    pv_panel: PVSensors = describe("not-in-drawing")
    electrical: ElectricalSensors = describe("electrical-plc", "192.168.1.15")
    fresh_water_tank: FreshWaterTankSensors = describe("K-5001")
    grey_water_tank: GreyWaterTankSensors = describe("K-3001")
    black_water_tank: WaterTankSensors = describe("K-2001/K-2002")
    technical_water_tank: WaterTankSensors = describe("K-4001")
    water_treatment: WaterTreatmentSensors = describe("F-3001", "35k10/9")
    water_maker: WaterMakerSensors = describe("F-5001")
    containers: ContainersSensors = describe("not-in-drawing")
    waste_pressure_sensor: PressureSensors = describe("PS-1002", "35k13/1")
    pipes_pressure_sensor: PressureSensors = describe("PS-1003", "35k13/2")
    pcm_yazaki_pressure_sensor: PressureSensors = describe("PS-1001", "35k13/0")
    technical_water_regulator: ValveSensors = describe("CV-4001", "35k18/4")
    water_filter_bypass_valve: ValveSensors = describe("CV-5001", "35k18/5")
    heat_pipes_flow_sensor: FlowSensors = flow_sensor(
        (lambda power_hub: power_hub.heat_pipes, HeatPipesPort.IN), "FS-1001", "35k9/1"
    )
    pcm_discharge_flow_sensor: FlowSensors = flow_sensor(
        (lambda power_hub: power_hub.pcm, PcmPort.DISCHARGE_IN), "FS-1003", "35k9/2"
    )
    hot_storage_flow_sensor: FlowSensors = flow_sensor(
        (lambda power_hub: power_hub.hot_switch_valve, ValvePort.AB),
        "FS-1011",
        "35k9/7",
    )
    yazaki_hot_flow_sensor: FlowSensors = flow_sensor(
        (lambda power_hub: power_hub.yazaki, YazakiPort.HOT_IN), "FS-1004", "35k9/3"
    )
    waste_flow_sensor: FlowSensors = flow_sensor(
        (lambda power_hub: power_hub.waste_mix, MixPort.AB), "FS-1012", "35k9/8"
    )
    chilled_flow_sensor: FlowSensors = flow_sensor(
        (lambda power_hub: power_hub.chill_mix, MixPort.AB), "FS-1006", "35k9/4"
    )
    cooling_demand_flow_sensor: FlowSensors = flow_sensor(
        (lambda power_hub: power_hub.cold_reservoir, BoilerPort.FILL_OUT),
        "FS-1005",
        "35k18/7",
    )
    heat_dump_flow_sensor: FlowSensors = flow_sensor(
        (lambda power_hub: power_hub.outboard_exchange, HeatExchangerPort.A_OUT),
        "FS-1009",
        "35k9/5",
    )
    domestic_hot_water_flow_sensor: FlowSensors = flow_sensor(
        (lambda power_hub: power_hub.hot_reservoir, BoilerPort.FILL_OUT),
        "FS-1010",
        "35k9/6",
    )
    fresh_to_kitchen_flow_sensor: FlowSensors = flow_sensor_not_simulated(
        "FS-5001", "35k9/10"
    )
    technical_to_sanitary_flow_sensor: FlowSensors = flow_sensor_not_simulated(
        "FS-4003", "35k18/2"
    )
    technical_to_wash_off_flow_sensor: FlowSensors = flow_sensor_not_simulated(
        "FS-4002", "35k18/1"
    )
    fresh_to_technical_flow_sensor: FlowSensors = flow_sensor_not_simulated(
        "FS-5002", "35k18/3"
    )
    treated_water_flow_sensor: FlowSensors = flow_sensor(
        (lambda power_hub: power_hub.water_treatment, WaterTreatmentPort.OUT),
        "FS-4001",
        "35k9/9",
    )

    rh33_pcm_discharge: RH33Sensors = rh33(
        (lambda power_hub: power_hub.pcm, PcmPort.DISCHARGE_OUT),
        (lambda power_hub: power_hub.pcm, PcmPort.DISCHARGE_IN),
        "TS-1031",
        "TS-1030",
        "EM-A",
    )
    rh33_preheat: RH33Sensors = rh33(
        (lambda power_hub: power_hub.preheat_reservoir, BoilerPort.HEAT_EXCHANGE_IN),
        (lambda power_hub: power_hub.preheat_reservoir, BoilerPort.HEAT_EXCHANGE_OUT),
        "TS-1032",
        "TS-1034",
        "EM-B",
    )
    rh33_domestic_hot_water: RH33Sensors = rh33(
        (lambda power_hub: power_hub.hot_reservoir, BoilerPort.FILL_OUT),
        (lambda power_hub: power_hub.preheat_reservoir, BoilerPort.FILL_IN),
        "TS-1040",
        "TS-1042",
        "EM-C",
    )
    rh33_heat_pipes: RH33Sensors = rh33(
        (lambda power_hub: power_hub.heat_pipes, HeatPipesPort.OUT),
        (lambda power_hub: power_hub.heat_pipes, HeatPipesPort.IN),
        "TS-1002",
        "TS-1001",
        "EM-E",
    )
    rh33_hot_storage: RH33Sensors = rh33(
        (lambda power_hub: power_hub.hot_switch_valve, ValvePort.AB),
        (lambda power_hub: power_hub.hot_mix, MixPort.AB),
        "TS-1005",
        "TS-1006",
        "EM-F",
    )
    rh33_yazaki_hot: RH33Sensors = rh33(
        (lambda power_hub: power_hub.yazaki, YazakiPort.HOT_IN),
        (lambda power_hub: power_hub.yazaki, YazakiPort.HOT_OUT),
        "TS-1010",
        "TS-1011",
        "EM-G",
    )
    rh33_waste: RH33Sensors = rh33(
        (lambda power_hub: power_hub.waste_mix, MixPort.AB),
        (lambda power_hub: power_hub.waste_switch_valve, ValvePort.AB),
        "TS-1014",
        "TS-1015",
        "EM-H",
    )
    rh33_chill: RH33Sensors = rh33(
        (lambda power_hub: power_hub.chiller_switch_valve, ValvePort.AB),
        (lambda power_hub: power_hub.chill_mix, MixPort.AB),
        "TS-1023",
        "TS-1024",
        "EM-I",
    )
    rh33_heat_dump: RH33Sensors = rh33(
        (lambda power_hub: power_hub.outboard_exchange, HeatExchangerPort.A_IN),
        (lambda power_hub: power_hub.outboard_exchange, HeatExchangerPort.A_OUT),
        "TS-1035",
        "TS-1036",
        "EM-J",
    )
    rh33_cooling_demand: RH33Sensors = rh33(
        (lambda power_hub: power_hub.cold_reservoir, BoilerPort.FILL_IN),
        (lambda power_hub: power_hub.cold_reservoir, BoilerPort.FILL_OUT),
        "TS-1026",
        "TS-1027",
        "EM-K",
    )


SensorName = str
SensorValue = float | Celsius | LiterPerSecond | WattPerMeterSquared


def sensor_values(
    sensor_name: SensorName, sensors: PowerHubSensors
) -> dict[SensorName, SensorValue]:
    sensor = getattr(sensors, sensor_name)

    return {field: getattr(sensor, field) for field in sensor_fields(type(sensor))}
