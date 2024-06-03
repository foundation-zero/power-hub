from energy_box_control.checks import checks, Severity
from energy_box_control.monitoring import (
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
    monitor = Monitor(checks)
    source = "test"
    assert monitor.run_sensor_values_checks(sensors, source)[0] == NotificationEvent(
        message=f"pcm_temperature_check is outside valid bounds with value: {pcm_fake_value}",
        source=source,
        dedup_key="pcm_temperature_check",
        severity=Severity.ERROR,
    )


def test_send_events(mocker):
    channel = PagerDutyNotificationChannel("test")
    mocker.patch.object(channel, "send_event")
    notifier = Notifier([channel])
    notifier.send_events([NotificationEvent("test", "test", "test", Severity.CRITICAL)])
    channel.send_event.assert_called_once()  # type: ignore
