from dataclasses import dataclass, fields
from math import isnan
from typing import Any, Awaitable, Callable, Optional, get_type_hints
import aiohttp
from enum import Enum
from http import HTTPStatus

from energy_box_control.monitoring.health_bounds import (
    HealthBound,
    CONTAINER_BOUNDS,
    TANK_BOUNDS,
    HOT_CIRCUIT_FLOW_BOUNDS,
    HOT_CIRCUIT_PRESSURE_BOUNDS,
    HOT_CIRCUIT_TEMPERATURE_BOUNDS,
    YAZAKI_BOUNDS,
)
from energy_box_control.sensors import Sensor, SensorType
from energy_box_control.network import NetworkControl
from energy_box_control.power_hub.network import PowerHub
from energy_box_control.power_hub.sensors import (
    PowerHubSensors,
    SwitchPumpSensors,
    ValveSensors,
)
from energy_box_control.power_hub.sensors import (
    ElectricBatterySensors,
    ContainersSensors,
)


POWER_HUB_API_URL = "https://api.staging.power-hub.foundationzero.org/"
INFLUXDB_URL = "https://influxdb.staging.power-hub.foundationzero.org/health"
MQTT_HEALTH_URL = "http://vernemq.staging.power-hub.foundationzero.org:8888/health"
DISPLAY_HEALTH_URL = "https://power-hub.pages.dev/"


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
    check: Callable[
        [PowerHubSensors, Optional[NetworkControl[PowerHub]], Optional[PowerHub]],
        CheckResult,
    ]


@dataclass
class UrlHealthCheck(Check):
    check: Callable[[], Awaitable[CheckResult]]


