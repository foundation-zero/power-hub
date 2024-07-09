import asyncio
from datetime import datetime, timedelta, timezone
from functools import partial
import json
import queue
from typing import Any, Tuple, no_type_check

import pytest
from energy_box_control.appliances.valve import ValveControl
from energy_box_control.config import CONFIG
from energy_box_control.monitoring.monitoring import Notifier
from energy_box_control.mqtt import (
    create_and_connect_client,
    publish_to_mqtt,
    run_listener,
)
from energy_box_control.network import NetworkControl, NetworkState
from energy_box_control.power_hub.control import (
    PowerHubControlState,
    control_power_hub,
    initial_control_state,
    no_control,
)
from energy_box_control.power_hub.network import PowerHub, PowerHubSchedules
from energy_box_control.power_hub.sensors import PowerHubSensors
from energy_box_control.power_hub_control import queue_on_message
from paho.mqtt import client as mqtt_client

from energy_box_control.api.api import execute_influx_query, get_influx_client
from energy_box_control.mqtt import create_and_connect_client, publish_to_mqtt
import fluxy
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync


survival_queue: queue.Queue[str] = queue.Queue()
SURVIVAL_MODE_TEST_TOPIC = "power_hub/test_survival"


def survival_mode(survival_mode_on: bool) -> bool:
    try:
        value_from_queue = survival_queue.get(block=True)
        return json.loads(value_from_queue)["survival"]
    except queue.Empty:
        return survival_mode_on


class DatetimeEncoder(json.JSONEncoder):
    def default(self, o: Any):
        if type(o) == datetime:
            return o.isoformat(timespec="microseconds")
        else:
            return json.JSONEncoder.default(self, o)


def publish_survival_mode(mqtt_client: mqtt_client.Client, on: bool):
    publish_to_mqtt(
        mqtt_client,
        SURVIVAL_MODE_TEST_TOPIC,
        json.dumps(
            {"survival": on, "time": datetime.now(timezone.utc)}, cls=DatetimeEncoder
        ),
        Notifier(),
    )


def step(
    power_hub: PowerHub,
    state: NetworkState,
    control_state: PowerHubControlState,
    power_hub_sensors: PowerHubSensors,
) -> Tuple[PowerHubControlState, NetworkControl, NetworkState]:
    power_hub_sensors = power_hub.sensors_from_state(state)
    control_state.setpoints.survival_mode = survival_mode(
        control_state.setpoints.survival_mode
    )
    control_state, control_values = control_power_hub(
        power_hub, control_state, power_hub_sensors, state.time.timestamp
    )
    return (control_state, control_values, power_hub.simulate(state, control_values))


@no_type_check
def assert_states(control_values: NetworkControl, power_hub: PowerHub):
    assert (
        control_values.name_to_control_values_mapping(power_hub)["outboard_pump"].on
        == True
    )
    assert (
        control_values.name_to_control_values_mapping(power_hub)[
            "chiller_switch_valve"
        ].position
        == ValveControl.b_position()
    )
    assert (
        control_values.name_to_control_values_mapping(power_hub)["chilled_loop_pump"].on
        == True
    )
    assert (
        control_values.name_to_control_values_mapping(power_hub)["waste_pump"].on
        == True
    )
    assert (
        control_values.name_to_control_values_mapping(power_hub)[
            "pcm_to_yazaki_pump"
        ].on
        == False
    )
    assert (
        control_values.name_to_control_values_mapping(power_hub)["heat_pipes_pump"].on
        == False
    )


@pytest.mark.integration
async def test_survival_mode():
    await run_listener(
        SURVIVAL_MODE_TEST_TOPIC, partial(queue_on_message, survival_queue)
    )
    mqtt_client = create_and_connect_client()
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    state = power_hub.simulate(
        power_hub.simple_initial_state(start_time=datetime.now(tz=timezone.utc)),
        no_control(power_hub),
    )
    control_state = initial_control_state()
    publish_survival_mode(mqtt_client, False)

    control_state, control_values, state = step(
        power_hub, state, control_state, power_hub.sensors_from_state(state)
    )

    publish_survival_mode(mqtt_client, True)

    control_state, control_values, state = step(
        power_hub, state, control_state, power_hub.sensors_from_state(state)
    )

    assert_states(control_values, power_hub)


async def get_survival_entries(
    client: InfluxDBClientAsync, topic: str, start: datetime, stop: datetime
):
    await execute_influx_query(
        client,
        fluxy.pipe(
            fluxy.from_bucket(CONFIG.influxdb_telegraf_bucket),
            fluxy.range(start, stop),
            fluxy.filter(lambda r: r.topic == topic),
        ),
    )


async def influx_has_survival_entries(
    client: InfluxDBClientAsync, topic: str, start: datetime, stop: datetime
) -> bool:
    try:
        results = get_survival_entries(client, topic, start, stop)
        return len(results["_value"]) > 0  # type: ignore
    except Exception:
        return False


# TODO still needs to be fixed.
@pytest.mark.integration
async def test_survival_mode_influx():
    mqtt_client = create_and_connect_client()
    survival_date = datetime(2000, 1, 1, 10, 0, 0, 0, tzinfo=timezone.utc)
    topic = "power_hub/survival_integration_test"
    json_string = json.dumps(
        {"survival": True, "time": survival_date}, cls=DatetimeEncoder
    )
    publish_to_mqtt(mqtt_client, topic, json_string, Notifier())

    start = survival_date - timedelta(days=1)
    stop = survival_date + timedelta(days=1)

    async with get_influx_client() as client:
        async with asyncio.timeout(20):
            while True:
                if await influx_has_survival_entries(client, topic, start, stop):
                    break
                await asyncio.sleep(0.5)
            assert await get_survival_entries(client, topic, start, stop)[0] == True  # type: ignore
