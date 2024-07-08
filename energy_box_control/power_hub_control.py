import asyncio
from dataclasses import dataclass, replace
import dataclasses
from datetime import datetime, timezone
import enum
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
from energy_box_control.monitoring.checks import service_checks
from energy_box_control.network import NetworkControl
from energy_box_control.power_hub.control import (
    ChillControlMode,
    HotControlMode,
    PowerHubControlState,
    Setpoints,
    WasteControlMode,
    control_power_hub,
    control_to_json,
    initial_control_state,
)
from energy_box_control.power_hub.network import PowerHub, PowerHubSchedules
from energy_box_control.power_hub.sensors import PowerHubSensors
from energy_box_control.sensors import sensors_to_json

logger = get_logger(__name__)

MQTT_TOPIC_BASE = "power_hub"
CONTROL_VALUES_TOPIC = f"{MQTT_TOPIC_BASE}/control_values"
SENSOR_VALUES_TOPIC = f"{MQTT_TOPIC_BASE}/sensor_values"
CONTROL_MODES_TOPIC = f"{MQTT_TOPIC_BASE}/control_modes"
ENRICHED_SENSOR_VALUES_TOPIC = f"{MQTT_TOPIC_BASE}/enriched_sensor_values"
SETPOINTS_TOPIC = f"{MQTT_TOPIC_BASE}/setpoints"


sensor_values_queue: queue.Queue[str] = queue.Queue()
setpoints_queue: queue.Queue[str] = queue.Queue()


@dataclass
class ControlModes:
    hot: HotControlMode
    chill: ChillControlMode
    waste: WasteControlMode
    time: datetime

    class ControlModesEncoder(json.JSONEncoder):
        def default(self, o: Any):
            if type(o) == datetime:
                return o.isoformat()
            if dataclasses.is_dataclass(o):
                return dataclasses.asdict(o)
            if issubclass(type(o), enum.Enum):
                return o.value
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


def publish_control_modes(
    mqtt_client: mqtt_client.Client,
    control_state: PowerHubControlState,
    notifier: Notifier,
):
    publish_to_mqtt(
        mqtt_client,
        CONTROL_MODES_TOPIC,
        json.dumps(
            ControlModes(
                control_state.hot_control.control_mode,
                control_state.chill_control.control_mode,
                control_state.waste_control.control_mode,
                datetime.now(timezone.utc),
            ),
            cls=ControlModes.ControlModesEncoder,
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


async def run():

    mqtt_client = create_and_connect_client()
    await run_listener(
        SENSOR_VALUES_TOPIC, partial(queue_on_message, sensor_values_queue)
    )

    await run_listener(SETPOINTS_TOPIC, partial(queue_on_message, setpoints_queue))

    notifier = Notifier([PagerDutyNotificationChannel(CONFIG.pagerduty_simulation_key)])
    monitor = Monitor(url_health_checks=service_checks)

    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    control_state = initial_control_state()

    while True:

        power_hub_sensors = power_hub.sensors_from_json(
            sensor_values_queue.get(block=True)
        )

        publish_sensor_values(power_hub_sensors, mqtt_client, notifier, enriched=True)

        notifier.send_events(
            monitor.run_sensor_values_checks(
                power_hub_sensors,
                "power_hub_simulation",
            )
        )

        control_state = (
            replace(control_state, setpoints=setpoints)
            if (setpoints := unqueue_setpoints())
            else control_state
        )

        control_state, control_values = control_power_hub(
            power_hub, control_state, power_hub_sensors, power_hub_sensors.time
        )

        publish_control_modes(mqtt_client, control_state, notifier)

        publish_control_values(mqtt_client, power_hub, control_values, notifier)


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
