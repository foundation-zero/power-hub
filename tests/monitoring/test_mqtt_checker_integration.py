from asyncio import CancelledError
from unittest.mock import MagicMock

import pytest

from energy_box_control.monitoring.checks import Severity
from energy_box_control.monitoring.monitoring import NotificationEvent
from energy_box_control.monitoring.mqtt_checker import MQTTChecker


@pytest.mark.integration
@pytest.mark.asyncio(timeout=5)
async def test_timeout_on_silent_topic():
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
        await mqtt_checker.run()
        assert False  # Unreachable
    except CancelledError:
        pass

    notifier_mock.send_events.assert_called_once_with(expected_event)
