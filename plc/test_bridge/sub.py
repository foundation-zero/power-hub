import asyncio
from functools import partial
import queue

from paho.mqtt.client import MQTTMessage, Client

from energy_box_control.config import CONFIG
from energy_box_control.mqtt import run_listener


bridge_queue: queue.Queue[str] = queue.Queue()
BRIDGE_TOPIC = "test_bridge"


def queue_on_message(
    queue: queue.Queue[str],
    client: Client,
    userdata: str,
    message: MQTTMessage,
):
    decoded_message = str(message.payload.decode("utf-8"))
    print(f"Received message: {decoded_message}")
    queue.put(decoded_message)


async def main():
    CONFIG.mqtt_host = "vernemq.staging.power-hub.foundationzero.org"
    CONFIG.mqtt_port = 8883
    CONFIG.mqtt_tls_enabled = True
    CONFIG.mqtt_tls_path = "./plc/vernemq/bridge/certificate/ISRG_ROOT_X1.crt"

    await run_listener(BRIDGE_TOPIC, partial(queue_on_message, bridge_queue))

    while True:
        print(bridge_queue.get(block=True))


if __name__ == "__main__":
    asyncio.run(main())
