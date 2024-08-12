from pydantic import ValidationError
from quart import Quart, request, Response
from quart.typing import ResponseTypes
from quart_schema import QuartSchema, validate_response, validate_querystring, RequestSchemaValidationError  # type: ignore
from typing import Literal
from dataclasses import fields
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
import fluxy  # type: ignore
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from typing import no_type_check
from pandas import DataFrame as df  # type: ignore
import pandas as pd  # type: ignore
from energy_box_control.power_hub.sensors import PowerHubSensors
from energy_box_control.sensors import sensor_fields
from energy_box_control.api.weather import WeatherClient, DailyWeather, CurrentWeather
from energy_box_control.custom_logging import get_logger

from energy_box_control.config import CONFIG
from quart_cors import cors  # type: ignore
from energy_box_control.api.schemas import (
    ApplianceSensorFieldValue,
    ReturnedAppliances,
    SensorName,
    ValuesQuery,
    WeatherQuery,
    AppliancesQuery,
    ComputedValuesQuery,
    ApplianceName,
    ComputedPowerQuery,
)
from energy_box_control.api.query_builders import (
    PrefixedFluxy,
    build_query_range,
    values_query,
    mean_values_query,
    timedelta_from_string,
    mean_per_hour_query,
)

from energy_box_control.api.decorators import token_required, limit_query, serialize_dataframe, serialize_single_cell, check_weather_location_whitelist  # type: ignore

logger = get_logger(__name__)

NUM_PV_PANEL = 4

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


async def execute_influx_query(
    client: InfluxDBClientAsync,
    query: fluxy.Query | PrefixedFluxy,
) -> df:
    return await client.query_api().query_data_frame(query.to_flux())  # type: ignore


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


@app.route(
    "/power_hub/appliance_sensors/<appliance_name>/<sensor_field_name>/last_values"
)
@token_required
@validate_querystring(ValuesQuery)  # type: ignore
@limit_query(aggregated=False)
@serialize_dataframe(["time", "value"])
async def get_values_for_appliance_sensor(
    appliance_name: str, sensor_field_name: str, query_args: ValuesQuery
) -> list[list[ApplianceSensorFieldValue]]:

    field_name = f"{appliance_name}_{sensor_field_name}"
    return (
        await execute_influx_query(
            app.influx,  # type: ignore
            values_query(
                lambda r: r._field == field_name, build_query_range(query_args)
            ),
        )
    ).rename(columns={field_name: "value", "_time": "time"})


@app.route("/power_hub/appliance_sensors/<appliance_name>/<sensor_field_name>/mean")
@token_required
@validate_querystring(ValuesQuery)  # type: ignore
@limit_query(aggregated=True)
@serialize_single_cell("value")
async def get_mean_value_for_appliance_sensor(
    appliance_name: str, sensor_field_name: str, query_args: ValuesQuery
) -> list[list[ApplianceSensorFieldValue]]:
    field_name = f"{appliance_name}_{sensor_field_name}"
    return (
        await execute_influx_query(
            app.influx,  # type: ignore
            fluxy.pipe(
                values_query(
                    lambda r: r._field == field_name,
                    build_query_range(query_args),
                ),
                fluxy.mean(column=field_name),
            ),
        )
    ).rename(columns={field_name: "value"})


@app.route("/power_hub/appliance_sensors/<appliance_name>/<sensor_field_name>/total")
@token_required
@validate_querystring(ValuesQuery)  # type: ignore
@limit_query(aggregated=True)
@serialize_single_cell("value")
async def get_total_value_for_appliance_sensor(
    appliance_name: str,
    sensor_field_name: str,
    query_args: ValuesQuery,
) -> str:

    field_name = f"{appliance_name}_{sensor_field_name}"
    return (
        await execute_influx_query(
            app.influx,  # type: ignore
            query=fluxy.pipe(
                values_query(
                    lambda r: r._field == field_name,
                    build_query_range(query_args),
                ),
                fluxy.sum(field_name),
            ),
        )
    ).rename(columns={field_name: "value"})


