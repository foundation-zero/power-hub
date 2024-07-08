import asyncio
from functools import partial
from queue import Empty
from energy_box_control.monitoring.checks import Severity
from energy_box_control.monitoring.monitoring import (
    NotificationEvent,
    Notifier,
    PagerDutyNotificationChannel,
)
from energy_box_control.mqtt import run_listener
from energy_box_control.power_hub_control import (
    queue_on_message,
    sensor_values_queue,
    SENSOR_VALUES_TOPIC,
)
from energy_box_control.simulation import control_values_queue, CONTROL_VALUES_TOPIC
from energy_box_control.config import CONFIG


async def run_listeners(timeout: int = 60):
    notifier = Notifier(
        [PagerDutyNotificationChannel(CONFIG.pagerduty_mqtt_checker_key)]
    )

    await run_listener(
        SENSOR_VALUES_TOPIC, partial(queue_on_message, sensor_values_queue)
    )

    await run_listener(
        CONTROL_VALUES_TOPIC, partial(queue_on_message, control_values_queue)
    )

    while True:
        try:
            sensor_values_queue.get(block=True, timeout=timeout)
        except Empty:
            notifier.send_events(
                [
                    NotificationEvent(
                        f"Did not receive sensor values for {timeout} seconds.",
                        "MQTT listener check",
                        "mqtt-listener-check-sensor-values",
                        Severity.CRITICAL,
                    )
                ]
            )

        try:
            control_values_queue.get(block=True, timeout=timeout)
        except Empty:
            notifier.send_events(
                [
                    NotificationEvent(
                        f"Did not receive control values for {timeout} seconds.",
                        "MQTT listener check",
                        "mqtt-listener-check-control-values",
                        Severity.CRITICAL,
                    )
                ]
            )


def main():
    asyncio.run(run_listeners())


if __name__ == "__main__":
    main()
