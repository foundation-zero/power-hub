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
class EmptyWeatherResponse:
    current: dict[str, int]
    hourly: dict[str, int]
    daily: dict[str, int]


@pytest.fixture
def lat_lon():
    return "?lat=50&lon=50"


def get_default_weather_response(weather: str):
    pass


async def get_empty_df(*args):
    pass


def mock_open_weather(*args):
    pass


def mock_publish_weather_values_to_mqtt(*args):
    pass


get_empty_df = mock.create_autospec(get_empty_df, return_value=pd.DataFrame())
mock_open_weather = mock.create_autospec(mock_open_weather, return_value="{'value': 1}")
get_default_weather_response = mock.create_autospec(
    get_default_weather_response,
    return_value=EmptyWeatherResponse({"value": 1}, {"value": 1}, {"value": 1}),
)
mock_publish_weather_values_to_mqtt = mock.create_autospec(
    mock_publish_weather_values_to_mqtt
)


@pytest.mark.parametrize("forecast_window", ["current", "hourly", "daily"])
async def test_get_weather(lat_lon, forecast_window, mocker):
    mocker.patch(
        "energy_box_control.api.weather.get_last_weather_from_influx", get_empty_df
    )
    mocker.patch("energy_box_control.api.weather.get_open_weather", mock_open_weather)
    mocker.patch(
        "energy_box_control.api.weather.WeatherResponse.from_json",
        get_default_weather_response,
    )
    mocker.patch(
        "energy_box_control.api.weather.publish_weather_values_to_mqtt",
        mock_publish_weather_values_to_mqtt,
    )

    response = await app.test_client().get(
        f"/weather/{forecast_window}{lat_lon}", headers=HEADERS
    )

    get_empty_df.assert_called()  # type: ignore
    mock_open_weather.assert_called()  # type: ignore
    mock_publish_weather_values_to_mqtt.assert_called()  # type: ignore

    assert (await response.json)["value"] == 1


async def get_recent_df(*args):
    pass


get_recent_df = mock.create_autospec(
    get_recent_df,
    return_value=pd.DataFrame(
        [[datetime.now(timezone.utc), 1]], columns=["_time", "_value"]  # type: ignore
    ),
)


@pytest.mark.parametrize("forecast_window", ["current", "hourly", "daily"])
async def test_weather_exists_in_cache(lat_lon, forecast_window, mocker):
    mocker.patch(
        "energy_box_control.api.weather.get_last_weather_from_influx", get_recent_df
    )
    mocker.patch(
        "energy_box_control.api.weather.WeatherResponse.from_json",
        get_default_weather_response,
    )
    response = await app.test_client().get(
        f"/weather/{forecast_window}{lat_lon}", headers=HEADERS
    )
    get_recent_df.assert_called()  # type: ignore
    assert (await response.json)["value"] == 1


def influx_exception(*args):
    pass


influx_exception = mock.create_autospec(influx_exception)


@pytest.mark.parametrize("forecast_window", ["current", "hourly", "daily"])
async def test_influx_cache_raises_exception(lat_lon, forecast_window, mocker):
    mocker.patch(
        "energy_box_control.api.weather.get_last_weather_from_influx", influx_exception
    )
    mocker.patch("energy_box_control.api.weather.get_open_weather", mock_open_weather)
    mocker.patch(
        "energy_box_control.api.weather.WeatherResponse.from_json",
        get_default_weather_response,
    )
    mocker.patch(
        "energy_box_control.api.weather.publish_weather_values_to_mqtt",
        mock_publish_weather_values_to_mqtt,
    )

    response = await app.test_client().get(
        f"/weather/{forecast_window}{lat_lon}", headers=HEADERS
    )

    influx_exception.assert_called()  # type: ignore
    mock_open_weather.assert_called()  # type: ignore
    mock_publish_weather_values_to_mqtt.assert_called()  # type: ignore

    assert (await response.json)["value"] == 1
