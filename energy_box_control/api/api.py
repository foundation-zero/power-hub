import os
from quart import Quart, request, make_response, Response
from dataclasses import dataclass
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from quart_schema import QuartSchema, validate_response, validate_querystring  # type: ignore
from dotenv import load_dotenv
from energy_box_control.power_hub import PowerHub
from energy_box_control.appliances.base import (
    Appliance,
    ConnectionState,
    Port,
    ApplianceState,
)
from typing import Any, Callable, get_args, get_origin, TypedDict, Literal
from types import get_original_bases
from dataclasses import fields
import fluxy  # type: ignore
from datetime import datetime, timezone, timedelta
from functools import wraps
from http import HTTPStatus
from typing import no_type_check
from pandas import DataFrame as df  # type: ignore

dotenv_path = os.path.normpath(
    os.path.join(os.path.realpath(__file__), "../../../", "simulation.env")
)
load_dotenv(dotenv_path)

TOKEN = os.environ["API_TOKEN"]
DEFAULT_MINUTES_BACK = 60
DEFAULT_POWER_INTERVAL_SECONDS = 10
MAX_POWER_SAMPLES = 2000

app = Quart(__name__)
QuartSchema(
    app,
    security=[{"power_hub_api": []}],
    security_schemes={
        "power_hub_api": {"type": "apiKey", "name": "Authorization", "in_": "header"}
    },
    conversion_preference="pydantic",
)


ConnectionFieldName = str
ApplianceFieldName = str
ConnectionName = str
ApplianceName = str
ApplianceFieldValue = str
ConnectionFieldValue = str
ApplianceTypeName = str
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


@dataclass
class ValuesQuery:
    minutes_back: int = DEFAULT_MINUTES_BACK


@dataclass
class ComputedValuesQuery(ValuesQuery):
    interval_seconds: int = DEFAULT_POWER_INTERVAL_SECONDS


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


async def execute_influx_query(client: InfluxDBClientAsync, query: fluxy.Query) -> df:
    return await client.query_api().query_data_frame(query.to_flux())  # type: ignore


def get_original_bases_element(
    base: type[Appliance[Any, Any, Any] | Port],
) -> type[Appliance[Any, Any, Any] | Port]:
    original_bases, *_ = get_original_bases(base)
    return original_bases


def get_port_types_by_appliance_type(
    appliance_type: type[Appliance[Any, Any, Any]],
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
    appliance_type: type[Appliance[Any, Any, Any]],
) -> dict[property, Connection]:
    return {
        port.value: {
            "fields": [field.name for field in fields(ConnectionState)],
            "type": port.__class__.__name__,
        }
        for port in get_port_types_by_appliance_type(appliance_type)
    }


def get_appliance_state_class_from_appliance_type(
    appliance_type: type[Appliance[Any, Any, Any]],
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


@no_type_check
def token_required(f):
    @wraps(f)
    @no_type_check
    async def decorator(*args, **kwargs):
        if (
            "Authorization" not in request.headers
            or request.headers["Authorization"] != f"Bearer {TOKEN}"
        ):
            return await make_response(
                "A valid token is missing!", HTTPStatus.UNAUTHORIZED
            )
        return await f(*args, **kwargs)

    return decorator


@no_type_check
def serialize_dataframe(columns: list[str]):
    @no_type_check
    def _serialize_dataframe[T: type](fn: T) -> Callable[[T], T]:

        @wraps(fn)
        @no_type_check
        async def decorator(
            *args: list[Any], **kwargs: dict[str, Any]
        ) -> list[Any] | Response:
            response: df = await fn(*args, **kwargs)
            if not isinstance(response, df):
                raise Exception("serialize_dataframe requires a dataframe")
            if response.empty:
                return []
            return Response(
                response.loc[:, columns].to_json(orient="records"),
                mimetype="application/json",
            )

        return decorator

    return _serialize_dataframe


@app.while_serving
async def influx_client():
    url = os.environ["DOCKER_INFLUXDB_URL"]
    token = os.environ["DOCKER_INFLUXDB_INIT_ADMIN_TOKEN"]
    org = os.environ["DOCKER_INFLUXDB_INIT_ORG"]
    try:
        async with InfluxDBClientAsync(url, token, org=org) as client:
            app.influx = client  # type: ignore
            yield
    except Exception as e:
        print(e)


@app.route("/")
async def hello_world() -> str:
    return "Hello World!"


@app.route("/appliances")  # type: ignore
@validate_response(ReturnedAppliances)  # type: ignore
@token_required
async def get_all_appliance_names() -> dict[
    Literal["appliances"],
    dict[
        ApplianceName,
        dict[
            Literal["fields", "connections", "type"],
            list[ApplianceFieldName] | dict[property, Connection] | Any,
        ],
    ],
]:

    power_hub = PowerHub.power_hub()

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
            for appliance_field in fields(power_hub)
        }
    }


