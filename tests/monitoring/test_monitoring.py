from dataclasses import fields
import pytest
from energy_box_control.monitoring.checks import (
    ValveAlarm,
    sensor_checks,
    Severity,
    alarm_checks,
    warning_checks,
    valve_alarm_checks,
)
from energy_box_control.monitoring.monitoring import (
    NotificationEvent,
    PagerDutyNotificationChannel,
    Monitor,
    Notifier,
)
from energy_box_control.power_hub.network import PowerHub, PowerHubSchedules
from energy_box_control.power_hub.sensors import PowerHubSensors


def test_run_sensor_values_checks():
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    pcm_fake_value = 1000
    sensors.pcm.temperature = pcm_fake_value
    monitor = Monitor(sensor_checks)
    source = "test"
    assert monitor.run_sensor_values_checks(sensors, source)[0] == NotificationEvent(
        message=f"pcm_temperature_check is outside valid bounds with value: {pcm_fake_value}",
        source=source,
        dedup_key="pcm_temperature_check",
        severity=Severity.ERROR,
    )


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


@pytest.mark.parametrize(
    "alarm,dedup_key",
    [
        (ValveAlarm.ACTUATOR_CANNOT_MOVE, "actuator"),
        (ValveAlarm.GEAR_TRAIN_DISENGAGED, "gear_train"),
    ],
)
def test_valve_alarm_checks(alarm, dedup_key):
    for valve_name in [
        field.name for field in fields(PowerHubSensors) if "valve" in field.name
    ]:
        power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
        sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
        setattr(getattr(sensors, valve_name), "service_info", alarm.value)
        monitor = Monitor(alarm_checks=valve_alarm_checks)
        source = "test"
        assert monitor.run_alarm_checks(sensors, source)[0] == NotificationEvent(
            message=f"{valve_name}_{dedup_key}_alarm is raised",
            source=source,
            dedup_key=f"{valve_name}_{dedup_key}_alarm",
            severity=Severity.CRITICAL,
        )


def test_send_events(mocker):
    channel = PagerDutyNotificationChannel("test")
    mocker.patch.object(channel, "send_event")
    notifier = Notifier([channel])
    notifier.send_events([NotificationEvent("test", "test", "test", Severity.CRITICAL)])
    channel.send_event.assert_called_once()  # type: ignore
