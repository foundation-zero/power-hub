from argparse import ArgumentParser
import asyncio
import json

from aiomqtt import Message
from energy_box_control.amqtt import get_mqtt_client, read_single_message_from_topic
from energy_box_control.config import CONFIG
from energy_box_control.custom_logging import get_logger
from energy_box_control.power_hub.control.state import parse_setpoints
from energy_box_control.power_hub_control import SETPOINTS_TOPIC

        
async def main():
    CONFIG.mqtt_host = "localhost"
    CONFIG.mqtt_port = 1883
    CONFIG.mqtt_tls_enabled = False
    parse = ArgumentParser()
    parse.add_argument("setpoint")
    parse.add_argument("value")
    
    args = parse.parse_args()

    logger = get_logger(__name__)
    async with get_mqtt_client(logger) as mqtt_client:
        message = await read_single_message_from_topic(logger,mqtt_client,SETPOINTS_TOPIC)

        setpoints_dict = json.loads(message.payload)
        
        setpoints_dict[args.setpoint] = args.value
        new_setpoints_str = json.dumps(setpoints_dict)
        
        if not parse_setpoints(new_setpoints_str):
            print("couldn't parse new setpoints")
            pass 
        else:
            print("sent new setpoints")
            print(setpoints_dict)
            await mqtt_client.publish(SETPOINTS_TOPIC,new_setpoints_str)



asyncio.run(main())
