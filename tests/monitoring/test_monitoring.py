import pytest
from energy_box_control.monitoring.checks import (
    sensor_checks,
    Severity,
    alarm_checks,
    warning_checks,
    water_tank_checks,
)
from energy_box_control.monitoring.monitoring import (
    NotificationEvent,
    PagerDutyNotificationChannel,
    Monitor,
    Notifier,
)
from energy_box_control.power_hub.network import PowerHub, PowerHubSchedules


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
    "water_tank,invalid_tank_fill",
    [
        ("grey_water_tank", 110),
        ("fresh_water_tank", 10),
        ("technical_water_tank", 10),
        ("black_water_tank", 100),
    ],
)
def test_tank_checks(water_tank: str, invalid_tank_fill: int):
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    setattr(getattr(sensors, water_tank), "percentage_fill", invalid_tank_fill)
    monitor = Monitor(sensor_value_checks=water_tank_checks)
    source = "test"
    assert monitor.run_sensor_values_checks(sensors, source)[0] == NotificationEvent(
        message=f"{water_tank}_percentage_fill is outside valid bounds with value: {invalid_tank_fill}",
        source=source,
        dedup_key=f"{water_tank}_percentage_fill",
        severity=Severity.CRITICAL,
    )


def test_send_events(mocker):
    channel = PagerDutyNotificationChannel("test")
    mocker.patch.object(channel, "send_event")
    notifier = Notifier([channel])
    notifier.send_events([NotificationEvent("test", "test", "test", Severity.CRITICAL)])
    channel.send_event.assert_called_once()  # type: ignore
