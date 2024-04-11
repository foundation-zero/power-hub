import json
import queue
import time
from typing import Any
from energy_box_control.network import Network, NetworkControl
from energy_box_control.power_hub.network import PowerHubControlState
from energy_box_control.power_hub.sensors import get_sensor_values
from mqtt import (
    create_and_connect_client,
    publish_value_to_mqtt,
    publish_to_mqtt,
    create_listener,
)
from paho.mqtt import client as mqtt_client

from energy_box_control.power_hub import PowerHub
from dataclasses import fields
from datetime import datetime
from uuid import UUID


MQTT_TOPIC_BASE = "power_hub"
CONTROL_VALUES_TOPIC = "power_hub/control_values"
SENSOR_VALUES_TOPIC = "power_hub/sensor_values"
control_values_queue: queue.Queue[str] = queue.Queue()
sensor_values_queue: queue.Queue[str] = queue.Queue()


def control_values_to_dict[
    Net: Network[Any]
](control: NetworkControl[Net], network: Net):
    return {
        network.find_appliance_name_by_id(item.id): value
        for item, value in control.__dict__["_controls"].items()
    }


class CustomEncoder(json.JSONEncoder):
    def default(self, o: Any):
        if hasattr(o, "__dict__"):
            return {attr: value for attr, value in o.__dict__.items() if attr != "spec"}
        if type(o) == UUID:
            return o.hex
        else:
            return json.JSONEncoder.default(self, o)


def publish_sensor_values(
    appliance_name: str,
    appliance_sensor_values: dict[str, float],
    mqtt_client: mqtt_client.Client,
    simulation_timestamp: datetime,
):
    for field_name, value in appliance_sensor_values.items():
        topic = f"{MQTT_TOPIC_BASE}/appliance_sensors/{appliance_name}/{field_name}"
        publish_value_to_mqtt(mqtt_client, topic, value, simulation_timestamp)


def control_values_on_message(client: mqtt_client.Client, userdata: str, message: str):
    decoded_message = str(message.payload.decode("utf-8"))  # type: ignore
    print("Received message:", decoded_message)
    control_values_queue.put(decoded_message)


def sensor_values_on_message(client: mqtt_client.Client, userdata: str, message: str):
    decoded_message = str(message.payload.decode("utf-8"))  # type: ignore
    print("Received message:", decoded_message)
    sensor_values_queue.put(decoded_message)


def run():
    mqtt_client = create_and_connect_client()
    create_listener(CONTROL_VALUES_TOPIC, control_values_on_message, mqtt_client)
    create_listener(SENSOR_VALUES_TOPIC, sensor_values_on_message, mqtt_client)
    power_hub = PowerHub.power_hub()

    state = power_hub.simulate(
        power_hub.simple_initial_state(start_time=datetime.now()),
        power_hub.no_control(),
    )

    control_state = PowerHubControlState()
    power_hub_sensors = power_hub.sensors_from_state(state)

    publish_to_mqtt(
        mqtt_client,
        SENSOR_VALUES_TOPIC,
        json.dumps(power_hub_sensors, cls=CustomEncoder),
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
                control_values_to_dict(control_values, power_hub), cls=CustomEncoder
            ),
        )
        control_values = control_values.from_json(
            control_values_queue.get(block=True), power_hub
        )

        new_state = power_hub.simulate(state, control_values)
        control_state = new_control_state
        state = new_state
        power_hub_sensors = power_hub.sensors_from_state(new_state)
        publish_to_mqtt(
            mqtt_client,
            SENSOR_VALUES_TOPIC,
            json.dumps(power_hub_sensors, cls=CustomEncoder),
        )

        for sensor_field in fields(power_hub_sensors):
            publish_sensor_values(
                sensor_field.name,
                get_sensor_values(sensor_field.name, power_hub_sensors),
                mqtt_client,
                state.time.timestamp,
            )

        time.sleep(1)


if __name__ == "__main__":
    run()
