from dataclasses import dataclass, fields
from typing import Any, Awaitable, Callable, Optional

import aiohttp
from energy_box_control.power_hub.sensors import PowerHubSensors, ValveSensors
from enum import Enum
from http import HTTPStatus
from energy_box_control.power_hub.sensors import ElectricBatterySensors
from typing import get_type_hints

from energy_box_control.units import BatteryAlarm


POWER_HUB_API_URL = "https://api.staging.power-hub.foundationzero.org/"
INFLUXDB_URL = "https://influxdb.staging.power-hub.foundationzero.org/health"
MQTT_HEALTH_URL = "http://vernemq.staging.power-hub.foundationzero.org:8888/health"
DISPLAY_HEALTH_URL = "https://power-hub.pages.dev/"


class Alarm(Enum):
    pass


class SensorAlarm(Alarm):
    WARNING = 1
    ALARM = 2


"""
1: Mechanical travel increased
2: Actuator cannot move
8: Internal activity
9: Gear train disengaged
10: Bus watchdog triggered
"""


class ValveAlarm(Alarm):
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
    check: Callable[[PowerHubSensors], CheckResult]


@dataclass
class UrlHealthCheck(Check):
    check: Callable[[], Awaitable[CheckResult]]


@dataclass
class AlarmHealthCheck(Check):
    check: Callable[[PowerHubSensors], CheckResult]


def value_check[
    A, B
](name: str, sensor_fn: Callable[[A], B], check_fn: Callable[[B], bool]) -> Callable[
    [A], CheckResult
]:

    def _check(sensor_values: A) -> CheckResult:
        if not check_fn(sensor_fn(sensor_values)):
            return (
                f"{name} is outside valid bounds with value: {sensor_fn(sensor_values)}"
            )
        else:
            return None

    return _check


def url_health_check(name: str, url: str, severity: Severity) -> UrlHealthCheck:

    async def _url_health_check(_: Optional[Any] = None) -> str | None:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != HTTPStatus.OK:
                    return f"{name} is returning error code {response.status}"
                return None

    return UrlHealthCheck(name=name, check=_url_health_check, severity=severity)


def sensor_alarm_check(
    type: Alarm, message: Callable[[str], str]
) -> Callable[[str, Callable[[PowerHubSensors], int], Severity], AlarmHealthCheck]:
    def _alarm_check(
        name: str, sensor_fn: Callable[[PowerHubSensors], int], severity: Severity
    ):
        def _alarm(sensor_values: PowerHubSensors) -> str | None:
            if sensor_fn(sensor_values) == type.value:
                return message(name)
            return None

        return AlarmHealthCheck(name=name, check=_alarm, severity=severity)

    return _alarm_check


alarm_check = sensor_alarm_check(
    SensorAlarm.ALARM, lambda name: f"{name} is raising an alarm"
)
warning_check = sensor_alarm_check(
    SensorAlarm.WARNING, lambda name: f"{name} is raising a warning"
)

valve_actuator_check = sensor_alarm_check(
    ValveAlarm.ACTUATOR_CANNOT_MOVE, lambda name: f"{name} is raised"
)
valve_gear_train_check = sensor_alarm_check(
    ValveAlarm.GEAR_TRAIN_DISENGAGED, lambda name: f"{name} is raised"
)


def valid_temp(
    name: str,
    value_fn: Callable[[PowerHubSensors], float],
    lower_bound: int = 5,
    upper_bound: int = 100,
    severity: Severity = Severity.ERROR,
) -> SensorValueCheck:
    return SensorValueCheck(
        name,
        value_check(
            name,
            value_fn,
            lambda value: lower_bound < value < upper_bound,
        ),
        severity,
    )


sensor_checks = [
    valid_temp("pcm_temperature_check", lambda sensors: sensors.pcm.temperature)
]

alarm_checks = [
    alarm_check(
        f"{attr}",
        lambda sensors, attr=attr: getattr(sensors.electric_battery, attr),
        Severity.CRITICAL,
    )
    for attr in [
        attr
        for attr, type in get_type_hints(ElectricBatterySensors).items()
        if type == BatteryAlarm
    ]
]
warning_checks = [
    warning_check(
        f"{attr}_warning",
        lambda sensors, attr=attr: getattr(sensors.electric_battery, attr),
        Severity.WARNING,
    )
    for attr in [
        attr
        for attr, type in get_type_hints(ElectricBatterySensors).items()
        if type == BatteryAlarm
    ]
]


valve_actuator_checks = [
    valve_actuator_check(
        f"{valve_name}_actuator_alarm",
        lambda sensors, valve_name=valve_name: getattr(
            sensors, valve_name
        ).service_info,
        Severity.CRITICAL,
    )
    for valve_name in [
        field.name
        for field in fields(PowerHubSensors)
        if field.type == ValveSensors or issubclass(field.type, ValveSensors)
    ]
]

valve_gear_train_checks = [
    valve_gear_train_check(
        f"{valve_name}_gear_train_alarm",
        lambda sensors, valve_name=valve_name: getattr(
            sensors, valve_name
        ).service_info,
        Severity.CRITICAL,
    )
    for valve_name in [
        field.name
        for field in fields(PowerHubSensors)
        if field.type == ValveSensors or issubclass(field.type, ValveSensors)
    ]
]

valve_alarm_checks = valve_actuator_checks + valve_gear_train_checks


service_checks = [
    url_health_check("Power Hub API", POWER_HUB_API_URL, severity=Severity.CRITICAL),
    url_health_check("InfluxDB Health", INFLUXDB_URL, severity=Severity.CRITICAL),
    url_health_check("MQTT Health", MQTT_HEALTH_URL, severity=Severity.CRITICAL),
    url_health_check(
        "Front End Health", DISPLAY_HEALTH_URL, severity=Severity.CRITICAL
    ),
]
