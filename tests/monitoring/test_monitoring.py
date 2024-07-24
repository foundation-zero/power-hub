from dataclasses import fields
from typing import get_type_hints
import pytest
from energy_box_control.monitoring.checks import (
    ValveAlarm,
    Severity,
    all_checks,
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
from energy_box_control.power_hub.sensors import (
    ContainersSensors,
    ElectricBatterySensors,
    PowerHubSensors,
    SwitchPumpSensors,
    ValveSensors,
)
from energy_box_control.sensors import Sensor, SensorType, attributes_for_type


@pytest.fixture
def power_hub():
    return PowerHub.power_hub(PowerHubSchedules.const_schedules())


@pytest.fixture
def sensors(power_hub):
    return power_hub.sensors_from_state(power_hub.simple_initial_state())


@pytest.fixture
def source():
    return "test"


def test_pcm_values_checks(sensors, source):
    pcm_fake_value = 1000
    sensors.pcm.temperature = pcm_fake_value
    monitor = Monitor(sensor_value_checks=all_checks)
    source = "test"
    assert monitor.run_sensor_value_checks(sensors, source)[0] == NotificationEvent(
        message=f"pcm_temperature_check is outside valid bounds with value: {pcm_fake_value}",
        source=source,
        dedup_key="pcm_temperature_check",
        severity=Severity.CRITICAL,
    )


def test_equal_bounds(sensors, source):
    sensors.hot_switch_valve.flow = 0
    sensors.hot_switch_valve.position = HOT_RESERVOIR_PCM_VALVE_PCM_POSITION
    monitor = Monitor(sensor_value_checks=all_checks)
    source = "test"
    assert len(monitor.run_sensor_value_checks(sensors, source)) == 0


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
    monitor = Monitor(sensor_value_checks=all_checks)
    source = "test"
    assert monitor.run_sensor_value_checks(sensors, source)[0] == NotificationEvent(
        message=f"{check_name} is outside valid bounds with value: {out_of_bounds_value}",
        source=source,
        dedup_key=check_name,
        severity=Severity.CRITICAL,
    )


def get_attrs(sensor, sensor_type):
    attrs = attributes_for_type(sensor, sensor_type)
    assert len(attrs) != 0
    return attrs


def test_battery_alarm_checks():
    for attr in get_attrs(ElectricBatterySensors, SensorType.ALARM):
        power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
        sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
        setattr(sensors.electric_battery, attr, 2)
        monitor = Monitor(sensor_value_checks=all_checks)
        source = "test"
        assert monitor.run_sensor_value_checks(sensors, source)[0] == NotificationEvent(
            message=f"{attr} is raising an alarm",
            source=source,
            dedup_key=f"{attr}",
            severity=Severity.CRITICAL,
        )


def test_battery_warning_checks():
    for attr in get_attrs(ElectricBatterySensors, SensorType.ALARM):
        power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
        sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
        setattr(sensors.electric_battery, attr, 1)
        monitor = Monitor(sensor_value_checks=all_checks)
        source = "test"
        assert monitor.run_sensor_value_checks(sensors, source)[0] == NotificationEvent(
            message=f"{attr}_warning is raising a warning",
            source=source,
            dedup_key=f"{attr}_warning",
            severity=Severity.WARNING,
        )


def test_fancoil_alarm_checks():
    for attr in get_attrs(ContainersSensors, SensorType.ALARM):
        power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
        sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
        setattr(sensors.containers, attr, 1)
        monitor = Monitor(sensor_value_checks=all_checks)
        source = "test"
        assert monitor.run_sensor_value_checks(sensors, source)[0] == NotificationEvent(
            message=f"{attr} is raising an alarm",
            source=source,
            dedup_key=attr,
            severity=Severity.CRITICAL,
        )


def test_fancoil_filter_checks():
    for attr in get_attrs(ContainersSensors, SensorType.REPLACE_FILTER_ALARM):
        power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
        sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
        setattr(sensors.containers, attr, 1)
        monitor = Monitor(sensor_value_checks=all_checks)
        source = "test"
        assert monitor.run_sensor_value_checks(sensors, source)[0] == NotificationEvent(
            message=f"{attr} gone bad",
            source=source,
            dedup_key=attr,
            severity=Severity.CRITICAL,
        )


def test_weather_station_alarm_checks():
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    alarm_value = 50
    sensors.weather.alarm = alarm_value
    monitor = Monitor(sensor_value_checks=all_checks)
    source = "test"
    assert monitor.run_sensor_value_checks(sensors, source)[0] == NotificationEvent(
        message=f"weather_station is raising an alarm with code {alarm_value}",
        source=source,
        dedup_key="weather_station",
        severity=Severity.CRITICAL,
    )


@pytest.mark.parametrize(
    "alarm,dedup_key",
    [
        (ValveAlarm.ACTUATOR_CANNOT_MOVE, "actuator"),
        (ValveAlarm.GEAR_TRAIN_DISENGAGED, "gear_train"),
    ],
)
def test_valve_alarm_checks(alarm, dedup_key):
    for valve_name in [
        field.name
        for field in fields(PowerHubSensors)
        if field.type == ValveSensors or issubclass(field.type, ValveSensors)
    ]:
        power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
        sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
        setattr(getattr(sensors, valve_name), "service_info", alarm.value)
        monitor = Monitor(sensor_value_checks=all_checks)
        source = "test"
        assert monitor.run_sensor_value_checks(sensors, source)[0] == NotificationEvent(
            message=f"{valve_name}_{dedup_key}_alarm is raised",
            source=source,
            dedup_key=f"{valve_name}_{dedup_key}_alarm",
            severity=Severity.CRITICAL,
        )


def test_pump_alarm_checks():
    pump_names = [
        appliance_name
        for appliance_name, type in get_type_hints(PowerHubSensors).items()
        if type == SwitchPumpSensors
    ]
    assert len(pump_names) != 0
    for pump_name in pump_names:
        for attr in get_attrs(SwitchPumpSensors, SensorType.ALARM):
            power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
            sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
            alarm_code = 50
            setattr(getattr(sensors, pump_name), attr, alarm_code)
            monitor = Monitor(sensor_value_checks=all_checks)
            source = "test"
            assert monitor.run_sensor_value_checks(sensors, source)[
                0
            ] == NotificationEvent(
                message=f"{pump_name}_{attr} is raising an alarm with code {alarm_code}",
                source=source,
                dedup_key=f"{pump_name}_{attr}",
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
    monitor = Monitor(sensor_value_checks=all_checks)
    assert monitor.run_sensor_value_checks(sensors, source, control, power_hub)[
        0
    ] == NotificationEvent(
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
    monitor = Monitor(sensor_value_checks=all_checks)
    assert (
        len(monitor.run_sensor_value_checks(sensors, source, control, power_hub)) == 0
    )


@pytest.mark.parametrize(
    "water_tank,invalid_tank_fill",
    [
        ("grey_water_tank", 1.1),
        ("fresh_water_tank", 1),
        ("technical_water_tank", 1),
        ("black_water_tank", 1),
    ],
)
def test_tank_checks(water_tank: str, invalid_tank_fill: int):
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    setattr(getattr(sensors, water_tank), "fill_ratio", invalid_tank_fill)
    monitor = Monitor(sensor_value_checks=all_checks)
    source = "test"
    assert monitor.run_sensor_value_checks(sensors, source)[0] == NotificationEvent(
        message=f"{water_tank}_fill_ratio is outside valid bounds with value: {invalid_tank_fill}",
        source=source,
        dedup_key=f"{water_tank}_fill_ratio",
        severity=Severity.CRITICAL,
    )


@pytest.mark.parametrize(
    "sensor_type,alerting_value",
    [
        (SensorType.CO2, 3),
        (SensorType.HUMIDITY, 3),
        (SensorType.TEMPERATURE, 100),
    ],
)
def test_container_sensor_values(sensor_type, alerting_value):
    for attr in get_attrs(ContainersSensors, sensor_type):
        power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
        sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
        setattr(sensors.containers, attr, alerting_value)
        monitor = Monitor(sensor_value_checks=all_checks)
        source = "test"
        assert monitor.run_sensor_value_checks(sensors, source)[0] == NotificationEvent(
            message=f"{attr} is outside valid bounds with value: {alerting_value}",
            source=source,
            dedup_key=attr,
            severity=Severity.CRITICAL,
        )


def test_send_events(mocker):
    channel = PagerDutyNotificationChannel("test")
    mocker.patch.object(channel, "send_event")
    notifier = Notifier([channel])
    notifier.send_events([NotificationEvent("test", "test", "test", Severity.CRITICAL)])
    channel.send_event.assert_called_once()  # type: ignore
