from asyncio import Future
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
import pytest
from quart import Response
from energy_box_control.api.api import app, build_query_range, build_get_values_query
import json
from datetime import datetime, timezone, timedelta
from freezegun import freeze_time
import fluxy
import os
import pandas as pd
import json
import unittest.mock as mock
from energy_box_control.api.weather import *


HEADERS = {"Authorization": f"Bearer {os.environ['API_TOKEN']}"}


@pytest.fixture(autouse=True)
async def mock_influx(mocker):
    with mocker.patch.object(
        InfluxDBClientAsync, "query_api", return_value=mock.Mock()
    ):
        app.influx = InfluxDBClientAsync("invalid_url")  # type: ignore
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
            f"/appliance_sensors/chiller_switch_valve/position/last_values",
            headers=HEADERS,
        )
    )


async def test_get_last_values_for_appliance_minutes_back():
    await assert_row_response(
        await app.test_client().get(
            f"/appliance_sensors/chiller_switch_valve/position/last_values?minutes_back=60",
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
    query = build_get_values_query(60, "chiller_switch_valve", "position")
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
            == f"power_hub/appliance_sensors/chiller_switch_valve/position"
        )
        in query.operations
    )
    assert query.range == fluxy.range(
        datetime.now(timezone.utc) - timedelta(minutes=60), datetime.now(timezone.utc)
    )


@dataclass
class SimpleWeather:
    current: dict[str, int]
    hourly: dict[str, int]
    daily: dict[str, int]


@pytest.fixture
def lat_lon():
    return "?lat=41.3874&lon=2.1686"


@pytest.fixture(autouse=True)
async def mock_weather(mocker):
    with mocker.patch.object(WeatherClient, "_fetch_weather"):
        app.weather_client = WeatherClient()  # type: ignore
        app.weather_client._fetch_weather.return_value = SimpleWeather({"value": 1}, {"value": 1}, {"value": 1})  # type: ignore
        yield


@pytest.mark.parametrize("forecast_window", ["current", "hourly", "daily"])
async def test_get_weather(lat_lon, forecast_window):
    response = await app.test_client().get(
        f"/weather/{forecast_window}{lat_lon}", headers=HEADERS
    )
    app.weather_client._fetch_weather.assert_called()  # type: ignore
    assert (await response.json)["value"] == 1


@pytest.mark.parametrize("forecast_window", ["current", "hourly", "daily"])
async def test_weather_from_cache(lat_lon, forecast_window):
    _ = await app.test_client().get(
        f"/weather/{forecast_window}{lat_lon}", headers=HEADERS
    )
    response = await app.test_client().get(
        f"/weather/{forecast_window}{lat_lon}", headers=HEADERS
    )
    app.weather_client._fetch_weather.assert_called_once()  # type: ignore
    assert (await response.json)["value"] == 1


@pytest.mark.parametrize("forecast_window", ["current", "hourly", "daily"])
async def test_weather_location_whitelist(forecast_window):
    lat = 50.0
    lon = 50.0
    response = await app.test_client().get(
        f"/weather/{forecast_window}?lat={lat}&lon={lon}", headers=HEADERS
    )
    assert response.status_code == 422
    assert (await response.data).decode(
        "utf-8"
    ) == f"(Lat, Lon) combination of ({lat}, {lon}) is not on the whitelist."


async def test_get_total_electrical_power():
    await assert_row_response(
        await app.test_client().get(
            f"/power_hub/electrical_power/last_values",
            headers=HEADERS,
        ),
    )
