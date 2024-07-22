from dataclasses import dataclass, fields
from typing import Any, Awaitable, Callable, Optional, get_type_hints

import aiohttp
from energy_box_control.monitoring.health_bounds import (
    CO2_LOWER_BOUND,
    CO2_UPPER_BOUND,
    CONTAINER_TEMPERATURE_LOWER_BOUND,
    CONTAINER_TEMPERATURE_UPPER_BOUND,
    HUMIDITY_LOWER_BOUND,
    HUMIDITY_UPPER_BOUND,
    TANK_BOUNDS,
)
from energy_box_control.power_hub.sensors import PowerHubSensors
from energy_box_control.power_hub.sensors import PowerHubSensors, SwitchPumpSensors
from enum import Enum
from http import HTTPStatus
from energy_box_control.power_hub.sensors import (
    ElectricBatterySensors,
    ContainersSensors,
)
from energy_box_control.sensors import Sensor, SensorType


POWER_HUB_API_URL = "https://api.staging.power-hub.foundationzero.org/"
INFLUXDB_URL = "https://influxdb.staging.power-hub.foundationzero.org/health"
MQTT_HEALTH_URL = "http://vernemq.staging.power-hub.foundationzero.org:8888/health"
DISPLAY_HEALTH_URL = "https://power-hub.pages.dev/"


class ElectricBatteryAlarm(Enum):
    WARNING = 1
    ALARM = 2


class FancoilAlarm(Enum):
    ALARM = 1


class PumpAlarm(Enum):
    NO_ALARM = 0


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
    type: ElectricBatteryAlarm | FancoilAlarm, message: Callable[[str], str]
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


def pump_alarm_check(
    type: PumpAlarm, message: Callable[[str, int], str]
) -> Callable[[str, Callable[[PowerHubSensors], int], Severity], AlarmHealthCheck]:
    def _pump_alarm_check(
        name: str, sensor_fn: Callable[[PowerHubSensors], int], severity: Severity
    ):
        def _alarm(sensor_values: PowerHubSensors) -> str | None:
            alarm_code = sensor_fn(sensor_values)
            if alarm_code != type.value:
                return message(name, alarm_code)
            return None

        return AlarmHealthCheck(name=name, check=_alarm, severity=severity)

    return _pump_alarm_check


battery_alarm_check = sensor_alarm_check(
    ElectricBatteryAlarm.ALARM, lambda name: f"{name} is raising an alarm"
)

battery_warning_check = sensor_alarm_check(
    ElectricBatteryAlarm.WARNING, lambda name: f"{name} is raising a warning"
)

fancoil_alarm_check = sensor_alarm_check(
    FancoilAlarm.ALARM, lambda name: f"{name} is raising an alarm"
)

fancoil_filter_check = sensor_alarm_check(
    FancoilAlarm.ALARM, lambda name: f"{name} gone bad"
)

