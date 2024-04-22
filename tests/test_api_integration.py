import asyncio
import json
import multiprocessing
import os
import pytest
import requests
from energy_box_control.simulation import run as run_simulation
from energy_box_control.api.api import run as run_api
from energy_box_control.api.api import (
    build_get_values_query,
    execute_influx_query,
    get_influx_client,
)
from dotenv import load_dotenv
from http import HTTPStatus
from unittest import mock


BASE_URL = "http://0.0.0.0:5001"

dotenv_path = os.path.normpath(os.path.join(os.path.realpath(__file__), "../", ".env"))
load_dotenv(dotenv_path)


def api_is_up():
    try:
        response = requests.get(f"{BASE_URL}/")
        return response.status_code == HTTPStatus.OK
    except Exception:
        return False


async def influx_has_entries():
    try:
        results = await execute_influx_query(
            get_influx_client(),
            build_get_values_query(
                5,
                "heat_pipes",
                "power",
            ),
        )
        return len(results["_value"]) > 0
    except Exception:
        return False


async def _check_simulation_entries():
    async with asyncio.timeout(20):
        while True:
            if await influx_has_entries():
                break
            await asyncio.sleep(0.5)


async def _check_api_is_up():
    async with asyncio.timeout(20):
        while True:
            if api_is_up():
                break
            await asyncio.sleep(0.5)


@pytest.fixture(scope="session", autouse=True)
async def setup():
    api_process = multiprocessing.Process(target=run_api)
    api_process.start()
    try:
        await _check_api_is_up()
        run_simulation(5)
        await _check_simulation_entries()
        yield
    finally:
        api_process.terminate()
        api_process.join()


@pytest.mark.integration
def test_hello_world():
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == HTTPStatus.OK
    assert response.text == "Hello World!"


@pytest.fixture()
def headers():
    return {"Authorization": f"Bearer {os.environ['API_TOKEN']}"}


@pytest.mark.integration
def test_get_appliances(headers):
    response = requests.get(f"{BASE_URL}/appliances", headers=headers)
    assert response.status_code == HTTPStatus.OK
    assert "appliances" in json.loads(response.text)


@pytest.mark.integration
def test_get_last_values(headers):
    response = requests.get(
        f"{BASE_URL}/appliance_sensors/heat_pipes/power/last_values", headers=headers
    )
    assert response.status_code == HTTPStatus.OK
    assert len(json.loads(response.text)) > 0


@pytest.mark.integration
def test_get_total_value(headers):
    response = requests.get(
        f"{BASE_URL}/appliance_sensors/heat_pipes/power/total", headers=headers
    )
    assert response.status_code == HTTPStatus.OK
    assert json.loads(response.text) > 0


@pytest.fixture
def lat_lon():
    return "?lat=50&lon=50"


@pytest.mark.integration
def test_get_current_weather(headers, lat_lon):
    response = requests.get(f"{BASE_URL}/weather/current{lat_lon}", headers=headers)
    assert response.status_code == HTTPStatus.OK
    assert set(["temp", "feels_like", "pressure"]).issubset(
        json.loads(response.text).keys()
    )


@pytest.mark.integration
def test_get_hourly_weather(headers, lat_lon):
    response = requests.get(f"{BASE_URL}/weather/hourly{lat_lon}", headers=headers)
    hourly_weather = json.loads(response.text)
    assert response.status_code == HTTPStatus.OK
    assert type(hourly_weather) == list
    assert set(["temp", "feels_like", "pressure"]).issubset(hourly_weather[0])


@pytest.mark.integration
def test_get_daily_weather(headers, lat_lon):
    response = requests.get(f"{BASE_URL}/weather/daily{lat_lon}", headers=headers)
    daily_weather = json.loads(response.text)
    assert response.status_code == HTTPStatus.OK
    assert type(daily_weather) == list
    assert set(["temp", "feels_like", "pressure"]).issubset(daily_weather[0])
