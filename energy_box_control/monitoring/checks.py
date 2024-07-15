from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional

import aiohttp
from energy_box_control.power_hub.sensors import PowerHubSensors
from enum import Enum
from http import HTTPStatus
from energy_box_control.power_hub.sensors import ElectricBatterySensors
from typing import get_type_hints

from energy_box_control.units import Alarm


POWER_HUB_API_URL = "https://api.staging.power-hub.foundationzero.org/"
INFLUXDB_URL = "https://influxdb.staging.power-hub.foundationzero.org/health"
MQTT_HEALTH_URL = "http://vernemq.staging.power-hub.foundationzero.org:8888/health"
DISPLAY_HEALTH_URL = "https://power-hub.pages.dev/"
WATER_TANK_LOWER_BOUND = 40
WATER_TANK_UPPER_BOUND = 100


class SensorAlarm(Enum):
    WARNING = 1
    ALARM = 2


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
    type: SensorAlarm, message: Callable[[str], str]
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


def valid_value(
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
    valid_value("pcm_temperature_check", lambda sensors: sensors.pcm.temperature)
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
        if type == Alarm
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
        if type == Alarm
    ]
]

water_tank_checks = [
    valid_value(
        f"{tank_name}_percentage_fill",
        lambda sensors, tank_name=tank_name: getattr(
            sensors, tank_name
        ).percentage_fill,
        lower_bound=WATER_TANK_LOWER_BOUND,
        upper_bound=WATER_TANK_UPPER_BOUND,
        severity=Severity.CRITICAL,
    )
    for tank_name in get_type_hints(PowerHubSensors).keys()
    if "tank" in tank_name
]


all_appliance_checks = sensor_checks + alarm_checks + warning_checks + water_tank_checks

service_checks = [
    url_health_check("Power Hub API", POWER_HUB_API_URL, severity=Severity.CRITICAL),
    url_health_check("InfluxDB Health", INFLUXDB_URL, severity=Severity.CRITICAL),
    url_health_check("MQTT Health", MQTT_HEALTH_URL, severity=Severity.CRITICAL),
    url_health_check(
        "Front End Health", DISPLAY_HEALTH_URL, severity=Severity.CRITICAL
    ),
]