@app.route("/appliances/<appliance_name>/<field_name>/last_values")
@token_required
@validate_querystring(ValuesQuery)  # type: ignore
@serialize_dataframe(["time", "value"])
async def get_last_values_for_appliances(
    appliance_name: str, field_name: str, query_args: ValuesQuery
) -> list[list[ApplianceFieldValue]]:
    return (
        await execute_influx_query(
            app.influx,  # type: ignore
            build_get_values_query(
                query_args.minutes_back,
                appliance_name,
                None,
                field_name,
            ),
        )
    ).rename(columns={"_value": "value", "_time": "time"})


@app.route(
    "/appliances/<appliance_name>/connections/<connection_name>/<field_name>/last_values"
)
@token_required
@serialize_dataframe(["time", "value"])
@validate_querystring(ValuesQuery)  # type: ignore
async def get_last_values_for_connections(
    appliance_name: str, connection_name: str, field_name: str, query_args: ValuesQuery
) -> list[list[ConnectionFieldValue]]:
    return (
        await execute_influx_query(
            app.influx,  # type: ignore
            build_get_values_query(
                query_args.minutes_back,
                appliance_name,
                connection_name,
                field_name,
            ),
        )
    ).rename(columns={"_time": "time", "_value": "value"})


def create_fluxy_for_power_over_time(
    minutes_back: int, interval_seconds: int
) -> fluxy.Query:
    in_temperature_topic = "power_hub/connections/heat_pipes/in/temperature"
    out_temperature_topic = "power_hub/connections/heat_pipes/out/temperature"
    flow_topic = "power_hub/connections/heat_pipes/in/flow"

    return fluxy.pipe(
        fluxy.from_bucket(os.environ["DOCKER_INFLUXDB_INIT_BUCKET"]),
        fluxy.range(*build_query_range(minutes_back)),
        fluxy.filter(lambda r: r._measurement == "mqtt_consumer"),
        fluxy.filter(lambda r: r._field == "value"),
        fluxy.filter(
            lambda r: (r.topic == in_temperature_topic)
            | (r.topic == out_temperature_topic)
            | (r.topic == flow_topic)
        ),
        fluxy.aggregate_window(
            every=timedelta(seconds=interval_seconds),
            fn=fluxy.WindowOperation.MEAN,
            create_empty=False,
        ),
        fluxy.pivot(row_key=["_time"], column_key=["topic"], value_column="_value"),
        fluxy.keep(
            [
                "_time",
                in_temperature_topic,
                out_temperature_topic,
                flow_topic,
            ]
        ),
        fluxy.map(
            f'(r) => ({{ r with power: (r["{flow_topic}"] * {PowerHub.power_hub().heat_pipes.specific_heat_medium}) * (r["{out_temperature_topic}"] - r["{in_temperature_topic}"]) }})'
        ),
        fluxy.keep(["_time", "power"]),
    )


@app.route("/appliances/heat_pipes/power/last_values")
@token_required
@serialize_dataframe(["time", "value"])
@validate_querystring(ComputedValuesQuery)  # type: ignore
async def get_heat_pipes_power_over_time(
    query_args: ComputedValuesQuery,
) -> str | tuple[str, Literal[HTTPStatus.UNPROCESSABLE_ENTITY]]:
    if (
        (query_args.minutes_back * 60) / query_args.interval_seconds
    ) > MAX_POWER_SAMPLES:
        return (
            f"Number of samples will exceeded {MAX_POWER_SAMPLES}, please choose a bigger interval or less minutes back.",
            HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    return (
        await execute_influx_query(
            app.influx,  # type: ignore
            query=create_fluxy_for_power_over_time(
                query_args.minutes_back,
                query_args.interval_seconds,
            ),
        )
    ).rename(columns={"power": "value", "_time": "time"})


@app.route("/appliances/heat_pipes/power/total")
@token_required
@validate_querystring(ValuesQuery)  # type: ignore
async def get_heat_pipes_total_power_over_time(
    query_args: ComputedValuesQuery,
) -> dict[str, float]:
    query_result = await execute_influx_query(
        app.influx,  # type: ignore
        query=fluxy.pipe(
            create_fluxy_for_power_over_time(
                query_args.minutes_back,
                1,
            ),
            fluxy.sum("power"),
        ),
    )
    return Response(query_result.iloc[0]["power"].astype(str) if len(query_result) > 0 else "0.0", mimetype="application/json")  # type: ignore


def run() -> None:
    app.run(host="0.0.0.0", port=5001)


if __name__ == "__main__":
    run()
