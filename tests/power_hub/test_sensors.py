import asyncio
from dataclasses import fields
from datetime import datetime, timezone
from functools import partial
import json
import queue
from pytest import fixture
import pytest
from energy_box_control.config import CONFIG
from energy_box_control.mqtt import run_listener
from energy_box_control.power_hub.control import no_control
from energy_box_control.power_hub.network import PowerHub, PowerHubSchedules
from energy_box_control.power_hub.sensors import sensor_values
from energy_box_control.power_hub_control import queue_on_message
from energy_box_control.sensors import sensors_to_json


@fixture
def power_hub():
    return PowerHub.power_hub(PowerHubSchedules.const_schedules())


@fixture
def sensors(power_hub):
    initial = power_hub.simple_initial_state()
    state = power_hub.simulate(initial, no_control(power_hub))

    return power_hub.sensors_from_state(state)


def test_sensors_to_json_roundtrips(power_hub, sensors):
    sensor_json = sensors_to_json(sensors)
    assert not "power" in json.loads(sensor_json)["heat_pipes"]
    assert "fault_code" in json.loads(sensor_json)["chiller"]
    roundtripped = power_hub.sensors_from_json(sensor_json)
    assert sensors == roundtripped


def test_sensors_to_json_roundtrips_when_stripped(power_hub, sensors):
    sensor_json = sensors_to_json(sensors)

    json_dict = json.loads(sensor_json)
    without_empty_dicts = {k: v for k, v in json_dict.items() if v}

    roundtripped = power_hub.sensors_from_json(json.dumps(without_empty_dicts))

    assert sensors == roundtripped


def test_enriched_sensors_to_json_roundtrips(power_hub, sensors):
    sensor_json = sensors_to_json(sensors, True)
    assert "power" in json.loads(sensor_json)["heat_pipes"]
    roundtripped = power_hub.sensors_from_json(sensor_json)
    assert sensors == roundtripped


def test_sensors_to_json_doesnt_include_is_sensor(sensors):
    returned = json.loads(sensors_to_json(sensors))
    assert all("is_sensor" not in value for value in returned.values())


def test_sensor_values(sensors):
    for field in fields(sensors):
        values = sensor_values(field.name, sensors)
        assert "is_sensor" not in values


def test_chiller_sensor_statuses(sensors):
    sensors.chiller.status = 5
    assert sensors.chiller.statuses() == ["Fan 1", "Inverter/compr."]


