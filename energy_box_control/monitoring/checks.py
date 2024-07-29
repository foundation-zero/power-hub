from dataclasses import dataclass, fields
from math import isnan
from typing import Any, Callable, Optional, get_type_hints
from enum import Enum

from energy_box_control.monitoring.health_bounds import (
    HealthBound,
    CONTAINER_BOUNDS,
    TANK_BOUNDS,
    HOT_CIRCUIT_FLOW_BOUNDS,
    HOT_CIRCUIT_PRESSURE_BOUNDS,
    HOT_CIRCUIT_TEMPERATURE_BOUNDS,
    YAZAKI_BOUNDS,
)
from energy_box_control.sensors import SensorType, attributes_for_type
from energy_box_control.network import NetworkControl
from energy_box_control.power_hub.network import PowerHub
from energy_box_control.power_hub.sensors import (
    PowerHubSensors,
    SwitchPumpSensors,
    ValveSensors,
    ElectricBatterySensors,
    ContainersSensors,
)


class Alarm(Enum):
    pass


class ElectricBatteryAlarm(Alarm):
    WARNING = 1
    ALARM = 2


class FancoilAlarm(Alarm):
    ALARM = 1


class PumpAlarm(Alarm):
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


class Severity(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Check:
    name: str
    check: Any
    severity: Severity


CheckResult = str | None


@dataclass
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


sensor_checks = [
    valid_value(
        "pcm_temperature_check",
        lambda sensors: sensors.pcm.temperature,
    ),
    valid_value(
        "hot_circuit_temperature_check",
        lambda sensors: sensors.pcm.charge_input_temperature,
        HOT_CIRCUIT_TEMPERATURE_BOUNDS,
    ),
    valid_value(
        "hot_circuit_flow_check",
        lambda sensors: sensors.pcm.charge_flow,
        HOT_CIRCUIT_FLOW_BOUNDS,
    ),
    valid_value(
        "hot_circuit_pressure_check",
        lambda sensors: sensors.pcm_yazaki_pressure_sensor.pressure,
        HOT_CIRCUIT_PRESSURE_BOUNDS,
    ),
]

battery_alarm_checks = [
    alarm(
        name=f"{attr}",
        value_fn=(lambda sensors, attr=attr: getattr(sensors.electric_battery, attr)),
        message_fn=(lambda name, _: f"{name} is raising an alarm"),
        alarm=ElectricBatteryAlarm.ALARM,
    )
    for attr in attributes_for_type(ElectricBatterySensors, SensorType.ALARM)
]

battery_warning_checks = [
    alarm(
        name=f"{attr}_warning",
        value_fn=lambda sensors, attr=attr: getattr(sensors.electric_battery, attr),
        message_fn=(lambda name, _: f"{name} is raising a warning"),
        alarm=ElectricBatteryAlarm.WARNING,
        severity=Severity.WARNING,
    )
    for attr in attributes_for_type(ElectricBatterySensors, SensorType.ALARM)
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

valve_actuator_checks = [
    alarm(
        name=f"{valve_name}_actuator_alarm",
        value_fn=lambda sensors, valve_name=valve_name: getattr(
            sensors, valve_name
        ).service_info,
        message_fn=lambda name, _: f"{name} is raised",
        alarm=ValveAlarm.ACTUATOR_CANNOT_MOVE,
    )
    for valve_name in [
        field.name
        for field in fields(PowerHubSensors)
        if field.type == ValveSensors or issubclass(field.type, ValveSensors)
    ]
]

valve_gear_train_checks = [
    alarm(
        name=f"{valve_name}_gear_train_alarm",
        value_fn=lambda sensors, valve_name=valve_name: getattr(
            sensors, valve_name
        ).service_info,
        message_fn=lambda name, _: f"{name} is raised",
        alarm=ValveAlarm.GEAR_TRAIN_DISENGAGED,
    )
    for valve_name in [
        field.name
        for field in fields(PowerHubSensors)
        if field.type == ValveSensors or issubclass(field.type, ValveSensors)
    ]
]

pump_alarm_checks = [
    alarm(
        name=f"{appliance_name}_{attr}",
        value_fn=lambda sensors, attr=attr, appliance_name=appliance_name: getattr(
            getattr(sensors, appliance_name), attr
        ),
        message_fn=lambda name, alarm_code: f"{name} is raising an alarm with code {alarm_code}",
        alarm=PumpAlarm.NO_ALARM,
        valid_value=False,
    )
    for appliance_name, appliance_type in get_type_hints(PowerHubSensors).items()
    if appliance_type == SwitchPumpSensors
    for attr in attributes_for_type(SwitchPumpSensors, SensorType.ALARM)
]

yazaki_bound_checks = [
    valid_value(
        f"yazaki_{attr}_check",
        lambda sensors, attr=attr: getattr(sensors.yazaki, attr),
        health_bound=bound,
        control_fn=lambda control_values, network: (
            control_values.appliance(network.yazaki).get().on
            if control_values and network
            else True
        ),
    )
    for attr, bound in YAZAKI_BOUNDS.items()
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
    battery_alarm_checks
    + battery_warning_checks
    + container_fancoil_alarm_checks
    + containers_fancoil_filter_checks
    + sensor_checks
    + container_checks
    + water_tank_checks
    + pump_alarm_checks
    + yazaki_bound_checks
    + weather_station_alarm_checks
    + valve_actuator_checks
    + valve_gear_train_checks
)
