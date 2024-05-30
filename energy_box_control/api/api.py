from pydantic import ValidationError
from quart import Quart, request, make_response, Response
from quart.typing import ResponseTypes
from dataclasses import dataclass, field
from quart_schema import QuartSchema, validate_response, validate_querystring, RequestSchemaValidationError  # type: ignore
from typing import Any, Callable, List, Literal, Optional, Tuple
from dataclasses import fields
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
import fluxy  # type: ignore
from datetime import datetime, timezone, timedelta
from functools import wraps
from http import HTTPStatus
from typing import no_type_check
from pandas import DataFrame as df  # type: ignore
from energy_box_control.power_hub.sensors import PowerHubSensors
from energy_box_control.sensors import sensor_fields
from energy_box_control.api.weather import WeatherClient, DailyWeather, CurrentWeather
from energy_box_control.custom_logging import get_logger

from energy_box_control.config import CONFIG
from quart_cors import cors  # type: ignore

logger = get_logger(__name__)


DEFAULT_MINUTES_BACK = 60
MAX_ROWS = 10000

app = Quart(__name__)
app = cors(app, allow_origin="*")

QuartSchema(
    app,
    security=[{"power_hub_api": []}],
    security_schemes={
        "power_hub_api": {"type": "apiKey", "name": "Authorization", "in_": "header"}
    },
    conversion_preference="pydantic",
)


@app.errorhandler(RequestSchemaValidationError)
async def handle_request_validation_error(
    error: RequestSchemaValidationError,
) -> Response:
    if isinstance(error.validation_error, ValidationError):
        return Response(error.validation_error.json(), HTTPStatus.UNPROCESSABLE_ENTITY)
    return Response("Internal error", HTTPStatus.INTERNAL_SERVER_ERROR)


ApplianceName = str
ApplianceSensorTypeName = str
SensorName = str
ApplianceSensorFieldValue = float


def timedelta_from_string(interval: str) -> timedelta:
    match interval:
        case "min":
            return timedelta(minutes=1)
        case "h":
            return timedelta(hours=1)
        case "d":
            return timedelta(days=1)
        case _:
            return timedelta(seconds=1)


@dataclass
class ReturnedAppliance:
    sensors: list[SensorName]
    sensors_type: ApplianceSensorTypeName


@dataclass
class ReturnedAppliances:
    appliances: dict[ApplianceName, ReturnedAppliance]


@dataclass
class ValuesQuery:
    between: Optional[str] = None


@dataclass
class AppliancesQuery(ValuesQuery):
    appliances: List[str] | str = field(default_factory=list)


@dataclass
class ComputedValuesQuery(AppliancesQuery):
    interval: Literal["s", "min", "h", "d"] = "s"


@dataclass
class WeatherQuery:
    lat: float
    lon: float


def build_query_range(query_args: ValuesQuery) -> tuple[datetime, datetime]:
    if query_args.between:
        start, stop = query_args.between.split(",")

        start = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
        stop = datetime.fromisoformat(stop).replace(tzinfo=timezone.utc)

        if start >= stop:
            raise ValueError

        return (start, stop)

    return (
        datetime.now(timezone.utc) - timedelta(minutes=DEFAULT_MINUTES_BACK),
        datetime.now(timezone.utc),
    )


def values_query(
    topic_filter: fluxy.FilterCallback, query_range: Tuple[datetime, datetime]
) -> fluxy.Query:

    start, stop = query_range
    return fluxy.pipe(
        fluxy.from_bucket(CONFIG.influxdb_telegraf_bucket),
        fluxy.range(start, stop),
        fluxy.filter(lambda r: r._measurement == "mqtt_consumer"),
        fluxy.filter(lambda r: r._field == "value"),
        fluxy.filter(topic_filter),
        fluxy.keep(["_value", "_time"]),
    )


def mean_values_query(
    topic_filter: fluxy.FilterCallback,
    interval: timedelta,
    query_range: Tuple[datetime, datetime],
) -> fluxy.Query:
    return fluxy.pipe(
        values_query(topic_filter, query_range),
        fluxy.aggregate_window(
            timedelta(seconds=interval.total_seconds()),
            fluxy.WindowOperation.MEAN,
            False,
        ),
    )


async def execute_influx_query(
    client: InfluxDBClientAsync,
    query: fluxy.Query,
) -> df:
    return await client.query_api().query_data_frame(query.to_flux())  # type: ignore


@no_type_check
def token_required(f):
    @wraps(f)
    @no_type_check
    async def decorator(*args, **kwargs):
        if (
            "Authorization" not in request.headers
            or request.headers["Authorization"] != f"Bearer {CONFIG.api_token}"
        ):
            return await make_response(
                "A valid token is missing!", HTTPStatus.UNAUTHORIZED
            )
        return await f(*args, **kwargs)

    return decorator


