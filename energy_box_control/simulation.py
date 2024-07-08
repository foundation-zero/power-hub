from datetime import datetime, timezone
import json

from dataclasses import dataclass
import schedule
from energy_box_control.monitoring.monitoring import (
    Monitor,
    Notifier,
    PagerDutyNotificationChannel,
)
from energy_box_control.custom_logging import get_logger
import queue
from queue import Empty
from energy_box_control.network import NetworkState
from energy_box_control.power_hub.control import (
    PowerHubControlState,
    Setpoints,
    control_from_json,
    control_power_hub,
    initial_control_state,
    no_control,
)

from energy_box_control.power_hub.network import PowerHubSchedules
from energy_box_control.monitoring.checks import sensor_checks
from energy_box_control.power_hub import PowerHub
from energy_box_control.mqtt import (
    create_and_connect_client,
    publish_to_mqtt,
    run_listener,
)
from paho.mqtt import client as mqtt_client

from functools import partial

from energy_box_control.power_hub_control import (
    publish_control_modes,
    publish_control_values,
)
from energy_box_control.sensors import sensors_to_json

import asyncio
from energy_box_control.config import CONFIG

logger = get_logger(__name__)


MQTT_TOPIC_BASE = "power_hub"
CONTROL_VALUES_TOPIC = "power_hub/control_values"
CONTROL_MODES_TOPIC = "power_hub/control_modes"
SENSOR_VALUES_TOPIC = "power_hub/sensor_values"
SETPOINTS_TOPIC = "power_hub/setpoints"
control_values_queue: queue.Queue[str] = queue.Queue()
sensor_values_queue: queue.Queue[str] = queue.Queue()
setpoints_queue: queue.Queue[str] = queue.Queue()


def queue_on_message(
    queue: queue.Queue[str],
    client: mqtt_client.Client,
    userdata: str,
    message: mqtt_client.MQTTMessage,
):
    decoded_message = str(message.payload.decode("utf-8"))
    logger.debug(f"Received message: {decoded_message}")
    queue.put(decoded_message)


@dataclass
class SimulationResult:
    power_hub: PowerHub
    state: NetworkState[PowerHub]
    control_state: PowerHubControlState

    def step(
        self,
        mqtt_client: mqtt_client.Client,
        monitor: Monitor,
        notifier: Notifier,
        power_hub: PowerHub,
    ) -> "SimulationResult":
        power_hub_sensors = self.power_hub.sensors_from_json(
            sensor_values_queue.get(block=True)
        )

        try:
            power_hub_control_setpoints_json = setpoints_queue.get(block=False)
            try:
                self.control_state.setpoints = Setpoints(
                    **json.loads(power_hub_control_setpoints_json)
                )
                logger.info(
                    f"Processed new setpoints successfully: {power_hub_control_setpoints_json}"
                )
            except TypeError as e:
                logger.error(
                    f"Couldn't process received setpoints ({power_hub_control_setpoints_json}) with error: {e}"
                )
        except Empty:
            pass

        notifier.send_events(
            monitor.run_sensor_values_checks(
                power_hub_sensors,
                "power_hub_simulation",
            )
        )

        control_state, control_values = control_power_hub(
            self.power_hub,
            self.control_state,
            power_hub_sensors,
            self.state.time.timestamp,
        )

        publish_control_modes(mqtt_client, control_state, notifier)

        publish_control_values(mqtt_client, power_hub, control_values, notifier)

        control_values = control_from_json(
            self.power_hub, control_values_queue.get(block=True)
        )

        state = self.power_hub.simulate(self.state, control_values)

        power_hub_sensors = self.power_hub.sensors_from_state(state)
        publish_to_mqtt(
            mqtt_client,
            SENSOR_VALUES_TOPIC,
            sensors_to_json(power_hub_sensors),
            notifier,
        )

        return SimulationResult(self.power_hub, state, control_state)


async def run(
    steps: int = 0, schedules: PowerHubSchedules = PowerHubSchedules.const_schedules()
):
    mqtt_client = create_and_connect_client()
    await run_listener(
        CONTROL_VALUES_TOPIC, partial(queue_on_message, control_values_queue)
    )
    await run_listener(
        SENSOR_VALUES_TOPIC, partial(queue_on_message, sensor_values_queue)
    )
    await run_listener(SETPOINTS_TOPIC, partial(queue_on_message, setpoints_queue))

    notifier = Notifier([PagerDutyNotificationChannel(CONFIG.pagerduty_simulation_key)])
    monitor = Monitor(sensor_checks)

    power_hub = PowerHub.power_hub(schedules)
    state = power_hub.simulate(
        power_hub.simple_initial_state(start_time=datetime.now(tz=timezone.utc)),
        no_control(power_hub),
    )
    control_state = initial_control_state()
    power_hub_sensors = power_hub.sensors_from_state(state)

    publish_to_mqtt(
        mqtt_client, SENSOR_VALUES_TOPIC, sensors_to_json(power_hub_sensors), notifier
    )

    result = SimulationResult(power_hub, state, control_state)

    run_queue: queue.Queue[None] = queue.Queue()

    def _add_step_to_queue():
        run_queue.put(None)

    step = schedule.every(1).seconds.do(_add_step_to_queue)  # type: ignore

    while True:
        schedule.run_pending()
        try:
            run_queue.get_nowait()
            result = result.step(mqtt_client, monitor, notifier, power_hub)
            if steps and steps < result.state.time.step:
                schedule.cancel_job(step)
                break

        except queue.Empty:
            pass


def main():
    asyncio.run(run(schedules=PowerHubSchedules.schedules_from_data()))


if __name__ == "__main__":
    main()
