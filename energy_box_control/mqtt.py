import os
from typing import Callable, Dict
from paho.mqtt import client as mqtt_client
from paho.mqtt.client import MQTTMessageInfo
from paho.mqtt.enums import CallbackAPIVersion, MQTTErrorCode
from dotenv import load_dotenv

import random
from datetime import datetime
import json
import time

import logging
import logging.config

logging.config.fileConfig(
    os.path.normpath(os.path.join(os.path.realpath(__file__), "../", "logging.conf")),
    disable_existing_loggers=False,
)

logger = logging.getLogger(__name__)

dotenv_path = os.path.normpath(
    os.path.join(os.path.realpath(__file__), "../../", ".env")
)
load_dotenv(dotenv_path)


HOST = os.environ["MQTT_HOST"]
PORT = 1883
MIN_CLIENT_ID_INT = 0
MAX_CLIEND_ID_INT = 1000000000
USERNAME = os.getenv("MQTT_USERNAME", default="")
PASSWORD = os.getenv("MQTT_PASSWORD", default="")


def on_connect(
    client: mqtt_client.Client, userdata: str, flags: Dict[str, str], rc: MQTTErrorCode
):
    if rc == MQTTErrorCode.MQTT_ERR_SUCCESS:
        logger.info("Connected to MQTT Broker!")
    else:
        logger.error(f"Failed to connect, return code {rc}")


def create_and_connect_client() -> mqtt_client.Client:
    logger.debug(f"Connecting to {HOST}:{PORT}")
    client_id = f"python-mqtt-{random.randint(MIN_CLIENT_ID_INT, MAX_CLIEND_ID_INT)}"
    client = mqtt_client.Client(CallbackAPIVersion.VERSION1, client_id)
    client.on_connect = on_connect
    if USERNAME and PASSWORD:
        client.username_pw_set(username=USERNAME, password=PASSWORD)
    client.connect(HOST, PORT)
    return client


def publish_value_to_mqtt(
    client: mqtt_client.Client,
    topic: str,
    value: float,
    value_timestamp: datetime,
):

    result = publish_to_mqtt(
        client,
        topic,
        json.dumps(
            {"value": value, "timestamp": time.mktime(value_timestamp.timetuple())}
        ),
    )
    if result.rc == MQTTErrorCode.MQTT_ERR_SUCCESS:
        logger.info(
            f"Send `{value}` to topic `{topic}` at timestamp {value_timestamp.strftime('%d-%m-%YT%H:%M:%SZ')}"
        )


def publish_to_mqtt(
    client: mqtt_client.Client, topic: str, json_str: str
) -> MQTTMessageInfo:
    result = client.publish(topic, json_str)
    if result.rc == MQTTErrorCode.MQTT_ERR_SUCCESS:
        logger.info(f"Send `{json_str}` to topic `{topic}`")
    else:
        logger.error(f"Failed to send message to topic {topic}")
    return result


def run_listener(
    topic: str,
    on_message: Callable[[mqtt_client.Client, str, mqtt_client.MQTTMessage], None],
):
    client = create_and_connect_client()
    client.subscribe(topic)
    client.on_message = on_message
    client.loop_start()
