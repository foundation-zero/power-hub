import json
import queue
import time
from typing import Any
from uuid import UUID
from energy_box_control.power_hub.sensors import get_sensor_values
from energy_box_control.power_hub import PowerHub
from energy_box_control.mqtt import (
    create_and_connect_client,
    publish_value_to_mqtt,
    publish_to_mqtt,
    run_listener,
)
from paho.mqtt import client as mqtt_client
from dataclasses import fields
from datetime import datetime

from functools import partial


def _encoder(blacklist: set[str] = set()) -> type[json.JSONEncoder]:

    class NestedEncoder(json.JSONEncoder):

        def default(self, o: Any):
            if hasattr(o, "__dict__"):
                return {
                    attr: value
                    for attr, value in o.__dict__.items()
                    if attr not in blacklist
                }
            if type(o) == UUID:
                return o.hex
            else:
                return json.JSONEncoder.default(self, o)

    return NestedEncoder


MQTT_TOPIC_BASE = "power_hub"
CONTROL_VALUES_TOPIC = "power_hub/control_values"
SENSOR_VALUES_TOPIC = "power_hub/sensor_values"
control_values_queue: queue.Queue[str] = queue.Queue()
sensor_values_queue: queue.Queue[str] = queue.Queue()


def publish_sensor_values(
    appliance_name: str,
    appliance_sensor_values: dict[str, float],
    mqtt_client: mqtt_client.Client,
    simulation_timestamp: datetime,
):
    for field_name, value in appliance_sensor_values.items():
        topic = f"{MQTT_TOPIC_BASE}/appliance_sensors/{appliance_name}/{field_name}"
        publish_value_to_mqtt(mqtt_client, topic, value, simulation_timestamp)


def queue_on_message(
    queue: queue.Queue[str],
    client: mqtt_client.Client,
    userdata: str,
    message: mqtt_client.MQTTMessage,
):
    decoded_message = str(message.payload.decode("utf-8"))
    print("Received message:", decoded_message)
    queue.put(decoded_message)


def run(steps: int = 0):
    mqtt_client = create_and_connect_client()
    run_listener(CONTROL_VALUES_TOPIC, partial(queue_on_message, control_values_queue))
    run_listener(SENSOR_VALUES_TOPIC, partial(queue_on_message, sensor_values_queue))
    power_hub = PowerHub.power_hub()

    state = power_hub.simulate(
        power_hub.simple_initial_state(start_time=datetime.now()),
        power_hub.no_control(),
    )

    control_state = PowerHub.initial_control_state()
    power_hub_sensors = power_hub.sensors_from_state(state)

    publish_to_mqtt(
        mqtt_client,
        SENSOR_VALUES_TOPIC,
        json.dumps(power_hub_sensors, cls=_encoder(set("spec"))),
    )
    control_values = power_hub.no_control()

    while True:

        power_hub_sensors = power_hub.sensors_from_json(
            sensor_values_queue.get(block=True)
        )
        new_control_state, control_values = power_hub.regulate(
            control_state, power_hub_sensors
        )

        publish_to_mqtt(
            mqtt_client,
            CONTROL_VALUES_TOPIC,
            json.dumps(
                control_values.name_to_control_values_mapping(power_hub),
                cls=_encoder(),
            ),
        )
        control_values = power_hub.control_from_json(
            control_values_queue.get(block=True)
        )

        new_state = power_hub.simulate(state, control_values)

        control_state = new_control_state
        state = new_state
        power_hub_sensors = power_hub.sensors_from_state(new_state)
        publish_to_mqtt(
            mqtt_client,
            SENSOR_VALUES_TOPIC,
            json.dumps(power_hub_sensors, cls=_encoder(set("spec"))),
        )

        for sensor_field in fields(power_hub_sensors):
            publish_sensor_values(
                sensor_field.name,
                get_sensor_values(sensor_field.name, power_hub_sensors),
                mqtt_client,
                state.time.timestamp,
            )
        if steps and steps < new_state.time.step:
            break

        time.sleep(1)


if __name__ == "__main__":
    run()
