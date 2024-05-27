from dataclasses import dataclass

from dotenv import load_dotenv
from energy_box_control.checks import Check
from energy_box_control.custom_logging import get_logger
from energy_box_control.power_hub.sensors import PowerHubSensors
import pdpyras  # type: ignore
import os
from typing import Literal, Optional, Protocol


logger = get_logger(__name__)

dotenv_path = os.path.normpath(
    os.path.join(os.path.realpath(__file__), "../../", ".env")
)

load_dotenv(dotenv_path)


@dataclass
class NotificationEvent:
    message: str | None
    source: str
    dedup_key: str
    severity: Optional[Literal["critical", "error", "warning", "info"]] = None


class NotificationAgent(Protocol):
    def send_event(self, event: NotificationEvent) -> None: ...


class PagerDutyNotificationAgent(NotificationAgent):

    def __init__(self, api_key: Optional[str] = None) -> None:
        if api_key:
            self.events_session = pdpyras.EventsAPISession(api_key)
            self.events_session.url = "https://events.eu.pagerduty.com/"

    def send_event(self, event: NotificationEvent):
        logger.info("Sending alert to PagerDuty")
        if os.environ["SEND_NOTIFICATIONS"] == "True":
            self.events_session.trigger(event.message, event.source, event.dedup_key)  # type: ignore


class Monitor:
    def __init__(
        self,
        notification_agent: NotificationAgent,
        checks: list[Check],
    ):
        self.checks = checks
        self.notification_agent = notification_agent

    def run_sensor_values_checks(self, sensor_values: PowerHubSensors, source: str):
        for check in self.checks:
            if check.check(sensor_values) is not None:
                self.notification_agent.send_event(
                    NotificationEvent(
                        check.check(sensor_values), source, check.name, check.severity
                    )
                )
