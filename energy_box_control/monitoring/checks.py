from dataclasses import dataclass, fields
from math import isnan
from typing import Any, Callable, Optional, get_type_hints
from enum import Enum

from energy_box_control.monitoring.health_bounds import (
    BATTERY_HEALTH_BOUNDS,
    CHILLED_CIRCUIT_BOUNDS,
    COOLING_DEMAND_CIRCUIT_BOUNDS,
    HEAT_PIPES_BOUNDS,
    HOT_CIRCUIT_BOUNDS,
    HealthBound,
    CONTAINER_BOUNDS,
    TANK_BOUNDS,
    YAZAKI_BOUNDS,
    CHILLER_BOUNDS,
)
from energy_box_control.sensors import SensorType, attributes_for_type
from energy_box_control.network import NetworkControl
from energy_box_control.power_hub.network import PowerHub
from energy_box_control.power_hub.sensors import (
    FlowSensors,
    PowerHubSensors,
    SmartPumpSensors,
    RH33Sensors,
    ValveSensors,
    ElectricalSensors,
    ContainersSensors,
)


class Alarm(Enum):
    pass


class ElectricalAlarm(Alarm):
    WARNING = 1
    ALARM = 2


class FancoilAlarm(Alarm):
    ALARM = 1


class PumpAlarm(Alarm):
    """
    For the alarm codes, see page 50 of https://drive.google.com/drive/folders/1XeCJmo5KDtKEwL4Dtf3eJ0gkJdJpffFI
    """

    NO_ALARM = 0


class WeatherStationAlarm(Alarm):
    NO_ALARM = 0


class ValveAlarm(Alarm):
    """
    1: Mechanical travel increased
    2: Actuator cannot move
    8: Internal activity
    9: Gear train disengaged
    10: Bus watchdog triggered
    """

    ACTUATOR_CANNOT_MOVE = 2
    GEAR_TRAIN_DISENGAGED = 9


class RH33Alarm(Alarm):
    OPEN_CIRCUIT = 1
    OVER_RANGE = 2
    UNDER_RANGE = 3
    INVALID_MEASUREMENT_VALUE = 4
    REPLACEMENT_VALUE = 5
    SENSOR_ERROR = 6
    LOWER_LIMIT_VALUE_VIOLATED = 7
    UPPER_LIMIT_VALUE_VIOLATED = 8
    COUNTER_OVERFLOW = 16


class FlowSensorAlarm(Alarm):
    REVERSE_FLOW = 3
    FLOW_ACTUAL_EXCEEDS_FS = 6
    FLOW_MEASUREMENT_ERROR = 7
    FLOWBODY_TEMPERATURE_SENSOR = 9
    COMMUNICATION_TO_SENSOR_INTERRUPTED = 10
    FREEZE_WARNING = 11
    GLYCOL_DETECTED = 12


class WaterMakerAlarm(Alarm):
    NO_ALARM = 0


