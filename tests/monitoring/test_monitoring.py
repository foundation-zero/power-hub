import pytest
from energy_box_control.monitoring.checks import (
    sensor_checks,
    Severity,
    alarm_checks,
    warning_checks,
    yazaki_bound_checks,
)
from energy_box_control.monitoring.monitoring import (
    NotificationEvent,
    PagerDutyNotificationChannel,
    Monitor,
    Notifier,
)
from energy_box_control.power_hub.components import (
    CHILLER_SWITCH_VALVE_YAZAKI_POSITION,
    WASTE_SWITCH_VALVE_YAZAKI_POSITION,
)
from energy_box_control.power_hub.control import no_control
from energy_box_control.power_hub.network import PowerHub, PowerHubSchedules


@pytest.fixture
def power_hub():
    return PowerHub.power_hub(PowerHubSchedules.const_schedules())


@pytest.fixture
def sensors(power_hub):
    return power_hub.sensors_from_state(power_hub.simple_initial_state())


@pytest.fixture
def source():
    return "test"


def test_run_sensor_values_checks(sensors, source):
    pcm_fake_value = 1000
    sensors.pcm.temperature = pcm_fake_value
    monitor = Monitor(sensor_checks)
    assert monitor.run_sensor_values_checks(sensors, source)[0] == NotificationEvent(
        message=f"pcm_temperature_check is outside valid bounds with value: {pcm_fake_value}",
        source=source,
        dedup_key="pcm_temperature_check",
        severity=Severity.ERROR,
    )


def test_alarm_checks(sensors, source):
    sensors.electric_battery.battery_fuse_blown_alarm = 2
    monitor = Monitor(alarm_checks=alarm_checks)
    assert monitor.run_alarm_checks(sensors, source)[0] == NotificationEvent(
        message=f"battery_fuse_blown_alarm is raising an alarm",
        source=source,
        dedup_key="battery_fuse_blown_alarm",
        severity=Severity.CRITICAL,
    )


def test_warning_checks(sensors, source):
    sensors.electric_battery.battery_fuse_blown_alarm = 1
    monitor = Monitor(alarm_checks=warning_checks)
    assert monitor.run_alarm_checks(sensors, source)[0] == NotificationEvent(
        message=f"battery_fuse_blown_alarm_warning is raising a warning",
        source=source,
        dedup_key="battery_fuse_blown_alarm_warning",
        severity=Severity.WARNING,
    )


@pytest.fixture
def out_of_bounds_value():
    return 10000


@pytest.fixture
def control(power_hub):
    return no_control(power_hub)


@pytest.mark.parametrize(
    "yazaki_attr,valve_name,valve_attr,valve_position",
    [
        ("hot_input_temperature", None, None, None),
        ("hot_flow", None, None, None),
        ("hot_pressure", None, None, None),
        (
            "cooling_input_temperature",
            "waste_switch_valve",
            "input_temperature",
            WASTE_SWITCH_VALVE_YAZAKI_POSITION,
        ),
        (
            "cooling_flow",
            "preheat_switch_valve",
            "input_flow",
            WASTE_SWITCH_VALVE_YAZAKI_POSITION,
        ),
        (
            "cooling_pressure",
            "preheat_switch_valve",
            "pressure",
            WASTE_SWITCH_VALVE_YAZAKI_POSITION,
        ),
        (
            "chilled_input_temperature",
            "chiller_switch_valve",
            "input_temperature",
            CHILLER_SWITCH_VALVE_YAZAKI_POSITION,
        ),
        (
            "chilled_flow",
            "cold_reservoir",
            "exchange_flow",
            CHILLER_SWITCH_VALVE_YAZAKI_POSITION,
        ),
        (
            "chilled_pressure",
            "chilled_loop_pump",
            "pressure",
            CHILLER_SWITCH_VALVE_YAZAKI_POSITION,
        ),
    ],
)
def test_yazaki_health_bound_checks(
    yazaki_attr: str,
    valve_name: str,
    valve_attr: str,
    valve_position: float,
    out_of_bounds_value: int,
    power_hub,
    sensors,
    control,
    source,
):
    control = control.replace_control(power_hub.yazaki, "on", True)
    if valve_attr and valve_position is not None and valve_name:
        setattr(getattr(sensors, valve_name), valve_attr, out_of_bounds_value)
        setattr(getattr(sensors, valve_name), "position", valve_position)
    else:
        setattr(sensors.yazaki, yazaki_attr, out_of_bounds_value)
    monitor = Monitor(appliance_sensor_value_checks=yazaki_bound_checks)
    assert monitor.run_appliance_sensor_value_checks(
        sensors, control, power_hub, source
    )[0] == NotificationEvent(
        message=f"yazaki_{yazaki_attr}_check is outside valid bounds with value: {out_of_bounds_value}",
        source=source,
        dedup_key=f"yazaki_{yazaki_attr}_check",
        severity=Severity.CRITICAL,
    )


@pytest.mark.parametrize(
    "yazaki_attr,valve_name,valve_attr,valve_position",
    [
        ("hot_input_temperature", None, None, None),
        ("hot_flow", None, None, None),
        ("hot_pressure", None, None, None),
        (
            "cooling_input_temperature",
            "waste_switch_valve",
            "input_temperature",
            WASTE_SWITCH_VALVE_YAZAKI_POSITION,
        ),
        (
            "cooling_flow",
            "preheat_switch_valve",
            "input_flow",
            WASTE_SWITCH_VALVE_YAZAKI_POSITION,
        ),
        (
            "cooling_pressure",
            "preheat_switch_valve",
            "pressure",
            WASTE_SWITCH_VALVE_YAZAKI_POSITION,
        ),
        (
            "chilled_input_temperature",
            "chiller_switch_valve",
            "input_temperature",
            CHILLER_SWITCH_VALVE_YAZAKI_POSITION,
        ),
        (
            "chilled_flow",
            "cold_reservoir",
            "exchange_flow",
            CHILLER_SWITCH_VALVE_YAZAKI_POSITION,
        ),
        (
            "chilled_pressure",
            "chilled_loop_pump",
            "pressure",
            CHILLER_SWITCH_VALVE_YAZAKI_POSITION,
        ),
    ],
)
def test_yazaki_property_health_bound_checks_yazaki_off(
    yazaki_attr: str,
    valve_name: str,
    valve_attr: str,
    valve_position: float,
    out_of_bounds_value: int,
    power_hub,
    sensors,
    control,
    source,
):
    control = control.replace_control(power_hub.yazaki, "on", False)
    if valve_attr and valve_position is not None and valve_name:
        setattr(getattr(sensors, valve_name), valve_attr, out_of_bounds_value)
        setattr(getattr(sensors, valve_name), "position", valve_position)
    else:
        setattr(sensors.yazaki, yazaki_attr, out_of_bounds_value)
    monitor = Monitor(appliance_sensor_value_checks=yazaki_bound_checks)
    assert (
        len(
            monitor.run_appliance_sensor_value_checks(
                sensors, control, power_hub, source
            )
        )
        == 0
    )


def test_send_events(mocker):
    channel = PagerDutyNotificationChannel("test")
    mocker.patch.object(channel, "send_event")
    notifier = Notifier([channel])
    notifier.send_events([NotificationEvent("test", "test", "test", Severity.CRITICAL)])
    channel.send_event.assert_called_once()  # type: ignore
