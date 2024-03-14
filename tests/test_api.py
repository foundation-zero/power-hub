import pytest
from energy_box_control.api.api import (
    app,
    build_query_range,
    build_get_values_query,
    get_connections_dict_by_appliance_type,
)
from energy_box_control.power_hub import PowerHub
from energy_box_control.appliances.mix import MixPort
import json
from pytest_mock import mocker
from datetime import datetime, timezone, timedelta
from freezegun import freeze_time
import fluxy
import os
from dotenv import load_dotenv


dotenv_path = os.path.normpath(
    os.path.join(os.path.realpath(__file__), "../../../", "simulation.env")
)
load_dotenv(dotenv_path)


HEADERS = {"Authorization": f"Bearer {os.environ['API_TOKEN']}"}


@pytest.fixture
def influx_mocker(mocker):
    return mocker.patch(
        "energy_box_control.api.api.execute_influx_query", return_value="_,_,_"
    )


@pytest.fixture
def api_client():
    return app.test_client()


@pytest.fixture
def appliance():
    return "chill_mix"


@pytest.fixture
def field():
    return "position"


@pytest.fixture
def minutes_back():
    return 60


@pytest.fixture
@freeze_time("2012-01-01")
def start_datetime(minutes_back) -> datetime:
    return datetime.now(timezone.utc) - timedelta(minutes=int(minutes_back))


@pytest.fixture
@freeze_time("2012-01-01")
def stop_datetime() -> datetime:
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_hello_world(api_client):
    response = await api_client.get("/")
    assert response.status_code == 200
    assert await response.get_data() == b"Hello World!"


@pytest.mark.asyncio
async def test_get_all_appliance_names(api_client):
    response = await api_client.get("/appliances", headers=HEADERS)
    response_data = json.loads((await response.get_data()).decode("utf-8"))
    assert response.status_code == 200
    assert "appliances" in response_data
    assert len(response_data["appliances"]) > 0


@pytest.mark.asyncio
async def test_get_last_values_for_appliance(
    influx_mocker, api_client, appliance, field
):
    response = await api_client.get(
        f"/appliances/{appliance}/{field}/last_values", headers=HEADERS
    )
    assert await response.get_data() == b"_,_,_"


@pytest.mark.asyncio
async def test_get_last_values_for_appliance_minutes_back(
    influx_mocker, api_client, appliance, field, minutes_back
):
    response = await api_client.get(
        f"/appliances/{appliance}/{field}/last_values?minutes_back={minutes_back}",
        headers=HEADERS,
    )
    assert await response.get_data() == b"_,_,_"


@pytest.mark.asyncio
async def test_get_last_values_for_connection(
    influx_mocker, api_client, appliance, field
):
    response = await api_client.get(
        f"/appliances/{appliance}/connections/{MixPort.A.value}/{field}/last_values",
        headers=HEADERS,
    )
    assert await response.get_data() == b"_,_,_"


@pytest.mark.asyncio
async def test_get_last_values_for_connection_minutes_back(
    influx_mocker, api_client, appliance, field, minutes_back
):
    response = await api_client.get(
        f"/appliances/{appliance}/connections/{field}/{MixPort.A.value}/last_values?minutes_back={minutes_back}",
        headers=HEADERS,
    )
    assert await response.get_data() == b"_,_,_"


@pytest.mark.asyncio
@freeze_time("2012-01-01")
async def test_build_query_range(minutes_back):
    query_range = build_query_range(minutes_back)
    start_datetime, stop_datetime = query_range
    assert type(query_range) == tuple
    assert start_datetime == datetime.now(timezone.utc) - timedelta(
        minutes=minutes_back
    )
    assert stop_datetime == datetime.now(timezone.utc)


@pytest.mark.asyncio
@freeze_time("2012-01-01")
async def test_build_get_appliance_values_query(
    appliance, field, minutes_back, start_datetime, stop_datetime
):
    fluxy_object = build_get_values_query(minutes_back, appliance, None, field)
    assert (
        len(
            [
                operation
                for operation in fluxy_object.operations
                if type(operation) == fluxy.Filter
            ]
        )
        == 3
    )

    assert (
        fluxy.filter(
            lambda query: query.topic == f"power_hub/appliances/{appliance}/{field}"
        )
        in build_get_values_query(minutes_back, appliance, None, field).operations
    )
    assert fluxy_object.range == fluxy.range(start_datetime, stop_datetime)


@pytest.mark.asyncio
@freeze_time("2012-01-01")
async def test_build_get_connection_values_query(
    appliance, field, minutes_back, start_datetime, stop_datetime
):
    connection = MixPort.A.value
    fluxy_object = build_get_values_query(minutes_back, appliance, connection, field)
    assert (
        len(
            [
                operation
                for operation in fluxy_object.operations
                if type(operation) == fluxy.Filter
            ]
        )
        == 3
    )
    assert (
        fluxy.filter(
            lambda query: query.topic
            == f"power_hub/connections/{appliance}/{connection}/{field}"
        )
        in build_get_values_query(minutes_back, appliance, connection, field).operations
    )
    assert fluxy_object.range == fluxy.range(start_datetime, stop_datetime)


@pytest.mark.asyncio
async def test_get_connections_dict_by_appliance_type():
    example_power_hub = PowerHub.example_power_hub()
    example_appliance = example_power_hub.chill_mix
    connections_dict = get_connections_dict_by_appliance_type(type(example_appliance))
    assert MixPort.A.value in connections_dict
    assert len(connections_dict[MixPort.A.value]["fields"]) > 0