@app.route("/power_hub/appliance_sensors/pcm/fill/current")
@token_required
@serialize_single_cell("value")
async def get_pcm_current_fill() -> str:

    last_empty: datetime = pd.Timestamp(
        (
            await execute_influx_query(
                app.influx,  # type: ignore
                query=fluxy.pipe(
                    fluxy.from_bucket(CONFIG.influxdb_telegraf_bucket),
                    fluxy.range(start=timedelta(days=-10)),
                    fluxy.filter(lambda r: r._field == "pcm_temperature"),
                    fluxy.literal('filter(fn: (r) => r["_value"] <= 77)'),
                    fluxy.sort(columns=["_time"], sort_order=fluxy.Order.DESC),
                    fluxy.limit(1),
                    fluxy.pivot(
                        row_key=["_time"], column_key=["_field"], value_column="_value"
                    ),
                ),
            )
        )["_time"].values[0]
    ).to_pydatetime()

    net_charge_name = "pcm_net_charge"
    return (
        await execute_influx_query(
            app.influx,  # type: ignore
            query=fluxy.pipe(
                fluxy.from_bucket(CONFIG.influxdb_telegraf_bucket),
                fluxy.range(
                    start=last_empty.replace(tzinfo=timezone.utc),
                    stop=datetime.now(tz=timezone.utc),
                ),
                fluxy.filter(lambda r: r._field == net_charge_name),
                fluxy.pivot(
                    row_key=["_time"], column_key=["_field"], value_column="_value"
                ),
                fluxy.sum(net_charge_name),
            ),
        )
    ).rename(columns={net_charge_name: "value"})


@app.route(
    "/power_hub/appliance_sensors/<appliance_name>/<sensor_field_name>/over/time"
)
@token_required
@validate_querystring(ComputedValuesQuery)  # type: ignore
@limit_query(aggregated=False)
@serialize_dataframe(["time", "value"])
async def get_sensor_value_over_time(
    appliance_name: str, sensor_field_name: str, query_args: ComputedValuesQuery
) -> list[list[ApplianceSensorFieldValue]] | ResponseTypes:

    field_name = f"{appliance_name}_{sensor_field_name}"
    return (
        await execute_influx_query(
            app.influx,  # type: ignore
            mean_values_query(
                lambda r: r._field == field_name,
                timedelta_from_string(query_args.interval),
                build_query_range(query_args),
            ),
        )
    ).rename(columns={"field": "value", "_time": "time"})


@app.route(
    "/power_hub/appliance_sensors/<appliance_name>/<sensor_field_name>/mean/per/hour_of_day"
)
@token_required
@validate_querystring(AppliancesQuery)  # type: ignore
@serialize_dataframe(["hour", "value"])
async def get_mean_sensor_value_per_hour(
    appliance_name: str,
    sensor_field_name: str,
    query_args: AppliancesQuery,
) -> list[list[ApplianceSensorFieldValue]]:

    return (
        await execute_influx_query(
            app.influx,  # type: ignore
            mean_per_hour_query(
                lambda r: r._field == f"{appliance_name}_{sensor_field_name}",
                build_query_range(query_args, default_timedelta=timedelta(days=7)),
            ),
        )
    ).rename(columns={"field": "value"})


def consumption_appliances():
    return [field.name for field in fields(PowerHubSensors) if "pump" in field.name]


@app.route("/power_hub/electric/power/consumption/over/time")
@token_required
@validate_querystring(ComputedPowerQuery)  # type: ignore
@limit_query(aggregated=False)
@serialize_dataframe(["time", "value"])
async def get_electrical_power_consumption(
    query_args: ComputedPowerQuery,
) -> list[list[ApplianceSensorFieldValue]]:
    appliance_names = request.args.getlist("appliances") or consumption_appliances()
    return (
        await execute_influx_query(
            app.influx,  # type: ignore
            mean_values_query(
                fluxy.any(
                    fluxy.conform,
                    [
                        {"_field": f"{appliance_name}_rated_power_consumption"}
                        for appliance_name in appliance_names
                    ],
                ),
                timedelta_from_string(query_args.interval),
                build_query_range(query_args),
            ),
        )
    ).rename(columns={"field": "value", "_time": "time"})


