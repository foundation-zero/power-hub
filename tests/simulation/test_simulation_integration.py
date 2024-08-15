from http import HTTPStatus
import json
import aiohttp
import pytest
import requests
from tests.api.test_api_integration import check_api_is_up, check_simulation_entries
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


@pytest.mark.parametrize(
    "url",
    [
        "/power_hub/electric/power/production/mean",
        "/power_hub/electric/power/consumption/mean",
        "/power_hub/appliance_sensors/heat_pipes/power/mean",
        "/power_hub/appliance_sensors/chiller/chill_power/mean",
        # "/power_hub/appliance_sensors/yazaki/chill_power/mean", yazaki is not activated in test period
        "/power_hub/appliance_sensors/cold_reservoir/cooling_supply/mean",
        "/power_hub/appliance_sensors/water_maker/production_flow/mean",
        "/power_hub/appliance_sensors/water_treatment/out_flow/mean",
        "/power_hub/appliance_sensors/fresh_water_tank/water_demand_flow/mean",
        "/power_hub/appliance_sensors/heat_pipes/output_temperature/mean",
        "/power_hub/appliance_sensors/heat_pipes/input_temperature/mean",
        "/power_hub/appliance_sensors/pcm/net_charge/mean",
        "/power_hub/appliance_sensors/pcm/charge_power/mean",
        "/power_hub/appliance_sensors/pcm/discharge_power/mean",
        "/power_hub/appliance_sensors/pcm/temperature/mean",
        # "/power_hub/appliance_sensors/yazaki/chilled_output_temperature/mean",
        "/power_hub/appliance_sensors/pcm/fill/current",
        "/power_hub/appliance_sensors/office_1_fancoil/ambient_temperature/mean",
        "/power_hub/appliance_sensors/weather/global_irradiance/mean",
        # "/power_hub/appliance_sensors/yazaki/used_power/mean", yazaki is not activated in test period
        "/power_hub/appliance_sensors/rh33_heat_pipes/delta_temperature/mean",
    ],
)
@pytest.mark.integration
async def test_app_endpoints_single_value(headers, url):
    response = await assert_get_url(f"{BASE_URL}{url}", headers)
    assert type(response) == float or int


@pytest.mark.parametrize(
    "url",
    [
        "/power_hub/appliance_sensors/fresh_water_tank/fill/last_values",
        "/power_hub/electric/power/production/over/time?interval=h",
        "/power_hub/electric/power/consumption/over/time?interval=h",
        "/power_hub/electric/power/production/mean/per/hour_of_day",
        "/power_hub/electric/power/consumption/mean/per/hour_of_day",
        "/power_hub/appliance_sensors/electrical/battery_system_soc/mean/per/hour_of_day",
        "/power_hub/appliance_sensors/electrical/battery_system_soc/last_values",
        "/power_hub/appliance_sensors/electrical/battery_system_soc/over/time?interval=h",
    ],
)
@pytest.mark.integration
async def test_app_endpoints_multiple_values(headers, url):
    response = await assert_get_url(f"{BASE_URL}{url}", headers)
    assert len(response) > 0
