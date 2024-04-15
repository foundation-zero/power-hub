from typing import Callable, Dict
from paho.mqtt import client as mqtt_client
from paho.mqtt.client import MQTTMessageInfo
from paho.mqtt.enums import CallbackAPIVersion, MQTTErrorCode

import random
from datetime import datetime
import json
import time


HOST = "mosquitto"
PORT = 1883
MIN_CLIENT_ID_INT = 0
MAX_CLIEND_ID_INT = 1000000000


def on_connect(
    client: mqtt_client.Client, userdata: str, flags: Dict[str, str], rc: MQTTErrorCode
):
    if rc == MQTTErrorCode.MQTT_ERR_SUCCESS:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)


def create_and_connect_client() -> mqtt_client.Client:
    print(f"Connecting to {HOST}:{PORT}")
    client_id = f"python-mqtt-{random.randint(MIN_CLIENT_ID_INT, MAX_CLIEND_ID_INT)}"
    client = mqtt_client.Client(CallbackAPIVersion.VERSION1, client_id)
    client.on_connect = on_connect
    client.connect(HOST, PORT)
    return client


def publish_value_to_mqtt(
    client: mqtt_client.Client, topic: str, value: float, value_timestamp: datetime
):

    result = publish_to_mqtt(
        client,
        topic,
        json.dumps(
            {"value": value, "timestamp": time.mktime(value_timestamp.timetuple())}
        ),
    )
    if result.rc == MQTTErrorCode.MQTT_ERR_SUCCESS:
        print(
            f"Send `{value}` to topic `{topic}` at timestamp {value_timestamp.strftime('%d-%m-%YT%H:%M:%SZ')}"
        )


def publish_to_mqtt(
    client: mqtt_client.Client, topic: str, json_str: str
) -> MQTTMessageInfo:
    result = client.publish(topic, json_str)
    if result.rc == MQTTErrorCode.MQTT_ERR_SUCCESS:
        print(f"Send `{json_str}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")
    return result


def run_listener(
    topic: str,
    on_message: Callable[[mqtt_client.Client, str, mqtt_client.MQTTMessage], None],
):
    client = create_and_connect_client()
    client.subscribe(topic)
    client.on_message = on_message
    client.loop_start()
