import asyncio
import json
import multiprocessing
from typing import Optional
import aiohttp
import pytest
import requests
from energy_box_control.simulation import run as run_simulation
from energy_box_control.api.api import run as run_api
from energy_box_control.api.api import (
    values_query,
    execute_influx_query,
    get_influx_client,
    build_query_range,
    ValuesQuery,
)
from http import HTTPStatus
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from energy_box_control.custom_logging import get_logger
from energy_box_control.config import CONFIG


logger = get_logger(__name__)


BASE_URL = "http://0.0.0.0:5001"


def api_is_up():
    try:
        response = requests.get(f"{BASE_URL}/")
        return response.status_code == HTTPStatus.OK
    except Exception:
        return False


async def influx_has_entries(client: InfluxDBClientAsync):
    try:
        results = await execute_influx_query(
            client,
            values_query(
                lambda r: r._field == f"heat_pipes_power",
                build_query_range(ValuesQuery()),
            ),
        )
        return len(results["_value"]) > 0
    except Exception:
        return False


async def check_simulation_entries():
    logger.debug("Checking for simulation entries")
    async with get_influx_client() as client:
        logger.debug("Influx client created")
        async with asyncio.timeout(20):
            while True:
                if await influx_has_entries(client):
                    logger.debug("Entries found in influx")
                    break
                await asyncio.sleep(0.5)


async def check_api_is_up():
    logger.debug("Checking if api is up")
    async with asyncio.timeout(20):
        while True:
            if api_is_up():
                logger.debug("API is up")
                break
            await asyncio.sleep(0.5)


@pytest.fixture(scope="session", autouse=True)
async def setup():
    api_process = multiprocessing.Process(target=run_api)
    api_process.start()
    try:
        await check_api_is_up()
        logger.debug("Running simulation")
        await run_simulation(5)
        logger.debug("Simulation is done")
        await check_simulation_entries()
        yield
    finally:
        api_process.terminate()
        api_process.join()


async def do_request(url: str, headers: Optional[dict[str, str]] = None) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            assert response.status == HTTPStatus.OK
            return await response.text()


@pytest.mark.integration
async def test_hello_world():
    assert await do_request(f"{BASE_URL}/") == "Hello World!"


@pytest.fixture()
def headers():
    return {"Authorization": f"Bearer {CONFIG.api_token}"}


@pytest.mark.integration
async def test_get_appliances(headers):
    assert "appliances" in json.loads(
        await do_request(f"{BASE_URL}/power_hub/appliances", headers=headers)
    )


@pytest.mark.integration
async def test_get_last_values(headers):
    assert (
        len(
            json.loads(
                await do_request(
                    f"{BASE_URL}/power_hub/appliance_sensors/heat_pipes/power/last_values",
                    headers=headers,
                )
            )
        )
        > 0
    )


@pytest.mark.integration
async def test_get_total_value(headers):
    assert (
        json.loads(
            await do_request(
                f"{BASE_URL}/power_hub/appliance_sensors/heat_pipes/power/total",
                headers=headers,
            )
        )
        > 0
    )


@pytest.mark.integration
async def test_get_mean_value(headers):
    assert (
        json.loads(
            await do_request(
                f"{BASE_URL}/power_hub/appliance_sensors/heat_pipes/power/mean",
                headers=headers,
            )
        )
        > 0
    )


@pytest.mark.integration
async def test_get_current_pcm_fill(headers):
    assert (
        json.loads(
            await do_request(
                f"{BASE_URL}/power_hub/appliance_sensors/pcm/fill/current",
                headers=headers,
            )
        )
        >= 0
    )


@pytest.mark.integration
async def test_get_values_over_time(headers):
    assert (
        len(
            json.loads(
                await do_request(
                    f"{BASE_URL}/power_hub/appliance_sensors/heat_pipes/power/over/time",
                    headers=headers,
                )
            )
        )
        > 0
    )


@pytest.mark.integration
async def test_get_electric_power_consumption(headers):
    assert len(
        json.loads(
            await do_request(
                f"{BASE_URL}/power_hub/electric/power/consumption/over/time",
                headers=headers,
            )
        )
    )


@pytest.mark.integration
async def test_get_electric_power_consumption_appliances(headers):
    assert (
        len(
            json.loads(
                await do_request(
                    f"{BASE_URL}/power_hub/electric/power/consumption/over/time?appliance=pcm_to_yazaki_pump&appliance=chilled_loop_pump",
                    headers=headers,
                )
            )
        )
        > 0
    )


@pytest.mark.integration
async def test_get_electric_power_consumption_mean(headers):
    assert (
        json.loads(
            await do_request(
                f"{BASE_URL}/power_hub/electric/power/consumption/mean", headers=headers
            )
        )
        > 0
    )


@pytest.mark.integration
async def test_get_electric_power_consumption_mean_per_hour(headers):
    assert (
        len(
            json.loads(
                await do_request(
                    f"{BASE_URL}/power_hub/electric/power/consumption/mean/per/hour",
                    headers=headers,
                )
            )
        )
        == 1
    )


@pytest.mark.integration
async def test_get_electric_power_production(headers):
    assert (
        len(
            json.loads(
                await do_request(
                    f"{BASE_URL}/power_hub/electric/power/production/over/time",
                    headers=headers,
                )
            )
        )
        > 1
    )


@pytest.mark.integration
async def test_get_electric_power_production_mean_per_hour(headers):
    assert (
        len(
            json.loads(
                await do_request(
                    f"{BASE_URL}/power_hub/electric/power/production/mean/per/hour",
                    headers=headers,
                )
            )
        )
        == 1
    )


@pytest.fixture
def lat_lon():
    return "?lat=41.3874&lon=2.1686"


@pytest.mark.integration
async def test_get_current_weather(headers, lat_lon):
    assert {"temp", "feels_like", "pressure"}.issubset(
        json.loads(
            await do_request(f"{BASE_URL}/weather/current{lat_lon}", headers=headers)
        ).keys()
    )


@pytest.mark.integration
@pytest.mark.parametrize("forecast_window", ["hourly", "daily"])
async def test_get_hourly_weather(headers, lat_lon, forecast_window):
    weather = json.loads(
        await do_request(
            f"{BASE_URL}/weather/{forecast_window}{lat_lon}", headers=headers
        )
    )
    assert type(weather) == list
    assert set(["temp", "feels_like", "pressure"]).issubset(next(iter(weather)))