@pytest.fixture
def plc_json():
    return """{"time": "1995-01-17T00:00:00.000000+00:00", "heat_pipes": {},"heat_pipes_valve": {"status": 588513280, "position": 6539037.43333333},"heat_pipes_power_hub_pump": {},"heat_pipes_supply_box_pump": {},"hot_switch_valve": {"status": 588513280, "position": 6539037.44444444},"hot_reservoir": {"temperature": 0.0},"pcm": {"temperature": 74.6999969482422},"yazaki_hot_bypass_valve": {"status": 588513280, "position": 6539037.44444444},"yazaki": {"operation_output": true, "error_output": true},"chiller": {"status": 0, "fault_code": 0},"chiller_switch_valve": {"status": 588513280, "position": 6539037.42222222},"cold_reservoir": {"temperature": 0.0},"waste_bypass_valve": {"status": 588513280, "position": 6539036.44444444},"preheat_switch_valve": {"status": 588513282, "position": 6539037.43333333},"preheat_reservoir": {},"waste_switch_valve": {"status": 588513280, "position": 6539037.44444444},"outboard_exchange": {},"weather": {"status": 0, "ambient_temperature": 2011955.2, "global_irradiance": 58851328.0},"pcm_to_yazaki_pump": {"status": 588517605, "pump_alarm": 0, "pump_warning": 0, "pressure": 0.0},"chilled_loop_pump": {"status": 588514219, "pump_alarm": 0, "pump_warning": 0, "pressure": 0.0},"waste_pump": {"status": 588518280, "pump_alarm": 0, "pump_warning": 0},"hot_water_pump": {},"outboard_pump": {},"cooling_demand_pump": {"status": 750, "pump_alarm": 0, "pump_warning": 280, "pressure": 3.0},"pv_panel": {"power": 0.0},"electrical": {"battery_high_internal_temperature_alarm": 0.0, "sim_room_storage_current_L2": 0.0, "high_temperature_alarm": 0.0, "center_1_voltage_L1": 0.0, "kitchen_sanitary_voltage_L3": 0.0, "kitchen_sanitary_current_L2": 0.0, "center_2_voltage_L3": 0.0, "thermo_cabinet_voltage_L1": 0.0, "low_temperature_alarm": 0.0, "thermo_cabinet_voltage_L3": 0.0, "center_1_power_L2": 0.0, "office_power_L2": 0.0, "overload_alarm": 0.0, "supply_box_power_L3": 0.0, "center_2_voltage_L1": 0.0, "workshop_power_L3": 0.0, "office_current_L3": 0.0, "ripple_alarm": 0.0, "workshop_current_L2": 0.0, "battery_error": 0.0, "battery_alarm": 0.0, "high_batt_voltage_alarm": 0.0, "center_2_current_L1": 0.0, "supply_box_voltage_L2": 0.0, "battery_low_soc_alarm": 0.0, "high_battery_voltage_alarm": 0.0, "supply_box_power_L1": 0.0, "workshop_current_L3": 0.0, "office_current_L1": 0.0, "thermo_cabinet_current_L2": 0.0, "office_voltage_L2": 0.0, "battery_internal_failure_alarm": 0.0, "battery_high_temperature_alarm": 0.0, "sim_room_storage_power_L1": 0.0, "battery_fuse_blown_alarm": 0.0, "supply_box_current_L2": 0.0, "high_ac_out_voltage_alarm": 0.0, "battery_high_voltage_alarm": 0.0, "sim_room_storage_power_L3": 0.0, "battery_low_charge_temperature_alarm": 0.0, "kitchen_sanitary_voltage_L2": 0.0, "center_1_voltage_L2": 0.0, "center_2_current_L2": 0.0, "office_power_L1": 0.0, "center_2_power_L3": 0.0, "battery_high_charge_current_alarm": 0.0, "workshop_voltage_L1": 0.0, "estop_active": 0.0, "battery_mid_voltage_alarm": 0.0, "low_ac_out_voltage_alarm": 0.0, "sim_room_storage_current_L3": 0.0, "thermo_cabinet_current_L3": 0.0, "low_batt_voltage_alarm": 0.0, "center_1_power_L3": 0.0, "center_1_power_L1": 0.0, "sim_room_storage_voltage_L1": 0.0, "kitchen_sanitary_current_L3": 0.0, "supply_box_current_L3": 0.0, "workshop_voltage_L2": 0.0, "thermo_cabinet_voltage_L2": 0.0, "battery_high_charge_temperature_alarm": 0.0, "current_battery_system": 0.0, "supply_box_current_L1": 0.0, "center_1_current_L3": 0.0, "office_current_L2": 0.0, "thermo_cabinet_power_L2": 0.0, "sim_room_storage_power_L2": 0.0, "kitchen_sanitary_voltage_L1": 0.0, "workshop_voltage_L3": 0.0, "center_2_power_L2": 0.0, "thermo_cabinet_current_L1": 0.0, "kitchen_sanitary_power_L3": 0.0, "supply_box_power_L2": 0.0, "thermo_cabinet_power_L1": 0.0, "battery_high_starter_voltage_alarm": 0.0, "kitchen_sanitary_power_L1": 0.0, "sim_room_storage_current_L1": 0.0, "thermo_cabinet_power_L3": 0.0, "power_battery_system": 0.0, "workshop_power_L1": 0.0, "center_2_power_L1": 0.0, "battery_low_temperature_alarm": 0.0, "battery_low_cell_voltage_alarm": 0.0, "center_1_current_L2": 0.0, "low_battery_voltage_alarm": 0.0, "supply_box_voltage_L3": 0.0, "office_power_L3": 0.0, "soc_battery_system": 0.0, "center_2_voltage_L2": 0.0, "battery_low_starter_voltage_alarm": 0.0, "battery_low_fused_voltage_alarm": 0.0, "center_1_current_L1": 0.0, "battery_high_fused_voltage_alarm": 0.0, "center_1_voltage_L3": 0.0, "battery_low_voltage_alarm": 0.0, "center_2_current_L3": 0.0, "battery_cell_imbalance_alarm": 0.0, "workshop_current_L1": 0.0, "office_voltage_L3": 0.0, "office_voltage_L1": 0.0, "voltage_battery_system": 0.0, "sim_room_storage_voltage_L3": 0.0, "battery_high_discharge_current_alarm": 0.0, "supply_box_voltage_L1": 0.0, "workshop_power_L2": 0.0, "kitchen_sanitary_power_L2": 0.0, "kitchen_sanitary_current_L1": 0.0, "sim_room_storage_voltage_L2": 0.0},"fresh_water_tank": {"fill_ratio": 0.0},"grey_water_tank": {"fill_ratio": 0.0},"black_water_tank": {"fill_ratio": 0.0},"technical_water_tank": {"fill_ratio": 0.0},"water_treatment": {},"water_maker": {"status": 0, "feed_pressure": 0.0, "membrane_pressure": 0.0, "production_flow": 0.0, "cumulative_operation_time": 0.0, "salinity": 0.0, "time_to_service": 0.0, "total_production": 0.0, "current_production": 0.0, "tank_empty": false, "last_error_id": 0.0, "last_warning_id": 0.0, "current_error_id": 0.0, "current_warning_id": 0.0},"containers": {"kitchen_ventilation_error": 0.0, "kitchen_co2": 0.0, "simulator_storage_co2": 0.0, "simulator_storage_humidity": 0.0, "power_hub_humidity": 0.0, "office_ventilation_error": 0.0, "office_temperature": 29.0, "kitchen_temperature": 26.0, "office_humidity": 0.0, "supply_box_temperature": 0.0, "kitchen_humidity": 0.0, "simulator_storage_temperature": 28.0, "simulator_storage_ventilation_filter_status": 0.0, "simulator_storage_ventilation_error": 0.0, "power_hub_temperature": 0.0, "office_co2": 0.0, "sanitary_temperature": 29.0, "kitchen_ventilation_filter_status": 0.0, "supply_box_humidity": 0.0, "office_ventilation_filter_status": 0.0},"waste_pressure_sensor": {"pressure": 1.37890625},"pipes_pressure_sensor": {"pressure": 1.298828125},"pcm_yazaki_pressure_sensor": {"pressure": 2.224609375},"technical_water_regulator": {"status": 0, "position": 0.0},"water_filter_bypass_valve": {"status": 0, "position": 0.0},"heat_pipes_flow_sensor": {"status": 0, "flow": 6.6, "temperature": 94.38, "glycol_concentration": 0.0, "total_volume": 1.63},"pcm_discharge_flow_sensor": {"status": 0, "flow": 29.4, "temperature": 68.24, "glycol_concentration": 1.5e-1, "total_volume": 10.74},"hot_storage_flow_sensor": {"status": 128, "flow": 0.0, "temperature": 78.38, "glycol_concentration": 0.0, "total_volume": 4.83},"yazaki_hot_flow_sensor": {"status": 0, "flow": 29.4, "temperature": 75.6, "glycol_concentration": 1.2e-1, "total_volume": 13.98},"waste_flow_sensor": {"status": 0, "flow": 147.0, "temperature": 29.61, "glycol_concentration": 1.39, "total_volume": 662.7},"chilled_flow_sensor": {"status": 0, "flow": 43.2, "temperature": 31.55, "glycol_concentration": 1.0e-2, "total_volume": 552.23},"cooling_demand_flow_sensor": {"status": 0, "flow": 0.0, "temperature": 29.13, "glycol_concentration": 7.0e-2, "total_volume": 7.99},"heat_dump_flow_sensor": {"status": 0, "flow": 147.6, "temperature": 28.29, "glycol_concentration": 0.0, "total_volume": 671.73},"domestic_hot_water_flow_sensor": {"status": 65664, "flow": 39321.6, "temperature": 690.44, "glycol_concentration": 655.36, "total_volume": 0.0},"fresh_to_kitchen_flow_sensor": {"status": 0, "flow": 0.0, "temperature": 38.43, "glycol_concentration": 0.0, "total_volume": 1.4e-1},"technical_to_sanitary_flow_sensor": {"status": 0, "flow": 0.0, "temperature": 30.91, "glycol_concentration": 1.6e-1, "total_volume": 1.5e-1},"technical_to_wash_off_flow_sensor": {"status": 0, "flow": 0.0, "temperature": 31.69, "glycol_concentration": 7.0e-2, "total_volume": 1.3e-1},"fresh_to_technical_flow_sensor": {"status": 0, "flow": 0.0, "temperature": 32.02, "glycol_concentration": 2.0e-2, "total_volume": 3.7e-1},"treated_water_flow_sensor": {"status": 65536, "flow": 39321.6, "temperature": 691.3, "glycol_concentration": 655.36, "total_volume": 2.0e-2},"rh33_pcm_discharge": {"hot_temperature": 74.6760101318359, "hot_temperature_status": 0, "cold_temperature": 68.223274230957, "cold_temperature_status": 0, "delta_temperature": 6.45273590087891, "delta_temperature_status": 0},"rh33_preheat": {"hot_temperature": 29.5737705230713, "hot_temperature_status": 0, "cold_temperature": 32.0126800537109, "cold_temperature_status": 0, "delta_temperature": -2.43890953063965, "delta_temperature_status": 0},"rh33_domestic_hot_water": {"hot_temperature": 34.7079620361328, "hot_temperature_status": 0, "cold_temperature": 36.0485038757324, "cold_temperature_status": 0, "delta_temperature": -1.34054183959961, "delta_temperature_status": 0},"rh33_heat_pipes": {"hot_temperature": 81.0863037109375, "hot_temperature_status": 0, "cold_temperature": 79.22802734375, "cold_temperature_status": 0, "delta_temperature": 1.8582763671875, "delta_temperature_status": 0},"rh33_hot_storage": {"hot_temperature": 74.6284484863281, "hot_temperature_status": 0, "cold_temperature": 87.262580871582, "cold_temperature_status": 0, "delta_temperature": -12.6341323852539, "delta_temperature_status": 0},"rh33_yazaki_hot": {"hot_temperature": 75.2038879394531, "hot_temperature_status": 0, "cold_temperature": 68.595832824707, "cold_temperature_status": 0, "delta_temperature": 6.60805511474609, "delta_temperature_status": 0},"rh33_waste": {"hot_temperature": 29.5862655639648, "hot_temperature_status": 0, "cold_temperature": 28.2897605895996, "cold_temperature_status": 0, "delta_temperature": 1.29650497436523, "delta_temperature_status": 0},"rh33_chill": {"hot_temperature": 31.7944297790527, "hot_temperature_status": 0, "cold_temperature": 31.6893672943115, "cold_temperature_status": 0, "delta_temperature": 1.21654046086485e76, "delta_temperature_status": 0},"rh33_heat_dump": {"hot_temperature": 29.3820552825928, "hot_temperature_status": 0, "cold_temperature": 28.3399181365967, "cold_temperature_status": 0, "delta_temperature": 1.04213714599609, "delta_temperature_status": 0},"rh33_cooling_demand": {"hot_temperature": 30.215238571167, "hot_temperature_status": 0, "cold_temperature": 30.9194049835205, "cold_temperature_status": 0, "delta_temperature": -8.15369000571591e76, "delta_temperature_status": 0}}"""