@app.route("/power_hub/electric/power/consumption/mean/per/hour_of_day")
@token_required
@validate_querystring(AppliancesQuery)  # type: ignore
@serialize_dataframe(["hour", "value"])
async def get_electrical_power_consumption_per_hour(
    query_args: AppliancesQuery,
) -> list[list[ApplianceSensorFieldValue]]:
    appliance_names = request.args.getlist("appliances") or consumption_appliances()

    return (
        await execute_influx_query(
            app.influx,  # type: ignore
            mean_per_hour_query(
                fluxy.any(
                    fluxy.conform,
                    [
                        {"_field": f"{appliance_name}_rated_power_consumption"}
                        for appliance_name in appliance_names
                    ],
                ),
                build_query_range(query_args, default_timedelta=timedelta(days=7)),
            ),
        )
    ).rename(columns={"field": "value"})


@app.route("/power_hub/electric/power/consumption/mean")
@token_required
@validate_querystring(AppliancesQuery)  # type: ignore
@serialize_single_cell("field")
async def get_electrical_power_consumption_mean(
    query_args: AppliancesQuery,
) -> list[list[ApplianceSensorFieldValue]]:
    appliance_names = request.args.getlist("appliances") or consumption_appliances()

    return await execute_influx_query(
        app.influx,  # type: ignore
        fluxy.pipe(
            mean_values_query(
                fluxy.any(
                    fluxy.conform,
                    [
                        {"_field": f"{appliance_name}_rated_power_consumption"}
                        for appliance_name in appliance_names
                    ],
                ),
                timedelta(seconds=1),
                build_query_range(query_args),
            ),
            fluxy.mean(column="field"),
        ),
    )


@app.route("/power_hub/electric/power/production/over/time")
@token_required
@validate_querystring(ComputedPowerQuery)  # type: ignore
@limit_query(aggregated=False)
@serialize_dataframe(["time", "value"])
async def get_electrical_power_production(
    query_args: ComputedPowerQuery,
) -> list[list[ApplianceSensorFieldValue]] | ResponseTypes:
    return (
        await execute_influx_query(
            app.influx,  # type: ignore
            mean_values_query(
                fluxy.any(
                    fluxy.conform,
                    [
                        {"_field": f"electrical_solar_{n}_PV_power"}
                        for n in range(1, NUM_PV_PANEL + 1)
                    ],
                ),
                timedelta_from_string(query_args.interval),
                build_query_range(query_args),
            ),
        )
    ).rename(columns={"field": "value", "_time": "time"})


@app.route("/power_hub/electric/power/production/mean/per/hour_of_day")
@token_required
@validate_querystring(AppliancesQuery)  # type: ignore
@serialize_dataframe(["hour", "value"])
async def get_electrical_power_production_interval(
    query_args: AppliancesQuery,
) -> list[list[ApplianceSensorFieldValue]] | ResponseTypes:
    return (
        await execute_influx_query(
            app.influx,  # type: ignore
            mean_per_hour_query(
                fluxy.any(
                    fluxy.conform,
                    [
                        {"_field": f"electrical_solar_{n}_PV_power"}
                        for n in range(1, NUM_PV_PANEL + 1)
                    ],
                ),
                build_query_range(query_args, default_timedelta=timedelta(days=7)),
            ),
        )
    ).rename(columns={"field": "value"})


@app.route("/power_hub/electric/power/production/mean")
@token_required
@validate_querystring(AppliancesQuery)  # type: ignore
@serialize_single_cell("field")
async def get_electrical_power_production_mean(
    query_args: AppliancesQuery,
) -> list[list[ApplianceSensorFieldValue]]:
    return await execute_influx_query(
        app.influx,  # type: ignore
        fluxy.pipe(
            mean_values_query(
                fluxy.any(
                    fluxy.conform,
                    [
                        {"_field": f"electrical_solar_{n}_PV_power"}
                        for n in range(1, NUM_PV_PANEL + 1)
                    ],
                ),
                timedelta(seconds=1),
                build_query_range(query_args),
            ),
            fluxy.mean(column="field"),
        ),
    )


WeatherProperty = str


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
