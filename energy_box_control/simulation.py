import time
from energy_box_control.power_hub.network import PowerHubControlState
from energy_box_control.power_hub.sensors import get_sensor_values
from mqtt import create_and_connect_client, publish_mqtt
from paho.mqtt import client as mqtt_client

from energy_box_control.power_hub import PowerHub
from dataclasses import fields


MQTT_TOPIC_BASE = "power_hub"


def publish_sensor_states(
    appliance_name: str,
    appliance_sensor_values: dict[str, float],
    mqtt_client: mqtt_client.Client,
):

    for field_name, value in appliance_sensor_values.items():
        topic = f"{MQTT_TOPIC_BASE}/appliance_sensors/{appliance_name}/{field_name}"
        publish_mqtt(mqtt_client, topic, value)


def run():
    power_hub = PowerHub.power_hub()
    state = power_hub.simulate(power_hub.simple_initial_state(), power_hub.no_control())
    control_state = PowerHubControlState()
    sensors = power_hub.sensors(state)
    mqtt_client = create_and_connect_client()
    control_values = power_hub.no_control()

    while True:
        new_control_state, control_values = power_hub.regulate(control_state, sensors)
        new_state = power_hub.simulate(state, control_values)
        control_state = new_control_state
        state = new_state
        power_hub_sensors = power_hub.sensors(new_state)
        for sensor_field in fields(power_hub_sensors):
            publish_sensor_states(
                sensor_field.name,
                get_sensor_values(sensor_field.name, power_hub_sensors),
                mqtt_client,
            )
        time.sleep(1)


if __name__ == "__main__":
    run()
