from asyncio import Future
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
import pytest
from quart import Response
from energy_box_control.api.api import (
    app,
)
import json
from datetime import datetime, timezone, timedelta
import pandas as pd
import json
import unittest.mock as mock
from energy_box_control.api.weather import *
from energy_box_control.config import CONFIG


HEADERS = {"Authorization": f"Bearer {CONFIG.api_token}"}


@pytest.fixture
def appliance_name():
    return "chiller_switch_valve"


@pytest.fixture
def sensor_field_name():
    return "position"


@pytest.fixture()
def field_name(appliance_name, sensor_field_name):
    return f"{appliance_name}_{sensor_field_name}"


@pytest.fixture
def start():
    return datetime.now() - timedelta(hours=1)


@pytest.fixture
def stop():
    return datetime.now()


@pytest.fixture
async def mock_influx_appliance(mocker, field_name):
    mocker.patch.object(InfluxDBClientAsync, "query_api", return_value=mock.Mock())
    app.influx = InfluxDBClientAsync("invalid_url")  # type: ignore
    fut = Future()
    fut.set_result(pd.DataFrame({"_time": [0, 0, 0], field_name: [0, 0, 0]}))
    app.influx.query_api().query_data_frame.return_value = fut  # type: ignore
    yield


@pytest.fixture
async def mock_influx_field(mocker):
    mocker.patch.object(InfluxDBClientAsync, "query_api", return_value=mock.Mock())
    app.influx = InfluxDBClientAsync("invalid_url")  # type: ignore
    fut = Future()
    fut.set_result(pd.DataFrame({"_time": [0, 0, 0], "field": [0, 0, 0]}))
    app.influx.query_api().query_data_frame.return_value = fut  # type: ignore
    yield


@pytest.fixture
async def mock_influx_hour_of_day(mocker):
    mocker.patch.object(InfluxDBClientAsync, "query_api", return_value=mock.Mock())
    app.influx = InfluxDBClientAsync("invalid_url")  # type: ignore
    fut = Future()
    fut.set_result(pd.DataFrame({"hour": [0, 0, 0], "value": [0, 0, 0]}))
    app.influx.query_api().query_data_frame.return_value = fut  # type: ignore
    yield


async def test_hello_world():
    response = await app.test_client().get("/")
    assert response.status_code == 200
    assert await response.get_data() == b"Hello World!"


async def test_get_all_appliance_names():
    response = await app.test_client().get("/power_hub/appliances", headers=HEADERS)
    response_data = json.loads((await response.get_data()).decode("utf-8"))
    assert response.status_code == 200
    assert "appliances" in response_data
    assert len(response_data["appliances"]) > 0


async def assert_row_response(response: Response, query: str):
    assert response.content_type == "application/json"
    result = json.loads(await response.get_data())
    assert type(result) == list
    assert len(result) == 3
    app.influx.query_api().query_data_frame.assert_called_with(query)  # type: ignore


async def assert_single_value_response(response: Response, query: str):
    assert response.content_type == "application/json"
    result = json.loads(await response.get_data())
    assert type(result) == float or int
    app.influx.query_api().query_data_frame.assert_called_with(query)  # type: ignore


async def test_get_last_values_for_appliance(
    mock_influx_appliance, appliance_name, sensor_field_name, field_name, start, stop
):
    query = f"""from(bucket: "simulation_data")
|> range(start: {start.replace(tzinfo=timezone.utc).isoformat()}, stop: {stop.replace(tzinfo=timezone.utc).isoformat()})
|> filter(fn: (r) => r["_field"] == "{field_name}")
|> filter(fn: (r) => r["topic"] == "power_hub/enriched_sensor_values")
|> keep(columns: ["_value", "_time", "_field"])
|> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")"""

    await assert_row_response(
        await app.test_client().get(
            f"/power_hub/appliance_sensors/{appliance_name}/{sensor_field_name}/last_values?between={start.isoformat()},{stop.isoformat()}",
            headers=HEADERS,
        ),
        query,
    )


