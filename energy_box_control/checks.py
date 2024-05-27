from dataclasses import dataclass
from typing import Callable, Literal, Optional
from energy_box_control.power_hub.sensors import PowerHubSensors


def value_check[
    A, B
](name: str, sensor_fn: Callable[[A], B], check_fn: Callable[[B], bool]) -> Callable[
    [A], str | None
]:

    def _check(sensor_values: A) -> str | None:
        if check_fn(sensor_fn(sensor_values)):
            return f"{name} is outside normal bounds: {sensor_fn(sensor_values)}"

    return _check


@dataclass
class Check:
    name: str
    check: Callable[[PowerHubSensors], str | None]
    severity: Optional[Literal["critical", "error", "warning", "info"]] = None


def valid_temp(name: str, value_fn: Callable[[PowerHubSensors], float]) -> Check:
    temp_alert_low = 5
    temp_alert_high = 100
    return Check(
        name,
        value_check(
            name, value_fn, lambda value: not temp_alert_low < value < temp_alert_high
        ),
    )


checks = [valid_temp("pcm_temperature_check", lambda sensors: sensors.pcm.temperature)]
