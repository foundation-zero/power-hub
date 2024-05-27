from datetime import datetime
from energy_box_control.checks import value_check, valid_temp
from energy_box_control.power_hub.network import PowerHub, PowerHubSchedules


def test_value_check():
    a = 1
    increment = 1
    value_fn = lambda value: value + increment
    check_fn = lambda value: value == a + increment
    name = "testing"
    value_check_fn = value_check(name, value_fn, check_fn)
    assert value_check_fn(a) == f"{name} is outside normal bounds: {a + increment}"


def test_valid_temp():
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    check = valid_temp("testing", lambda sensors: sensors.pcm.temperature)
    assert not check.check(
        power_hub.sensors_from_state(power_hub.simple_initial_state())
    )