@pytest.mark.skip()
def test_plc_json_to_sensor_parse(plc_json, power_hub):
    power_hub.sensors_from_json(plc_json)


@pytest.mark.skip()
def test_compare_plc_sensors(plc_json, power_hub):
    state = power_hub.simulate(
        power_hub.simple_initial_state(start_time=datetime.now(tz=timezone.utc)),
        no_control(power_hub),
    )
    sensors = power_hub.sensors_from_state(state)
    plc = json.loads(plc_json)
    control = json.loads(sensors_to_json(sensors))
    extra_in_plc = compare_dicts(plc, control, "control")
    extra_in_control = compare_dicts(control, plc, "plc")
    assert len(extra_in_plc) == 0 and len(extra_in_control) == 0


def compare_dicts(dict1, dict2, dict2_name):
    missing = []
    for key, value in dict1.items():
        if key not in dict2:
            missing.append(f"{key} not in {dict2_name}")
        else:
            if type(value) == dict:
                for key1, value1 in value.items():
                    if key1 not in dict2[key]:
                        missing.append(f"{key1} not in {dict2_name} {key}")
    return missing


sensor_values_queue: queue.Queue[str] = queue.Queue()
SENSOR_VALUES_TOPIC = "power_hub/sensor_values"


async def get_message():
    await run_listener(
        SENSOR_VALUES_TOPIC, partial(queue_on_message, sensor_values_queue)
    )
    return sensor_values_queue.get(block=True)