@no_type_check
def limit_query_result(f):
    @wraps(f)
    @no_type_check
    async def decorator(*args, query_args: ValuesQuery, **kwargs):
        try:
            start, stop = build_query_range(query_args)
        except ValueError:
            return await make_response(
                "Invalid value for query param 'between'. 'between' be formatted as 'start,stop', where 'start' & 'stop' follow ISO8601 and 'stop' > 'start'.",
                HTTPStatus.UNPROCESSABLE_ENTITY,
            )
        interval = (
            timedelta_from_string(query_args.interval)
            if hasattr(query_args, "interval")
            else timedelta(seconds=1)
        )
        if (stop - start) / interval > MAX_ROWS:
            return await make_response(
                "Requested too many rows", HTTPStatus.UNPROCESSABLE_ENTITY
            )
        return await f(*args, query_args=query_args, **kwargs)

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
            if isinstance(response, Response):
                return response
            elif not isinstance(response, df):
                raise Exception("serialize_dataframe requires a dataframe")
            if response.empty:
                return []
            return Response(
                response.loc[:, columns].to_json(orient="records"),
                mimetype="application/json",
            )

        return decorator

    return _serialize_dataframe


@no_type_check
def serialize_single_cell(column: str):
    @no_type_check
    def _serialize_single_cell[T: type](fn: T) -> Callable[[T], T]:
        @wraps(fn)
        @no_type_check
        async def decorator(
            *args: list[Any], **kwargs: dict[str, Any]
        ) -> list[Any] | Response:
            response: df = await fn(*args, **kwargs)
            if not isinstance(response, df):
                raise Exception("serialize_single_cell requires a dataframe")
            if len(response) == 0:
                return await make_response(
                    "No mean/total value found", HTTPStatus.NOT_FOUND
                )
            return Response(
                response.iloc[0][column].astype(str), content_type="application/json"
            )

        return decorator

    return _serialize_single_cell


def get_influx_client() -> InfluxDBClientAsync:
    return InfluxDBClientAsync(
        CONFIG.influxdb_url,
        CONFIG.influxdb_token,
        org=CONFIG.influxdb_organisation,
    )


@app.while_serving
async def influx_client():
    try:
        async with get_influx_client() as client:
            app.influx = client  # type: ignore
            yield
    except Exception as e:
        logger.exception(e)


@app.while_serving
async def weather_client():
    app.weather_client = WeatherClient()  # type: ignore
    yield


@app.route("/")
async def hello_world() -> str:
    return "Hello World!"


@app.route("/power_hub/appliances")  # type: ignore
@validate_response(ReturnedAppliances)  # type: ignore
@token_required
async def get_all_appliance_names() -> dict[
    Literal["appliances"],
    dict[ApplianceName, dict[Literal["sensors", "sensors_type"], set[SensorName]]],
]:
    return {
        "appliances": {
            appliance_field.name: {
                "sensors": sensor_fields(appliance_field.type),
                "sensors_type": appliance_field.type.__name__,
            }
            for appliance_field in fields(PowerHubSensors)
        }
    }


@app.route("/power_hub/appliance_sensors/<appliance_name>/<field_name>/last_values")
@token_required
@validate_querystring(ValuesQuery)  # type: ignore
@limit_query_result
@serialize_dataframe(["time", "value"])
async def get_values_for_appliance_sensor(
    appliance_name: str, field_name: str, query_args: ValuesQuery
) -> list[list[ApplianceSensorFieldValue]]:

    return (
        await execute_influx_query(
            app.influx,  # type: ignore
            values_query(
                lambda r: r.topic
                == f"power_hub/appliance_sensors/{appliance_name}/{field_name}",
                build_query_range(query_args),
            ),
        )
    ).rename(columns={"_value": "value", "_time": "time"})


@app.route("/power_hub/appliance_sensors/<appliance_name>/<field_name>/mean")
@token_required
@validate_querystring(ValuesQuery)  # type: ignore
@limit_query_result
@serialize_single_cell("_value")
async def get_mean_value_for_appliance_sensor(
    appliance_name: str, field_name: str, query_args: ValuesQuery
) -> list[list[ApplianceSensorFieldValue]]:
    return await execute_influx_query(
        app.influx,  # type: ignore
        fluxy.pipe(
            values_query(
                lambda r: r.topic
                == f"power_hub/appliance_sensors/{appliance_name}/{field_name}",
                build_query_range(query_args),
            ),
            fluxy.mean(column="_value"),
        ),
    )


@app.route("/power_hub/appliance_sensors/<appliance_name>/<field_name>/total")
@token_required
@validate_querystring(ValuesQuery)  # type: ignore
@limit_query_result
@serialize_single_cell("_value")
async def get_total_value_for_appliance_sensor(
    appliance_name: str,
    field_name: str,
    query_args: ValuesQuery,
) -> str:

    return await execute_influx_query(
        app.influx,  # type: ignore
        query=fluxy.pipe(
            values_query(
                lambda r: r.topic
                == f"power_hub/appliance_sensors/{appliance_name}/{field_name}",
                build_query_range(query_args),
            ),
            fluxy.sum("_value"),
        ),
    )


