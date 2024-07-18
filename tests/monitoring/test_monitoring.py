from typing import List, get_type_hints
import pytest
from energy_box_control.monitoring.checks import (
    SensorValueCheck,
    sensor_checks,
    Severity,
    battery_alarm_checks,
    battery_warning_checks,
    container_fancoil_alarm_checks,
    containers_fancoil_filter_checks,
    container_co2_checks,
    container_humidity_checks,
    container_temperature_checks,
)
from energy_box_control.monitoring.monitoring import (
    NotificationEvent,
    PagerDutyNotificationChannel,
    Monitor,
    Notifier,
)
from energy_box_control.power_hub.network import PowerHub, PowerHubSchedules
from energy_box_control.power_hub.sensors import ContainersSensors
from energy_box_control.sensors import Sensor, SensorType


def test_run_sensor_values_checks():
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    pcm_fake_value = 1000
    sensors.pcm.temperature = pcm_fake_value
    monitor = Monitor(sensor_checks)
    source = "test"
    assert monitor.run_appliance_checks(sensors, source)[0] == NotificationEvent(
        message=f"pcm_temperature_check is outside valid bounds with value: {pcm_fake_value}",
        source=source,
        dedup_key="pcm_temperature_check",
        severity=Severity.ERROR,
    )


def test_battery_alarm_checks():
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    sensors.electric_battery.battery_fuse_blown_alarm = 2
    monitor = Monitor(appliance_checks=battery_alarm_checks)
    source = "test"
    assert monitor.run_appliance_checks(sensors, source)[0] == NotificationEvent(
        message=f"battery_fuse_blown_alarm is raising an alarm",
        source=source,
        dedup_key="battery_fuse_blown_alarm",
        severity=Severity.CRITICAL,
    )


def test_battery_warning_checks():
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    sensors.electric_battery.battery_fuse_blown_alarm = 1
    monitor = Monitor(appliance_checks=battery_warning_checks)
    source = "test"
    assert monitor.run_appliance_checks(sensors, source)[0] == NotificationEvent(
        message=f"battery_fuse_blown_alarm_warning is raising a warning",
        source=source,
        dedup_key="battery_fuse_blown_alarm_warning",
        severity=Severity.WARNING,
    )


@pytest.mark.parametrize(
    "fancoil_alarm",
    [
        "simulator_storage_ventilation_error",
        "office_ventilation_error",
        "kitchen_ventilation_error",
    ],
)
def test_fancoil_alarm_checks(fancoil_alarm: str):
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    setattr(sensors.containers, fancoil_alarm, 1)
    monitor = Monitor(appliance_checks=container_fancoil_alarm_checks)
    source = "test"
    assert monitor.run_appliance_checks(sensors, source)[0] == NotificationEvent(
        message=f"{fancoil_alarm} is raising an alarm",
        source=source,
        dedup_key=fancoil_alarm,
        severity=Severity.CRITICAL,
    )


@pytest.mark.parametrize(
    "filter_property",
    [
        "simulator_storage_ventilation_filter_status",
        "office_ventilation_filter_status",
        "kitchen_ventilation_filter_status",
    ],
)
def test_fancoil_filter_checks(filter_property: str):
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    setattr(sensors.containers, filter_property, 1)
    monitor = Monitor(appliance_checks=containers_fancoil_filter_checks)
    source = "test"
    assert monitor.run_appliance_checks(sensors, source)[0] == NotificationEvent(
        message=f"{filter_property} gone bad",
        source=source,
        dedup_key=filter_property,
        severity=Severity.CRITICAL,
    )


@pytest.mark.parametrize(
    "sensor_type,alerting_value,checks,severity",
    [
        (SensorType.CO2, 3, container_co2_checks, Severity.CRITICAL),
        (SensorType.HUMIDITY, 3, container_humidity_checks, Severity.ERROR),
        (SensorType.TEMPERATURE, 100, container_temperature_checks, Severity.CRITICAL),
    ],
)
def test_container_sensor_valules(
    sensor_type, alerting_value: int, checks: List[SensorValueCheck], severity
):
    for attr in [
        attr
        for attr in dir(ContainersSensors)
        if isinstance(getattr(ContainersSensors, attr), Sensor)
        and getattr(ContainersSensors, attr).type == sensor_type
    ]:
        power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
        sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
        setattr(sensors.containers, attr, alerting_value)
        monitor = Monitor(appliance_checks=checks)
        source = "test"
        assert monitor.run_appliance_checks(sensors, source)[0] == NotificationEvent(
            message=f"{attr} is outside valid bounds with value: {alerting_value}",
            source=source,
            dedup_key=attr,
            severity=severity,
        )


def test_send_events(mocker):
    channel = PagerDutyNotificationChannel("test")
    mocker.patch.object(channel, "send_event")
    notifier = Notifier([channel])
    notifier.send_events([NotificationEvent("test", "test", "test", Severity.CRITICAL)])
    channel.send_event.assert_called_once()  # type: ignore
