from argparse import ArgumentParser
import asyncio
from functools import partial
import json
from energy_box_control.config import CONFIG
from energy_box_control.mqtt import run_listener
from energy_box_control.power_hub_control import SENSOR_VALUES_TOPIC
import paho.mqtt.client as mqtt


def message(
    appliance: str,
    fut: asyncio.Future[None],
    client: mqtt.Client,
    topic: str,
    message: mqtt.MQTTMessage,
):
    content = str(message.payload, "utf-8")
    content = content.replace("-#Inf", '"-#Inf"').replace("#Inf", '"#Inf"')
    dict = json.loads(content)
    if appliance in dict:
        print(dict[appliance])
    else:
        print(f"didn't find {appliance} in {content}")
    fut.get_loop().call_soon_threadsafe(fut.set_result, None)


async def main():
    CONFIG.mqtt_host = "vernemq.prod.power-hub.foundationzero.org"
    CONFIG.mqtt_port = 8883
    CONFIG.mqtt_tls_enabled = True
    CONFIG.mqtt_tls_path = "./plc/vernemq/bridge/certificate/ISRG_ROOT_X1.crt"
    parse = ArgumentParser()
    parse.add_argument("appliance")
    args = parse.parse_args()
    fut: asyncio.Future[None] = asyncio.Future()
    await run_listener(SENSOR_VALUES_TOPIC, partial(message, args.appliance, fut))
    await fut


asyncio.run(main())
