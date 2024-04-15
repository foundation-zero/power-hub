import json
import multiprocessing
import os
import time
import pytest
import requests
from energy_box_control.simulation import run as run_simulation
from energy_box_control.api.api import run as run_api
from dotenv import load_dotenv
from http import HTTPStatus


BASE_URL = "http://0.0.0.0:5001"

dotenv_path = os.path.normpath(
    os.path.join(os.path.realpath(__file__), "../../../", "simulation.env")
)
load_dotenv(dotenv_path)


@pytest.fixture(scope="session", autouse=True)
def _start_api():
    api_process = multiprocessing.Process(target=run_api)
    api_process.start()
    time.sleep(
        3
    )  # sleeping for 3 seconds is enough to allow the API to start before making calls.
    yield
    api_process.terminate()
    api_process.join()


@pytest.fixture(scope="session", autouse=True)
def _run_simulation():
    run_simulation(5)
    time.sleep(
        3
    )  # sleeping here to give MQTT and Telegraf some time to put the results into InfluxDB


@pytest.fixture()
def headers():
    return {"Authorization": f"Bearer {os.environ['API_TOKEN']}"}


@pytest.mark.integration
def test_hello_world():
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == HTTPStatus.OK
    assert response.text == "Hello World!"


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


@pytest.mark.integration
def test_get_weather(headers):
    response = requests.get(
        f"{BASE_URL}/weather/current?lat=41.3874&lon=2.1686", headers=headers
    )
    assert response.status_code == HTTPStatus.OK
    assert set(["country", "temp", "location_name"]).issubset(
        json.loads(response.text).keys()
    )