async def test_get_mean_for_appliance(
    mock_influx_appliance, appliance_name, sensor_field_name, field_name, start, stop
):
    query = f"""from(bucket: "simulation_data")
|> range(start: {start.replace(tzinfo=timezone.utc).isoformat()}, stop: {stop.replace(tzinfo=timezone.utc).isoformat()})
|> filter(fn: (r) => r["_field"] == "{field_name}")
|> filter(fn: (r) => r["topic"] == "power_hub/enriched_sensor_values")
|> keep(columns: ["_value", "_time", "_field"])
|> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
|> mean(column: "{field_name}")"""

    await assert_single_value_response(
        await app.test_client().get(
            f"/power_hub/appliance_sensors/{appliance_name}/{sensor_field_name}/mean?between={start.isoformat()},{stop.isoformat()}",
            headers=HEADERS,
        ),
        query,
    )


async def test_get_total_for_appliance(
    mock_influx_appliance, appliance_name, sensor_field_name, field_name, start, stop
):
    query = f"""from(bucket: "simulation_data")
|> range(start: {start.replace(tzinfo=timezone.utc).isoformat()}, stop: {stop.replace(tzinfo=timezone.utc).isoformat()})
|> filter(fn: (r) => r["_field"] == "{field_name}")
|> filter(fn: (r) => r["topic"] == "power_hub/enriched_sensor_values")
|> keep(columns: ["_value", "_time", "_field"])
|> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
|> sum(column: "{field_name}")"""

    await assert_single_value_response(
        await app.test_client().get(
            f"/power_hub/appliance_sensors/{appliance_name}/{sensor_field_name}/total?between={start.isoformat()},{stop.isoformat()}",
            headers=HEADERS,
        ),
        query,
    )


async def test_get_sensor_value_over_time(
    mock_influx_field, appliance_name, sensor_field_name, field_name, start, stop
):
    query = f"""from(bucket: "simulation_data")
|> range(start: {start.replace(tzinfo=timezone.utc).isoformat()}, stop: {stop.replace(tzinfo=timezone.utc).isoformat()})
|> filter(fn: (r) => r["_field"] == "{field_name}")
|> filter(fn: (r) => r["topic"] == "power_hub/enriched_sensor_values")
|> keep(columns: ["_value", "_time"])
|> aggregateWindow(every: 1s, fn: mean, createEmpty: false)
|> map(fn: (r) => ({{_time: r._time, _value: r._value, _field: "field"}}))
|> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")"""

    await assert_single_value_response(
        await app.test_client().get(
            f"/power_hub/appliance_sensors/{appliance_name}/{sensor_field_name}/over/time?between={start.isoformat()},{stop.isoformat()}",
            headers=HEADERS,
        ),
        query,
    )


async def test_get_mean_sensor_value_hourly_over_time(
    mock_influx_hour_of_day, appliance_name, field_name
):
    start = datetime.now() - timedelta(days=7)
    stop = datetime.now()

    query = f"""import "date"
 from(bucket: "simulation_data")
|> range(start: {start.replace(tzinfo=timezone.utc).isoformat()}, stop: {stop.replace(tzinfo=timezone.utc).isoformat()})
|> filter(fn: (r) => r["_field"] == "{appliance_name}_{field_name}")
|> filter(fn: (r) => r["topic"] == "power_hub/enriched_sensor_values")
|> keep(columns: ["_value", "_time"])
|> aggregateWindow(every: 3600s, fn: mean, createEmpty: true)
|> map(fn: (r) => ({{_time: r._time, _value: r._value, hour: date.hour(t: r._time)}}))
|> group(columns: ["hour"])
|> mean(column: "_value")
|> group()
|> sort(columns: ["hour"], desc: false)
|> map(fn: (r) => ({{_value: r._value, hour: r.hour, _field: "field"}}))
|> pivot(rowKey: ["hour"], columnKey: ["_field"], valueColumn: "_value")"""

    endpoint = f"/power_hub/appliance_sensors/{appliance_name}/{field_name}/mean/per/hour_of_day?between={start.isoformat()},{stop.isoformat()}"
    await assert_row_response(
        await app.test_client().get(
            endpoint,
            headers=HEADERS,
        ),
        query,
    )


