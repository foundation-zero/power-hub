from typing import Dict
from paho.mqtt import client as mqtt_client
from paho.mqtt.enums import CallbackAPIVersion, MQTTErrorCode
import random
from datetime import datetime
import json
import time


HOST = "mosquitto"
PORT = 1883


def on_connect(
    client: mqtt_client.Client, userdata: str, flags: Dict[str, str], rc: MQTTErrorCode
):
    if rc == MQTTErrorCode.MQTT_ERR_SUCCESS:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)


def create_and_connect_client() -> mqtt_client.Client:
    print(f"Connecting to {HOST}:{PORT}")
    client_id = f"python-mqtt-{random.randint(0, 1000)}"
    client = mqtt_client.Client(CallbackAPIVersion.VERSION1, client_id)
    client.on_connect = on_connect
    client.connect(HOST, PORT)
    return client


def publish_mqtt(
    client: mqtt_client.Client, topic: str, value: float, value_timestamp: datetime
):
    result = client.publish(
        topic,
        json.dumps(
            {"value": value, "timestamp": time.mktime(value_timestamp.timetuple())}
        ),
    )
    if result.rc == MQTTErrorCode.MQTT_ERR_SUCCESS:
        print(
            f"Send `{value}` to topic `{topic}` at timestamp {value_timestamp.strftime('%d-%m-%YT%H:%M:%SZ')}"
        )
    else:
        print(f"Failed to send message to topic {topic}")