def value_check[
    A, B, C, D
](
    name: str,
    sensor_fn: Callable[[A], B],
    check_fn: Callable[[B, bool], bool],
    message_fn: Callable[[str, B], str],
    control_fn: Optional[Callable[[Optional[C], Optional[D]], bool]] = None,
) -> Callable[[A, Optional[C], Optional[D]], CheckResult]:

    def _check(
        sensor_values: A,
        control_values: Optional[C] = None,
        power_hub: Optional[D] = None,
    ) -> CheckResult:
        if not check_fn(
            sensor_fn(sensor_values),
            control_fn(control_values, power_hub) if control_fn is not None else True,
        ):
            return message_fn(name, sensor_fn(sensor_values))
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
            check_fn=lambda value, appliance_on: (
                health_bound.lower_bound < value < health_bound.upper_bound
                if appliance_on and not isnan(value)
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
    severity: Severity,
    valid_value: bool = True,
) -> SensorValueCheck:
    return SensorValueCheck(
        name=name,
        check=value_check(
            name=name,
            sensor_fn=value_fn,
            check_fn=lambda value, _: (
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
        lambda sensors: sensors.pcm.charge_pressure,
        HOT_CIRCUIT_PRESSURE_BOUNDS,
    ),
]

battery_alarm_checks = [
    alarm(
        name=f"{attr}",
        value_fn=(lambda sensors, attr=attr: getattr(sensors.electric_battery, attr)),
        message_fn=(lambda name, _: f"{name} is raising an alarm"),
        alarm=ElectricBatteryAlarm.ALARM,
        severity=Severity.CRITICAL,
    )
    for attr in dir(ElectricBatterySensors)
    if isinstance(getattr(ElectricBatterySensors, attr), Sensor)
    and getattr(ElectricBatterySensors, attr).type == SensorType.ALARM
]

battery_warning_checks = [
    alarm(
        name=f"{attr}_warning",
        value_fn=lambda sensors, attr=attr: getattr(sensors.electric_battery, attr),
        message_fn=(lambda name, _: f"{name} is raising a warning"),
        alarm=ElectricBatteryAlarm.WARNING,
        severity=Severity.WARNING,
    )
    for attr in dir(ElectricBatterySensors)
    if isinstance(getattr(ElectricBatterySensors, attr), Sensor)
    and getattr(ElectricBatterySensors, attr).type == SensorType.ALARM
]

container_fancoil_alarm_checks = [
    alarm(
        name=f"{attr}",
        value_fn=lambda sensors, attr=attr: getattr(sensors.containers, attr),
        message_fn=lambda name, _: f"{name} is raising an alarm",
        alarm=FancoilAlarm.ALARM,
        severity=Severity.CRITICAL,
    )
    for attr in dir(ContainersSensors)
    if isinstance(getattr(ContainersSensors, attr), Sensor)
    and getattr(ContainersSensors, attr).type == SensorType.ALARM
]

containers_fancoil_filter_checks = [
    alarm(
        name=f"{attr}",
        value_fn=lambda sensors, attr=attr: getattr(sensors.containers, attr),
        message_fn=lambda name, _: f"{name} gone bad",
        alarm=FancoilAlarm.ALARM,
        severity=Severity.CRITICAL,
    )
    for attr in dir(ContainersSensors)
    if isinstance(getattr(ContainersSensors, attr), Sensor)
    and getattr(ContainersSensors, attr).type == SensorType.REPLACE_FILTER_ALARM
]

weather_station_alarm_checks = [
    alarm(
        name=f"weather_station",
        value_fn=lambda sensors,: getattr(sensors.weather, "alarm"),
        message_fn=lambda name, alarm_code: f"{name} is raising an alarm with code {alarm_code}",
        alarm=WeatherStationAlarm.NO_ALARM,
        severity=Severity.ERROR,
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
        severity=Severity.CRITICAL,
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
        severity=Severity.CRITICAL,
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
        severity=Severity.CRITICAL,
        valid_value=False,
    )
    for appliance_name, appliance_type in get_type_hints(PowerHubSensors).items()
    if appliance_type == SwitchPumpSensors
    for attr in dir(SwitchPumpSensors)
    if isinstance(getattr(SwitchPumpSensors, attr), Sensor)
    and getattr(SwitchPumpSensors, attr).type == SensorType.ALARM
]

yazaki_bound_checks = [
    valid_value(
        f"yazaki_{attr}_check",
        lambda sensors, attr=attr: getattr(sensors.yazaki, attr),
        YAZAKI_BOUNDS[attr],
        lambda control_values, network: (
            control_values.appliance(network.yazaki).get().on
            if control_values and network
            else True
        ),
    )
    for attr, _ in YAZAKI_BOUNDS.items()
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
    for attr in dir(ContainersSensors)
    if isinstance(getattr(ContainersSensors, attr), Sensor)
    and getattr(ContainersSensors, attr).type == SensorType.TEMPERATURE
]

container_humidity_checks = [
    valid_value(
        attr,
        lambda sensors, attr=attr: getattr(sensors.containers, attr),
        health_bound=CONTAINER_BOUNDS["humidity"],
        severity=Severity.ERROR,
    )
    for attr in dir(ContainersSensors)
    if isinstance(getattr(ContainersSensors, attr), Sensor)
    and getattr(ContainersSensors, attr).type == SensorType.HUMIDITY
]

container_co2_checks = [
    valid_value(
        attr,
        lambda sensors, attr=attr: getattr(sensors.containers, attr),
        health_bound=CONTAINER_BOUNDS["co2"],
        severity=Severity.CRITICAL,
    )
    for attr in dir(ContainersSensors)
    if isinstance(getattr(ContainersSensors, attr), Sensor)
    and getattr(ContainersSensors, attr).type == SensorType.CO2
]

all_checks = (
    battery_alarm_checks
    + battery_warning_checks
    + container_fancoil_alarm_checks
    + containers_fancoil_filter_checks
    + sensor_checks
    + container_temperature_checks
    + container_humidity_checks
    + container_co2_checks
    + water_tank_checks
    + pump_alarm_checks
    + yazaki_bound_checks
    + weather_station_alarm_checks
    + valve_actuator_checks
    + valve_gear_train_checks
)

service_checks = [
    url_health_check("Power Hub API", POWER_HUB_API_URL, severity=Severity.CRITICAL),
    url_health_check("InfluxDB Health", INFLUXDB_URL, severity=Severity.CRITICAL),
    url_health_check("MQTT Health", MQTT_HEALTH_URL, severity=Severity.CRITICAL),
    url_health_check(
        "Front End Health", DISPLAY_HEALTH_URL, severity=Severity.CRITICAL
    ),
]
