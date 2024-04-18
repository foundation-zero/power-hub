import json
import queue
import time
from energy_box_control.simulation_json import encoder
from energy_box_control.power_hub.control import (
    control_from_json,
    control_power_hub,
    control_to_json,
    initial_control_state,
    no_control,
)

from energy_box_control.power_hub.network import PowerHubSchedules
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

from energy_box_control.schedules import ConstSchedule
from energy_box_control.power_hub.power_hub_components import (
    COOLING_DEMAND,
    GLOBAL_IRRADIANCE,
)


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

    power_hub = PowerHub.power_hub(
        PowerHubSchedules(
            ConstSchedule(GLOBAL_IRRADIANCE), ConstSchedule(COOLING_DEMAND)
        )
    )

    state = power_hub.simulate(
        power_hub.simple_initial_state(start_time=datetime.now()),
        no_control(power_hub),
    )

    control_state = initial_control_state()
    power_hub_sensors = power_hub.sensors_from_state(state)

    publish_to_mqtt(
        mqtt_client,
        SENSOR_VALUES_TOPIC,
        json.dumps(power_hub_sensors, cls=encoder(set("spec"))),
    )

    while True:

        power_hub_sensors = power_hub.sensors_from_json(
            sensor_values_queue.get(block=True)
        )
        new_control_state, control_values = control_power_hub(
            power_hub, control_state, power_hub_sensors, state.time
        )

        publish_to_mqtt(
            mqtt_client,
            CONTROL_VALUES_TOPIC,
            control_to_json(power_hub, control_values),
        )
        control_values = control_from_json(
            power_hub, control_values_queue.get(block=True)
        )

        new_state = power_hub.simulate(state, control_values)

        control_state = new_control_state
        state = new_state
        power_hub_sensors = power_hub.sensors_from_state(new_state)
        publish_to_mqtt(
            mqtt_client,
            SENSOR_VALUES_TOPIC,
            json.dumps(power_hub_sensors, cls=encoder(set("spec"))),
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