@app.route("/power_hub/electric/power/consumption/over/time")
@token_required
@validate_querystring(ComputedValuesQuery)  # type: ignore
@limit_query_result
@serialize_dataframe(["time", "value"])
async def get_electrical_power_consumption(
    query_args: ComputedValuesQuery,
) -> list[list[ApplianceSensorFieldValue]]:
    appliance_names = request.args.getlist("appliances") or [
        field.name for field in fields(PowerHubSensors) if "pump" in field.name
    ]
    return (
        await execute_influx_query(
            app.influx,  # type: ignore
            mean_values_query(
                fluxy.any(
                    fluxy.conform,
                    [
                        {
                            "topic": f"power_hub/appliance_sensors/{appliance_name}/electrical_power"
                        }
                        for appliance_name in appliance_names
                    ],
                ),
                timedelta_from_string(query_args.interval),
                build_query_range(query_args),
            ),
        )
    ).rename(columns={"_value": "value", "_time": "time"})


@app.route("/power_hub/electric/power/consumption/mean")
@token_required
@validate_querystring(AppliancesQuery)  # type: ignore
@serialize_single_cell("_value")
async def get_electrical_power_consumption_mean(
    query_args: AppliancesQuery,
) -> list[list[ApplianceSensorFieldValue]]:
    appliance_names = request.args.getlist("appliances") or [
        field.name for field in fields(PowerHubSensors) if "pump" in field.name
    ]

    return await execute_influx_query(
        app.influx,  # type: ignore
        fluxy.pipe(
            mean_values_query(
                fluxy.any(
                    fluxy.conform,
                    [
                        {
                            "topic": f"power_hub/appliance_sensors/{appliance_name}/electrical_power"
                        }
                        for appliance_name in appliance_names
                    ],
                ),
                timedelta(seconds=1),
                build_query_range(query_args),
            ),
            fluxy.mean(column="_value"),
        ),
    )


@app.route("/power_hub/electric/power/production/over/time")
@token_required
@validate_querystring(ComputedValuesQuery)  # type: ignore
@limit_query_result
@serialize_dataframe(["time", "value"])
async def get_electrical_power_production(
    query_args: ComputedValuesQuery,
) -> list[list[ApplianceSensorFieldValue]] | ResponseTypes:
    appliance_names = request.args.getlist("appliances") or ["pv_panel"]

    if any("pv_panel" not in item for item in appliance_names):
        return await make_response(
            "Please only provide pv_panel(s)", HTTPStatus.UNPROCESSABLE_ENTITY
        )

    return (
        await execute_influx_query(
            app.influx,  # type: ignore
            mean_values_query(
                fluxy.any(
                    fluxy.conform,
                    [
                        {"topic": f"power_hub/appliance_sensors/{appliance_name}/power"}
                        for appliance_name in appliance_names
                    ],
                ),
                timedelta_from_string(query_args.interval),
                build_query_range(query_args),
            ),
        )
    ).rename(columns={"_value": "value", "_time": "time"})


WeatherProperty = str
WEATHER_LOCATION_WHITELIST = {(41.3874, 2.1686)}


@no_type_check
def check_weather_location_whitelist(f):
    @wraps(f)
    @no_type_check
    async def decorator(*args, query_args, **kwargs):
        lat = query_args.lat
        lon = query_args.lon
        if (lat, lon) not in WEATHER_LOCATION_WHITELIST:
            return await make_response(
                f"(Lat, Lon) combination of ({lat}, {lon}) is not on the whitelist.",
                HTTPStatus.UNPROCESSABLE_ENTITY,
            )
        return await f(*args, query_args=query_args, **kwargs)

    return decorator


@app.route("/weather/current")
@token_required
@validate_querystring(WeatherQuery)  # type: ignore
@check_weather_location_whitelist
async def get_current_weather(
    query_args: WeatherQuery,
) -> dict[WeatherProperty, float | str | list[dict[str, str]]]:
    return (await app.weather_client.get_weather(query_args.lat, query_args.lon)).current  # type: ignore


@app.route("/weather/hourly")
@token_required
@validate_querystring(WeatherQuery)  # type: ignore
@check_weather_location_whitelist
async def get_hourly_weather(
    query_args: WeatherQuery,
) -> list[CurrentWeather]:
    return (await app.weather_client.get_weather(query_args.lat, query_args.lon)).hourly  # type: ignore


@app.route("/weather/daily")
@no_type_check
@token_required
@validate_querystring(WeatherQuery)  # type: ignore
@check_weather_location_whitelist
async def get_daily_weather(
    query_args: WeatherQuery,
) -> list[DailyWeather]:
    return (
        await app.weather_client.get_weather(
            query_args.lat, query_args.lon, timedelta(days=1)
        )
    ).daily


def run() -> None:
    app.run(host="0.0.0.0", port=5001)


if __name__ == "__main__":
    run()
