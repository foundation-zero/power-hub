from datetime import datetime
import json
from unittest import mock

import pytest
from energy_box_control.monitoring.checks import (
    value_check,
    valid_temp,
    service_checks,
)
from energy_box_control.power_hub.network import PowerHub, PowerHubSchedules
import requests
from http import HTTPStatus


def test_value_check():
    value_fn = lambda _value: 0
    check_fn = lambda value: value == 1
    name = "testing"
    value_check_fn = value_check(name, value_fn, check_fn)
    assert value_check_fn(100) == f"{name} is outside valid bounds with value: {0}"


def test_valid_temp():
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    check = valid_temp("testing", lambda sensors: sensors.pcm.temperature)
    assert not check.check(
        power_hub.sensors_from_state(power_hub.simple_initial_state())
    )


class MockResponse:
    def __init__(self, text, status):
        self._text = text
        self.status = status

    async def text(self):
        return self._text

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __aenter__(self):
        return self


@pytest.mark.asyncio
async def test_urls_healty(mocker):
    resp = MockResponse(json.dumps({}), HTTPStatus.OK)
    mocker.patch("aiohttp.ClientSession.get", return_value=resp)
    for check in service_checks:
        assert await check.check() == None


def test_urls_unhealthy(mocker):
    mocker.patch.object(requests, "get", return_value=mock.Mock())
    requests.get().status_code = HTTPStatus.FORBIDDEN  # type: ignore
    for check in service_checks:
        assert f"404 in {check.check()}"