class ChillerAlarm(Alarm):
    DATA_COMMUNICATION = "INIT"
    SEA_WATER_FLOW_INSUFFICIENT = "SEA"
    REQUIRED_COLD_WATER_TEMPERATURE_NOT_YET_REACHED = "BA11"
    COMPRESSORS_DEACTIVATED = "CA11"
    UNDERVOLTAGE = "AAA"
    LOW_PRESSURE_COMPRESSOR_1 = "A01"
    HIGH_PRESSURE_COMPRESSOR_1 = "A02"
    LOW_PRESSURE_COMPRESSOR_2 = "A03"
    HIGH_PRESSURE_COMPRESSOR_2 = "A04"
    CABIN_TEMPERATURE_SENSOR = "A09"
    COLD_WATER_TEMPERATURE_SENSOR = "A10"
    COLD_WATER_FLOW = "A15"
    HIGH_PRESSURE_COMPRESSOR_1_AGAIN = "A20"
    EXCESS_CURRENT_INVERTER = "A21"
    EXCESS_TEMPERATURE_INVERTER = "A22"
    EXCESS_TEMPERATURE_COMPRESSOR_1 = "A23"
    HIGH_PRESSURE_SENSOR = "A24"
    LOW_PRESSURE_SENSOR = "A25"
    COMPRESSOR_TEMPERATURE_SENSOR = "A26"
    DATA_COMMUNICATION_INVERTER = "A27"
    CHARACTERISTIC_DIAGRAM = "A28"
    EXCESS_TEMPERATURE_INVERTER_AGAIN = "A30"
    EXCESS_CURRENT_INVERTER_AGAIN = "A31"
    PHASE_CONNECTION_COMPRESSOR_1 = "A32"
    EARTH_LEAKAGE_CURRENT = "A33"
    EXCESS_CURRENT_INVERTER_AGAIN2 = "A34"
    DC_BUS_INVERTER = "A35"
    UNDERVOLTAGE_INVERTER_PFC = "A36"
    UNDERVOLTAGE_INVERTER = "A37"
    COMPRESSOR_SPEED_1 = "A38"
    CABLE_BRIDGE_INVERTER = "A39"
    COMPRESSOR_1_OVERLOAD = "A40"
    OVERVOLTAGE = "A41"
    UNDER_TEMPERATURE_INVERTER = "A42"
    EXCESS_TEMPERATURE_COMPRESSOR_1_AGAIN = "A43"
    IGBT_INVERTER = "A44"
    CPU_INVERTER = "A45"
    PARAMETER_INVERTER = "A46"
    DATA_COMMUNICATION_INVERTER_AGAIN = "A47"
    THERMISTOR_INVERTER = "A48"
    AUTOMATIC_ADJUSTMENT_INVERTER = "A49"
    FAN_INVERTER = "A50"
    PFC_MODULE_INVERTER = "A51"
    STO_INVERTER = "A53"
    NO_DISPLAY_ON_SCREEN = "A54"


