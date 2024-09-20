import asyncio
from asyncio import CancelledError
from unittest.mock import MagicMock

import pytest

from energy_box_control.amqtt import get_mqtt_client
from energy_box_control.monitoring.checks import Severity
from energy_box_control.monitoring.monitoring import NotificationEvent
from energy_box_control.monitoring.mqtt_checker import MQTTChecker, logger
from energy_box_control.power_hub_control import SENSOR_VALUES_TOPIC


@pytest.fixture
async def mqtt_client():
    async with get_mqtt_client(logger) as client:
        yield client


@pytest.mark.integration
@pytest.mark.asyncio(timeout=5)
async def test_timeout_on_silent_topic(mqtt_client):
    expected_event = [
        NotificationEvent(
            f"Did not receive nonexistent values for 2 seconds.",
            "MQTT listener check",
            f"mqtt-listener-check-nonexistent-values",
            Severity.CRITICAL,
        )
    ]
    notifier_mock = MagicMock()
    # Async event loop is shut down after single call
    notifier_mock.send_events.side_effect = [CancelledError()]

    mqtt_checker = MQTTChecker(notifier_mock, "nonexistent", timeout=2)
    try:
        await mqtt_checker.run(mqtt_client)
        assert False  # Unreachable
    except CancelledError:
        pass

    notifier_mock.send_events.assert_called_once_with(expected_event)


@pytest.mark.integration
@pytest.mark.asyncio(timeout=15)
async def test_no_timeout_on_real_topic(mqtt_client):
    notifier_mock = MagicMock()
    mqtt_checker = MQTTChecker(notifier_mock, SENSOR_VALUES_TOPIC, timeout=11)
    async with asyncio.timeout(12):
        await mqtt_checker.run(mqtt_client)

    notifier_mock.send_events.assert_not_called()
