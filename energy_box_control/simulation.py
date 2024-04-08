import time
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceState,
    ConnectionState,
    Port,
)
from energy_box_control.power_hub.network import PowerHubControlState
from mqtt import create_and_connect_client, publish_mqtt
from paho.mqtt import client as mqtt_client
from typing import Any

from energy_box_control.power_hub import PowerHub
from dataclasses import fields


MQTT_TOPIC_BASE = "power_hub"


def publish_appliance_states(
    power_hub: PowerHub,
    appliance_states: dict[Appliance[Any, Any, Any], ApplianceState],
    mqtt_client: mqtt_client.Client,
):
    for appliance, appliance_state in appliance_states.items():
        for field in fields(appliance_state):
            topic = f"{MQTT_TOPIC_BASE}/appliances/{power_hub.find_appliance_name_by_id(appliance.id)}/{field.name}"
            publish_mqtt(mqtt_client, topic, getattr(appliance_state, field.name))


def publish_connection_states(
    power_hub: PowerHub,
    connection_states: dict[tuple[Appliance[Any, Any, Any], Port], ConnectionState],
    mqtt_client: mqtt_client.Client,
):
    for (appliance, port), connection_state in connection_states.items():
        for field in fields(connection_state):
            topic = f"{MQTT_TOPIC_BASE}/connections/{power_hub.find_appliance_name_by_id(appliance.id)}/{port.value}/{field.name}"
            publish_mqtt(mqtt_client, topic, getattr(connection_state, field.name))


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
        publish_appliance_states(
            power_hub, new_state.get_appliances_states(), mqtt_client
        )
        publish_connection_states(
            power_hub, new_state.get_connections_states(), mqtt_client
        )
        time.sleep(1)


if __name__ == "__main__":
    run()
