from pyowm import OWM  # type: ignore
from pyowm.weatherapi25.weather_manager import WeatherManager  # type: ignore
from pyowm.utils import config  # type: ignore
from pyowm.utils import timestamps  # type: ignore
import os


def create_weather_manager() -> WeatherManager:
    key = os.environ["OPEN_WEATHER_API_KEY"]
    owm = OWM(key)
    return owm.weather_manager()
