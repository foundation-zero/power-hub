from argparse import ArgumentParser
import asyncio

from energy_box_control.amqtt import get_mqtt_client, read_single_message_from_topic
from energy_box_control.config import CONFIG
from energy_box_control.custom_logging import get_logger
from energy_box_control.power_hub.control.state import Setpoints
from energy_box_control.power_hub_control import SETPOINTS_TOPIC


async def main():
    CONFIG.mqtt_host = "127.0.0.1"
    CONFIG.mqtt_port = 1883
    CONFIG.mqtt_tls_enabled = False
    CONFIG.mqtt_password = "w*j4kyhLPxaGwsuPi%pgL"
    parse = ArgumentParser()
    parse.add_argument("setpoint")
    parse.add_argument("value")

    args = parse.parse_args()

    logger = get_logger(__name__)
    async with get_mqtt_client(logger) as mqtt_client:
        message = await read_single_message_from_topic(
            logger, mqtt_client, SETPOINTS_TOPIC
        )
        if message is None or message.payload is None:
            print("No initial setpoints in mqtt")
        elif not isinstance(message.payload, str | bytes | bytearray):
            print(f"message payload not str | bytes | bytearray: {message.payload}")
        else:
            setpoints = Setpoints.model_validate_json(message.payload)
            setpoints_dict = setpoints.model_dump()
            setpoints_dict[args.setpoint] = args.value

            new_setpoints_str = Setpoints.model_validate(
                setpoints_dict
            ).model_dump_json()
            print(f"sent new setpoints:\n{new_setpoints_str}")
            await mqtt_client.publish(SETPOINTS_TOPIC, new_setpoints_str, retain=True)


asyncio.run(main())
