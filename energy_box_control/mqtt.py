from functools import partial
from typing import Any, Callable, Dict
from paho.mqtt import client as mqtt_client
from paho.mqtt.client import MQTTMessageInfo
from paho.mqtt.enums import CallbackAPIVersion, MQTTErrorCode
from paho.mqtt.reasoncodes import ReasonCode
import asyncio

import random
from datetime import datetime
import json
import time
from energy_box_control.monitoring.checks import Severity
from energy_box_control.custom_logging import get_logger
from energy_box_control.monitoring.monitoring import NotificationEvent, Notifier

from energy_box_control.config import CONFIG

logger = get_logger(__name__)


PORT = 1883
MIN_CLIENT_ID_INT = 0
MAX_CLIEND_ID_INT = 1000000000

ClientID = str


def on_subscribe(
    topic: str,
    client_id: ClientID,
    future: asyncio.Future[None],
    client: mqtt_client.Client,
    userdata: str,
    mid: int,
    reason_code_list: list[ReasonCode],
    *_args: Any,
):
    logger.info(f"Subscribed to topic {topic} for {client_id}")
    future.get_loop().call_soon_threadsafe(future.set_result, None)


def subscribe_to_topic(
    topic: str,
    on_message: Callable[[mqtt_client.Client, str, mqtt_client.MQTTMessage], None],
    future: asyncio.Future[None],
    client_id: ClientID,
    client: mqtt_client.Client,
):
    client.on_subscribe = partial(on_subscribe, topic, client_id, future)
    client.subscribe(topic, qos=1)
    client.on_message = on_message


def on_connect[
    ClientID
](
    client_id: ClientID,
    callback: Callable[[ClientID, mqtt_client.Client], Any] | None,
    client: mqtt_client.Client,
    userdata: str,
    flags: Dict[str, str],
    rc: MQTTErrorCode,
):
    if rc == MQTTErrorCode.MQTT_ERR_SUCCESS:
        logger.info(f"Connected to MQTT Broker for client {client_id}")
        if callback:
            callback(client_id, client)
    else:
        logger.error(f"Failed to connect, return code {rc} for client {client_id}")


def create_and_connect_client(
    on_connect_callback: Callable[..., None] | None = None
) -> mqtt_client.Client:
    client_id = f"python-mqtt-{random.randint(MIN_CLIENT_ID_INT, MAX_CLIEND_ID_INT)}"
    logger.info(f"Connecting to {CONFIG.mqtt_host}:{PORT} for client {client_id}")
    client = mqtt_client.Client(CallbackAPIVersion.VERSION1, client_id)
    client.on_connect = partial(on_connect, client_id, on_connect_callback)
    client.connect(CONFIG.mqtt_host, PORT)
    if CONFIG.mqtt_username and CONFIG.mqtt_password:
        client.username_pw_set(
            username=CONFIG.mqtt_username, password=CONFIG.mqtt_password
        )
    client.loop_start()
    return client


def publish_value_to_mqtt(
    client: mqtt_client.Client,
    topic: str,
    value: float,
    value_timestamp: datetime,
    notifier: Notifier,
):

    result = publish_to_mqtt(
        client,
        topic,
        json.dumps(
            {"value": value, "timestamp": time.mktime(value_timestamp.timetuple())}
        ),
        notifier,
    )
    if result.rc == MQTTErrorCode.MQTT_ERR_SUCCESS:
        logger.info(
            f"Send `{value}` to topic `{topic}` at timestamp {value_timestamp.strftime('%d-%m-%YT%H:%M:%SZ')}"
        )


def publish_to_mqtt(
    client: mqtt_client.Client,
    topic: str,
    json_str: str,
    notifier: Notifier,
) -> MQTTMessageInfo:
    result = client.publish(topic, json_str, qos=1)
    if result.rc == MQTTErrorCode.MQTT_ERR_SUCCESS:
        logger.info(f"Send `{json_str}` to topic `{topic}`")
    else:
        logger.error(
            f"Failed to send message to topic {topic} with error code: {result.rc}, client connected: {client.is_connected()}"
        )

        notifier.send_events(
            [
                NotificationEvent(
                    f"Failed to publish to MQTT: {result.rc}, please check the logs.",
                    "power_hub_simulation_mqtt",
                    "mqtt_publish",
                    Severity.ERROR,
                )
            ]
        )

    return result


def run_listener(
    topic: str,
    on_message: Callable[[mqtt_client.Client, str, mqtt_client.MQTTMessage], None],
) -> asyncio.Future[None]:
    future: asyncio.Future[None] = asyncio.get_event_loop().create_future()
    create_and_connect_client(partial(subscribe_to_topic, topic, on_message, future))
    return future
