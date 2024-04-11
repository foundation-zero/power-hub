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


class MotionSystem:
    position: float
    velocity: float
    mass: float

    def __init__(self, mass: float):
        self.mass = mass
        self.position = 0
        self.velocity = 0

    def control(self, value: float) -> float:
        self.velocity += value / self.mass
        self.position += self.velocity
        return self.position


def test_overshoot_limitation():
    system = MotionSystem(1)

    def run_control(pid):
        control = 0.0
        measures = []
        for i in range(100000):
            measure = system.control(control)
            pid, control = pid.run(measure)
            measures.append(measure)
        return measures

    kp = 0.01

    without_overshoot_limitation = run_control(Pid(PidConfig(10, kp, 0, 0)))
    assert max(without_overshoot_limitation) > 12

    with_overshoot_limitation = run_control(Pid(PidConfig(10, kp, 0, 1)))

    assert max(with_overshoot_limitation) < 11


def test_upper_bound():
    one_to_one = LinearSystem(1, 0, 0)

    pid = Pid(PidConfig(100, 1, 0, 0, (0, 50)))

    measure = one_to_one.control(0)
    _, control = pid.run(measure)
    assert control == 50


def test_lower_bound():
    one_to_one = LinearSystem(1, 0, 0)

    pid = Pid(PidConfig(-100, 1, 0, 0, (0, 50)))

    measure = one_to_one.control(0)
    _, control = pid.run(measure)
    assert control == 0
