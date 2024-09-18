import asyncio
from functools import partial
import queue
from energy_box_control.config import CONFIG
from energy_box_control.mqtt import run_listener
from energy_box_control.power_hub_control import queue_on_message


bridge_queue: queue.Queue[str] = queue.Queue()
BRIDGE_TOPIC = "test_bridge"


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
