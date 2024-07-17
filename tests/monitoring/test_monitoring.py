import pytest
from energy_box_control.monitoring.checks import (
    sensor_checks,
    Severity,
    alarm_checks,
    warning_checks,
)
from energy_box_control.monitoring.monitoring import (
    NotificationEvent,
    PagerDutyNotificationChannel,
    Monitor,
    Notifier,
)
from energy_box_control.power_hub.components import HOT_RESERVOIR_PCM_VALVE_PCM_POSITION
from energy_box_control.power_hub.network import PowerHub, PowerHubSchedules


def test_alarm_checks():
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    sensors.electric_battery.battery_fuse_blown_alarm = 2
    monitor = Monitor(alarm_checks=alarm_checks)
    source = "test"
    assert monitor.run_alarm_checks(sensors, source)[0] == NotificationEvent(
        message=f"battery_fuse_blown_alarm is raising an alarm",
        source=source,
        dedup_key="battery_fuse_blown_alarm",
        severity=Severity.CRITICAL,
    )


def test_warning_checks():
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    sensors.electric_battery.battery_fuse_blown_alarm = 1
    monitor = Monitor(alarm_checks=warning_checks)
    source = "test"
    assert monitor.run_alarm_checks(sensors, source)[0] == NotificationEvent(
        message=f"battery_fuse_blown_alarm_warning is raising a warning",
        source=source,
        dedup_key="battery_fuse_blown_alarm_warning",
        severity=Severity.WARNING,
    )


@pytest.fixture
def out_of_bounds_value():
    return 10000


@pytest.mark.parametrize(
    "attr,check_name,valve_name,valve_attr,valve_position",
    [
        (
            "charge_input_temperature",
            "hot_circuit_temperature_check",
            "hot_switch_valve",
            "input_temperature",
            HOT_RESERVOIR_PCM_VALVE_PCM_POSITION,
        ),
        (
            "charge_flow",
            "hot_circuit_flow_check",
            "hot_switch_valve",
            "flow",
            HOT_RESERVOIR_PCM_VALVE_PCM_POSITION,
        ),
        (
            "charge_pressure",
            "hot_circuit_pressure_check",
            "hot_switch_valve",
            "pressure",
            HOT_RESERVOIR_PCM_VALVE_PCM_POSITION,
        ),
        ("temperature", "pcm_temperature_check", None, None, None),
    ],
)
def test_hot_circuit_checks(
    attr, check_name, valve_name, valve_attr, valve_position, out_of_bounds_value
):
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    if valve_name and valve_position is not None and valve_attr:
        setattr(getattr(sensors, valve_name), valve_attr, out_of_bounds_value)
        setattr(getattr(sensors, valve_name), "position", valve_position)
    else:
        setattr(sensors.pcm, attr, out_of_bounds_value)
    monitor = Monitor(sensor_value_checks=sensor_checks)
    source = "test"
    assert monitor.run_sensor_values_checks(sensors, source)[0] == NotificationEvent(
        message=f"{check_name} is outside valid bounds with value: {out_of_bounds_value}",
        source=source,
        dedup_key=check_name,
        severity=Severity.CRITICAL,
    )


def test_send_events(mocker):
    channel = PagerDutyNotificationChannel("test")
    mocker.patch.object(channel, "send_event")
    notifier = Notifier([channel])
    notifier.send_events([NotificationEvent("test", "test", "test", Severity.CRITICAL)])
    channel.send_event.assert_called_once()  # type: ignore
