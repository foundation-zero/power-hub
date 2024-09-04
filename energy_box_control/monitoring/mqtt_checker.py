import asyncio
from asyncio import CancelledError

from energy_box_control.amqtt import get_mqtt_client
from energy_box_control.config import CONFIG
from energy_box_control.custom_logging import get_logger
from energy_box_control.monitoring.checks import Severity
from energy_box_control.monitoring.monitoring import (
    NotificationEvent,
    Notifier,
    PagerDutyNotificationChannel,
)
from energy_box_control.power_hub_control import SENSOR_VALUES_TOPIC
from energy_box_control.simulation import CONTROL_VALUES_TOPIC


logger = get_logger(__name__)


class MQTTChecker:

    def __init__(
        self,
        notifier: Notifier,
        topic: str,
        timeout: int = 15,
    ):
        self.timeout: int = timeout
        self.notifier = notifier
        self.topic = topic

    async def run(self):
        async with get_mqtt_client(logger) as client:
            await client.subscribe(self.topic)
            msg_iter = aiter(client.messages)
            while True:
                try:
                    message = await asyncio.wait_for(
                        anext(msg_iter), timeout=self.timeout
                    )
                    logger.info(f"recieved message: {message}")
                except TimeoutError:
                    self.notifier.send_events(
                        [
                            NotificationEvent(
                                f"Did not receive {self.topic} values for {self.timeout} seconds.",
                                "MQTT listener check",
                                f"mqtt-listener-check-{self.topic}-values",
                                Severity.CRITICAL,
                            )
                        ]
                    )
                except CancelledError:
                    break


async def main():
    pagerduty_notifier = Notifier(
        [PagerDutyNotificationChannel(CONFIG.pagerduty_mqtt_checker_key)]
    )
    sensor_mqtt_task = MQTTChecker(pagerduty_notifier, SENSOR_VALUES_TOPIC).run()
    control_mqtt_task = MQTTChecker(pagerduty_notifier, CONTROL_VALUES_TOPIC).run()

    await asyncio.gather(sensor_mqtt_task, control_mqtt_task)


if __name__ == "__main__":
    asyncio.run(main())
