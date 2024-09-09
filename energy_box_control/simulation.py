from datetime import datetime, timezone

from dataclasses import dataclass
import schedule
from energy_box_control.monitoring.monitoring import (
    Notifier,
    PagerDutyNotificationChannel,
)
from energy_box_control.custom_logging import get_logger
import queue
from energy_box_control.network import NetworkState
from energy_box_control.power_hub.control.control import (
    control_from_json,
    no_control,
)

from energy_box_control.power_hub.network import PowerHubSchedules
from energy_box_control.power_hub import PowerHub, PowerHubSensors
from energy_box_control.mqtt import (
    create_and_connect_client,
    run_listener,
    publish_to_mqtt,
)
from paho.mqtt import client as mqtt_client

from functools import partial

from energy_box_control.power_hub_control import (
    CONTROL_VALUES_TOPIC,
    SENSOR_VALUES_TOPIC,
    ENRICHED_SENSOR_VALUES_TOPIC,
)

import asyncio
from energy_box_control.config import CONFIG
from energy_box_control.sensors import sensors_to_json

logger = get_logger(__name__)


control_values_queue: queue.Queue[str] = queue.Queue()
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


def publish_sensor_values(
    sensor_values: PowerHubSensors,
    mqtt_client: mqtt_client.Client,
    notifier: Notifier,
    enriched: bool = False,
):
    publish_to_mqtt(
        mqtt_client,
        ENRICHED_SENSOR_VALUES_TOPIC if enriched else SENSOR_VALUES_TOPIC,
        sensors_to_json(sensor_values, include_properties=enriched),
        notifier,
    )


@dataclass
class SimulationResult:
    power_hub: PowerHub
    state: NetworkState[PowerHub]

    def step(
        self,
        mqtt_client: mqtt_client.Client,
        notifier: Notifier,
        power_hub: PowerHub,
    ) -> "SimulationResult":

        try:
            control_values = control_from_json(
                self.power_hub, control_values_queue.get(block=True, timeout=10)
            )
            state = self.power_hub.simulate(self.state, control_values)
        except queue.Empty:
            state = self.state

        publish_sensor_values(
            power_hub.sensors_from_state(state), mqtt_client, notifier
        )
        return SimulationResult(self.power_hub, state)


async def run(
    steps: int = 0, schedules: PowerHubSchedules = PowerHubSchedules.const_schedules()
):
    mqtt_client = create_and_connect_client()
    await run_listener(
        CONTROL_VALUES_TOPIC, partial(queue_on_message, control_values_queue)
    )

    notifier = Notifier([PagerDutyNotificationChannel(CONFIG.pagerduty_simulation_key)])

    power_hub = PowerHub.power_hub(schedules)
    state = power_hub.simulate(
        power_hub.simple_initial_state(start_time=datetime.now(tz=timezone.utc)),
        no_control(power_hub),
    )

    publish_sensor_values(power_hub.sensors_from_state(state), mqtt_client, notifier)

    result = SimulationResult(power_hub, state)

    run_queue: queue.Queue[None] = queue.Queue()

    def _add_step_to_queue():
        run_queue.put(None)

    step = schedule.every(1).seconds.do(_add_step_to_queue)  # type: ignore

    while True:
        schedule.run_pending()
        try:
            run_queue.get_nowait()
            result = result.step(mqtt_client, notifier, power_hub)
            if steps and steps < result.state.time.step:
                schedule.cancel_job(step)
                break

        except queue.Empty:
            pass


def main():
    asyncio.run(run(schedules=PowerHubSchedules.schedules_from_data()))


if __name__ == "__main__":
    main()
