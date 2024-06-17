import asyncio
from functools import partial
import queue
from paho.mqtt import client as mqtt_client
from energy_box_control.config import CONFIG
from energy_box_control.custom_logging import get_logger
from energy_box_control.monitoring.monitoring import (
    Monitor,
    Notifier,
    PagerDutyNotificationChannel,
)
from energy_box_control.mqtt import (
    create_and_connect_client,
    publish_to_mqtt,
    run_listener,
)
from energy_box_control.monitoring.checks import service_checks
from energy_box_control.power_hub.control import (
    control_power_hub,
    control_to_json,
    initial_control_state,
)
from energy_box_control.power_hub.network import PowerHub, PowerHubSchedules

logger = get_logger(__name__)

MQTT_TOPIC_BASE = "power_hub"
CONTROL_VALUES_TOPIC = "power_hub/control_values"
SENSOR_VALUES_TOPIC = "power_hub/sensor_values"


sensor_values_queue: queue.Queue[str] = queue.Queue()


def queue_on_message(
    queue: queue.Queue[str],
    client: mqtt_client.Client,
    userdata: str,
    message: mqtt_client.MQTTMessage,
):
    decoded_message = str(message.payload.decode("utf-8"))
    logger.debug(f"Received message: {decoded_message}")
    queue.put(decoded_message)


async def run():

    mqtt_client = create_and_connect_client()
    await run_listener(
        SENSOR_VALUES_TOPIC, partial(queue_on_message, sensor_values_queue)
    )

    notifier = Notifier([PagerDutyNotificationChannel(CONFIG.pagerduty_key)])
    monitor = Monitor(url_health_checks=service_checks)

    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    control_state = initial_control_state()

    while True:
        power_hub_sensors = power_hub.sensors_from_json(
            sensor_values_queue.get(block=True)
        )

        notifier.send_events(
            monitor.run_sensor_values_checks(
                power_hub_sensors,
                "power_hub_simulation",
            )
        )

        control_state, control_values = control_power_hub(
            power_hub, control_state, power_hub_sensors, power_hub_sensors.time
        )

        publish_to_mqtt(
            mqtt_client,
            CONTROL_VALUES_TOPIC,
            control_to_json(power_hub, control_values),
            notifier,
        )


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
