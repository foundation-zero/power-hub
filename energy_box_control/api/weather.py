from http import HTTPStatus
from dacite import from_dict
from dataclasses import dataclass
import aiohttp
from energy_box_control.units import (
    Celsius,
    HectoPascal,
    MeterPerSecond,
    Percentage,
    Degree,
)
from datetime import datetime, timedelta
import json

from energy_box_control.config import CONFIG


class CacheMissError(Exception):
    pass


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
    dt: int
    temp: Celsius
    feels_like: Celsius
    pressure: HectoPascal
    humidity: Percentage
    wind_speed: MeterPerSecond
    wind_deg: Degree
    weather: list[Weather]


@dataclass
class DailyWeather:
    dt: int
    summary: str
    temp: DailyTemp
    feels_like: DailyFeelsLike
    pressure: HectoPascal
    humidity: Percentage
    wind_speed: MeterPerSecond
    wind_deg: Degree
    weather: list[Weather]


@dataclass
class WeatherResponse:
    lat: float
    lon: float
    current: CurrentWeather
    hourly: list[CurrentWeather]
    daily: list[DailyWeather]
    timezone: str


class WeatherClient:

    def __init__(self) -> None:
        self.cached_weather: dict[
            tuple[float, float], tuple[datetime, WeatherResponse] | None
        ] = {}

    async def get_weather(
        self, lat: float, lon: float, cache_delta: timedelta = timedelta(hours=1)
    ) -> WeatherResponse:
        try:
            return self._get_weather_from_cache(lat, lon, cache_delta)
        except CacheMissError:
            weather = await self._fetch_weather(lat, lon)
            self.cached_weather[(lat, lon)] = (datetime.now(), weather)
            return weather

    def _get_weather_from_cache(
        self, lat: float, lon: float, cache_delta: timedelta
    ) -> WeatherResponse:
        if self.cached_weather and (entry := self.cached_weather.get((lat, lon), None)):
            time, weather = entry
            if (datetime.now() - time) < cache_delta:
                return weather
        raise CacheMissError(f"No recent weather for {lat}, {lon} exists in cache.")

    async def _fetch_weather(self, lat: float, lon: float) -> WeatherResponse:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={CONFIG.open_weather_api_key}&units={UNIT_SYSTEM}"
            ) as response:
                if response.status != HTTPStatus.OK:
                    raise Exception(
                        f"Call to Open Weather failed with status {response.status}"
                    )
                return from_dict(WeatherResponse, json.loads(await response.text()))
