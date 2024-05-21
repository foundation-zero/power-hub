from enum import Enum
import os
from quart import Quart, request, make_response, Response
from dataclasses import dataclass
from quart_schema import QuartSchema, validate_response, validate_querystring  # type: ignore
from dotenv import load_dotenv
from typing import Any, Callable, List, Literal, Tuple
from dataclasses import fields
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
import fluxy  # type: ignore
from datetime import datetime, timezone, timedelta
from functools import partial, reduce, wraps
from http import HTTPStatus
from typing import no_type_check
from pandas import DataFrame as df  # type: ignore
from energy_box_control.power_hub.sensors import PowerHubSensors
from energy_box_control.sensors import sensor_fields
from energy_box_control.api.weather import WeatherClient, DailyWeather, CurrentWeather
from energy_box_control.custom_logging import get_logger


logger = get_logger(__name__)

dotenv_path = os.path.normpath(
    os.path.join(os.path.realpath(__file__), "../../../", ".env")
)
load_dotenv(dotenv_path)

TOKEN = os.environ["API_TOKEN"]
DEFAULT_MINUTES_BACK = 60
MAX_ROWS = 172800  # 48 hours

app = Quart(__name__)
QuartSchema(
    app,
    security=[{"power_hub_api": []}],
    security_schemes={
        "power_hub_api": {"type": "apiKey", "name": "Authorization", "in_": "header"}
    },
    conversion_preference="pydantic",
)


ApplianceName = str
ApplianceSensorTypeName = str
SensorName = str
ApplianceSensorFieldValue = float


class Interval(Enum):
    SECONDS = 1.0
    MINUTES = 60.0
    HOURS = 60 * 60.0
    DAYS = 60 * 60 * 24.0

    @classmethod
    def from_string(cls, interval: str) -> "Interval":
        if interval == "m":
            return Interval.MINUTES
        elif interval == "h":
            return Interval.HOURS
        elif interval == "d":
            return Interval.DAYS
        return Interval.SECONDS


@dataclass
class ReturnedAppliance:
    sensors: list[SensorName]
    sensors_type: ApplianceSensorTypeName


@dataclass
class ReturnedAppliances:
    appliances: dict[ApplianceName, ReturnedAppliance]


@dataclass
class ValuesQuery:
    minutes_back: int = DEFAULT_MINUTES_BACK
    start: str | None = None
    stop: str | None = None


DEFAULT_COMPUTED_INTERVAL = "s"


@dataclass
class AppliancesQuery(ValuesQuery):
    appliances: str = ""


@dataclass
class ComputedValuesQuery(AppliancesQuery):
    interval: str = DEFAULT_COMPUTED_INTERVAL


@dataclass
class WeatherQuery:
    lat: float
    lon: float


def build_query_range(
    minutes_back: float, start: str | None, stop: str | None
) -> tuple[datetime, datetime]:

    if start and stop:
        time_format = "%d-%m-%YT%H:%M:%S"
        return (
            datetime.strptime(start, time_format).replace(tzinfo=timezone.utc)
        ), datetime.strptime(stop, time_format).replace(tzinfo=timezone.utc)

    return (
        datetime.now(timezone.utc) - timedelta(minutes=minutes_back),
        datetime.now(timezone.utc),
    )


def values_query(
    topic_filter: fluxy.FilterCallback, query_range: Tuple[datetime, datetime]
) -> fluxy.Query:

    start, stop = query_range
    return fluxy.pipe(
        fluxy.from_bucket(os.environ["INFLUXDB_TELEGRAF_BUCKET"]),
        fluxy.range(start, stop),
        fluxy.filter(lambda r: r._measurement == "mqtt_consumer"),
        fluxy.filter(lambda r: r._field == "value"),
        fluxy.filter(topic_filter),
        fluxy.keep(["_value", "_time"]),
    )


