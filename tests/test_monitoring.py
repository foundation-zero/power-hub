from energy_box_control.checks import checks
from energy_box_control.monitoring import (
    NotificationEvent,
    PagerDutyNotificationAgent,
    Monitor,
)
from energy_box_control.power_hub.network import PowerHub, PowerHubSchedules


def test_run_sensor_values_checks(mocker):
    mocker_send_event = mocker.patch(
        "energy_box_control.monitoring.PagerDutyNotificationAgent.send_event",
        return_value="test",
    )
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    monitor = Monitor(PagerDutyNotificationAgent(), checks)
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    pcm_fake_value = 1000
    sensors.pcm.temperature = pcm_fake_value
    source = "test"
    monitor.run_sensor_values_checks(sensors, source)
    mocker_send_event.assert_called_once_with(
        NotificationEvent(
            message=f"pcm_temperature_check is outside normal bounds: {pcm_fake_value}",
            source=source,
            dedup_key="pcm_temperature_check",
            severity=None,
        )
    )
