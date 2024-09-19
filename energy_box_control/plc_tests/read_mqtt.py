from argparse import ArgumentParser
import asyncio
from functools import partial
import json
from typing import Any
from energy_box_control.config import CONFIG
from energy_box_control.mqtt import run_listener
from energy_box_control.power_hub_control import (
    CONTROL_MODES_TOPIC,
    CONTROL_VALUES_TOPIC,
    ENRICHED_SENSOR_VALUES_TOPIC,
    SENSOR_VALUES_TOPIC,
    SETPOINTS_TOPIC,
)
import paho.mqtt.client as mqtt


def int_to_bit_list(val: int):
    bin_str = list(reversed(bin(val)))

    return [i for i in range(0, len(bin_str) - 2) if bin_str[i] == "1"]


def message(
    modes: bool,
    raw: bool,
    appliance: str,
    fut: asyncio.Future[None],
    client: mqtt.Client,
    topic: str,
    message: mqtt.MQTTMessage,
):
    content = str(message.payload, "utf-8")
    content = content.replace("-#Inf", '"-#Inf"').replace("#Inf", '"#Inf"')
    if modes or raw:
        print(content)
    else:
        dict = json.loads(content)
        if appliance in dict:
            if "status" in dict[appliance]:
                status = dict[appliance]["status"]
                dict[appliance]["status"] = {
                    "raw": status,
                    "bins": int_to_bit_list(status),
                }
            print(dict[appliance])
        else:
            print(f"didn't find {appliance} in {content}")
    fut.get_loop().call_soon_threadsafe(fut.set_result, None)


def topic(args: Any):
    match (args.enriched, args.control_mode, args.control_values, args.setpoints):
        case (True, _, _, _):
            return ENRICHED_SENSOR_VALUES_TOPIC
        case (_, True, _, _):
            return CONTROL_MODES_TOPIC
        case (_, _, True, _):
            return CONTROL_VALUES_TOPIC
        case (_, _, _, True):
            return SETPOINTS_TOPIC
        case _:
            return SENSOR_VALUES_TOPIC


async def main():
    parse = ArgumentParser()
    parse.add_argument("appliance", default=None, nargs="?")
    parse.add_argument("-e", "--enriched", action="store_true")
    parse.add_argument("-m", "--control-mode", action="store_true")
    parse.add_argument("-v", "--control-values", action="store_true")
    parse.add_argument("-s", "--setpoints", action="store_true")
    parse.add_argument("-r", "--raw", action="store_true")
    parse.add_argument("-l", "--local", action="store_true")
    args = parse.parse_args()

    if args.local:
        CONFIG.mqtt_host = "127.0.0.1"
        CONFIG.mqtt_port = 1883
        CONFIG.mqtt_tls_enabled = False
        CONFIG.logging_level = "DEBUG"
    else:
        CONFIG.mqtt_host = "vernemq.prod.power-hub.foundationzero.org"
        CONFIG.mqtt_port = 8883
        CONFIG.mqtt_tls_enabled = True
        CONFIG.mqtt_tls_path = "./plc/certs/ISRG_ROOT_X1.crt"
        CONFIG.logging_level = "DEBUG"
        CONFIG.mqtt_username = "readonly"
    CONFIG.mqtt_password = "w*j4kyhLPxaGwsuPi%pgL"
    fut: asyncio.Future[None] = asyncio.Future()

    await run_listener(
        topic(args), partial(message, args.control_mode, args.raw, args.appliance, fut)
    )
    await fut


# main()
asyncio.run(main())
