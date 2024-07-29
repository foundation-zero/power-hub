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
    source = "test"
    assert run_monitor(sensors, source) == [
        NotificationEvent(
            message=f"pcm_temperature_check is outside valid bounds with value: {pcm_fake_value}",
            source=source,
            dedup_key="pcm_temperature_check",
            severity=Severity.CRITICAL,
        )
    ]


def test_equal_bounds(sensors, source):
    sensors.hot_switch_valve.flow = 0
    sensors.hot_switch_valve.position = HOT_RESERVOIR_PCM_VALVE_PCM_POSITION
    source = "test"
    assert not run_monitor(sensors, source)


def run_monitor(sensors, source, control=None, power_hub=None):
    monitor = Monitor(sensor_value_checks=all_checks, url_health_checks=[])
    return monitor.run_sensor_value_checks(sensors, source, control, power_hub)


def test_hot_circuit_hot_circuit_temperature_check(
    sensors: PowerHubSensors, source, out_of_bounds_value
):
    sensors.rh33_hot_storage.hot_temperature = out_of_bounds_value
    assert run_monitor(sensors, source) == [
        NotificationEvent(
            message=f"hot_circuit_temperature_check is outside valid bounds with value: {out_of_bounds_value}",
            source=source,
            dedup_key="hot_circuit_temperature_check",
            severity=Severity.CRITICAL,
        )
    ]


def test_hot_circuit_flow_check(sensors: PowerHubSensors, source, out_of_bounds_value):
    sensors.hot_switch_valve.flow = out_of_bounds_value
    sensors.hot_switch_valve.position = HOT_RESERVOIR_PCM_VALVE_PCM_POSITION
    assert run_monitor(sensors, source) == [
        NotificationEvent(
            message=f"hot_circuit_flow_check is outside valid bounds with value: {out_of_bounds_value}",
            source=source,
            dedup_key="hot_circuit_flow_check",
            severity=Severity.CRITICAL,
        )
    ]


def test_hot_circuit_pressure_check(
    sensors: PowerHubSensors, source, out_of_bounds_value
):
    sensors.hot_switch_valve.pressure = out_of_bounds_value
    sensors.hot_switch_valve.position = HOT_RESERVOIR_PCM_VALVE_PCM_POSITION
    assert run_monitor(sensors, source) == [
        NotificationEvent(
            message=f"hot_circuit_pressure_check is outside valid bounds with value: {out_of_bounds_value}",
            source=source,
            dedup_key="hot_circuit_pressure_check",
            severity=Severity.CRITICAL,
        )
    ]


def test_pcm_temperature_check(sensors: PowerHubSensors, source, out_of_bounds_value):
    sensors.pcm.temperature = out_of_bounds_value
    assert run_monitor(sensors, source) == [
        NotificationEvent(
            message=f"pcm_temperature_check is outside valid bounds with value: {out_of_bounds_value}",
            source=source,
            dedup_key="pcm_temperature_check",
            severity=Severity.CRITICAL,
        )
    ]


def get_attrs(sensor, sensor_type):
    attrs = attributes_for_type(sensor, sensor_type)
    assert len(attrs) != 0
    return attrs


def test_battery_alarm_checks():
    for attr in get_attrs(ElectricBatterySensors, SensorType.ALARM):
        power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
        sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
        setattr(sensors.electric_battery, attr, 2)
        source = "test"
        assert run_monitor(sensors, source) == [
            NotificationEvent(
                message=f"{attr} is raising an alarm",
                source=source,
                dedup_key=f"{attr}",
                severity=Severity.CRITICAL,
            )
        ]


def test_battery_warning_checks():
    for attr in get_attrs(ElectricBatterySensors, SensorType.ALARM):
        power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
        sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
        setattr(sensors.electric_battery, attr, 1)
        source = "test"
        assert run_monitor(sensors, source) == [
            NotificationEvent(
                message=f"{attr}_warning is raising a warning",
                source=source,
                dedup_key=f"{attr}_warning",
                severity=Severity.WARNING,
            )
        ]


def test_fancoil_alarm_checks():
    for attr in get_attrs(ContainersSensors, SensorType.ALARM):
        power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
        sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
        setattr(sensors.containers, attr, 1)
        source = "test"
        assert run_monitor(sensors, source) == [
            NotificationEvent(
                message=f"{attr} is raising an alarm",
                source=source,
                dedup_key=attr,
                severity=Severity.CRITICAL,
            )
        ]


def test_fancoil_filter_checks():
    for attr in get_attrs(ContainersSensors, SensorType.REPLACE_FILTER_ALARM):
        power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
        sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
        setattr(sensors.containers, attr, 1)
        source = "test"
        assert run_monitor(sensors, source) == [
            NotificationEvent(
                message=f"{attr} gone bad",
                source=source,
                dedup_key=attr,
                severity=Severity.CRITICAL,
            )
        ]


