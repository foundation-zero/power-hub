from dataclasses import fields
from typing import List
import pytest
from energy_box_control.monitoring.checks import (
    SensorValueCheck,
    sensor_checks,
    Severity,
    battery_alarm_checks,
    battery_warning_checks,
    container_fancoil_alarm_checks,
    containers_fancoil_filter_checks,
    container_co2_checks,
    container_humidity_checks,
    container_temperature_checks,
    water_tank_checks,
    pump_alarm_checks,
    yazaki_bound_checks,
    weather_station_alarm_checks,
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
from energy_box_control.power_hub.components import HOT_RESERVOIR_PCM_VALVE_PCM_POSITION
from energy_box_control.power_hub.network import PowerHub, PowerHubSchedules
from energy_box_control.power_hub.sensors import ContainersSensors, PowerHubSensors
from energy_box_control.sensors import Sensor, SensorType


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
    source = "test"
    assert monitor.run_appliance_checks(sensors, source)[0] == NotificationEvent(
        message=f"pcm_temperature_check is outside valid bounds with value: {pcm_fake_value}",
        source=source,
        dedup_key="pcm_temperature_check",
        severity=Severity.CRITICAL,
    )


def test_battery_alarm_checks():
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    sensors.electric_battery.battery_fuse_blown_alarm = 2
    monitor = Monitor(appliance_checks=battery_alarm_checks)
    source = "test"
    assert monitor.run_appliance_checks(sensors, source)[0] == NotificationEvent(
        message=f"battery_fuse_blown_alarm is raising an alarm",
        source=source,
        dedup_key="battery_fuse_blown_alarm",
        severity=Severity.CRITICAL,
    )


def test_battery_warning_checks():
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    sensors.electric_battery.battery_fuse_blown_alarm = 1
    monitor = Monitor(appliance_checks=battery_warning_checks)
    source = "test"
    assert monitor.run_appliance_checks(sensors, source)[0] == NotificationEvent(
        message=f"battery_fuse_blown_alarm_warning is raising a warning",
        source=source,
        dedup_key="battery_fuse_blown_alarm_warning",
        severity=Severity.WARNING,
    )


@pytest.mark.parametrize(
    "fancoil_alarm",
    [
        "simulator_storage_ventilation_error",
        "office_ventilation_error",
        "kitchen_ventilation_error",
    ],
)
def test_fancoil_alarm_checks(fancoil_alarm: str):
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    setattr(sensors.containers, fancoil_alarm, 1)
    monitor = Monitor(appliance_checks=container_fancoil_alarm_checks)
    source = "test"
    assert monitor.run_appliance_checks(sensors, source)[0] == NotificationEvent(
        message=f"{fancoil_alarm} is raising an alarm",
        source=source,
        dedup_key=fancoil_alarm,
        severity=Severity.CRITICAL,
    )


@pytest.mark.parametrize(
    "water_tank,invalid_tank_fill",
    [
        ("grey_water_tank", 110),
        ("fresh_water_tank", 10),
        ("technical_water_tank", 10),
        ("black_water_tank", 100),
    ],
)
def test_tank_checks(water_tank: str, invalid_tank_fill: int):
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    setattr(getattr(sensors, water_tank), "percentage_fill", invalid_tank_fill)
    monitor = Monitor(appliance_checks=water_tank_checks)
    source = "test"
    assert monitor.run_appliance_checks(sensors, source)[0] == NotificationEvent(
        message=f"{water_tank}_percentage_fill is outside valid bounds with value: {invalid_tank_fill}",
        source=source,
        dedup_key=f"{water_tank}_percentage_fill",
        severity=Severity.CRITICAL,
    )


@pytest.mark.parametrize(
    "filter_property",
    [
        "simulator_storage_ventilation_filter_status",
        "office_ventilation_filter_status",
        "kitchen_ventilation_filter_status",
    ],
)
def test_fancoil_filter_checks(filter_property: str):
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    setattr(sensors.containers, filter_property, 1)
    monitor = Monitor(appliance_checks=containers_fancoil_filter_checks)
    source = "test"
    assert monitor.run_appliance_checks(sensors, source)[0] == NotificationEvent(
        message=f"{filter_property} gone bad",
        source=source,
        dedup_key=filter_property,
        severity=Severity.CRITICAL,
    )


@pytest.mark.parametrize(
    "sensor_type,alerting_value,checks,severity",
    [
        (SensorType.CO2, 3, container_co2_checks, Severity.CRITICAL),
        (SensorType.HUMIDITY, 3, container_humidity_checks, Severity.ERROR),
        (SensorType.TEMPERATURE, 100, container_temperature_checks, Severity.CRITICAL),
    ],
)
def test_container_sensor_valules(
    sensor_type, alerting_value: int, checks: List[SensorValueCheck], severity
):
    for attr in [
        attr
        for attr in dir(ContainersSensors)
        if isinstance(getattr(ContainersSensors, attr), Sensor)
        and getattr(ContainersSensors, attr).type == sensor_type
    ]:
        power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
        sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
        setattr(sensors.containers, attr, alerting_value)
        monitor = Monitor(appliance_checks=checks)
        source = "test"
        assert monitor.run_appliance_checks(sensors, source)[0] == NotificationEvent(
            message=f"{attr} is outside valid bounds with value: {alerting_value}",
            source=source,
            dedup_key=attr,
            severity=severity,
        )


def test_pump_alarm_checks():
    for pump_name in [
        field.name for field in fields(PowerHubSensors) if "pump" in field.name
    ]:
        power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
        sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
        attr_name = "pump_1_alarm"
        alarm_code = 50
        setattr(getattr(sensors, pump_name), attr_name, alarm_code)
        monitor = Monitor(appliance_checks=pump_alarm_checks)
        source = "test"
        assert monitor.run_appliance_checks(sensors, source)[0] == NotificationEvent(
            message=f"{pump_name}_{attr_name} is raising an alarm with code {alarm_code}",
            source=source,
            dedup_key=f"{pump_name}_{attr_name}",
            severity=Severity.CRITICAL,
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
    "attr,check_name,valve_name,valve_attr,valve_position",
    [
        (
            "charge_input_temperature",
            "hot_circuit_temperature_check",
            "hot_switch_valve",
            "input_temperature",
            HOT_RESERVOIR_PCM_VALVE_PCM_POSITION,
        ),
        (
            "charge_flow",
            "hot_circuit_flow_check",
            "hot_switch_valve",
            "flow",
            HOT_RESERVOIR_PCM_VALVE_PCM_POSITION,
        ),
        (
            "charge_pressure",
            "hot_circuit_pressure_check",
            "hot_switch_valve",
            "pressure",
            HOT_RESERVOIR_PCM_VALVE_PCM_POSITION,
        ),
        ("temperature", "pcm_temperature_check", None, None, None),
    ],
)
def test_hot_circuit_checks(
    attr, check_name, valve_name, valve_attr, valve_position, out_of_bounds_value
):
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    if valve_name and valve_position is not None and valve_attr:
        setattr(getattr(sensors, valve_name), valve_attr, out_of_bounds_value)
        setattr(getattr(sensors, valve_name), "position", valve_position)
    else:
        setattr(sensors.pcm, attr, out_of_bounds_value)
    monitor = Monitor(appliance_checks=sensor_checks)
    source = "test"
    assert monitor.run_appliance_checks(sensors, source)[0] == NotificationEvent(
        message=f"{check_name} is outside valid bounds with value: {out_of_bounds_value}",
        source=source,
        dedup_key=check_name,
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


def test_weather_station_alarm_checks():
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    alarm_value = 50
    sensors.weather.alarm = alarm_value
    monitor = Monitor(appliance_checks=weather_station_alarm_checks)
    source = "test"
    assert monitor.run_appliance_checks(sensors, source)[0] == NotificationEvent(
        message=f"weather_station is raising an alarm with code {alarm_value}",
        source=source,
        dedup_key="weather_station",
        severity=Severity.ERROR,
    )


def test_send_events(mocker):
    channel = PagerDutyNotificationChannel("test")
    mocker.patch.object(channel, "send_event")
    notifier = Notifier([channel])
    notifier.send_events([NotificationEvent("test", "test", "test", Severity.CRITICAL)])
    channel.send_event.assert_called_once()  # type: ignore
