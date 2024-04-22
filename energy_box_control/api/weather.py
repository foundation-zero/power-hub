import os
from typing import Union
import requests
from http import HTTPStatus
from dataclass_wizard import JSONWizard  # type: ignore
from dataclasses import dataclass
from energy_box_control.units import (
    Celsius,
    HectoPascal,
    MeterPerSecond,
    MoisturePercentage,
    MeteorologicalDegree,
    Degrees,
)
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from datetime import datetime, timedelta, UTC
from energy_box_control.mqtt import publish_to_mqtt, create_and_connect_client
from energy_box_control.api.influx import execute_influx_query  # , build_query_range
import json
from pandas import DataFrame as df  # type: ignore


UNIT_SYSTEM = "metric"
WEATHER_TOPIC = "weather/onecall"


@dataclass
class Weather:
    main: str
    description: str
    icon: str


@dataclass
class DailyFeelsLike:
    day: Celsius
    night: Celsius
    eve: Celsius
    morn: Celsius


@dataclass
class DailyTemp(DailyFeelsLike):
    min: Celsius
    max: Celsius


@dataclass
class CurrentWeather:
    temp: Celsius
    feels_like: Celsius
    pressure: HectoPascal
    humidity: MoisturePercentage
    wind_speed: MeterPerSecond
    wind_deg: MeteorologicalDegree
    weather: list[Weather]


@dataclass
class DailyWeather:
    dt: int
    summary: str
    temp: DailyTemp
    feels_like: DailyFeelsLike
    pressure: HectoPascal
    humidity: MoisturePercentage
    wind_speed: MeterPerSecond
    wind_deg: MeteorologicalDegree
    weather: list[Weather]


@dataclass
class HourlyWeather(CurrentWeather):
    dt: int


@dataclass
class WeatherResponse(JSONWizard):
    lat: Degrees
    lon: Degrees
    current: CurrentWeather
    hourly: list[HourlyWeather]
    daily: list[DailyWeather]
    timezone: str


async def get_last_weather_from_influx(
    minutes_back: float, influx_client: InfluxDBClientAsync, lat: Degrees, lon: Degrees
) -> df:
    query = f"""import "math"
        from(bucket: "simulation_data")
        |> range(start: -{int(minutes_back)}m)
        |> filter(fn: (r) => r["_measurement"] == "mqtt_consumer")
        |> filter(fn: (r) => r["_field"] == "weather_values")
        |> filter(fn: (r) => math.abs(x: (float(v: r["lat"])) - {lat}) < 1)
        |> filter(fn: (r) => math.abs(x: (float(v: r["lat"])) - {lon}) < 1)
        |> last()
        """
    return await execute_influx_query(influx_client, query_string=query)


async def validate_weather_from_influx(
    influx_client: InfluxDBClientAsync,
    lat: Degrees,
    lon: Degrees,
    cache_delta: timedelta,
) -> Union[WeatherResponse, list[WeatherResponse]]:
    response = await get_last_weather_from_influx(
        cache_delta.total_seconds() / 60, influx_client, lat, lon
    )
    if response.empty or (datetime.now(UTC) - response["_time"].iloc[0].to_pydatetime()) > cache_delta:  # type: ignore
        raise ValueError("No recent value found in cache")
    return WeatherResponse.from_json(response["_value"].iloc[0])  # type: ignore


def get_open_weather(lat: Degrees, lon: Degrees) -> str:
    r = requests.get(
        f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={os.environ['OPEN_WEATHER_API_KEY']}&units={UNIT_SYSTEM}"
    )
    if r.status_code != HTTPStatus.OK:
        raise Exception
    return r.text


def publish_weather_values_to_mqtt(lat: Degrees, lon: Degrees, weather_values: str):
    publish_to_mqtt(
        create_and_connect_client(),
        WEATHER_TOPIC,
        json.dumps(
            {
                "timestamp": datetime.now(UTC).timestamp(),
                "lat": lat,
                "lon": lon,
                "weather_values": weather_values,
            }
        ),
    )


async def get_weather(
    lat: Degrees,
    lon: Degrees,
    influx_client: InfluxDBClientAsync,
    cache_delta: timedelta = timedelta(hours=1),
) -> Union[WeatherResponse, list[WeatherResponse]]:
    try:
        return await validate_weather_from_influx(influx_client, lat, lon, cache_delta)
    except Exception:
        weather_values = get_open_weather(lat, lon)
        publish_weather_values_to_mqtt(lat, lon, weather_values)
        return WeatherResponse.from_json(weather_values)  # type: ignore