async def test_get_electrical_power_consumption(mock_influx_field, start, stop):

    query = f"""from(bucket: "simulation_data")
|> range(start: {start.replace(tzinfo=timezone.utc).isoformat()}, stop: {stop.replace(tzinfo=timezone.utc).isoformat()})
|> filter(fn: (r) => r["_field"] == "heat_pipes_power_hub_pump_rated_power_consumption" or r["_field"] == "heat_pipes_supply_box_pump_rated_power_consumption" or r["_field"] == "pcm_to_yazaki_pump_rated_power_consumption" or r["_field"] == "chilled_loop_pump_rated_power_consumption" or r["_field"] == "waste_pump_rated_power_consumption" or r["_field"] == "hot_water_pump_rated_power_consumption" or r["_field"] == "outboard_pump_rated_power_consumption" or r["_field"] == "cooling_demand_pump_rated_power_consumption")
|> filter(fn: (r) => r["topic"] == "power_hub/enriched_sensor_values")
|> keep(columns: ["_value", "_time"])
|> aggregateWindow(every: 1s, fn: mean, createEmpty: false)
|> map(fn: (r) => ({{_time: r._time, _value: r._value, _field: "field"}}))
|> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")"""

    await assert_row_response(
        await app.test_client().get(
            f"/power_hub/electric/power/consumption/over/time?between={start.isoformat()},{stop.isoformat()}",
            headers=HEADERS,
        ),
        query,
    )


async def test_get_electrical_power_consumption_hourly_over_time(
    mock_influx_hour_of_day,
):
    start = datetime.now() - timedelta(days=7)
    stop = datetime.now()

    query = f"""import "date"
 from(bucket: "simulation_data")
|> range(start: {start.replace(tzinfo=timezone.utc).isoformat()}, stop: {stop.replace(tzinfo=timezone.utc).isoformat()})
|> filter(fn: (r) => r["_field"] == "heat_pipes_power_hub_pump_rated_power_consumption" or r["_field"] == "heat_pipes_supply_box_pump_rated_power_consumption" or r["_field"] == "pcm_to_yazaki_pump_rated_power_consumption" or r["_field"] == "chilled_loop_pump_rated_power_consumption" or r["_field"] == "waste_pump_rated_power_consumption" or r["_field"] == "hot_water_pump_rated_power_consumption" or r["_field"] == "outboard_pump_rated_power_consumption" or r["_field"] == "cooling_demand_pump_rated_power_consumption")
|> filter(fn: (r) => r["topic"] == "power_hub/enriched_sensor_values")
|> keep(columns: ["_value", "_time"])
|> aggregateWindow(every: 3600s, fn: mean, createEmpty: true)
|> map(fn: (r) => ({{_time: r._time, _value: r._value, hour: date.hour(t: r._time)}}))
|> group(columns: ["hour"])
|> mean(column: "_value")
|> group()
|> sort(columns: ["hour"], desc: false)
|> map(fn: (r) => ({{_value: r._value, hour: r.hour, _field: "field"}}))
|> pivot(rowKey: ["hour"], columnKey: ["_field"], valueColumn: "_value")"""

    endpoint = f"/power_hub/electric/power/consumption/mean/per/hour_of_day?between={start.isoformat()},{stop.isoformat()}"
    await assert_row_response(
        await app.test_client().get(
            endpoint,
            headers=HEADERS,
        ),
        query,
    )


async def test_get_mean_electrical_power_consumption(mock_influx_field, start, stop):

    query = f"""from(bucket: "simulation_data")
|> range(start: {start.replace(tzinfo=timezone.utc).isoformat()}, stop: {stop.replace(tzinfo=timezone.utc).isoformat()})
|> filter(fn: (r) => r["_field"] == "heat_pipes_power_hub_pump_rated_power_consumption" or r["_field"] == "heat_pipes_supply_box_pump_rated_power_consumption" or r["_field"] == "pcm_to_yazaki_pump_rated_power_consumption" or r["_field"] == "chilled_loop_pump_rated_power_consumption" or r["_field"] == "waste_pump_rated_power_consumption" or r["_field"] == "hot_water_pump_rated_power_consumption" or r["_field"] == "outboard_pump_rated_power_consumption" or r["_field"] == "cooling_demand_pump_rated_power_consumption")
|> filter(fn: (r) => r["topic"] == "power_hub/enriched_sensor_values")
|> keep(columns: ["_value", "_time"])
|> aggregateWindow(every: 1s, fn: mean, createEmpty: false)
|> map(fn: (r) => ({{_time: r._time, _value: r._value, _field: "field"}}))
|> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
|> mean(column: "field")"""

    await assert_single_value_response(
        await app.test_client().get(
            f"/power_hub/electric/power/consumption/mean?between={start.isoformat()},{stop.isoformat()}",
            headers=HEADERS,
        ),
        query,
    )


