# type: ignore
import os
from quart import Quart, request, make_response
from dataclasses import dataclass
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from quart_schema import QuartSchema, validate_response
from dotenv import load_dotenv
from energy_box_control.power_hub import PowerHub
from energy_box_control.appliances.base import (
    Appliance,
    ConnectionState,
    Port,
    ApplianceState,
)
from typing import get_args, get_origin, TypedDict, Literal
from types import get_original_bases
from dataclasses import fields
import fluxy
from datetime import datetime, timezone, timedelta
from functools import wraps

dotenv_path = os.path.normpath(
    os.path.join(os.path.realpath(__file__), "../../../", "simulation.env")
)
load_dotenv(dotenv_path)

TOKEN = os.environ["API_TOKEN"]
DEFAULT_MINUTES_BACK = 60

app = Quart(__name__)
QuartSchema(app, conversion_preference="pydantic")

ConnectionName = str
ConnectionFieldName = str
ApplianceFieldName = str
ConnectionName = str
ApplianceName = str
ApplianceFieldValue = str
ConnectionFieldValue = str
ApplianceTypeName = str
PortTypeName = str
ConnectionTypeName = str


@dataclass
class Connection(TypedDict):
    fields: list[ConnectionFieldName]
    type: ConnectionTypeName


@dataclass
class ReturnedAppliance:
    fields: list[ApplianceFieldName]
    connections: dict[ConnectionName, Connection]
    type: ApplianceTypeName


@dataclass
class ReturnedAppliances:
    appliances: dict[ApplianceName, ReturnedAppliance]


def build_query_range(minutes_back: int) -> tuple[datetime, datetime]:
    return (
        datetime.now(timezone.utc) - timedelta(minutes=minutes_back),
        datetime.now(timezone.utc),
    )


def build_get_values_query(
    minutes_back: int, appliance_name: str, connection_name: str | None, field_name: str
) -> fluxy.Query:
    if connection_name is None:
        topic = f"power_hub/appliances/{appliance_name}/{field_name}"
    else:
        topic = f"power_hub/connections/{appliance_name}/{connection_name}/{field_name}"

    return fluxy.pipe(
        fluxy.from_bucket(os.environ["DOCKER_INFLUXDB_INIT_BUCKET"]),
        fluxy.range(*build_query_range(minutes_back)),
        fluxy.filter(lambda r: r._measurement == "mqtt_consumer"),
        fluxy.filter(lambda r: r._field == "value"),
        fluxy.filter(lambda r: r.topic == topic),
        fluxy.keep(["_value", "_time", "topic"]),
    )


async def execute_influx_query(query: fluxy.Query) -> list[list[str]]:
    url = os.environ["DOCKER_INFLUXDB_URL"]
    token = os.environ["DOCKER_INFLUXDB_INIT_ADMIN_TOKEN"]
    org = os.environ["DOCKER_INFLUXDB_INIT_ORG"]
    async with InfluxDBClientAsync(url, token, org=org) as client:
        df = await client.query_api().query_data_frame(query.to_flux())
    return df.to_csv()


def get_original_bases_element(
    base: type[Appliance, Port],
) -> type[Appliance, Port]:
    original_bases, *_ = get_original_bases(base)
    return original_bases


def get_port_types_by_appliance_type(
    appliance_type: type[Appliance],
) -> list[type[Port]]:
    return [
        port
        for port in next(
            base
            for base in get_args(get_original_bases_element(appliance_type))
            if get_original_bases_element(base) == Port
        )
    ]


def get_connections_dict_by_appliance_type(
    appliance_type: type[Appliance],
) -> dict[ConnectionName, Connection]:
    return {
        port.value: {
            "fields": [field.name for field in fields(ConnectionState)],
            "type": port.__class__.__name__,
        }
        for port in get_port_types_by_appliance_type(appliance_type)
    }


def get_appliance_state_class_from_appliance_type(
    appliance_type: type[Appliance],
) -> type[ApplianceState]:
    gen_args = get_args(
        next(
            base
            for base in get_original_bases(appliance_type)
            if get_origin(base) == Appliance
        )
    )
    state_type, *_ = gen_args
    return state_type


def token_required(f):
    @wraps(f)
    async def decorator(*args, **kwargs):
        if (
            "Authorization" not in request.headers
            or request.headers["Authorization"] != f"Bearer {TOKEN}"
        ):
            return await make_response("A valid token is missing!", 401)
        return await f(*args, **kwargs)

    return decorator


@app.route("/")
async def hello_world() -> str:
    return "Hello World!"


@app.route("/appliances")
@validate_response(ReturnedAppliances)
@token_required
async def get_all_appliance_names() -> dict[
    Literal["appliances"],
    ReturnedAppliances,
]:

    example_power_hub = PowerHub.example_power_hub()

    return {
        "appliances": {
            appliance_field.name: {
                "fields": [
                    field.name
                    for field in fields(
                        get_appliance_state_class_from_appliance_type(
                            appliance_field.type
                        )
                    )
                ],
                "connections": get_connections_dict_by_appliance_type(
                    appliance_field.type
                ),
                "type": appliance_field.type.__name__,
            }
            for appliance_field in fields(example_power_hub)
        }
    }


@app.route("/appliances/<appliance_name>/<field_name>/last_values")
@token_required
async def get_last_values_for_appliances(
    appliance_name: str, field_name: str
) -> list[list[ApplianceFieldValue]]:
    return await execute_influx_query(
        build_get_values_query(
            request.args.get("minutes_back", type=int, default=DEFAULT_MINUTES_BACK),
            appliance_name,
            None,
            field_name,
        )
    )


@app.route(
    "/appliances/<appliance_name>/connections/<connection_name>/<field_name>/last_values"
)
@token_required
async def get_last_values_for_connections(
    appliance_name: str, connection_name: str, field_name: str
) -> list[list[ConnectionFieldValue]]:
    return await execute_influx_query(
        build_get_values_query(
            request.args.get("minutes_back", type=int, default=DEFAULT_MINUTES_BACK),
            appliance_name,
            connection_name,
            field_name,
        )
    )


def run() -> None:
    app.run(host="0.0.0.0", port=5001)


if __name__ == "__main__":
    run()
