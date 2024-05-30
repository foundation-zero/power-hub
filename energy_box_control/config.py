from typing import Any, Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PowerHubConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    influxdb_user: str = Field(default="")
    influxdb_pass: str = Field(default="")
    influxdb_organisation: str = Field(default="")
    influxdb_telegraf_bucket: str = Field(default="")
    influxdb_token: str = Field(default="")
    influxdb_url: str = Field(
        pattern="(https?)://([a-zA-Z0-9.-]+):(\\d+)", default="http://influxdb:8086"
    )
    mqtt_host: str = Field(pattern="^[^/:]+$", default=" ")
    mqtt_password: str = Field(default="")
    mqtt_username: str = Field(default="")
    api_token: str = Field(default="")
    open_weather_api_key: str = Field(default="")
    logging_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO"
    )

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)


CONFIG = PowerHubConfig()
