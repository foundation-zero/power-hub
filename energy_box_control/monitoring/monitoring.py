from dataclasses import dataclass

from energy_box_control.monitoring.checks import (
    AlarmHealthCheck,
    ApplianceSensorValueCheck,
    SensorValueCheck,
    Severity,
    UrlHealthCheck,
)
from energy_box_control.custom_logging import get_logger
from energy_box_control.network import NetworkControl
from energy_box_control.power_hub.network import PowerHub
from energy_box_control.power_hub.sensors import PowerHubSensors
import pdpyras  # type: ignore
from typing import Protocol
from energy_box_control.config import CONFIG


logger = get_logger(__name__)


@dataclass(frozen=True)
class NotificationEvent:
    message: str
    source: str
    dedup_key: str
    severity: Severity


class NotificationChannel(Protocol):
    def send_event(self, event: NotificationEvent) -> None: ...


class PagerDutyNotificationChannel(NotificationChannel):

    def __init__(self, api_key: str) -> None:
        self._events_session = pdpyras.EventsAPISession(api_key)
        self._events_session.url = "https://events.eu.pagerduty.com/"

    def send_event(self, event: NotificationEvent):
        logger.info(f"Triggering alert to PagerDuty: {event.message}")
        if CONFIG.send_notifications:
            logger.info(f"Sending alert to PagerDuty: {event.message}")
            self._events_session.trigger(event.message, event.source, event.dedup_key)  # type: ignore


class Notifier:
    def __init__(self, notification_channels: list[NotificationChannel] = []):
        self._notification_channels = notification_channels

    def send_events(self, events: list[NotificationEvent]):
        for event in events:
            for channel in self._notification_channels:
                channel.send_event(event)


class Monitor:
    def __init__(
        self,
        sensor_value_checks: list[SensorValueCheck] = [],
        appliance_sensor_value_checks: list[ApplianceSensorValueCheck] = [],
        url_health_checks: list[UrlHealthCheck] = [],
        alarm_checks: list[AlarmHealthCheck] = [],
    ):
        self._sensor_value_checks = sensor_value_checks
        self._url_health_checks = url_health_checks
        self._alarm_checks = alarm_checks
        self._appliance_sensor_value_checks = appliance_sensor_value_checks

    def run_sensor_values_checks(
        self, sensor_values: PowerHubSensors, source: str
    ) -> list[NotificationEvent]:
        return [
            NotificationEvent(result, source, check.name, check.severity)
            for check in self._sensor_value_checks
            if (result := check.check(sensor_values)) is not None
        ]

    def run_appliance_sensor_value_checks(
        self,
        sensor_values: PowerHubSensors,
        control: NetworkControl[PowerHub],
        power_hub: PowerHub,
        source: str,
    ) -> list[NotificationEvent]:
        return [
            NotificationEvent(result, source, check.name, check.severity)
            for check in self._appliance_sensor_value_checks
            if (result := check.check(sensor_values, control, power_hub)) is not None
        ]

    async def run_url_health_checks(self, source: str) -> list[NotificationEvent]:

        return [
            NotificationEvent(result, source, check.name, check.severity)
            for check in self._url_health_checks
            if (result := await check.check()) is not None
        ]

    def run_alarm_checks(
        self, sensor_values: PowerHubSensors, source: str
    ) -> list[NotificationEvent]:
        return [
            NotificationEvent(result, source, check.name, check.severity)
            for check in self._alarm_checks
            if (result := check.check(sensor_values)) is not None
        ]
