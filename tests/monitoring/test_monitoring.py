from energy_box_control.monitoring.checks import (
    sensor_checks,
    Severity,
    battery_alarm_checks,
    battery_warning_checks,
    weather_station_alarm_checks,
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


def test_battery_alarm_checks():
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    sensors.electric_battery.battery_fuse_blown_alarm = 2
    monitor = Monitor(alarm_checks=battery_alarm_checks)
    source = "test"
    assert monitor.run_alarm_checks(sensors, source)[0] == NotificationEvent(
        message=f"battery_fuse_blown_alarm is raising an alarm",
        source=source,
        dedup_key="battery_fuse_blown_alarm",
        severity=Severity.CRITICAL,
    )


def test_battery_warning_checks():
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    sensors.electric_battery.battery_fuse_blown_alarm = 1
    monitor = Monitor(alarm_checks=battery_warning_checks)
    source = "test"
    assert monitor.run_alarm_checks(sensors, source)[0] == NotificationEvent(
        message=f"battery_fuse_blown_alarm_warning is raising a warning",
        source=source,
        dedup_key="battery_fuse_blown_alarm_warning",
        severity=Severity.WARNING,
    )


def test_weather_station_alarm_checks():
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    sensors.weather.alarm = 50
    monitor = Monitor(alarm_checks=weather_station_alarm_checks)
    source = "test"
    assert monitor.run_alarm_checks(sensors, source)[0] == NotificationEvent(
        message=f"weather_station is raising an alarm",
        source=source,
        dedup_key="weather_station",
        severity=Severity.ERROR,
    )


def test_send_events(mocker):
    channel = PagerDutyNotificationChannel("test")
    mocker.patch.object(channel, "send_event")
    notifier = Notifier([channel])
    notifier.send_events([NotificationEvent("test", "test", "test", Severity.CRITICAL)])
    channel.send_event.assert_called_once()  # type: ignore
