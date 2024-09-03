import asyncio
from dataclasses import dataclass
from functools import partial
from asyncio import Queue
from typing import List, Dict

from paho.mqtt import client as mqtt_client

from energy_box_control.custom_logging import get_logger
from energy_box_control.monitoring.checks import Severity
from energy_box_control.monitoring.monitoring import (
    NotificationEvent,
    Notifier,
    PagerDutyNotificationChannel,
)
from energy_box_control.mqtt import run_listener
from energy_box_control.power_hub_control import SENSOR_VALUES_TOPIC
from energy_box_control.simulation import CONTROL_VALUES_TOPIC
from energy_box_control.config import CONFIG


logger = get_logger(__name__)


async def async_queue_on_message(
    queue: Queue[str],
    _client: mqtt_client.Client,
    _userdata: str,
    message: mqtt_client.MQTTMessage,
):
    decoded_message = str(message.payload.decode("utf-8"))
    # logger.debug(f"Received message: {decoded_message}")
    await queue.put(decoded_message)


@dataclass
class MQTTCheckConfig:
    topic: str
    topic_short_name: str


DEFAULT_MQTT_CHECKER_CONFIG = [
    MQTTCheckConfig(topic=SENSOR_VALUES_TOPIC, topic_short_name="sensor"),
    MQTTCheckConfig(topic=CONTROL_VALUES_TOPIC, topic_short_name="control"),
]


class MQTTChecker:

    def __init__(
        self,
        notifier: Notifier,
        config: List[MQTTCheckConfig],
        timeout: int = 180,
    ):
        self.timeout: int = timeout
        self.notifier = notifier
        self.config = config
        self.queues: Dict[str, Queue[str]] = {}
        for c in self.config:
            self.queues[c.topic] = Queue()

    async def run_with_timeout(self, queue: Queue[str], topic_short_name: str):
        while True:
            try:
                await asyncio.wait_for(queue.get(), timeout=self.timeout)
            except TimeoutError:
                logger.info(f"Received timeout on {topic_short_name}")
                self.notifier.send_events(
                    [
                        NotificationEvent(
                            f"Did not receive {topic_short_name} values for {self.timeout} seconds.",
                            "MQTT listener check",
                            f"mqtt-listener-check-{topic_short_name}-values",
                            Severity.CRITICAL,
                        )
                    ]
                )

    async def run_listeners(self):

        listen_tasks = []
        for c in self.config:
            await run_listener(
                c.topic,
                partial(async_queue_on_message, self.queues[c.topic]),
            )
            t = self.run_with_timeout(self.queues[c.topic], c.topic_short_name)
            listen_tasks.append(t)

        await asyncio.gather(*listen_tasks)


if __name__ == "__main__":
    pagerduty_notifier = Notifier(
        [PagerDutyNotificationChannel(CONFIG.pagerduty_mqtt_checker_key)]
        # [LoggerNotificationChannel(logger)]
    )
    mqtt_checker = MQTTChecker(pagerduty_notifier, DEFAULT_MQTT_CHECKER_CONFIG)
    asyncio.run(mqtt_checker.run_listeners())
