from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Awaitable, Callable, Optional
from energy_box_control.monitoring.checks import Check, CheckResult, Severity


POWER_HUB_API_URL = "https://api.staging.power-hub.foundationzero.org/"
INFLUXDB_URL = "https://influxdb.staging.power-hub.foundationzero.org/health"
MQTT_HEALTH_URL = "http://vernemq.staging.power-hub.foundationzero.org:8888/health"
DISPLAY_HEALTH_URL = "https://power-hub.pages.dev/"


@dataclass
class UrlHealthCheck(Check):
    check: Callable[[], Awaitable[CheckResult]]


def url_health_check(name: str, url: str, severity: Severity) -> UrlHealthCheck:

    async def _url_health_check(_: Optional[Any] = None) -> str | None:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != HTTPStatus.OK:
                    return f"{name} is returning error code {response.status}"
                return None

    return UrlHealthCheck(name=name, check=_url_health_check, severity=severity)


service_checks = [
    url_health_check("Power Hub API", POWER_HUB_API_URL, severity=Severity.CRITICAL),
    url_health_check("InfluxDB Health", INFLUXDB_URL, severity=Severity.CRITICAL),
    url_health_check("MQTT Health", MQTT_HEALTH_URL, severity=Severity.CRITICAL),
    url_health_check(
        "Front End Health", DISPLAY_HEALTH_URL, severity=Severity.CRITICAL
    ),
]
