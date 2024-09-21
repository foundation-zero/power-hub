import asyncio
from asyncio import CancelledError

from aiomqtt import Client, MqttError

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

MQTT_RECONNECT_INTERVAL_SECONDS = 10


class MQTTChecker:

    def __init__(
        self,
        notifier: Notifier,
        topic: str,
        timeout: int = 180,
    ):
        self.timeout: int = timeout
        self.notifier = notifier
        self.topic = topic

    async def run(self, client: Client):
        logger.info(f"Subscribing to {self.topic}")
        await client.subscribe(self.topic)
        msg_iter = aiter(client.messages)
        while True:
            try:
                message = await asyncio.wait_for(anext(msg_iter), timeout=self.timeout)
                logger.debug(f"recieved message: {message}")
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
                logger.info(f"Shutting down MQTTChecker for {self.topic}")
                await client.unsubscribe(self.topic)
                break


async def main():

    pagerduty_notifier = Notifier(
        [PagerDutyNotificationChannel(CONFIG.pagerduty_mqtt_checker_key)]
    )
    sensor_checker = MQTTChecker(pagerduty_notifier, SENSOR_VALUES_TOPIC)
    control_checker = MQTTChecker(pagerduty_notifier, CONTROL_VALUES_TOPIC)
    while True:
        try:
            async with get_mqtt_client(logger) as client:
                sensor_mqtt_task = sensor_checker.run(client)
                control_mqtt_task = control_checker.run(client)

                await asyncio.gather(sensor_mqtt_task, control_mqtt_task)
        except MqttError as e:
            logger.error(e)
            logger.info(
                f"Connection lost; Reconnecting in {MQTT_RECONNECT_INTERVAL_SECONDS} seconds ..."
            )
            await asyncio.sleep(MQTT_RECONNECT_INTERVAL_SECONDS)
        except CancelledError:
            logger.info("Shutting down")
            break


if __name__ == "__main__":
    asyncio.run(main())
