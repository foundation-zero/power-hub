from dataclasses import dataclass

from energy_box_control.appliances.base import (
    Appliance,
    ApplianceState,
    Port,
)
from energy_box_control.time import ProcessTime
from energy_box_control.schedules import Schedule
from energy_box_control.units import Ampere, Celsius, Volt, Watt


BatteryAlarm = int  # 0: no Alarm, 1: Warning, 2: Alarm
NO_ALARM = 0
DEFAULT_VOLTAGE = 230
DEFAULT_CURRENT = 1
DEFAULT_POWER = 230


@dataclass(frozen=True, eq=True)
class ElectricalState(ApplianceState):
    voltage_battery_system: int = 0
    current_battery_system: int = 0
    power_battery_system: int = 0
    soc_battery_system: float = 75
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
    estop_active: bool = False
    office_voltage_L1: Volt = DEFAULT_VOLTAGE
    office_current_L1: Ampere = DEFAULT_CURRENT
    office_power_L1: Watt = DEFAULT_POWER
    office_voltage_L2: Volt = DEFAULT_VOLTAGE
    office_current_L2: Ampere = DEFAULT_CURRENT
    office_power_L2: Watt = DEFAULT_POWER
    office_voltage_L3: Volt = DEFAULT_VOLTAGE
    office_current_L3: Ampere = DEFAULT_CURRENT
    office_power_L3: Watt = DEFAULT_POWER
    workshop_voltage_L1: Volt = DEFAULT_VOLTAGE
    workshop_current_L1: Ampere = DEFAULT_CURRENT
    workshop_power_L1: Watt = DEFAULT_POWER
    workshop_voltage_L2: Volt = DEFAULT_VOLTAGE
    workshop_current_L2: Ampere = DEFAULT_CURRENT
    workshop_power_L2: Watt = DEFAULT_POWER
    workshop_voltage_L3: Volt = DEFAULT_VOLTAGE
    workshop_current_L3: Ampere = DEFAULT_CURRENT
    workshop_power_L3: Watt = DEFAULT_POWER
    sim_room_storage_voltage_L1: Volt = DEFAULT_VOLTAGE
    sim_room_storage_current_L1: Ampere = DEFAULT_CURRENT
    sim_room_storage_power_L1: Watt = DEFAULT_POWER
    sim_room_storage_voltage_L2: Volt = DEFAULT_VOLTAGE
    sim_room_storage_current_L2: Ampere = DEFAULT_CURRENT
    sim_room_storage_power_L2: Watt = DEFAULT_POWER
    sim_room_storage_voltage_L3: Volt = DEFAULT_VOLTAGE
    sim_room_storage_current_L3: Ampere = DEFAULT_CURRENT
    sim_room_storage_power_L3: Watt = DEFAULT_POWER
    kitchen_sanitary_voltage_L1: Volt = DEFAULT_VOLTAGE
    kitchen_sanitary_current_L1: Ampere = DEFAULT_CURRENT
    kitchen_sanitary_power_L1: Watt = DEFAULT_POWER
    kitchen_sanitary_voltage_L2: Volt = DEFAULT_VOLTAGE
    kitchen_sanitary_current_L2: Ampere = DEFAULT_CURRENT
    kitchen_sanitary_power_L2: Watt = DEFAULT_POWER
    kitchen_sanitary_voltage_L3: Volt = DEFAULT_VOLTAGE
    kitchen_sanitary_current_L3: Ampere = DEFAULT_CURRENT
    kitchen_sanitary_power_L3: Watt = DEFAULT_POWER
    kitchen_sanitary_voltage_L1: Volt = DEFAULT_VOLTAGE
    kitchen_sanitary_current_L1: Ampere = DEFAULT_CURRENT
    kitchen_sanitary_power_L1: Watt = DEFAULT_POWER
    kitchen_sanitary_voltage_L2: Volt = DEFAULT_VOLTAGE
    kitchen_sanitary_current_L2: Ampere = DEFAULT_CURRENT
    kitchen_sanitary_power_L2: Watt = DEFAULT_POWER
    kitchen_sanitary_voltage_L3: Volt = DEFAULT_VOLTAGE
    kitchen_sanitary_current_L3: Ampere = DEFAULT_CURRENT
    kitchen_sanitary_power_L3: Watt = DEFAULT_POWER
    supply_box_voltage_L1: Volt = DEFAULT_VOLTAGE
    supply_box_current_L1: Ampere = DEFAULT_CURRENT
    supply_box_power_L1: Watt = DEFAULT_POWER
    supply_box_voltage_L2: Volt = DEFAULT_VOLTAGE
    supply_box_current_L2: Ampere = DEFAULT_CURRENT
    supply_box_power_L2: Watt = DEFAULT_POWER
    supply_box_voltage_L3: Volt = DEFAULT_VOLTAGE
    supply_box_current_L3: Ampere = DEFAULT_CURRENT
    supply_box_power_L3: Watt = DEFAULT_POWER
    center_1_voltage_L1: Volt = DEFAULT_VOLTAGE
    center_1_current_L1: Ampere = DEFAULT_CURRENT
    center_1_power_L1: Watt = DEFAULT_POWER
    center_1_voltage_L2: Volt = DEFAULT_VOLTAGE
    center_1_current_L2: Ampere = DEFAULT_CURRENT
    center_1_power_L2: Watt = DEFAULT_POWER
    center_1_voltage_L3: Volt = DEFAULT_VOLTAGE
    center_1_current_L3: Ampere = DEFAULT_CURRENT
    center_1_power_L3: Watt = DEFAULT_POWER
    center_2_voltage_L1: Volt = DEFAULT_VOLTAGE
    center_2_current_L1: Ampere = DEFAULT_CURRENT
    center_2_power_L1: Watt = DEFAULT_POWER
    center_2_voltage_L2: Volt = DEFAULT_VOLTAGE
    center_2_current_L2: Ampere = DEFAULT_CURRENT
    center_2_power_L2: Watt = DEFAULT_POWER
    center_2_voltage_L3: Volt = DEFAULT_VOLTAGE
    center_2_current_L3: Ampere = DEFAULT_CURRENT
    center_2_power_L3: Watt = DEFAULT_POWER
    thermo_cabinet_voltage_L1: Volt = DEFAULT_VOLTAGE
    thermo_cabinet_current_L1: Ampere = DEFAULT_CURRENT
    thermo_cabinet_power_L1: Watt = DEFAULT_POWER
    thermo_cabinet_voltage_L2: Volt = DEFAULT_VOLTAGE
    thermo_cabinet_current_L2: Ampere = DEFAULT_CURRENT
    thermo_cabinet_power_L2: Watt = DEFAULT_POWER
    thermo_cabinet_voltage_L3: Volt = DEFAULT_VOLTAGE
    thermo_cabinet_current_L3: Ampere = DEFAULT_CURRENT
    thermo_cabinet_power_L3: Watt = DEFAULT_POWER


class ElectricalPort(Port):
    pass


@dataclass(frozen=True, eq=True)
class Electrical(
    Appliance[ElectricalState, None, Port, dict[None, None], dict[None, None]]
):
    global_irradiance_schedule: Schedule[Celsius]

    def simulate(
        self,
        inputs: dict[None, None],
        previous_state: ElectricalState,
        control: None,
        simulation_time: ProcessTime,
    ) -> tuple[ElectricalState, dict[None, None]]:

        return (
            ElectricalState(
                soc_battery_system=self.global_irradiance_schedule.at(simulation_time)
                * 0.1,
            ),
            {},
        )
