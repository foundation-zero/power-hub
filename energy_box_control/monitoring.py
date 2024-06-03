from dataclasses import dataclass

from energy_box_control.checks import Check, Severity
from energy_box_control.custom_logging import get_logger
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
        logger.info("Sending alert to PagerDuty")
        if CONFIG.send_notifications:
            self._events_session.trigger(event.message, event.source, event.dedup_key)  # type: ignore


class Notifier:
    def __init__(self, notification_channels: list[NotificationChannel] = []):
        self._notification_channels = notification_channels

    def send_events(self, events: list[NotificationEvent]):
        for event in events:
            for channel in self._notification_channels:
                channel.send_event(event)


class Monitor:
    def __init__(self, checks: list[Check]):
        self._checks = checks

    def run_sensor_values_checks(
        self, sensor_values: PowerHubSensors, source: str
    ) -> list[NotificationEvent]:
        return [
            NotificationEvent(result, source, check.name, check.severity)
            for check in self._checks
            if (result := check.check(sensor_values)) is not None
        ]