def mean_values_query(
    topic_filter: fluxy.FilterCallback,
    interval: float,
    query_range: Tuple[datetime, datetime],
) -> fluxy.Query:
    return fluxy.pipe(
        values_query(topic_filter, query_range),
        fluxy.aggregate_window(
            timedelta(seconds=interval),
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
            or request.headers["Authorization"] != f"Bearer {TOKEN}"
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
    async def decorator(*args, **kwargs):
        if kwargs["query_args"].start and kwargs["query_args"].stop:
            start, stop = build_query_range(
                kwargs["query_args"].minutes_back,
                kwargs["query_args"].start,
                kwargs["query_args"].stop,
            )
        else:
            start, stop = build_query_range(
                kwargs["query_args"].minutes_back, None, None
            )
        interval_seconds = (
            Interval.from_string(kwargs["query_args"].interval).value
            if hasattr(kwargs["query_args"], "interval")
            else 1
        )
        if (stop - start).total_seconds() / interval_seconds > MAX_ROWS:
            return await make_response(
                "Requested dataframe is too large", HTTPStatus.FORBIDDEN
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


def get_influx_client() -> InfluxDBClientAsync:
    return InfluxDBClientAsync(
        os.environ["INFLUXDB_URL"],
        os.environ["INFLUXDB_TOKEN"],
        org=os.environ["INFLUXDB_ORGANISATION"],
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


@app.route("/appliances")  # type: ignore
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


@app.route("/appliance_sensors/<appliance_name>/<field_name>/last_values")
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
                build_query_range(
                    query_args.minutes_back, query_args.start, query_args.stop
                ),
            ),
        )
    ).rename(columns={"_value": "value", "_time": "time"})


@app.route("/appliance_sensors/<appliance_name>/<field_name>/mean")
@token_required
@validate_querystring(ValuesQuery)  # type: ignore
@limit_query_result
async def get_mean_value_for_appliance_sensor(
    appliance_name: str, field_name: str, query_args: ValuesQuery
) -> list[list[ApplianceSensorFieldValue]]:

    query_result = await execute_influx_query(
        app.influx,  # type: ignore
        fluxy.pipe(
            values_query(
                lambda r: r.topic
                == f"power_hub/appliance_sensors/{appliance_name}/{field_name}",
                build_query_range(
                    query_args.minutes_back, query_args.start, query_args.stop
                ),
            ),
            fluxy.mean(column="_value"),
        ),
    )
    return Response(query_result.iloc[0]["_value"].astype(str) if len(query_result) > 0 else "0.0", mimetype="application/json")  # type: ignore


@app.route("/appliance_sensors/<appliance_name>/<field_name>/total")
@token_required
@validate_querystring(ValuesQuery)  # type: ignore
@limit_query_result
async def get_total_value_for_appliance_sensor(
    appliance_name: str,
    field_name: str,
    query_args: ValuesQuery,
) -> str:

    query_result = await execute_influx_query(
        app.influx,  # type: ignore
        query=fluxy.pipe(
            values_query(
                lambda r: r.topic
                == f"power_hub/appliance_sensors/{appliance_name}/{field_name}",
                build_query_range(
                    query_args.minutes_back, query_args.start, query_args.stop
                ),
            ),
            fluxy.sum("_value"),
        ),
    )
    return Response(query_result.iloc[0]["_value"].astype(str) if len(query_result) > 0 else "0.0", mimetype="application/json")  # type: ignore


def _topic_filters(appliance_names: List[str], field: str, r: fluxy.Row):

    exps = [
        r.topic == f"power_hub/appliance_sensors/{appliance_name}/{field}"
        for appliance_name in appliance_names
    ]
    return reduce(lambda prev, cur: prev | cur, exps)


@app.route("/power_hub/consumption/electric/power/over/time")
@token_required
@validate_querystring(ComputedValuesQuery)  # type: ignore
@limit_query_result
@serialize_dataframe(["time", "value"])
async def get_electrical_power_consumption(
    query_args: ComputedValuesQuery,
) -> list[list[ApplianceSensorFieldValue]]:
    if not query_args.appliances:
        appliance_names = [
            field.name for field in fields(PowerHubSensors) if "pump" in field.name
        ]
    else:
        appliance_names = query_args.appliances.split(",")

    return (
        await execute_influx_query(
            app.influx,  # type: ignore
            mean_values_query(
                partial(_topic_filters, appliance_names, "electrical_power"),
                Interval.from_string(query_args.interval).value,
                build_query_range(
                    query_args.minutes_back, query_args.start, query_args.stop
                ),
            ),
        )
    ).rename(columns={"_value": "value", "_time": "time"})


@app.route("/power_hub/consumption/electric/power/mean")
@token_required
@validate_querystring(AppliancesQuery)  # type: ignore
async def get_electrical_power_consumption_mean(
    query_args: AppliancesQuery,
) -> list[list[ApplianceSensorFieldValue]]:

    if not query_args.appliances:
        appliance_names = [
            field.name for field in fields(PowerHubSensors) if "pump" in field.name
        ]
    else:
        appliance_names = query_args.appliances.split(",")

    query_result = await execute_influx_query(
        app.influx,  # type: ignore
        fluxy.pipe(
            mean_values_query(
                partial(_topic_filters, appliance_names, "electrical_power"),
                1,
                build_query_range(
                    query_args.minutes_back, query_args.start, query_args.stop
                ),
            ),
            fluxy.mean(column="_value"),
        ),
    )

    return Response(query_result.iloc[0]["_value"].astype(str) if len(query_result) > 0 else "0.0", mimetype="application/json")  # type: ignore


@app.route("/power_hub/production/electric/power/over/time")
@token_required
@validate_querystring(ComputedValuesQuery)  # type: ignore
@limit_query_result
@serialize_dataframe(["time", "value"])
async def get_electrical_power_production(
    query_args: ComputedValuesQuery,
) -> list[list[ApplianceSensorFieldValue]]:

    if not query_args.appliances:
        appliance_names = ["pv_panel"]
    else:
        appliance_names = query_args.appliances.split(",")

    return (
        await execute_influx_query(
            app.influx,  # type: ignore
            mean_values_query(
                partial(_topic_filters, appliance_names, "power"),
                Interval.from_string(query_args.interval).value,
                build_query_range(
                    query_args.minutes_back, query_args.start, query_args.stop
                ),
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