class Severity(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Check:
    name: str
    check: Any
    severity: Severity


CheckResult = str | None


@dataclass(eq=True, frozen=True)
class SensorValueCheck(Check):
    check: Callable[
        [PowerHubSensors, Optional[NetworkControl[PowerHub]], Optional[PowerHub]],
        CheckResult,
    ]


def value_check[
    Sensors, SensorValue, Control
](
    name: str,
    sensor_fn: Callable[[Sensors], SensorValue],
    check_fn: Callable[[SensorValue], bool],
    message_fn: Callable[[str, SensorValue], str],
    control_fn: Optional[
        Callable[[Optional[Control], Optional[PowerHub]], bool]
    ] = None,
) -> Callable[[Sensors, Optional[Control], Optional[PowerHub]], CheckResult]:

    def _check(
        sensor_values: Sensors,
        control_values: Optional[Control] = None,
        power_hub: Optional[PowerHub] = None,
    ) -> CheckResult:
        control_active = control_fn is None or control_fn(control_values, power_hub)
        sensor_value = sensor_fn(sensor_values)
        check_valid = check_fn(sensor_value)
        if control_active and not check_valid:
            return message_fn(name, sensor_value)
        else:
            return None

    return _check


def valid_value(
    name: str,
    value_fn: Callable[[PowerHubSensors], float],
    health_bound: HealthBound = HealthBound(5, 100),
    control_fn: Optional[
        Callable[[Optional[NetworkControl[PowerHub]], Optional[PowerHub]], bool]
    ] = None,
    severity: Severity = Severity.CRITICAL,
) -> SensorValueCheck:
    return SensorValueCheck(
        name,
        value_check(
            name=name,
            sensor_fn=value_fn,
            check_fn=lambda value: (
                health_bound.lower_bound <= value <= health_bound.upper_bound
                if not isnan(value)
                else True
            ),
            message_fn=lambda name, value: f"{name} is outside valid bounds with value: {value}",
            control_fn=control_fn,
        ),
        severity,
    )


def valid_value_check(
    name: str,
    value_fn: Callable[[PowerHubSensors], bool],
    message_fn: Callable[[str, bool], str],
    valid: object,
    severity: Severity = Severity.CRITICAL,
) -> SensorValueCheck:
    return SensorValueCheck(
        name=name,
        check=value_check(
            name=name,
            sensor_fn=value_fn,
            check_fn=lambda value: value == valid,
            message_fn=message_fn,
        ),
        severity=severity,
    )


def alarm(
    name: str,
    value_fn: Callable[[PowerHubSensors], int],
    message_fn: Callable[[str, int], str],
    alarm: Alarm,
    severity: Severity = Severity.CRITICAL,
    valid_value: bool = True,
) -> SensorValueCheck:
    return SensorValueCheck(
        name=name,
        check=value_check(
            name=name,
            sensor_fn=value_fn,
            check_fn=lambda value: (
                (value != alarm.value) if valid_value else (value == alarm.value)
            ),
            message_fn=message_fn,
        ),
        severity=severity,
    )


pcm_checks = [
    valid_value(
        "pcm_temperature_check",
        lambda sensors: sensors.pcm.temperature,
    )
]

hot_circuit_checks = [
    valid_value(
        "hot_circuit_temperature_check",
        lambda sensors: sensors.rh33_hot_storage.hot_temperature,
        HOT_CIRCUIT_BOUNDS["temperature"],
    ),
    valid_value(
        "hot_circuit_flow_check",
        lambda sensors: sensors.hot_storage_flow_sensor.flow,
        HOT_CIRCUIT_BOUNDS["flow"],
    ),
    valid_value(
        "hot_circuit_pressure_check",
        lambda sensors: sensors.pipes_pressure_sensor.pressure,
        HOT_CIRCUIT_BOUNDS["pressure"],
    ),
]

chilled_circuit_checks = [
    valid_value(
        "chilled_circuit_temperature_check",
        lambda sensors: sensors.rh33_chill.cold_temperature,
        CHILLED_CIRCUIT_BOUNDS["temperature"],
    ),
    valid_value(
        "chilled_circuit_flow_check",
        lambda sensors: sensors.chilled_flow_sensor.flow,
        CHILLED_CIRCUIT_BOUNDS["flow"],
    ),
    valid_value(
        "chilled_circuit_pressure_check",
        lambda sensors: sensors.chilled_loop_pump.pressure,
        CHILLED_CIRCUIT_BOUNDS["pressure"],
    ),
]

cooling_demand_circuit_checks = [
    valid_value(
        "cooling_demand_circuit_temperature_check",
        lambda sensors: sensors.rh33_cooling_demand.cold_temperature,
        COOLING_DEMAND_CIRCUIT_BOUNDS["temperature"],
    ),
    valid_value(
        "cooling_demand_circuit_flow_check",
        lambda sensors: sensors.cooling_demand_flow_sensor.flow,
        COOLING_DEMAND_CIRCUIT_BOUNDS["flow"],
    ),
    valid_value(
        "cooling_demand_circuit_pressure_check",
        lambda sensors: sensors.cooling_demand_pump.pressure,
        COOLING_DEMAND_CIRCUIT_BOUNDS["pressure"],
    ),
]


heat_pipes_checks = [
    valid_value(
        "heat_pipes_temperature_check",
        lambda sensors: sensors.rh33_heat_pipes.hot_temperature,
        HEAT_PIPES_BOUNDS["temperature"],
    ),
    valid_value(
        "heat_pipes_flow_check",
        lambda sensors: sensors.heat_pipes_flow_sensor.flow,
        HEAT_PIPES_BOUNDS["flow"],
    ),
    # pressure check is already done in hot switch circuit checks
]


battery_alarm_checks = [
    alarm(
        name=f"{attr}",
        value_fn=lambda sensors, attr=attr: getattr(sensors.electrical, attr),
        message_fn=lambda name, _: f"{name} is raising an alarm",
        alarm=ElectricalAlarm.ALARM,
    )
    for attr in attributes_for_type(ElectricalSensors, SensorType.ALARM)
]

battery_warning_checks = [
    alarm(
        name=f"{attr}_warning",
        value_fn=lambda sensors, attr=attr: getattr(sensors.electrical, attr),
        message_fn=lambda name, _: f"{name} is raising a warning",
        alarm=ElectricalAlarm.WARNING,
        severity=Severity.WARNING,
    )
    for attr in attributes_for_type(ElectricalSensors, SensorType.ALARM)
]

battery_soc_checks = [
    valid_value(
        "battery_soc",
        lambda sensors: sensors.electrical.soc_battery_system,
        BATTERY_HEALTH_BOUNDS["soc"],
    )
]

battery_estop_checks = [
    valid_value_check(
        name="estop_active",
        value_fn=lambda sensors: sensors.electrical.estop_active,
        message_fn=lambda _, value: f"estop active is {value}",
        valid=False,
    )
]

container_fancoil_alarm_checks = [
    alarm(
        name=f"{attr}",
        value_fn=lambda sensors, attr=attr: getattr(sensors.containers, attr),
        message_fn=lambda name, _: f"{name} is raising an alarm",
        alarm=FancoilAlarm.ALARM,
    )
    for attr in attributes_for_type(ContainersSensors, SensorType.ALARM)
]

containers_fancoil_filter_checks = [
    alarm(
        name=f"{attr}",
        value_fn=lambda sensors, attr=attr: getattr(sensors.containers, attr),
        message_fn=lambda name, _: f"{name} gone bad",
        alarm=FancoilAlarm.ALARM,
    )
    for attr in attributes_for_type(ContainersSensors, SensorType.REPLACE_FILTER_ALARM)
]

weather_station_alarm_checks = [
    alarm(
        name=f"weather_station",
        value_fn=lambda sensors,: getattr(sensors.weather, "alarm"),
        message_fn=lambda name, alarm_code: f"{name} is raising an alarm with code {alarm_code}",
        alarm=WeatherStationAlarm.NO_ALARM,
        valid_value=False,
    )
]


pump_alarm_checks = [
    alarm(
        name=f"{appliance_name}_{attr}",
        value_fn=lambda sensors, attr=attr, appliance_name=appliance_name: getattr(
            getattr(sensors, appliance_name), attr
        ),
        message_fn=lambda name, alarm_code: f"{name} is raised with code {alarm_code}",
        alarm=PumpAlarm.NO_ALARM,
        valid_value=False,
    )
    for appliance_name, appliance_type in get_type_hints(PowerHubSensors).items()
    if issubclass(appliance_type, SmartPumpSensors)
    for attr in attributes_for_type(SmartPumpSensors, SensorType.ALARM)
]

pump_warning_checks = [
    alarm(
        name=f"{appliance_name}_{attr}",
        value_fn=lambda sensors, attr=attr, appliance_name=appliance_name: getattr(
            getattr(sensors, appliance_name), attr
        ),
        message_fn=lambda name, alarm_code: f"{name} is raised with code {alarm_code}",
        alarm=PumpAlarm.NO_ALARM,
        valid_value=False,
        severity=Severity.WARNING,
    )
    for appliance_name, appliance_type in get_type_hints(PowerHubSensors).items()
    if issubclass(appliance_type, SmartPumpSensors)
    for attr in attributes_for_type(SmartPumpSensors, SensorType.WARNING)
]

flow_sensor_alarm_checks = [
    alarm(
        name=f"{field.name}_{flow_sensor_alarm.name.lower()}_alarm",
        value_fn=lambda sensors, flow_sensor_name=field.name: getattr(
            sensors, flow_sensor_name
        ).service_info,
        message_fn=lambda name, _: f"{name} is raised",
        alarm=flow_sensor_alarm,
        severity=Severity.ERROR,
    )
    for field in fields(PowerHubSensors)
    if field.type == FlowSensors
    for flow_sensor_alarm in FlowSensorAlarm
]

rh33_alarm_checks = [
    alarm(
        name=f"{field.name}_{rh33_alarm.name.lower()}_alarm",
        value_fn=lambda sensors, rh33_name=field.name: getattr(
            sensors, rh33_name
        ).status,
        message_fn=lambda name, _: f"{name} is raised",
        alarm=rh33_alarm,
        severity=Severity.ERROR,
    )
    for field in fields(PowerHubSensors)
    if field.type == RH33Sensors
    for rh33_alarm in RH33Alarm
]


valve_alarm_checks = [
    alarm(
        name=f"{field.name}_{valve_alarm.name.lower()}_alarm",
        value_fn=lambda sensors, valve_name=field.name: getattr(
            sensors, valve_name
        ).service_info,
        message_fn=lambda name, _: f"{name} is raised",
        alarm=valve_alarm,
        severity=Severity.ERROR,
    )
    for field in fields(PowerHubSensors)
    if field.type == ValveSensors or issubclass(field.type, ValveSensors)
    for valve_alarm in ValveAlarm
]

chiller_alarm_checks = [
    alarm(
        name=f"chiller_{chiller_alarm.name.lower()}_alarm",
        value_fn=lambda sensors: sensors.chiller.fault_code,
        message_fn=lambda name, _: f"{name} is raised",
        alarm=chiller_alarm,
    )
    for chiller_alarm in ChillerAlarm
]


yazaki_bound_checks = [
    valid_value(
        f"yazaki_{attr}_check",
        lambda sensors, attr=attr: getattr(sensors.yazaki, attr),
        health_bound=bound,
        control_fn=lambda control_values, network: (
            control_values.appliance(network.yazaki).get().on
            if control_values and network
            else False
        ),
    )
    for attr, bound in YAZAKI_BOUNDS.items()
]

chiller_bound_checks = [
    valid_value(
        f"chiller_{attr}_check",
        lambda sensors, attr=attr: getattr(sensors.chiller, attr),
        health_bound=bound,
        control_fn=lambda control_values, network: (
            control_values.appliance(network.chiller).get().on
            if control_values and network
            else False
        ),
    )
    for attr, bound in CHILLER_BOUNDS.items()
]

chiller_alarm_checks = [
    alarm(
        name=f"chiller_{chiller_alarm.name.lower()}_alarm",
        value_fn=lambda sensors: sensors.chiller.fault_code,
        message_fn=lambda name, _: f"{name} is raised",
        alarm=chiller_alarm,
    )
    for chiller_alarm in ChillerAlarm
]

water_maker_alarm_checks = [
    alarm(
        name=f"water maker error",
        value_fn=lambda sensors: (
            sensors.water_maker.last_error_id if sensors.water_maker.error == 1 else 0
        ),
        message_fn=lambda name, value: f"{name} with code {value}",
        alarm=WaterMakerAlarm.NO_ALARM,
        severity=Severity.ERROR,
        valid_value=False,
    ),
    alarm(
        name=f"water maker warning",
        value_fn=lambda sensors: (
            sensors.water_maker.last_warning_id
            if sensors.water_maker.warning == 1
            else 0
        ),
        message_fn=lambda name, value: f"{name} with code {value}",
        alarm=WaterMakerAlarm.NO_ALARM,
        severity=Severity.WARNING,
        valid_value=False,
    ),
]

water_tank_checks = [
    valid_value(
        f"{tank_name}_fill_ratio",
        lambda sensors, tank_name=tank_name: getattr(sensors, tank_name).fill_ratio,
        health_bound=bound,
    )
    for tank_name, bound in TANK_BOUNDS.items()
]

container_checks = [
    valid_value(
        attr,
        lambda sensors, attr=attr: getattr(sensors.containers, attr),
        health_bound=CONTAINER_BOUNDS[sensor],
    )
    for sensor, sensor_type in [
        ("temperature", SensorType.TEMPERATURE),
        ("humidity", SensorType.HUMIDITY),
        ("co2", SensorType.CO2),
    ]
    for attr in attributes_for_type(ContainersSensors, sensor_type)
]

all_checks = (
    pcm_checks
    + hot_circuit_checks
    + chilled_circuit_checks
    + cooling_demand_circuit_checks
    + heat_pipes_checks
    + battery_alarm_checks
    + battery_warning_checks
    + battery_soc_checks
    + battery_estop_checks
    + container_fancoil_alarm_checks
    + containers_fancoil_filter_checks
    + weather_station_alarm_checks
    + valve_alarm_checks
    + pump_alarm_checks
    + pump_warning_checks
    + yazaki_bound_checks
    + chiller_bound_checks
    + chiller_alarm_checks
    + water_tank_checks
    + container_checks
    + water_maker_alarm_checks
    + flow_sensor_alarm_checks
    + rh33_alarm_checks
)
