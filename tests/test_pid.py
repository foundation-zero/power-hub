from collections import deque
from dataclasses import dataclass, replace
from itertools import pairwise
from random import random
from hypothesis import given
from pytest import approx
from energy_box_control.pid import Pid, PidConfig
from hypothesis.strategies import floats, lists


@given(
    lists(
        floats(allow_infinity=False, allow_nan=False, max_value=1e100, min_value=-1e100)
    )
)
def test_zero_pid(measurements):
    config = PidConfig(50, 0, 0, 0)
    pid = Pid(config)
    for measurement in measurements:
        pid, control = pid.run(measurement)
        assert control == 0


@given(lists(floats(allow_infinity=False, allow_nan=False)))
def test_no_deviation(measured):
    config = PidConfig(measured, 1, 1, 1)
    pid = Pid(config)
    for measure in measured:
        pid.config = replace(config, setpoint=measure)
        pid, control = pid.run(measure)
        assert control == 0


@given(floats(allow_infinity=False, allow_nan=False))
def test_only_proportional(measure):
    config = PidConfig(50, 1, 0, 0)
    pid = Pid(config)
    _, control = pid.run(measure)
    assert control == 50 - measure


@given(floats(allow_infinity=False, allow_nan=False))
def test_integral_single_step(measure):
    config = PidConfig(50, 0, 1, 0)
    pid = Pid(config)
    _, control = pid.run(measure)
    assert control == 50 - measure


@given(floats(allow_infinity=False, allow_nan=False))
def test_integral_over_multiple_steps(measure):
    config = PidConfig(50, 0, 0.1, 0)
    pid = Pid(config)
    control = 0.0
    for i in range(1000):
        pid, control = pid.run(control - measure)
    assert control == approx(50 + measure)


@dataclass
class LinearSystem:
    slope: float
    offset: float
    noise: float

    def control(self, value: float) -> float:
        return value * self.slope + self.offset + (random() * 2 - 1) * self.noise


def test_noisy_system():
    system = LinearSystem(5, -20, 0.5)
    pid = Pid(PidConfig(10, 0.00, 0.0001, 0))
    control = 0.0
    total = 0.0
    n = 1000000
    for i in range(n):
        measure = system.control(control)
        total += measure
        pid, control = pid.run(measure)

    assert total / n == approx(10, abs=0.1)


class SlowSystem:
    acc: float

    def __init__(self, offset: float, ratio: float):
        self.offset = offset
        self.ratio = ratio
        self.acc = offset

    def control(self, value: float) -> float:
        new_value = value + self.offset
        self.acc = (self.acc * self.ratio) + new_value * (1 - self.ratio)
        return self.acc


def test_overshoot_limitation():
    system = SlowSystem(-20, 0.9)
    pid = Pid(
        PidConfig(10, 0, 0.05, -4)
    )  # ki calibrated to overshoot at 0 kd and tuned not to overshoot
    control = 0.0
    measures = []
    for i in range(100000):
        measure = system.control(control)
        pid, control = pid.run(measure)
        measures.append(measure)

    assert max(measures) < 10.1
