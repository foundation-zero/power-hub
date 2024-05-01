from http import HTTPStatus
import json
import os
from dotenv import load_dotenv
import pytest
import requests
from tests.test_api_integration import check_api_is_up, check_simulation_entries

BASE_URL = "http://0.0.0.0:5001"


dotenv_path = os.path.normpath(os.path.join(os.path.realpath(__file__), "../", ".env"))
load_dotenv(dotenv_path)


@pytest.fixture()
def headers():
    return {"Authorization": f"Bearer {os.environ['API_TOKEN']}"}


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
