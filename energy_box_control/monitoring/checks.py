from dataclasses import dataclass
from typing import Any, Callable, Optional, Protocol
from energy_box_control.power_hub.sensors import PowerHubSensors
from enum import Enum
from http import HTTPStatus
import requests


POWER_HUB_API_URL = "https://power-hub-api.staging.power-hub.foundationzero.org/"
INFLUXDB_URL = "https://influxdb.staging.power-hub.foundationzero.org/health"
MQTT_HEALTH_URL = "http://vernemq.staging.power-hub.foundationzero.org:8888/health"
DISPLAY_HEALTH_URL = "https://power-hub.pages.dev/"


class Severity(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class CheckProtocol(Protocol):
    name: str
    check: Callable[[Optional[Any]], str | None]
    severity: Severity


@dataclass
class Check(CheckProtocol):
    name: str
    severity: Severity


@dataclass
class SensorValueCheck(Check):
    check: Callable[[PowerHubSensors], str | None]


@dataclass
class UrlHealthCheck(Check):
    check: Callable[[Optional[Any]], str | None]


def value_check[
    A, B
](name: str, sensor_fn: Callable[[A], B], check_fn: Callable[[B], bool]) -> Callable[
    [A], str | None
]:

    def _check(sensor_values: A) -> str | None:
        if not check_fn(sensor_fn(sensor_values)):
            return (
                f"{name} is outside valid bounds with value: {sensor_fn(sensor_values)}"
            )

    return _check


def url_health_check(name: str, url: str, severity: Severity) -> UrlHealthCheck:

    def _url_health_check(_: Optional[Any] = None) -> str | None:
        try:
            response = requests.get(url)
            if not response.status_code == HTTPStatus.OK:
                return f"{name} is returning error code {response.status_code}"
        except Exception as e:
            return f"{name} is returning an exception: {e}"

    return UrlHealthCheck(name=name, check=_url_health_check, severity=severity)


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
cloud_services_checks = [
    url_health_check("Power Hub API", POWER_HUB_API_URL, severity=Severity.CRITICAL),
    url_health_check("InfluxDB Health", INFLUXDB_URL, severity=Severity.CRITICAL),
    url_health_check("MQTT Health", MQTT_HEALTH_URL, severity=Severity.CRITICAL),
    url_health_check(
        "Front End Health", DISPLAY_HEALTH_URL, severity=Severity.CRITICAL
    ),
]
