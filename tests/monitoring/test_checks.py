from datetime import datetime
from unittest import mock

import pytest
from energy_box_control.monitoring.checks import (
    value_check,
    valid_temp,
    cloud_services_checks,
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


def test_urls_healty(mocker):
    mocker.patch.object(requests, "get", return_value=mock.Mock())
    requests.get().status_code = HTTPStatus.OK  # type: ignore
    for check in cloud_services_checks:
        assert check.check(None) == None


def test_urls_unhealthy(mocker):
    mocker.patch.object(requests, "get", return_value=mock.Mock())
    requests.get().status_code = HTTPStatus.FORBIDDEN  # type: ignore
    for check in cloud_services_checks:
        assert f"404 in {check.check(None)}"
