from asyncio import Future
from unittest.mock import MagicMock
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
import pytest
from quart import Response
from energy_box_control.api.api import (
    app,
    build_query_range,
    build_get_values_query,
    get_connections_dict_by_appliance_type,
)
from energy_box_control.power_hub import PowerHub
from energy_box_control.appliances import ValvePort
import json
from datetime import datetime, timezone, timedelta
from freezegun import freeze_time
import fluxy
import os
import pandas as pd
import json


HEADERS = {"Authorization": f"Bearer {os.environ['API_TOKEN']}"}


@pytest.fixture(autouse=True)
async def mock_influx(mocker):
    app.influx = mocker.patch.object(InfluxDBClientAsync, "query_api")  # type: ignore
    fut = Future()
    fut.set_result(pd.DataFrame({"_time": [0, 0, 0], "_value": [0, 0, 0]}))

    app.influx.query_api().query_data_frame.return_value = fut  # type: ignore

    yield


@pytest.fixture
@freeze_time("2012-01-01")
def start_datetime(minutes_back) -> datetime:
    return datetime.now(timezone.utc) - timedelta(minutes=int(minutes_back))


@pytest.fixture
@freeze_time("2012-01-01")
def stop_datetime() -> datetime:
    return datetime.now(timezone.utc)


async def test_hello_world():
    response = await app.test_client().get("/")
    assert response.status_code == 200
    assert await response.get_data() == b"Hello World!"


async def test_get_all_appliance_names():
    response = await app.test_client().get("/appliances", headers=HEADERS)
    response_data = json.loads((await response.get_data()).decode("utf-8"))
    assert response.status_code == 200
    assert "appliances" in response_data
    assert len(response_data["appliances"]) > 0


async def assert_row_response(response: Response):
    assert response.content_type == "application/json"
    result = json.loads(await response.get_data())
    assert type(result) == list
    assert len(result) == 3


async def test_get_last_values_for_appliance():
    await assert_row_response(
        await app.test_client().get(
            f"/appliances/chiller_switch_valve/position/last_values", headers=HEADERS
        )
    )


async def test_get_last_values_for_appliance_minutes_back():
    await assert_row_response(
        await app.test_client().get(
            f"/appliances/chiller_switch_valve/position/last_values?minutes_back=60",
            headers=HEADERS,
        )
    )


async def test_get_last_values_for_connection():
    await assert_row_response(
        await app.test_client().get(
            f"/appliances/chiller_switch_valve/connections/{ValvePort.A.value}/position/last_values",
            headers=HEADERS,
        )
    )


async def test_get_last_values_for_connection_minutes_back():
    await assert_row_response(
        await app.test_client().get(
            f"/appliances/chiller_switch_valve/connections/position/{ValvePort.A.value}/last_values?minutes_back=60",
            headers=HEADERS,
        )
    )


@freeze_time("2012-01-01")
async def test_build_query_range():
    start_datetime, stop_datetime = build_query_range(60)
    assert start_datetime == datetime.now(timezone.utc) - timedelta(minutes=60)
    assert stop_datetime == datetime.now(timezone.utc)


@freeze_time("2012-01-01")
async def test_build_get_appliance_values_query():
    query = build_get_values_query(60, "chiller_switch_valve", None, "position")
    assert (
        len(
            [
                operation
                for operation in query.operations
                if type(operation) == fluxy.Filter
            ]
        )
        == 3
    )

    assert (
        fluxy.filter(
            lambda query: query.topic
            == f"power_hub/appliances/chiller_switch_valve/position"
        )
        in query.operations
    )
    assert query.range == fluxy.range(
        datetime.now(timezone.utc) - timedelta(minutes=60), datetime.now(timezone.utc)
    )


@freeze_time("2012-01-01")
async def test_build_get_connection_values_query():
    connection = ValvePort.A.value
    query = build_get_values_query(
        60, "chiller_switch_valve", connection, "temperature"
    )
    assert (
        len(
            [
                operation
                for operation in query.operations
                if type(operation) == fluxy.Filter
            ]
        )
        == 3
    )
    assert (
        fluxy.filter(
            lambda query: query.topic
            == f"power_hub/connections/chiller_switch_valve/{connection}/temperature"
        )
        in query.operations
    )
    assert query.range == fluxy.range(
        datetime.now(timezone.utc) - timedelta(minutes=60), datetime.now(timezone.utc)
    )


async def test_get_connections_dict_by_appliance_type():
    power_hub = PowerHub.power_hub()
    example_appliance = power_hub.chiller_switch_valve
    connections_dict = get_connections_dict_by_appliance_type(type(example_appliance))
    assert ValvePort.A.value in connections_dict
    assert len(connections_dict[ValvePort.A.value]["fields"]) > 0