pump_alarm = pump_alarm_check(
    PumpAlarm.NO_ALARM,
    lambda name, alarm_code: f"{name} is raising an alarm with code {alarm_code}",
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

battery_alarm_checks = [
    battery_alarm_check(
        f"{attr}",
        lambda sensors, attr=attr: getattr(sensors.electric_battery, attr),
        Severity.CRITICAL,
    )
    for attr in [
        attr
        for attr in dir(ElectricBatterySensors)
        if isinstance(getattr(ElectricBatterySensors, attr), Sensor)
        and getattr(ElectricBatterySensors, attr).type == SensorType.BATTERY_ALARM
    ]
]
battery_warning_checks = [
    battery_warning_check(
        f"{attr}_warning",
        lambda sensors, attr=attr: getattr(sensors.electric_battery, attr),
        Severity.WARNING,
    )
    for attr in [
        attr
        for attr in dir(ElectricBatterySensors)
        if isinstance(getattr(ElectricBatterySensors, attr), Sensor)
        and getattr(ElectricBatterySensors, attr).type == SensorType.BATTERY_ALARM
    ]
]

water_tank_checks = [
    valid_value(
        f"{tank_name}_percentage_fill",
        lambda sensors, tank_name=tank_name: getattr(
            sensors, tank_name
        ).percentage_fill,
        lower_bound=TANK_BOUNDS[tank_name]["lower_bound"],
        upper_bound=TANK_BOUNDS[tank_name]["upper_bound"],
        severity=Severity.CRITICAL,
    )
    for tank_name in TANK_BOUNDS.keys()
]


container_temperature_checks = [
    valid_value(
        attr,
        lambda sensors, attr=attr: getattr(sensors.containers, attr),
        lower_bound=CONTAINER_TEMPERATURE_LOWER_BOUND,
        upper_bound=CONTAINER_TEMPERATURE_UPPER_BOUND,
        severity=Severity.CRITICAL,
    )
    for attr in [
        attr
        for attr in dir(ContainersSensors)
        if isinstance(getattr(ContainersSensors, attr), Sensor)
        and getattr(ContainersSensors, attr).type == SensorType.TEMPERATURE
    ]
]

container_humidity_checks = [
    valid_value(
        attr,
        lambda sensors, attr=attr: getattr(sensors.containers, attr),
        lower_bound=HUMIDITY_LOWER_BOUND,
        upper_bound=HUMIDITY_UPPER_BOUND,
        severity=Severity.ERROR,
    )
    for attr in [
        attr
        for attr in dir(ContainersSensors)
        if isinstance(getattr(ContainersSensors, attr), Sensor)
        and getattr(ContainersSensors, attr).type == SensorType.HUMIDITY
    ]
]

container_co2_checks = [
    valid_value(
        attr,
        lambda sensors, attr=attr: getattr(sensors.containers, attr),
        lower_bound=CO2_LOWER_BOUND,
        upper_bound=CO2_UPPER_BOUND,
        severity=Severity.CRITICAL,
    )
    for attr in [
        attr
        for attr in dir(ContainersSensors)
        if isinstance(getattr(ContainersSensors, attr), Sensor)
        and getattr(ContainersSensors, attr).type == SensorType.CO2
    ]
]

container_fancoil_alarm_checks = [
    fancoil_alarm_check(
        f"{attr}",
        lambda sensors, attr=attr: getattr(sensors.containers, attr),
        Severity.CRITICAL,
    )
    for attr in [
        attr
        for attr in dir(ContainersSensors)
        if isinstance(getattr(ContainersSensors, attr), Sensor)
        and getattr(ContainersSensors, attr).type == SensorType.FAN_ALARM
    ]
]

containers_fancoil_filter_checks = [
    fancoil_filter_check(
        f"{attr}",
        lambda sensors, attr=attr: getattr(sensors.containers, attr),
        Severity.CRITICAL,
    )
    for attr in [
        attr
        for attr in dir(ContainersSensors)
        if isinstance(getattr(ContainersSensors, attr), Sensor)
        and getattr(ContainersSensors, attr).type == SensorType.FAN_FILTER_ALARM
    ]
]

pump_alarm_checks = [
    pump_alarm(
        f"{appliance_name}_{attr}",
        lambda sensors, attr=attr, appliance_name=appliance_name: getattr(
            getattr(sensors, appliance_name), attr
        ),
        Severity.CRITICAL,
    )
    for appliance_name in [
        field.name for field in fields(PowerHubSensors) if "pump" in field.name
    ]
    for attr in [
        attr for attr, _ in get_type_hints(SwitchPumpSensors).items() if "alarm" in attr
    ]
]


all_appliance_checks = (
    sensor_checks
    + battery_alarm_checks
    + battery_warning_checks
    + container_temperature_checks
    + container_humidity_checks
    + container_co2_checks
    + container_fancoil_alarm_checks
    + containers_fancoil_filter_checks
)

service_checks = [
    url_health_check("Power Hub API", POWER_HUB_API_URL, severity=Severity.CRITICAL),
    url_health_check("InfluxDB Health", INFLUXDB_URL, severity=Severity.CRITICAL),
    url_health_check("MQTT Health", MQTT_HEALTH_URL, severity=Severity.CRITICAL),
    url_health_check(
        "Front End Health", DISPLAY_HEALTH_URL, severity=Severity.CRITICAL
    ),
]
