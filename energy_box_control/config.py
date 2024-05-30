from typing import Any, Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PowerHubConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    influxdb_user: str
    influxdb_pass: str
    influxdb_organisation: str
    influxdb_telegraf_bucket: str
    influxdb_token: str
    influxdb_url: str = Field(pattern="(https?)://([a-zA-Z0-9.-]+):(\\d+)")
    mqtt_host: str = Field(pattern="^[^/:]+$")
    mqtt_password: str
    mqtt_username: str
    api_token: str
    open_weather_api_key: str = Field(default="")
    logging_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO"
    )

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)


CONFIG = PowerHubConfig()
