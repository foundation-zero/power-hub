from dataclasses import dataclass


@dataclass
class PidConfig:
    setpoint: float
    kp: float
    ki: float
    kd: float
    bounds: tuple[float, float] | None = None


class Pid:
    config: PidConfig
    _integral: float
    _e_prev: float

    def __init__(self, config: PidConfig):
        self.config = config
        self._integral = 0
        self._e_prev = 0

    def run(self, measurement: float) -> "tuple[Pid, float]":
        e = self.config.setpoint - measurement

        p = self.config.kp * e
        i = self._integral + self.config.ki * e
        d = self.config.kd * (e - self._e_prev)

        raw_control_value = p + i + d

        if self.config.bounds:
            lower, upper = self.config.bounds
            bounded_control_value = max(lower, min(raw_control_value, upper))
        else:
            bounded_control_value = raw_control_value

        pid = Pid(self.config)
        pid._integral = i
        pid._e_prev = e
        return pid, bounded_control_value
