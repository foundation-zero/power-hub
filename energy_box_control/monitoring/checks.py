from dataclasses import dataclass, fields
from typing import Any, Awaitable, Callable, Optional, get_type_hints

import aiohttp
from energy_box_control.monitoring.health_bounds import (
    CONTAINER_BOUNDS,
    TANK_BOUNDS,
)
from dataclasses import dataclass
from math import isnan
from typing import Any, Awaitable, Callable, Optional
from energy_box_control.monitoring.health_bounds import (
    YAZAKI_BOUNDS,
    HealthBound,
)
from energy_box_control.network import NetworkControl
from energy_box_control.power_hub.network import PowerHub
from dataclasses import dataclass
from math import isnan
from typing import Any, Awaitable, Callable, Optional

from energy_box_control.monitoring.health_bounds import (
    HealthBound,
    HOT_CIRCUIT_FLOW_BOUNDS,
    HOT_CIRCUIT_PRESSURE_BOUNDS,
    HOT_CIRCUIT_TEMPERATURE_BOUNDS,
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
from energy_box_control.power_hub.sensors import ElectricBatterySensors
from typing import get_type_hints


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


class WeatherStationAlarm(Enum):
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
class ApplianceSensorValueCheck(Check):
    check: Callable[[PowerHubSensors, NetworkControl[PowerHub], PowerHub], CheckResult]


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


def appliance_value_check(
    name: str,
    sensor_fn: Callable[[PowerHubSensors], float],
    check_fn: Callable[[float, bool], bool],
    control_fn: Callable[[NetworkControl[PowerHub], PowerHub], bool],
) -> Callable[[PowerHubSensors, NetworkControl[PowerHub], PowerHub], CheckResult]:

    def _check(
        sensor_values: PowerHubSensors,
        control_values: NetworkControl[PowerHub],
        power_hub: PowerHub,
    ) -> CheckResult:
        if not check_fn(
            sensor_fn(sensor_values), control_fn(control_values, power_hub)
        ):
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


def no_pump_alarm_check(
    type: PumpAlarm | WeatherStationAlarm, message: Callable[[str, int], str]
) -> Callable[[str, Callable[[PowerHubSensors], int], Severity], AlarmHealthCheck]:
    def _no_pump_alarm_check(
        name: str, sensor_fn: Callable[[PowerHubSensors], int], severity: Severity
    ):
        def _alarm(sensor_values: PowerHubSensors) -> str | None:
            alarm_code = sensor_fn(sensor_values)
            if alarm_code != type.value:
                return message(name, alarm_code)
            return None

        return AlarmHealthCheck(name=name, check=_alarm, severity=severity)

    return _no_pump_alarm_check


battery_alarm_check = sensor_alarm_check(
    ElectricBatteryAlarm.ALARM, lambda name: f"{name} is raising an alarm"
)

battery_warning_check = sensor_alarm_check(
    ElectricBatteryAlarm.WARNING, lambda name: f"{name} is raising a warning"
)

weather_station_alarm_check = no_pump_alarm_check(
    WeatherStationAlarm.NO_ALARM,
    lambda name, alarm_code: f"{name} is raising an alarm with code {alarm_code}",
)


fancoil_alarm_check = sensor_alarm_check(
    FancoilAlarm.ALARM, lambda name: f"{name} is raising an alarm"
)

fancoil_filter_check = sensor_alarm_check(
    FancoilAlarm.ALARM, lambda name: f"{name} gone bad"
)

pump_alarm = no_pump_alarm_check(
    PumpAlarm.NO_ALARM,
    lambda name, alarm_code: f"{name} is raising an alarm with code {alarm_code}",
)


def valid_value(
    name: str,
    value_fn: Callable[[PowerHubSensors], float],
    health_bound: HealthBound = HealthBound(5, 100),
    severity: Severity = Severity.CRITICAL,
) -> SensorValueCheck:
    return SensorValueCheck(
        name,
        value_check(
            name,
            value_fn,
            lambda value: health_bound.lower_bound <= value <= health_bound.upper_bound
            or isnan(value),
        ),
        severity,
    )


def valid_appliance_value(
    name: str,
    value_fn: Callable[[PowerHubSensors], float],
    control_fn: Callable[[NetworkControl[PowerHub], PowerHub], bool],
    health_bound: HealthBound,
    severity: Severity = Severity.CRITICAL,
) -> ApplianceSensorValueCheck:
    return ApplianceSensorValueCheck(
        name,
        appliance_value_check(
            name,
            value_fn,
            lambda value, appliance_on: (
                health_bound.lower_bound < value < health_bound.upper_bound
                if appliance_on and not isnan(value)
                else True
            ),
            control_fn,
        ),
        severity,
    )


sensor_checks = [
    valid_value("pcm_temperature_check", lambda sensors: sensors.pcm.temperature),
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
        lambda sensors: sensors.pcm.charge_pressure,
        HOT_CIRCUIT_PRESSURE_BOUNDS,
    ),
]

yazaki_bound_checks = [
    valid_appliance_value(
        f"yazaki_{attr}_check",
        lambda sensors, attr=attr: getattr(sensors.yazaki, attr),
        lambda control_values, network: control_values.appliance(network.yazaki)
        .get()
        .on,
        YAZAKI_BOUNDS[attr],
    )
    for attr in [attr for attr, _ in YAZAKI_BOUNDS.items()]
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
        health_bound=TANK_BOUNDS[tank_name],
        severity=Severity.CRITICAL,
    )
    for tank_name in TANK_BOUNDS.keys()
]


container_temperature_checks = [
    valid_value(
        attr,
        lambda sensors, attr=attr: getattr(sensors.containers, attr),
        health_bound=CONTAINER_BOUNDS["temperature"],
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
        health_bound=CONTAINER_BOUNDS["humidity"],
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
        health_bound=CONTAINER_BOUNDS["co2"],
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

weather_station_alarm_checks = [
    weather_station_alarm_check(
        f"weather_station",
        lambda sensors,: getattr(sensors.weather, "alarm"),
        Severity.ERROR,
    )
]

service_checks = [
    url_health_check("Power Hub API", POWER_HUB_API_URL, severity=Severity.CRITICAL),
    url_health_check("InfluxDB Health", INFLUXDB_URL, severity=Severity.CRITICAL),
    url_health_check("MQTT Health", MQTT_HEALTH_URL, severity=Severity.CRITICAL),
    url_health_check(
        "Front End Health", DISPLAY_HEALTH_URL, severity=Severity.CRITICAL
    ),
]
