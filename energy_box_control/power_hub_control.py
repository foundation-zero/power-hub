import asyncio
import dataclasses
from datetime import datetime, time
import json
from typing import Any

import aiomqtt

from energy_box_control.amqtt import get_mqtt_client, publish_initial_value
from energy_box_control.config import CONFIG
from energy_box_control.custom_logging import get_logger
from energy_box_control.monitoring.monitoring import (
    Monitor,
    Notifier,
    PagerDutyNotificationChannel,
)
from energy_box_control.monitoring.checks import all_checks
from energy_box_control.power_hub import PowerHubSensors

from energy_box_control.power_hub.control.control import (
    control_power_hub,
    control_to_json,
)
from energy_box_control.power_hub.control.state import (
    initial_control_state,
    initial_setpoints,
    PowerHubControlState,
    parse_setpoints,
)
from energy_box_control.power_hub.network import PowerHub, PowerHubSchedules
from energy_box_control.sensors import sensors_to_json
from energy_box_control.time import time_ms

logger = get_logger(__name__)

MQTT_TOPIC_BASE = "power_hub"
CONTROL_VALUES_TOPIC = f"{MQTT_TOPIC_BASE}/control_values"
SENSOR_VALUES_TOPIC = f"{MQTT_TOPIC_BASE}/sensor_values"
CONTROL_MODES_TOPIC = f"{MQTT_TOPIC_BASE}/control_modes"
ENRICHED_SENSOR_VALUES_TOPIC = f"{MQTT_TOPIC_BASE}/enriched_sensor_values"
SETPOINTS_TOPIC = f"{MQTT_TOPIC_BASE}/setpoints"
SURVIVAL_MODE_TOPIC = f"{MQTT_TOPIC_BASE}/survival"


class ControlModesEncoder(json.JSONEncoder):
    def default(self, o: Any):
        if isinstance(o, datetime | time):
            return o.isoformat()
        else:
            return json.JSONEncoder.default(self, o)


def control_modes_to_json(control_state: PowerHubControlState) -> str:
    return json.dumps(
        {
            **{
                name: getattr(control_state, name).control_mode.value
                for name in [f.name for f in dataclasses.fields(control_state)]
                if "control" in name
            },
            **{"time": time_ms()},
        },
        cls=ControlModesEncoder,
    )


class PowerHubControl:
    def __init__(self):
        self.notifier = Notifier(
            [PagerDutyNotificationChannel(CONFIG.pagerduty_control_app_key)]
        )
        self.last_events = []
        self.cycles_since_events = 0
        self.monitor = Monitor(sensor_value_checks=all_checks, url_health_checks=[])
        self.control_state = initial_control_state()
        self.power_hub_sensors: PowerHubSensors | None = None
        self.power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
        self.survival_mode: bool = False

    async def run(self):

        async with get_mqtt_client(logger) as mqtt_client:
            logger.info("Starting power hub control loop")

            async with asyncio.TaskGroup() as tg:
                tg.create_task(
                    publish_initial_value(
                        logger,
                        SETPOINTS_TOPIC,
                        json.dumps(
                            dataclasses.asdict(initial_setpoints()),
                            cls=ControlModesEncoder,
                        ),
                    )
                )
                tg.create_task(
                    publish_initial_value(logger, SURVIVAL_MODE_TOPIC, "false")
                )

            await mqtt_client.subscribe(SENSOR_VALUES_TOPIC, qos=1)
            await mqtt_client.subscribe(SETPOINTS_TOPIC, qos=1)
            await mqtt_client.subscribe(SURVIVAL_MODE_TOPIC, qos=1)

            async for message in mqtt_client.messages:
                if not isinstance(message.payload, bytes):
                    logger.warning(
                        f"expected bytes in payload of message: {message.payload}"
                    )
                    continue
                if message.topic.matches(SENSOR_VALUES_TOPIC):
                    logger.info(f"Received sensor values {message.payload}")
                    power_hub_sensors_new = self.power_hub.sensors_from_json(
                        message.payload
                    )
                    enriched_power_hub_sensors = sensors_to_json(
                        self.power_hub_sensors, include_properties=True
                    )

                    await mqtt_client.publish(
                        ENRICHED_SENSOR_VALUES_TOPIC,
                        payload=enriched_power_hub_sensors,
                        qos=1,
                    )
                    if power_hub_sensors_new != self.power_hub_sensors:
                        self.power_hub_sensors = power_hub_sensors_new
                        await self.control_powerhub(mqtt_client)

                if message.topic.matches(SETPOINTS_TOPIC):
                    new_setpoints = parse_setpoints(message.payload)
                    logger.info(f"Received setpoints")
                    if new_setpoints is None:
                        logger.error(f"Couldn't process received setpoints ({message})")

                    elif self.control_state.setpoints != new_setpoints:
                        logger.info(
                            f"Processed changed setpoints successfully: {message.payload}"
                        )
                        self.control_state.setpoints = new_setpoints

                if message.topic.matches(SURVIVAL_MODE_TOPIC):
                    survival_mode_new = json.loads(message.payload)
                    logger.info(f"Received survivalmode: {survival_mode_new}")
                    if survival_mode_new != self.survival_mode:
                        self.survival_mode = survival_mode_new
                        logger.info(
                            f"Processed changed survival mode {self.survival_mode}"
                        )

    async def control_powerhub(self, mqtt_client: aiomqtt.Client):
        if not self.power_hub_sensors:
            logger.info("No sensor data known, cant control powerhub")
            return

        logger.info("Controlling powerhub")
        control_state, control_values = control_power_hub(
            self.power_hub,
            self.control_state,
            self.power_hub_sensors,
            self.power_hub_sensors.time,
            self.survival_mode,
        )

        self.control_state = control_state

        events = self.monitor.run_sensor_value_checks(
            self.power_hub_sensors,
            "power_hub_simulation",
            control_values,
            self.power_hub,
        )
        if (
            events != self.last_events or self.cycles_since_events > 60
        ):  # keep alive every minute and on change
            self.notifier.send_events(events)
            self.cycles_since_events = 0
            self.last_events = events

        cm_task = mqtt_client.publish(
            CONTROL_MODES_TOPIC,
            control_modes_to_json(control_state),
            qos=1,
        )

        cv_task = mqtt_client.publish(
            CONTROL_VALUES_TOPIC,
            control_to_json(self.power_hub, control_values),
            qos=1,
        )
        await asyncio.gather(cm_task, cv_task)
        self.cycles_since_events += 1


def main():
    asyncio.run(PowerHubControl().run())


if __name__ == "__main__":
    main()
