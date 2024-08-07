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

RH33_LOWER_BITS_MASK = 0b1111


class Alarm(Enum):
    pass


class AlarmValue(Alarm):
    pass


class AlarmBit(Alarm):
    """
    Alarm bits start at 0.
    """

    pass


class ElectricalAlarm(AlarmValue):
    WARNING = 1
    ALARM = 2


class FancoilAlarm(AlarmValue):
    ALARM = 1


class PumpAlarm(AlarmValue):
    """
    For the alarm codes, see page 50 of https://drive.google.com/drive/folders/1XeCJmo5KDtKEwL4Dtf3eJ0gkJdJpffFI
    """

    NO_ALARM = 0


class WeatherStationAlarm(AlarmBit):
    GPS_NO_VALID_RMC_TELEGRAM_RECEIVED = 2
    GPS_TIME_INVALID = 3
    ADC_INVALID_VALUES = 4
    INVALID_AIR_PRESSURE_VALUE = 5
    INVALID_BRIGHTNESS_NORTH_VALUE = 6
    INVALID_BRIGHTNESS_EAST_VALUE = 7
    INVALID_BRIGHTNESS_SOUTCH_VALUE = 8
    INVALID_BRIGHNESS_WEST_VALUE = 9
    INVALID_TWILIGHT_VALUE = 10
    INVALID_GLOBAL_IRRADIANCE_VALUE = 11
    INVALID_AIR_TEMPERATURE_VALUE = 12
    INVALID_PRECIPITATION_VALUE = 13
    INVALID_WIND_SPEED_VALUE = 14
    INVALID_WIND_DIRECTION_VALUE = 15
    INVALID_HUMIDITY_VALUE = 16
    WATCHDOG_RESET = 17
    INVALID_INTERNAL_EEPROM_PARAMS = 18


class YazakiAlarm(AlarmValue):
    NO_ALARM = False


class ValveAlarm(AlarmBit):
    """
    1: Mechanical travel increased
    2: Actuator cannot move
    8: Internal activity
    9: Gear train disengaged
    10: Bus watchdog triggered
    """

    ACTUATOR_CANNOT_MOVE = 2
    GEAR_TRAIN_DISENGAGED = 9


class RH33AlarmLowerBitsValues(AlarmValue):
    OPEN_CIRCUIT = 1
    OVER_RANGE = 2
    UNDER_RANGE = 3
    INVALID_MEASUREMENT_VALUE = 4
    REPLACEMENT_VALUE = 6
    SENSOR_ERROR = 7


class RH33AlarmUpperBits(AlarmBit):
    LOWER_LIMIT_VALUE_VIOLATED = 4
    UPPER_LIMIT_VALUE_VIOLATED = 5
    COUNTER_OVERFLOW = 15


class FlowSensorAlarm(AlarmBit):
    REVERSE_FLOW = 3
    FLOW_ACTUAL_EXCEEDS_FS = 6
    FLOW_MEASUREMENT_ERROR = 7
    FLOWBODY_TEMPERATURE_SENSOR = 9
    COMMUNICATION_TO_SENSOR_INTERRUPTED = 10
    FREEZE_WARNING = 11
    GLYCOL_DETECTED = 12


class WaterMakerAlarm(AlarmValue):
    NO_ALARM = 0


