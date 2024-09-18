from argparse import ArgumentParser
import asyncio
from dataclasses import fields
from functools import partial
from time import sleep
from energy_box_control.appliances.base import control_class
from energy_box_control.config import CONFIG
from energy_box_control.monitoring.monitoring import Notifier
from energy_box_control.mqtt import create_and_connect_client, run_listener
from energy_box_control.power_hub.network import PowerHub
from energy_box_control.power_hub.schedules import PowerHubSchedules
from energy_box_control.power_hub_control import (
    CONTROL_VALUES_TOPIC,
    publish_control_values,
)
import paho.mqtt.client as mqtt


def int_to_bit_list(val: int):
    bin_str = list(reversed(bin(val)))

    return [i for i in range(0, len(bin_str) - 2) if bin_str[i] == "1"]


def message(
    fut: asyncio.Future[None],
    client: mqtt.Client,
    topic: str,
    message: mqtt.MQTTMessage,
):
    fut.get_loop().call_soon_threadsafe(fut.set_result, None)


async def main():
    CONFIG.mqtt_host = "localhost"
    CONFIG.mqtt_port = 1883
    CONFIG.mqtt_tls_enabled = False
    parse = ArgumentParser()
    parse.add_argument("appliance")
    parse.add_argument("property")
    parse.add_argument("value")

    args = parse.parse_args()

    topic = CONTROL_VALUES_TOPIC
    mqtt_client = create_and_connect_client()

    fut: asyncio.Future[None] = asyncio.Future()

    run_listener(topic, partial(message, fut))

    sleep(0.3)  # sleep to get listener up and running (would prefer awaiting, but ok)

    mqtt_client.loop_start()

    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())

    appliance = getattr(power_hub, args.appliance)
    control_cls = control_class(appliance)
    property_type = next(
        field for field in fields(control_cls) if field.name == args.property
    ).type
    if property_type == bool:
        value_converted = args.value.lower() in ["1", "true"]
    else:
        value_converted = property_type(args.value)

    control = (
        power_hub.control(appliance)
        .value(control_cls(**{args.property: value_converted}))
        .build()
    )

    publish_control_values(mqtt_client, power_hub, control, Notifier())

    await fut
    mqtt_client.loop_stop()


asyncio.run(main())