def test_weather_station_alarm_checks():
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    alarm_value = 50
    sensors.weather.alarm = alarm_value
    source = "test"
    assert run_monitor(sensors, source) == [
        NotificationEvent(
            message=f"weather_station is raising an alarm with code {alarm_value}",
            source=source,
            dedup_key="weather_station",
            severity=Severity.CRITICAL,
        )
    ]


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
        source = "test"
        assert run_monitor(sensors, source) == [
            NotificationEvent(
                message=f"{valve_name}_{dedup_key}_alarm is raised",
                source=source,
                dedup_key=f"{valve_name}_{dedup_key}_alarm",
                severity=Severity.CRITICAL,
            )
        ]


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
            source = "test"
            assert run_monitor(sensors, source) == [
                NotificationEvent(
                    message=f"{pump_name}_{attr} is raising an alarm with code {alarm_code}",
                    source=source,
                    dedup_key=f"{pump_name}_{attr}",
                    severity=Severity.CRITICAL,
                )
            ]


@pytest.fixture
def out_of_bounds_value():
    return 10000


@pytest.fixture
def control(power_hub):
    return no_control(power_hub)


@pytest.fixture
def yazaki_on(power_hub, control):
    return control.replace_control(power_hub.yazaki, "on", True)


@pytest.fixture
def yazaki_off(power_hub, control):
    return control.replace_control(power_hub.yazaki, "on", False)


@pytest.fixture
def yazaki_test(
    power_hub,
    sensors: PowerHubSensors,
    yazaki_on,
    yazaki_off,
    source,
    out_of_bounds_value,
):
    def _test(dedup_key):
        assert not run_monitor(sensors, source, yazaki_off, power_hub)
        assert run_monitor(sensors, source, yazaki_on, power_hub) == [
            NotificationEvent(
                message=f"{dedup_key} is outside valid bounds with value: {out_of_bounds_value}",
                source=source,
                dedup_key=dedup_key,
                severity=Severity.CRITICAL,
            )
        ]

    return _test


def test_yazaki_hot_input_temperature_check(sensors, yazaki_test, out_of_bounds_value):
    sensors.rh33_yazaki_hot.hot_temperature = out_of_bounds_value
    yazaki_test("yazaki_hot_input_temperature_check")


def test_yazaki_hot_flow_check(sensors, yazaki_test, out_of_bounds_value):
    sensors.yazaki.hot_flow = out_of_bounds_value
    yazaki_test("yazaki_hot_flow_check")


def test_yazaki_hot_pressure_check(sensors, yazaki_test, out_of_bounds_value):
    sensors.yazaki.hot_pressure = out_of_bounds_value
    yazaki_test("yazaki_hot_pressure_check")


def test_yazaki_waste_input_temperature_check(
    sensors, yazaki_test, out_of_bounds_value
):
    sensors.rh33_waste.cold_temperature = out_of_bounds_value
    sensors.waste_switch_valve.position = WASTE_SWITCH_VALVE_YAZAKI_POSITION
    yazaki_test("yazaki_waste_input_temperature_check")


def test_yazaki_waste_flow_check(sensors, yazaki_test, out_of_bounds_value):
    sensors.waste_mix.flow = out_of_bounds_value
    sensors.waste_switch_valve.position = WASTE_SWITCH_VALVE_YAZAKI_POSITION
    yazaki_test("yazaki_waste_flow_check")


def test_yazaki_waste_pressure_check(sensors, yazaki_test, out_of_bounds_value):
    sensors.waste_switch_valve.pressure = out_of_bounds_value
    sensors.waste_switch_valve.position = WASTE_SWITCH_VALVE_YAZAKI_POSITION
    yazaki_test("yazaki_waste_pressure_check")


def test_yazaki_chilled_input_temperature_check(
    sensors, yazaki_test, out_of_bounds_value
):
    sensors.rh33_chill.hot_temperature = out_of_bounds_value
    sensors.chiller_switch_valve.position = WASTE_SWITCH_VALVE_YAZAKI_POSITION
    yazaki_test("yazaki_chilled_input_temperature_check")


def test_yazaki_chilled_flow_check(sensors, yazaki_test, out_of_bounds_value):
    sensors.cold_reservoir.exchange_flow = out_of_bounds_value
    sensors.chiller_switch_valve.position = WASTE_SWITCH_VALVE_YAZAKI_POSITION
    yazaki_test("yazaki_chilled_flow_check")


def test_yazaki_chilled_pressure_check(sensors, yazaki_test, out_of_bounds_value):
    sensors.chilled_loop_pump.pressure = out_of_bounds_value
    sensors.chiller_switch_valve.position = WASTE_SWITCH_VALVE_YAZAKI_POSITION
    yazaki_test("yazaki_chilled_pressure_check")


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
    monitor = Monitor(sensor_value_checks=all_checks, url_health_checks=[])
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
        monitor = Monitor(sensor_value_checks=all_checks, url_health_checks=[])
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
