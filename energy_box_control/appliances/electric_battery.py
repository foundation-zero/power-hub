from dataclasses import dataclass

from energy_box_control.appliances.base import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    Port,
)
from energy_box_control.time import ProcessTime
from energy_box_control.schedules import Schedule
from energy_box_control.units import Celsius


BatteryAlarm = int  # 0: no Alarm, 1: Warning, 2: Alarm
NO_ALARM = 0
from energy_box_control.units import BatteryAlarm, Celsius


@dataclass(frozen=True, eq=True)
class ElectricBatteryState(ApplianceState):
    voltage_battery_system: int = 0
    current_battery_system: int = 0
    power_battery_system: int = 0
    soc_battery_system: float = 0
    battery_alarm: int = NO_ALARM
    battery_low_voltage_alarm: int = NO_ALARM
    battery_high_voltage_alarm: int = NO_ALARM
    battery_low_starter_voltage_alarm: int = NO_ALARM
    battery_high_starter_voltage_alarm: int = NO_ALARM
    battery_low_soc_alarm: BatteryAlarm = NO_ALARM
    battery_low_temperature_alarm: BatteryAlarm = NO_ALARM
    battery_high_temperature_alarm: BatteryAlarm = NO_ALARM
    battery_mid_voltage_alarm: BatteryAlarm = NO_ALARM
    battery_low_fused_voltage_alarm: BatteryAlarm = NO_ALARM
    battery_high_fused_voltage_alarm: BatteryAlarm = NO_ALARM
    battery_fuse_blown_alarm: BatteryAlarm = NO_ALARM
    battery_high_internal_temperature_alarm: BatteryAlarm = NO_ALARM
    battery_high_charge_current_alarm: BatteryAlarm = NO_ALARM
    battery_high_discharge_current_alarm: BatteryAlarm = NO_ALARM
    battery_cell_imbalance_alarm: BatteryAlarm = NO_ALARM
    battery_internal_failure_alarm: BatteryAlarm = NO_ALARM
    battery_high_charge_temperature_alarm: BatteryAlarm = NO_ALARM
    battery_low_charge_temperature_alarm: BatteryAlarm = NO_ALARM
    battery_low_cell_voltage_alarm: BatteryAlarm = NO_ALARM
    battery_error: int = NO_ALARM
    high_temperature_alarm: BatteryAlarm = NO_ALARM
    high_battery_voltage_alarm: BatteryAlarm = NO_ALARM
    high_ac_out_voltage_alarm: BatteryAlarm = NO_ALARM
    low_temperature_alarm: BatteryAlarm = NO_ALARM
    low_battery_voltage_alarm: BatteryAlarm = NO_ALARM
    low_ac_out_voltage_alarm: BatteryAlarm = NO_ALARM
    overload_alarm: BatteryAlarm = NO_ALARM
    ripple_alarm: BatteryAlarm = NO_ALARM
    low_batt_voltage_alarm: BatteryAlarm = NO_ALARM
    high_batt_voltage_alarm: BatteryAlarm = NO_ALARM


class ElectricBatteryPort(Port):
    pass


@dataclass(frozen=True, eq=True)
class ElectricBatteryControl(ApplianceControl):
    pass


@dataclass(frozen=True, eq=True)
class ElectricBattery(
    Appliance[ElectricBatteryState, None, Port, dict[None, None], dict[None, None]]
):
    global_irradiance_schedule: Schedule[Celsius]

    def simulate(
        self,
        inputs: dict[None, None],
        previous_state: ElectricBatteryState,
        control: None,
        simulation_time: ProcessTime,
    ) -> tuple[ElectricBatteryState, dict[None, None]]:

        return (
            ElectricBatteryState(
                soc_battery_system=self.global_irradiance_schedule.at(simulation_time)
                * 0.1,
            ),
            {},
        )
