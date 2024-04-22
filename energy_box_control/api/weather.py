from http import HTTPStatus
from typing import Union
from dataclass_wizard import JSONWizard  # type: ignore
from dataclasses import dataclass

import requests
from energy_box_control.units import (
    Celsius,
    HectoPascal,
    MeterPerSecond,
    MoisturePercentage,
    MeteorologicalDegree,
    Degrees,
)
from datetime import datetime, timedelta
from quart import Quart
import os


UNIT_SYSTEM = "metric"


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


def get_open_weather(lat: Degrees, lon: Degrees) -> str:
    r = requests.get(
        f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={os.environ['OPEN_WEATHER_API_KEY']}&units={UNIT_SYSTEM}"
    )
    if r.status_code != HTTPStatus.OK:
        raise Exception
    return r.text


async def get_weather(
    lat: Degrees, lon: Degrees, app: Quart, cache_delta: timedelta = timedelta(hours=1)
) -> Union[WeatherResponse, list[WeatherResponse]]:
    if (lat, lon) in app.weather and (  # type: ignore
        datetime.now() - app.weather[(lat, lon)]["datetime"]  # type: ignore
    ) < cache_delta:
        return app.weather[(lat, lon)]["weather"]  # type: ignore
    weather = WeatherResponse.from_json(get_open_weather(lat, lon))  # type: ignore
    app.weather[(lat, lon)] = {"datetime": datetime.now(), "weather": weather}  # type: ignore
    return weather
