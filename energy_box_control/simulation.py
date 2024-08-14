from datetime import datetime, timezone

from dataclasses import dataclass
import schedule
from energy_box_control.monitoring.monitoring import (
    Monitor,
    Notifier,
    PagerDutyNotificationChannel,
)
from energy_box_control.custom_logging import get_logger
import queue
from energy_box_control.network import NetworkState
from energy_box_control.power_hub.control import (
    PowerHubControlState,
    control_from_json,
    initial_control_state,
    no_control,
)

from energy_box_control.power_hub.network import PowerHubSchedules
from energy_box_control.monitoring.checks import all_checks
from energy_box_control.power_hub import PowerHub
from energy_box_control.mqtt import (
    create_and_connect_client,
    run_listener,
)
from paho.mqtt import client as mqtt_client

from functools import partial

from energy_box_control.power_hub_control import (
    SETPOINTS_TOPIC,
    CONTROL_VALUES_TOPIC,
    SENSOR_VALUES_TOPIC,
    SURVIVAL_MODE_TOPIC,
    combine_survival_setpoints,
    publish_sensor_values,
    unqueue_setpoints,
    queue_on_message,
    unqueue_survival_mode,
    survival_queue,
    setpoints_queue,
)

import asyncio
from energy_box_control.config import CONFIG

logger = get_logger(__name__)


control_values_queue: queue.Queue[str] = queue.Queue()
sensor_values_queue: queue.Queue[str] = queue.Queue()


@dataclass
class SimulationResult:
    power_hub: PowerHub
    state: NetworkState[PowerHub]
    control_state: PowerHubControlState

    def step(
        self,
        mqtt_client: mqtt_client.Client,
        monitor: Monitor,
        notifier: Notifier,
        power_hub: PowerHub,
    ) -> "SimulationResult":

        control_state = combine_survival_setpoints(
            self.control_state,
            setpoints=unqueue_setpoints() or self.control_state.setpoints,
            survival_mode=unqueue_survival_mode()
            or self.control_state.setpoints.survival_mode,
        )

        try:
            control_values = control_from_json(
                self.power_hub, control_values_queue.get(block=True, timeout=10)
            )
            state = self.power_hub.simulate(self.state, control_values)
        except queue.Empty:
            state = self.state

        publish_sensor_values(
            power_hub.sensors_from_state(state), mqtt_client, notifier
        )
        return SimulationResult(self.power_hub, state, control_state)


async def run(
    steps: int = 0, schedules: PowerHubSchedules = PowerHubSchedules.const_schedules()
):
    mqtt_client = create_and_connect_client()
    await run_listener(
        CONTROL_VALUES_TOPIC, partial(queue_on_message, control_values_queue)
    )
    await run_listener(
        SENSOR_VALUES_TOPIC, partial(queue_on_message, sensor_values_queue)
    )
    await run_listener(SETPOINTS_TOPIC, partial(queue_on_message, setpoints_queue))
    await run_listener(SURVIVAL_MODE_TOPIC, partial(queue_on_message, survival_queue))

    notifier = Notifier([PagerDutyNotificationChannel(CONFIG.pagerduty_simulation_key)])
    monitor = Monitor(sensor_value_checks=all_checks, url_health_checks=[])

    power_hub = PowerHub.power_hub(schedules)
    state = power_hub.simulate(
        power_hub.simple_initial_state(start_time=datetime.now(tz=timezone.utc)),
        no_control(power_hub),
    )
    control_state = initial_control_state()

    publish_sensor_values(power_hub.sensors_from_state(state), mqtt_client, notifier)

    result = SimulationResult(power_hub, state, control_state)

    run_queue: queue.Queue[None] = queue.Queue()

    def _add_step_to_queue():
        run_queue.put(None)

    step = schedule.every(1).seconds.do(_add_step_to_queue)  # type: ignore

    while True:
        schedule.run_pending()
        try:
            run_queue.get_nowait()
            result = result.step(mqtt_client, monitor, notifier, power_hub)
            if steps and steps < result.state.time.step:
                schedule.cancel_job(step)
                break

        except queue.Empty:
            pass


def main():
    asyncio.run(run(schedules=PowerHubSchedules.schedules_from_data()))


if __name__ == "__main__":
    main()