class Severity(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "current_error_id"
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
    alarm: AlarmValue,
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


def bit_check(
    name: str,
    value_fn: Callable[[PowerHubSensors], int],
    message_fn: Callable[[str, int], str],
    alarm: AlarmBit,
    severity: Severity = Severity.CRITICAL,
) -> SensorValueCheck:
    return SensorValueCheck(
        name=name,
        check=value_check(
            name=name,
            sensor_fn=value_fn,
            check_fn=lambda value: (value & 1 << alarm.value) == 0,
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
    bit_check(
        name=f"weather_station_{alarm.name.lower()}",
        value_fn=lambda sensors,: sensors.weather.status,
        message_fn=lambda name, _: f"{name} is raised",
        alarm=alarm,
    )
    for alarm in WeatherStationAlarm
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
    bit_check(
        name=f"{field.name}_{flow_sensor_alarm.name.lower()}_alarm",
        value_fn=lambda sensors, flow_sensor_name=field.name: getattr(
            sensors, flow_sensor_name
        ).status,
        message_fn=lambda name, _: f"{name} is raised",
        alarm=flow_sensor_alarm,
        severity=Severity.CRITICAL,
    )
    for field in fields(PowerHubSensors)
    if field.type == FlowSensors
    for flow_sensor_alarm in FlowSensorAlarm
]


rh33_upper_bits_checks = [
    bit_check(
        name=f"{field.name}_{attr}_{rh33_alarm.name.lower()}_alarm",
        value_fn=lambda sensors, rh33_name=field.name, attr=attr: getattr(
            getattr(sensors, rh33_name), attr
        ),
        message_fn=lambda name, _: f"{name} is raised",
        alarm=rh33_alarm,
        severity=Severity.ERROR,
    )
    for field in fields(PowerHubSensors)
    if field.type == RH33Sensors
    for attr in attributes_for_type(RH33Sensors, SensorType.ALARM)
    for rh33_alarm in RH33AlarmUpperBits
]


rh33_lower_bits_checks = [
    alarm(
        name=f"{field.name}_{attr}_{rh33_alarm.name.lower()}_alarm",
        value_fn=lambda sensors, rh33_name=field.name, attr=attr: getattr(
            getattr(sensors, rh33_name), attr
        )
        & RH33_LOWER_BITS_MASK,
        message_fn=lambda name, _: f"{name} is raised",
        alarm=rh33_alarm,
        severity=Severity.ERROR,
    )
    for field in fields(PowerHubSensors)
    if field.type == RH33Sensors
    for attr in attributes_for_type(RH33Sensors, SensorType.ALARM)
    for rh33_alarm in RH33AlarmLowerBitsValues
]

valve_alarm_checks = [
    bit_check(
        name=f"{field.name}_{valve_alarm.name.lower()}_alarm",
        value_fn=lambda sensors, valve_name=field.name: getattr(
            sensors, valve_name
        ).status,
        message_fn=lambda name, _: f"{name} is raised",
        alarm=valve_alarm,
        severity=Severity.ERROR,
    )
    for field in fields(PowerHubSensors)
    if field.type == ValveSensors or issubclass(field.type, ValveSensors)
    for valve_alarm in ValveAlarm
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

yazaki_alarm_checks = [
    alarm(
        name=f"yazaki_alarm",
        value_fn=lambda sensors: sensors.yazaki.error_output,
        message_fn=lambda name, _: f"{name} is raised",
        alarm=YazakiAlarm.NO_ALARM,
        valid_value=False,
    )
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


def chiller_fault_check(
    name: str,
    value_fn: Callable[[PowerHubSensors], list[str]],
    severity: Severity = Severity.CRITICAL,
):
    return SensorValueCheck(
        name,
        value_check(
            name=name,
            sensor_fn=value_fn,
            check_fn=lambda faults: len(faults) == 0,
            message_fn=lambda _, faults: f"chiller faults are raised: {", ".join(faults)}",
        ),
        severity=severity,
    )


chiller_alarm_checks = [
    chiller_fault_check("chiller_fault_alarm", lambda sensors: sensors.chiller.faults())
]

water_maker_alarm_checks = [
    alarm(
        name=f"water maker error",
        value_fn=lambda sensors: (
            sensors.water_maker.last_error_id
            if sensors.water_maker.current_error_id == 1
            else 0
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
            if sensors.water_maker.current_warning_id == 1
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
    + yazaki_alarm_checks
    + chiller_bound_checks
    + chiller_alarm_checks
    + water_tank_checks
    + container_checks
    + water_maker_alarm_checks
    + flow_sensor_alarm_checks
    + rh33_upper_bits_checks
    + rh33_lower_bits_checks
)
