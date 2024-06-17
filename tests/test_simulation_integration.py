from http import HTTPStatus
import json
import os
import aiohttp
import pytest
import requests
from tests.test_api_integration import check_api_is_up, check_simulation_entries
from energy_box_control.config import CONFIG


BASE_URL = "http://0.0.0.0:5001"


@pytest.fixture()
def headers():
    return {"Authorization": f"Bearer {CONFIG.api_token}"}


@pytest.fixture(scope="session", autouse=True)
async def setup():
    await check_api_is_up()
    await check_simulation_entries()
    yield


@pytest.mark.integration
def test_hello_world():
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == HTTPStatus.OK
    assert response.text == "Hello World!"


@pytest.mark.integration
def test_thermal_circuit(headers):
    response = requests.get(
        f"{BASE_URL}/power_hub/appliance_sensors/heat_pipes/power/last_values",
        headers=headers,
    )
    assert response.status_code == HTTPStatus.OK
    assert len(json.loads(response.text)) > 0


@pytest.mark.integration
def test_water_circuit(headers):
    response = requests.get(
        f"{BASE_URL}/power_hub/appliance_sensors/fresh_water_tank/fill/last_values",
        headers=headers,
    )
    assert response.status_code == HTTPStatus.OK
    assert len(json.loads(response.text)) > 0


async def assert_get_url(url: str, headers: dict[str, str]):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            assert response.status == HTTPStatus.OK
            return json.loads(await response.text())


@pytest.mark.integration
async def test_app_endpoints(headers):
    multiple_value_endpoints = [
        "/power_hub/appliance_sensors/fresh_water_tank/fill/last_values",
        "/power_hub/electric/power/production/over/time?interval=h",
        "/power_hub/electric/power/consumption/over/time?interval=h",
    ]
    single_value_endpoints = [
        "/power_hub/appliance_sensors/pv_panel/power/mean",
        "/power_hub/electric/power/consumption/mean",
        "/power_hub/appliance_sensors/heat_pipes/power/mean",
        "/power_hub/appliance_sensors/chiller/chill_power/mean",
        "/power_hub/appliance_sensors/yazaki/chill_power/mean",
        "/power_hub/appliance_sensors/cold_reservoir/fill_power/mean",
        "/power_hub/appliance_sensors/water_maker/out_flow/mean",
        "/power_hub/appliance_sensors/water_treatment/out_flow/mean",
        "/power_hub/appliance_sensors/fresh_water_tank/water_demand/mean",
        "/power_hub/appliance_sensors/heat_pipes/output_temperature/mean",
        "/power_hub/appliance_sensors/heat_pipes/input_temperature/mean",
        "/power_hub/appliance_sensors/pcm/net_charge/mean",
        "/power_hub/appliance_sensors/pcm/charge_power/mean",
        "/power_hub/appliance_sensors/pcm/discharge_power/mean",
        "/power_hub/appliance_sensors/pcm/temperature/mean",
        "/power_hub/appliance_sensors/yazaki/chilled_output_temperature/mean",
    ]

    for endpoint in multiple_value_endpoints:
        response = await assert_get_url(f"{BASE_URL}{endpoint}", headers)
        assert len(response) > 0

    for endpoint in single_value_endpoints:
        response = await assert_get_url(f"{BASE_URL}{endpoint}", headers)
        assert type(response) == float or int


@pytest.mark.skip
async def test_remaining_endpoints(headers):
    endpoints = [
        "/power_hub/appliance_sensors/compound/overall_temperature/mean",
        "/power_hub/weather_station/pyranometer/irradiance/mean",
    ]

    for endpoint in endpoints:
        response = await assert_get_url(f"{BASE_URL}{endpoint}", headers)
        assert len(response) > 0
