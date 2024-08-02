from energy_box_control.config import CONFIG
from energy_box_control.monitoring.monitoring import (
    Monitor,
    Notifier,
    PagerDutyNotificationChannel,
)
from energy_box_control.mqtt import create_and_connect_client, publish_to_mqtt
from pathlib import Path

from energy_box_control.power_hub.network import PowerHub
from energy_box_control.power_hub.schedules import PowerHubSchedules
from energy_box_control.monitoring.checks import all_checks


def main():

    notifier = Notifier(
        [PagerDutyNotificationChannel(CONFIG.pagerduty_control_app_key)]
    )
    monitor = Monitor(sensor_value_checks=all_checks, url_health_checks=[])
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())

    topic = "power_hub/sensor_values"
    client = create_and_connect_client()
    data = Path("energy_box_control/plc_tests/test_json.json").read_text()
    publish_to_mqtt(client, topic, data, notifier)
    sensor_values = power_hub.sensors_from_json(data)
    notifier.send_events(monitor.run_sensor_value_checks(sensor_values, "testing_mqtt"))


if __name__ == "__main__":
    main()
