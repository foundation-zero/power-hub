from dataclasses import dataclass


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


@dataclass
class PidConfig:
    kp: float
    ki: float
    kd: float
    output_limits: tuple[float, float] | None = None


class Pid:
    config: PidConfig
    _integral: float
    _e_prev: float

    def __init__(self, config: PidConfig):
        self.config = config
        self._integral = 0
        self._e_prev = 0

    def run(self, setpoint: float, measurement: float) -> "tuple[Pid, float]":
        e = setpoint - measurement

        p = self.config.kp * e
        i = self._integral + self.config.ki * e
        d = self.config.kd * (e - self._e_prev)

        raw_control_value = p + i + d

        if self.config.output_limits:
            lower, upper = self.config.output_limits
            bounded_control_value = _clamp(raw_control_value, lower, upper)
            i = _clamp(i, lower, upper)
        else:
            bounded_control_value = raw_control_value

        pid = Pid(self.config)
        pid._integral = i
        pid._e_prev = e
        return pid, bounded_control_value