async def test_get_electrical_power_production(mock_influx_field, start, stop):
    query = f"""from(bucket: "simulation_data")
|> range(start: {start.replace(tzinfo=timezone.utc).isoformat()}, stop: {stop.replace(tzinfo=timezone.utc).isoformat()})
|> filter(fn: (r) => r["_field"] == "pv_panel_power")
|> filter(fn: (r) => r["topic"] == "power_hub/enriched_sensor_values")
|> keep(columns: ["_value", "_time"])
|> aggregateWindow(every: 1s, fn: mean, createEmpty: false)
|> map(fn: (r) => ({{_time: r._time, _value: r._value, _field: "field"}}))
|> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")"""

    await assert_row_response(
        await app.test_client().get(
            f"/power_hub/electric/power/production/over/time?between={start.isoformat()},{stop.isoformat()}",
            headers=HEADERS,
        ),
        query,
    )


async def test_get_electrical_power_production_hourly_over_time(
    mock_influx_hour_of_day,
):
    start = datetime.now() - timedelta(days=7)
    stop = datetime.now()

    query = f"""import "date"
 from(bucket: "simulation_data")
|> range(start: {start.replace(tzinfo=timezone.utc).isoformat()}, stop: {stop.replace(tzinfo=timezone.utc).isoformat()})
|> filter(fn: (r) => r["_field"] == "pv_panel_power")
|> filter(fn: (r) => r["topic"] == "power_hub/enriched_sensor_values")
|> keep(columns: ["_value", "_time"])
|> aggregateWindow(every: 3600s, fn: mean, createEmpty: true)
|> map(fn: (r) => ({{_time: r._time, _value: r._value, hour: date.hour(t: r._time)}}))
|> group(columns: ["hour"])
|> mean(column: "_value")
|> group()
|> sort(columns: ["hour"], desc: false)
|> map(fn: (r) => ({{_value: r._value, hour: r.hour, _field: "field"}}))
|> pivot(rowKey: ["hour"], columnKey: ["_field"], valueColumn: "_value")"""

    await assert_row_response(
        await app.test_client().get(
            f"/power_hub/electric/power/production/mean/per/hour_of_day?between={start.isoformat()},{stop.isoformat()}",
            headers=HEADERS,
        ),
        query,
    )


async def test_get_electrical_power_production_non_pv_panel(mock_influx_field):
    response = await app.test_client().get(
        f"/power_hub/electric/power/production/over/time?appliances=test",
        headers=HEADERS,
    )

    assert response.status_code == 422
    assert (await response.get_data()).decode(
        "utf-8"
    ) == "Please only provide pv_panel(s)"


INVALID_VALUES_ERROR_MESSAGE = "Invalid value for query param 'between'. 'between' be formatted as 'start,stop', where 'start' & 'stop' follow ISO8601 and 'stop' > 'start'."


async def test_equal_start_stop():

    response = await app.test_client().get(
        f"/power_hub/appliance_sensors/chiller_switch_valve/position/last_values?between=2000-01-01T00:00:00,2000-01-01T00:00:00",
        headers=HEADERS,
    )
    assert response.status_code == 422
    assert (await response.get_data()).decode("utf-8") == INVALID_VALUES_ERROR_MESSAGE


async def test_start_bigger_than_stop():

    response = await app.test_client().get(
        f"/power_hub/appliance_sensors/chiller_switch_valve/position/last_values?between=2000-01-01T00:00:01,2000-01-01T00:00:00",
        headers=HEADERS,
    )
    assert response.status_code == 422
    assert (await response.get_data()).decode("utf-8") == INVALID_VALUES_ERROR_MESSAGE


async def test_invalid_between():

    response = await app.test_client().get(
        f"/power_hub/appliance_sensors/chiller_switch_valve/position/last_values?between=test",
        headers=HEADERS,
    )
    assert response.status_code == 422
    assert (await response.get_data()).decode("utf-8") == INVALID_VALUES_ERROR_MESSAGE


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
    mocker.patch.object(WeatherClient, "_fetch_weather")
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
