import asyncio
from dataclasses import fields, replace
from datetime import datetime
from functools import partial
import json
import queue
from typing import Any, Optional
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
from energy_box_control.monitoring.checks import all_checks
from energy_box_control.network import NetworkControl
from energy_box_control.power_hub.control import (
    PowerHubControlState,
    Setpoints,
    control_power_hub,
    control_to_json,
    initial_control_state,
)
from energy_box_control.power_hub.network import PowerHub, PowerHubSchedules
from energy_box_control.power_hub.sensors import PowerHubSensors
from energy_box_control.sensors import sensors_to_json
from energy_box_control.time import time_ms


logger = get_logger(__name__)

MQTT_TOPIC_BASE = "power_hub"
CONTROL_VALUES_TOPIC = f"{MQTT_TOPIC_BASE}/control_values"
SENSOR_VALUES_TOPIC = f"{MQTT_TOPIC_BASE}/sensor_values"
CONTROL_MODES_TOPIC = f"{MQTT_TOPIC_BASE}/control_modes"
ENRICHED_SENSOR_VALUES_TOPIC = f"{MQTT_TOPIC_BASE}/enriched_sensor_values"
SETPOINTS_TOPIC = f"{MQTT_TOPIC_BASE}/setpoints"
SURVIVAL_MODE_TOPIC = f"{MQTT_TOPIC_BASE}/survival"


sensor_values_queue: queue.Queue[str] = queue.Queue()
setpoints_queue: queue.Queue[str] = queue.Queue()
survival_queue: queue.Queue[str] = queue.Queue()


class ControlModesEncoder(json.JSONEncoder):
    def default(self, o: Any):
        if type(o) == datetime:
            return o.isoformat()
        else:
            return json.JSONEncoder.default(self, o)


def queue_on_message(
    queue: queue.Queue[str],
    client: mqtt_client.Client,
    userdata: str,
    message: mqtt_client.MQTTMessage,
):
    decoded_message = str(message.payload.decode("utf-8"))
    logger.debug(f"Received message: {decoded_message}")
    queue.put(decoded_message)


def get_setpoints(control_state: PowerHubControlState):
    try:
        power_hub_control_setpoints_json = setpoints_queue.get(block=False)
        try:
            control_state.setpoints = Setpoints(
                **json.loads(power_hub_control_setpoints_json)
            )
            logger.info(
                f"Processed new setpoints successfully: {power_hub_control_setpoints_json}"
            )
        except TypeError as e:
            logger.error(
                f"Couldn't process received setpoints ({power_hub_control_setpoints_json}) with error: {e}"
            )
    except queue.Empty:
        pass

    return control_state


def publish_control_modes(
    mqtt_client: mqtt_client.Client,
    control_state: PowerHubControlState,
    notifier: Notifier,
):
    publish_to_mqtt(
        mqtt_client,
        CONTROL_MODES_TOPIC,
        json.dumps(
            {
                **{
                    name: getattr(control_state, name).control_mode.value
                    for name in [f.name for f in fields(control_state)]
                    if "control" in name
                },
                **{"time": time_ms()},
            },
            cls=ControlModesEncoder,
        ),
        notifier,
    )


def publish_control_values(
    mqtt_client: mqtt_client.Client,
    power_hub: PowerHub,
    control_values: NetworkControl[PowerHub],
    notifier: Notifier,
):
    publish_to_mqtt(
        mqtt_client,
        CONTROL_VALUES_TOPIC,
        control_to_json(power_hub, control_values),
        notifier,
    )


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


def unqueue_setpoints() -> Optional[Setpoints]:
    try:
        setpoints_json = setpoints_queue.get(block=False)
        try:
            setpoints = Setpoints(**json.loads(setpoints_json))
            logger.info(f"Processed new setpoints successfully: {setpoints_json}")
            return setpoints
        except TypeError as e:
            logger.error(
                f"Couldn't process received setpoints ({setpoints_json}) with error: {e}"
            )
    except queue.Empty:
        pass

    return None


def unqueue_survival_mode() -> bool | None:
    try:
        return json.loads(survival_queue.get(block=False))["survival"]
    except queue.Empty:
        return None


def combine_survival_setpoints(
    control_state: PowerHubControlState, setpoints: Setpoints, survival_mode: bool
):
    setpoints = replace(setpoints, survival_mode=survival_mode)
    return replace(control_state, setpoints=setpoints)


async def run(steps: Optional[int] = None):

    mqtt_client = create_and_connect_client()
    await run_listener(
        SENSOR_VALUES_TOPIC, partial(queue_on_message, sensor_values_queue)
    )

    await run_listener(SETPOINTS_TOPIC, partial(queue_on_message, setpoints_queue))

    await run_listener(SURVIVAL_MODE_TOPIC, partial(queue_on_message, survival_queue))

    notifier = Notifier(
        [PagerDutyNotificationChannel(CONFIG.pagerduty_control_app_key)]
    )
    monitor = Monitor(sensor_value_checks=all_checks, url_health_checks=[])

    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    control_state = initial_control_state()

    while True:

        power_hub_sensors = power_hub.sensors_from_json(
            sensor_values_queue.get(block=True)
        )

        publish_sensor_values(power_hub_sensors, mqtt_client, notifier, enriched=True)

        control_state = combine_survival_setpoints(
            control_state,
            setpoints=unqueue_setpoints() or control_state.setpoints,
            survival_mode=unqueue_survival_mode()
            or control_state.setpoints.survival_mode,
        )
        control_state, control_values = control_power_hub(
            power_hub, control_state, power_hub_sensors, power_hub_sensors.time
        )

        # notifier.send_events(
        #     monitor.run_sensor_value_checks(
        #         power_hub_sensors, "power_hub_simulation", control_values, power_hub
        #     )
        # )

        publish_control_modes(mqtt_client, control_state, notifier)
        publish_control_values(mqtt_client, power_hub, control_values, notifier)


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
