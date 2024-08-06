from dataclasses import fields
from typing import get_type_hints
import pytest
from energy_box_control.monitoring.checks import (
    ChillerAlarm,
    FlowSensorAlarm,
    RH33AlarmLowerBitsValues,
    RH33AlarmUpperBits,
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
    CHILLER_SWITCH_VALVE_CHILLER_POSITION,
    WASTE_SWITCH_VALVE_CHILLER_POSITION,
    WASTE_SWITCH_VALVE_YAZAKI_POSITION,
)
from energy_box_control.power_hub.control import no_control
from energy_box_control.power_hub.components import HOT_RESERVOIR_PCM_VALVE_PCM_POSITION
from energy_box_control.power_hub.network import PowerHub, PowerHubSchedules
from energy_box_control.power_hub.sensors import (
    ContainersSensors,
    ElectricalSensors,
    FlowSensors,
    PowerHubSensors,
    SmartPumpSensors,
    RH33Sensors,
    ValveSensors,
)
from energy_box_control.sensors import (
    Sensor,
    SensorType,
    attributes_for_type,
    sensor_encoder,
)


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
    assert not run_monitor(sensors, source)


def run_monitor(sensors, source, control=None, power_hub=None):
    monitor = Monitor(sensor_value_checks=all_checks, url_health_checks=[])
    return monitor.run_sensor_value_checks(sensors, source, control, power_hub)