@pytest.fixture
def prod_plc_dict():
    CONFIG.mqtt_host = "vernemq.prod.power-hub.foundationzero.org"
    CONFIG.mqtt_port = 8883
    CONFIG.mqtt_tls_enabled = True
    CONFIG.mqtt_tls_path = "./plc/vernemq/bridge/certificate/ISRG_ROOT_X1.crt"
    return json.loads(asyncio.run(get_message()).replace("#Inf", "0"))


@pytest.mark.skip()
def test_compare_prod_plc_sensors(prod_plc_dict):
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())

    state = power_hub.simulate(
        power_hub.simple_initial_state(start_time=datetime.now(tz=timezone.utc)),
        no_control(power_hub),
    )
    sensors = power_hub.sensors_from_state(state)

    control = json.loads(sensors_to_json(sensors))
    extra_in_plc = compare_dicts(prod_plc_dict, control, "control")
    extra_in_control = compare_dicts(control, prod_plc_dict, "plc")
    assert len(extra_in_plc) == 0 and len(extra_in_control) == 0


@pytest.mark.skip()
def test_prod_plc_zeroes(prod_plc_dict):
    contains_zero = [
        f"{appliance_key}.{field_key}"
        for appliance_key, appliance_value in prod_plc_dict.items()
        if isinstance(appliance_value, dict)
        for field_key, field_value in appliance_value.items()
        if field_value == 0
        and field_key not in ["status", "fault_code", "pump_alarm", "pump_warning"]
    ]
    assert len(contains_zero) == 0
