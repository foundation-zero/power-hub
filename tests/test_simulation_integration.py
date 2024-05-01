import asyncio
from http import HTTPStatus
import json
import os
import sys
from dotenv import load_dotenv
import pytest
import requests

from energy_box_control.api.api import (
    build_get_values_query,
    execute_influx_query,
    get_influx_client,
)

from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

BASE_URL = "http://0.0.0.0:5001"


dotenv_path = os.path.normpath(os.path.join(os.path.realpath(__file__), "../", ".env"))
load_dotenv(dotenv_path)


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
    async with get_influx_client() as client:
        async with asyncio.timeout(20):
            while True:
                if await influx_has_entries(client):
                    break
                await asyncio.sleep(0.5)


async def _check_api_is_up():
    async with asyncio.timeout(20):
        while True:
            if api_is_up():
                break
            await asyncio.sleep(0.5)


@pytest.fixture()
def headers():
    return {"Authorization": f"Bearer {os.environ['API_TOKEN']}"}


@pytest.fixture(scope="session", autouse=True)
async def setup():
    await _check_api_is_up()
    await _check_simulation_entries()
    yield


@pytest.mark.integration
def test_hello_world():
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == HTTPStatus.OK
    assert response.text == "Hello World!"


@pytest.mark.integration
def test_thermal_circuit(headers):
    response = requests.get(
        f"{BASE_URL}/appliance_sensors/heat_pipes/power/last_values", headers=headers
    )
    assert response.status_code == HTTPStatus.OK
    assert len(json.loads(response.text)) > 0


@pytest.mark.integration
def test_water_circuit(headers):
    response = requests.get(
        f"{BASE_URL}/appliance_sensors/fresh_water_tank/fill/last_values",
        headers=headers,
    )
    assert response.status_code == HTTPStatus.OK
    assert len(json.loads(response.text)) > 0