def test_hot_circuit_temperature_check(
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
    sensors.hot_storage_flow_sensor.flow = out_of_bounds_value
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
    sensors.pipes_pressure_sensor.pressure = out_of_bounds_value
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


def test_chilled_circuit_temperature_check(
    sensors: PowerHubSensors, source, out_of_bounds_value
):
    sensors.rh33_chill.cold_temperature = out_of_bounds_value
    assert run_monitor(sensors, source) == [
        NotificationEvent(
            message=f"chilled_circuit_temperature_check is outside valid bounds with value: {out_of_bounds_value}",
            source=source,
            dedup_key="chilled_circuit_temperature_check",
            severity=Severity.CRITICAL,
        )
    ]


def test_chilled_circuit_flow_check(
    sensors: PowerHubSensors, source, out_of_bounds_value
):
    sensors.chilled_flow_sensor.flow = out_of_bounds_value
    assert run_monitor(sensors, source) == [
        NotificationEvent(
            message=f"chilled_circuit_flow_check is outside valid bounds with value: {out_of_bounds_value}",
            source=source,
            dedup_key="chilled_circuit_flow_check",
            severity=Severity.CRITICAL,
        )
    ]


def test_chilled_circuit_pressure_check(
    sensors: PowerHubSensors, source, out_of_bounds_value
):
    sensors.chilled_loop_pump.pressure = out_of_bounds_value
    assert run_monitor(sensors, source) == [
        NotificationEvent(
            message=f"chilled_circuit_pressure_check is outside valid bounds with value: {out_of_bounds_value}",
            source=source,
            dedup_key="chilled_circuit_pressure_check",
            severity=Severity.CRITICAL,
        )
    ]


def test_cooling_demand_circuit_temperature_check(
    sensors: PowerHubSensors, source, out_of_bounds_value
):
    sensors.rh33_cooling_demand.cold_temperature = out_of_bounds_value
    assert run_monitor(sensors, source) == [
        NotificationEvent(
            message=f"cooling_demand_circuit_temperature_check is outside valid bounds with value: {out_of_bounds_value}",
            source=source,
            dedup_key="cooling_demand_circuit_temperature_check",
            severity=Severity.CRITICAL,
        )
    ]


def test_cooling_demand_circuit_flow_check(
    sensors: PowerHubSensors, source, out_of_bounds_value
):
    sensors.cooling_demand_flow_sensor.flow = out_of_bounds_value
    assert run_monitor(sensors, source) == [
        NotificationEvent(
            message=f"cooling_demand_circuit_flow_check is outside valid bounds with value: {out_of_bounds_value}",
            source=source,
            dedup_key="cooling_demand_circuit_flow_check",
            severity=Severity.CRITICAL,
        )
    ]


def test_cooling_demand_circuit_pressure_check(
    sensors: PowerHubSensors, source, out_of_bounds_value
):
    sensors.cooling_demand_pump.pressure = out_of_bounds_value
    assert run_monitor(sensors, source) == [
        NotificationEvent(
            message=f"cooling_demand_circuit_pressure_check is outside valid bounds with value: {out_of_bounds_value}",
            source=source,
            dedup_key="cooling_demand_circuit_pressure_check",
            severity=Severity.CRITICAL,
        )
    ]


def test_heat_pipes_temperature_check(
    sensors: PowerHubSensors, source, out_of_bounds_value
):
    sensors.rh33_heat_pipes.hot_temperature = out_of_bounds_value
    assert run_monitor(sensors, source) == [
        NotificationEvent(
            message=f"heat_pipes_temperature_check is outside valid bounds with value: {out_of_bounds_value}",
            source=source,
            dedup_key="heat_pipes_temperature_check",
            severity=Severity.CRITICAL,
        )
    ]


def test_heat_pipes_flow_check(sensors: PowerHubSensors, source, out_of_bounds_value):
    sensors.heat_pipes_flow_sensor.flow = out_of_bounds_value
    assert run_monitor(sensors, source) == [
        NotificationEvent(
            message=f"heat_pipes_flow_check is outside valid bounds with value: {out_of_bounds_value}",
            source=source,
            dedup_key="heat_pipes_flow_check",
            severity=Severity.CRITICAL,
        )
    ]


def get_attrs(sensor, sensor_type):
    attrs = attributes_for_type(sensor, sensor_type)
    assert len(attrs) != 0
    return attrs


def test_battery_alarm_checks(source):
    for attr in get_attrs(ElectricalSensors, SensorType.ALARM):
        power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
        sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
        setattr(sensors.electrical, attr, 2)
        assert run_monitor(sensors, source) == [
            NotificationEvent(
                message=f"{attr} is raising an alarm",
                source=source,
                dedup_key=f"{attr}",
                severity=Severity.CRITICAL,
            )
        ]


def test_battery_warning_checks(source):
    for attr in get_attrs(ElectricalSensors, SensorType.ALARM):
        power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
        sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
        setattr(sensors.electrical, attr, 1)
        assert run_monitor(sensors, source) == [
            NotificationEvent(
                message=f"{attr}_warning is raising a warning",
                source=source,
                dedup_key=f"{attr}_warning",
                severity=Severity.WARNING,
            )
        ]


def test_battery_soc_checks(source):
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    value = 25
    sensors.electrical.soc_battery_system = value
    assert run_monitor(sensors, source) == [
        NotificationEvent(
            message=f"battery_soc is outside valid bounds with value: {value}",
            source=source,
            dedup_key="battery_soc",
            severity=Severity.CRITICAL,
        )
    ]


def test_battery_estop_checks(source):
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    sensors.electrical.estop_active = True
    assert run_monitor(sensors, source) == [
        NotificationEvent(
            message=f"estop active is {True}",
            source=source,
            dedup_key="estop_active",
            severity=Severity.CRITICAL,
        )
    ]


def test_fancoil_alarm_checks(source):
    for attr in get_attrs(ContainersSensors, SensorType.ALARM):
        power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
        sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
        setattr(sensors.containers, attr, 1)
        assert run_monitor(sensors, source) == [
            NotificationEvent(
                message=f"{attr} is raising an alarm",
                source=source,
                dedup_key=attr,
                severity=Severity.CRITICAL,
            )
        ]


def test_fancoil_filter_checks(source):
    for attr in get_attrs(ContainersSensors, SensorType.REPLACE_FILTER_ALARM):
        power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
        sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
        setattr(sensors.containers, attr, 1)
        assert run_monitor(sensors, source) == [
            NotificationEvent(
                message=f"{attr} gone bad",
                source=source,
                dedup_key=attr,
                severity=Severity.CRITICAL,
            )
        ]


def test_weather_station_alarm_checks(source):
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    alarm_value = 50
    sensors.weather.alarm = alarm_value
    assert run_monitor(sensors, source) == [
        NotificationEvent(
            message=f"weather_station is raising an alarm with code {alarm_value}",
            source=source,
            dedup_key="weather_station",
            severity=Severity.CRITICAL,
        )
    ]


def test_water_maker_error_check(source):
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    error_value = 50
    sensors.water_maker.error = 1
    sensors.water_maker.last_error_id = error_value
    assert run_monitor(sensors, source) == [
        NotificationEvent(
            message=f"water maker error with code {error_value}",
            source=source,
            dedup_key="water maker error",
            severity=Severity.ERROR,
        )
    ]


def test_water_maker_warning_check(source):
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    warning_value = 50
    sensors.water_maker.warning = 1
    sensors.water_maker.last_warning_id = warning_value
    assert run_monitor(sensors, source) == [
        NotificationEvent(
            message=f"water maker warning with code {warning_value}",
            source=source,
            dedup_key="water maker warning",
            severity=Severity.WARNING,
        )
    ]


def test_valve_alarm_checks(source):
    for alarm in ValveAlarm:
        for valve_name in [
            field.name
            for field in fields(PowerHubSensors)
            if field.type == ValveSensors or issubclass(field.type, ValveSensors)
        ]:
            power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
            sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
            setattr(getattr(sensors, valve_name), "service_info", alarm.value)
            assert run_monitor(sensors, source) == [
                NotificationEvent(
                    message=f"{valve_name}_{alarm.name.lower()}_alarm is raised",
                    source=source,
                    dedup_key=f"{valve_name}_{alarm.name.lower()}_alarm",
                    severity=Severity.ERROR,
                )
            ]


def test_flow_sensor_alarm_checks(source):
    for alarm in FlowSensorAlarm:
        for flow_sensor_name in [
            field.name for field in fields(PowerHubSensors) if field.type == FlowSensors
        ]:
            power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
            sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
            setattr(getattr(sensors, flow_sensor_name), "service_info", alarm.value)
            assert run_monitor(sensors, source) == [
                NotificationEvent(
                    message=f"{flow_sensor_name}_{alarm.name.lower()}_alarm is raised",
                    source=source,
                    dedup_key=f"{flow_sensor_name}_{alarm.name.lower()}_alarm",
                    severity=Severity.ERROR,
                )
            ]


def test_pump_alarm_checks(source):
    pump_names = [
        appliance_name
        for appliance_name, type in get_type_hints(PowerHubSensors).items()
        if issubclass(type, SmartPumpSensors)
    ]
    assert len(pump_names) != 0
    for pump_name in pump_names:
        for attr in get_attrs(SmartPumpSensors, SensorType.ALARM):
            power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
            sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
            alarm_code = 50
            setattr(getattr(sensors, pump_name), attr, alarm_code)
            assert run_monitor(sensors, source) == [
                NotificationEvent(
                    message=f"{pump_name}_{attr} is raised with code {alarm_code}",
                    source=source,
                    dedup_key=f"{pump_name}_{attr}",
                    severity=Severity.CRITICAL,
                )
            ]


def test_pump_warning_checks(source):
    pump_names = [
        appliance_name
        for appliance_name, type in get_type_hints(PowerHubSensors).items()
        if issubclass(type, SmartPumpSensors)
    ]
    assert len(pump_names) != 0
    for pump_name in pump_names:
        for attr in get_attrs(SmartPumpSensors, SensorType.WARNING):
            power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
            sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
            alarm_code = 50
            setattr(getattr(sensors, pump_name), attr, alarm_code)
            assert run_monitor(sensors, source) == [
                NotificationEvent(
                    message=f"{pump_name}_{attr} is raised with code {alarm_code}",
                    source=source,
                    dedup_key=f"{pump_name}_{attr}",
                    severity=Severity.WARNING,
                )
            ]


def test_rh33_lower_bits_alarm_checks(source):
    for alarm in RH33AlarmLowerBitsValues:
        for rh33_name in [
            field.name for field in fields(PowerHubSensors) if field.type == RH33Sensors
        ]:
            for attr in get_attrs(RH33Sensors, SensorType.ALARM):
                power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
                sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
                setattr(getattr(sensors, rh33_name), attr, alarm.value)

                assert run_monitor(sensors, source) == [
                    NotificationEvent(
                        message=f"{rh33_name}_{attr}_{alarm.name.lower()}_alarm is raised",
                        source=source,
                        dedup_key=f"{rh33_name}_{attr}_{alarm.name.lower()}_alarm",
                        severity=Severity.ERROR,
                    )
                ]


def test_rh33_upper_bits_alarm_checks(source):
    for alarm in RH33AlarmUpperBits:
        for rh33_name in [
            field.name for field in fields(PowerHubSensors) if field.type == RH33Sensors
        ]:
            for attr in get_attrs(RH33Sensors, SensorType.ALARM):
                power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
                sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
                setattr(getattr(sensors, rh33_name), attr, 1 << alarm.value)
                assert run_monitor(sensors, source) == [
                    NotificationEvent(
                        message=f"{rh33_name}_{attr}_{alarm.name.lower()}_alarm is raised",
                        source=source,
                        dedup_key=f"{rh33_name}_{attr}_{alarm.name.lower()}_alarm",
                        severity=Severity.ERROR,
                    )
                ]


def test_rh33_upper_and_lower_alarm_check(source):
    alarm_value = 0b100011  # if 5th bit is set, Upper limit value is violated, if 0+1 is set, there is an Under range
    for rh33_name in [
        field.name for field in fields(PowerHubSensors) if field.type == RH33Sensors
    ]:
        for attr in get_attrs(RH33Sensors, SensorType.ALARM):
            power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
            sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
            setattr(getattr(sensors, rh33_name), attr, alarm_value)

            assert run_monitor(sensors, source) == [
                NotificationEvent(
                    message=f"{rh33_name}_{attr}_{RH33AlarmUpperBits.UPPER_LIMIT_VALUE_VIOLATED.name.lower()}_alarm is raised",
                    source=source,
                    dedup_key=f"{rh33_name}_{attr}_{RH33AlarmUpperBits.UPPER_LIMIT_VALUE_VIOLATED.name.lower()}_alarm",
                    severity=Severity.ERROR,
                ),
                NotificationEvent(
                    message=f"{rh33_name}_{attr}_{RH33AlarmLowerBitsValues.UNDER_RANGE.name.lower()}_alarm is raised",
                    source=source,
                    dedup_key=f"{rh33_name}_{attr}_{RH33AlarmLowerBitsValues.UNDER_RANGE.name.lower()}_alarm",
                    severity=Severity.ERROR,
                ),
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
        before = run_monitor(sensors, source, yazaki_off, power_hub)
        after = run_monitor(sensors, source, yazaki_on, power_hub)
        assert (set(after) - set(before)) == set(
            [
                NotificationEvent(
                    message=f"{dedup_key} is outside valid bounds with value: {out_of_bounds_value}",
                    source=source,
                    dedup_key=dedup_key,
                    severity=Severity.CRITICAL,
                )
            ]
        )

    return _test


def test_yazaki_hot_input_temperature_check(sensors, yazaki_test, out_of_bounds_value):
    sensors.rh33_yazaki_hot.hot_temperature = out_of_bounds_value
    yazaki_test("yazaki_hot_input_temperature_check")


def test_yazaki_hot_flow_check(sensors, yazaki_test, out_of_bounds_value):
    sensors.yazaki_hot_flow_sensor.flow = out_of_bounds_value
    yazaki_test("yazaki_hot_flow_check")


def test_yazaki_hot_pressure_check(sensors, yazaki_test, out_of_bounds_value):
    sensors.pcm_yazaki_pressure_sensor.pressure = out_of_bounds_value
    yazaki_test("yazaki_hot_pressure_check")


def test_yazaki_waste_input_temperature_check(
    sensors, yazaki_test, out_of_bounds_value
):
    sensors.rh33_waste.cold_temperature = out_of_bounds_value
    sensors.waste_switch_valve.position = WASTE_SWITCH_VALVE_YAZAKI_POSITION
    yazaki_test("yazaki_waste_input_temperature_check")


def test_yazaki_waste_flow_check(sensors, yazaki_test, out_of_bounds_value):
    sensors.waste_flow_sensor.flow = out_of_bounds_value
    sensors.waste_switch_valve.position = WASTE_SWITCH_VALVE_YAZAKI_POSITION
    yazaki_test("yazaki_waste_flow_check")


def test_yazaki_waste_pressure_check(sensors, yazaki_test, out_of_bounds_value):
    sensors.waste_pressure_sensor.pressure = out_of_bounds_value
    sensors.waste_switch_valve.position = WASTE_SWITCH_VALVE_YAZAKI_POSITION
    yazaki_test("yazaki_waste_pressure_check")


def test_yazaki_chilled_input_temperature_check(
    sensors, yazaki_test, out_of_bounds_value
):
    sensors.rh33_chill.hot_temperature = out_of_bounds_value
    sensors.chiller_switch_valve.position = WASTE_SWITCH_VALVE_YAZAKI_POSITION
    yazaki_test("yazaki_chilled_input_temperature_check")


def test_yazaki_chilled_flow_check(sensors, yazaki_test, out_of_bounds_value):
    sensors.chilled_flow_sensor.flow = out_of_bounds_value
    sensors.chiller_switch_valve.position = WASTE_SWITCH_VALVE_YAZAKI_POSITION
    yazaki_test("yazaki_chilled_flow_check")


def test_yazaki_chilled_pressure_check(sensors, yazaki_test, out_of_bounds_value):
    sensors.chilled_loop_pump.pressure = out_of_bounds_value
    sensors.chiller_switch_valve.position = WASTE_SWITCH_VALVE_YAZAKI_POSITION
    yazaki_test("yazaki_chilled_pressure_check")


@pytest.fixture
def chiller_on(power_hub, yazaki_off):
    return yazaki_off.replace_control(power_hub.chiller, "on", True)


@pytest.fixture
def chiller_off(power_hub, yazaki_off):
    return yazaki_off.replace_control(power_hub.chiller, "on", False)


@pytest.fixture
def chiller_sensors(sensors: PowerHubSensors):
    sensors.chiller_switch_valve.position = CHILLER_SWITCH_VALVE_CHILLER_POSITION
    sensors.chilled_flow_sensor.flow = 1
    sensors.waste_switch_valve.position = WASTE_SWITCH_VALVE_CHILLER_POSITION
    sensors.waste_flow_sensor.flow = 1
    return sensors


@pytest.fixture
def chiller_test(
    power_hub,
    chiller_sensors: PowerHubSensors,
    chiller_on,
    chiller_off,
    source,
    out_of_bounds_value,
):
    def _test(dedup_key):
        before = run_monitor(chiller_sensors, source, chiller_off, power_hub)
        after = run_monitor(chiller_sensors, source, chiller_on, power_hub)
        assert set(after) - set(before) == set(
            [
                NotificationEvent(
                    message=f"{dedup_key} is outside valid bounds with value: {out_of_bounds_value}",
                    source=source,
                    dedup_key=dedup_key,
                    severity=Severity.CRITICAL,
                )
            ]
        )

    return _test


def test_chiller_waste_input_temperature_check(
    chiller_sensors: PowerHubSensors, chiller_test, out_of_bounds_value
):
    chiller_sensors.rh33_waste.cold_temperature = out_of_bounds_value
    chiller_test("chiller_waste_input_temperature_check")


def test_chiller_waste_flow_check(
    chiller_sensors: PowerHubSensors, chiller_test, out_of_bounds_value
):
    chiller_sensors.waste_flow_sensor.flow = out_of_bounds_value
    chiller_test("chiller_waste_flow_check")


def test_chiller_waste_pressure_check(
    chiller_sensors: PowerHubSensors, chiller_test, out_of_bounds_value
):
    chiller_sensors.waste_pressure_sensor.pressure = out_of_bounds_value
    chiller_test("chiller_waste_pressure_check")


def test_chiller_chilled_input_temperature_check(
    chiller_sensors: PowerHubSensors, chiller_test, out_of_bounds_value
):
    chiller_sensors.rh33_chill.hot_temperature = out_of_bounds_value
    chiller_test("chiller_chilled_input_temperature_check")


def test_chiller_chilled_flow_check(
    chiller_sensors: PowerHubSensors, chiller_test, out_of_bounds_value
):
    chiller_sensors.chilled_flow_sensor.flow = out_of_bounds_value
    chiller_test("chiller_chilled_flow_check")


def test_chiller_chilled_pressure_check(
    chiller_sensors: PowerHubSensors, chiller_test, out_of_bounds_value
):
    chiller_sensors.chilled_loop_pump.pressure = out_of_bounds_value
    chiller_test("chiller_chilled_pressure_check")


def test_chiller_alarm_checks(source):
    for alarm in ChillerAlarm:
        power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
        sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
        setattr(sensors.chiller, "fault_code", 1 << alarm.value)
        assert run_monitor(sensors, source) == [
            NotificationEvent(
                message=f"chiller_{alarm.name.lower()}_alarm is raised",
                source=source,
                dedup_key=f"chiller_{alarm.name.lower()}_alarm",
                severity=Severity.CRITICAL,
            )
        ]


def test_chiller_two_alarm_checks(source):
    fault_code = 8320  # 7th and 13th bits are set
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    setattr(sensors.chiller, "fault_code", fault_code)
    assert run_monitor(sensors, source) == [
        NotificationEvent(
            message=f"chiller_{ChillerAlarm.HIGH_PRESSURE_COMPRESSOR_1_AGAIN.name.lower()}_alarm is raised",
            source=source,
            dedup_key=f"chiller_{ChillerAlarm.HIGH_PRESSURE_COMPRESSOR_1_AGAIN.name.lower()}_alarm",
            severity=Severity.CRITICAL,
        ),
        NotificationEvent(
            message=f"chiller_{ChillerAlarm.COMPRESSOR_TEMPERATURE_SENSOR.name.lower()}_alarm is raised",
            source=source,
            dedup_key=f"chiller_{ChillerAlarm.COMPRESSOR_TEMPERATURE_SENSOR.name.lower()}_alarm",
            severity=Severity.CRITICAL,
        ),
    ]


@pytest.mark.parametrize(
    "water_tank,invalid_tank_fill",
    [
        ("grey_water_tank", 1.1),
        ("fresh_water_tank", 1),
        ("technical_water_tank", 1),
        ("black_water_tank", 1),
    ],
)
def test_tank_checks(water_tank: str, invalid_tank_fill: int, source):
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
    setattr(getattr(sensors, water_tank), "fill_ratio", invalid_tank_fill)
    monitor = Monitor(sensor_value_checks=all_checks, url_health_checks=[])
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
def test_container_sensor_values(sensor_type, alerting_value, source):
    for attr in get_attrs(ContainersSensors, sensor_type):
        power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
        sensors = power_hub.sensors_from_state(power_hub.simple_initial_state())
        setattr(sensors.containers, attr, alerting_value)
        assert run_monitor(sensors, source) == [
            NotificationEvent(
                message=f"{attr} is outside valid bounds with value: {alerting_value}",
                source=source,
                dedup_key=attr,
                severity=Severity.CRITICAL,
            )
        ]


def test_send_events(mocker):
    channel = PagerDutyNotificationChannel("test")
    mocker.patch.object(channel, "send_event")
    notifier = Notifier([channel])
    notifier.send_events([NotificationEvent("test", "test", "test", Severity.CRITICAL)])
    channel.send_event.assert_called_once()  # type: ignore
