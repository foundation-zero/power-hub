import asyncio
from logging import Logger
from typing import Optional

import aiomqtt
from aiomqtt import TLSParameters, Message, Client
from aiomqtt.types import PayloadType

from energy_box_control.config import CONFIG


def get_mqtt_client(logger: Logger):
    if CONFIG.mqtt_tls_enabled:
        tls_parameters = TLSParameters(ca_certs=CONFIG.mqtt_tls_path)
    else:
        tls_parameters = None

    return aiomqtt.Client(
        CONFIG.mqtt_host,
        port=CONFIG.mqtt_port,
        username=CONFIG.mqtt_username,
        password=CONFIG.mqtt_password,
        logger=logger,
        tls_params=tls_parameters,
    )


async def read_single_message_from_topic(
    logger: Logger, mqtt_client: Client, topic: str
) -> Optional[Message]:
    await mqtt_client.subscribe(topic)
    result = None
    try:
        result = await asyncio.wait_for(anext(mqtt_client.messages), 1)

        logger.info(f"Found initial value for topic {topic}. Value: {result}")
        return result
    except StopAsyncIteration:
        pass
    except asyncio.TimeoutError:
        pass
    if result is None:
        logger.info(f"Did not find initial value for topic {topic}")
    await mqtt_client.unsubscribe(topic)
    return result


async def publish_initial_value(
    logger: Logger, mqtt_client: Client, topic: str, initial_value: PayloadType
):
    value = await read_single_message_from_topic(logger, mqtt_client, topic)
    if not value:
        await mqtt_client.publish(topic, initial_value, retain=True)
