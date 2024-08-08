from datetime import datetime
import time
from energy_box_control.config import CONFIG
from energy_box_control.monitoring.monitoring import Notifier
from energy_box_control.mqtt import create_and_connect_client, publish_to_mqtt

BRIDGE_TOPIC = "test_bridge"


def main():
    CONFIG.mqtt_host = "0.0.0.0"
    mqtt_client = create_and_connect_client()
    notifier = Notifier([])
    while True:
        publish_to_mqtt(mqtt_client, BRIDGE_TOPIC, datetime.now().isoformat(), notifier)
        time.sleep(2)


if __name__ == "__main__":
    main()
