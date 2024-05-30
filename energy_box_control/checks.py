from dataclasses import dataclass
from typing import Callable
from energy_box_control.power_hub.sensors import PowerHubSensors
from enum import Enum


class Severity(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


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


@dataclass
class Check:
    name: str
    check: Callable[[PowerHubSensors], str | None]
    severity: Severity


def valid_temp(
    name: str,
    value_fn: Callable[[PowerHubSensors], float],
    lower_bound: int = 5,
    upper_bound: int = 100,
    severity: Severity = Severity.ERROR,
) -> Check:
    return Check(
        name,
        value_check(
            name,
            value_fn,
            lambda value: lower_bound < value < upper_bound,
        ),
        severity,
    )


checks = [valid_temp("pcm_temperature_check", lambda sensors: sensors.pcm.temperature)]
